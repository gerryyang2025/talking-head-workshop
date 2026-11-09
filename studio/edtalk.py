"""EDTalk's 256 px audio-to-lip ONNX model on the project's 25 fps master clock."""

import cv2 as cv
import numpy as np
import onnxruntime as ort
from scipy import signal

from .engine import FaceLandmarks, mouth_mask
from .media import FPS, MODELS
from .mouth_rest import lip_contours, lip_offsets, mouth_geometry, smoothstep
from .setup_models import EDTALK_FILE


# On the 25 fps master clock, SyncNet finds the published forward-looking
# window anticipates articulation by roughly two frames on the demo narration.
AUDIO_LOOKBACK_FRAMES = 2


def mel_features(wav16):
    # The published ONNX uses peak-normalized PCM and unnormalized HTK bands.
    wave = np.asarray(wav16, dtype=np.float32)
    wave = wave / max(float(np.max(np.abs(wave), initial=0)), 1e-7)
    wave = np.pad(wave, (0, max(0, 800 - len(wave))))
    wave[1:] -= .97 * wave[:-1]
    spectrum = np.abs(signal.stft(wave, nperseg=800, noverlap=600, nfft=800)[2])
    mel_bounds = 2595 * np.log10(1 + np.array([55., 7600.]) / 700)
    hz = 700 * (10 ** (np.linspace(*mel_bounds, 82) / 2595) - 1)
    edges = np.floor(801 * hz / 16000).astype(int)
    filters = np.zeros((80, 401), dtype=np.float32)
    # This ONNX frontend uses one adjacent-bin interval per channel.
    for band, (lo, hi) in enumerate(zip(edges[:80], edges[1:81])):
        filters[band, lo:hi] = signal.windows.triang(hi - lo)
    features = np.log10(np.maximum(filters @ spectrum, 1e-5)) * 1.6 + 3.2
    return np.clip(features, -4, 4)


def audio_window(features, frame):
    # 80 mel columns per second, 16 per prediction. Outside the track is silence.
    start = frame * 80 // FPS
    stop = start + 16
    window = np.full((1, 1, 80, 16), -4, dtype=np.float32)
    first, last = max(0, start), min(stop, features.shape[1])
    if first < last:
        window[0, 0, :, first - start:last - start] = features[:, first:last]
    return window


def restore_tooth_detail(transported, predicted, source_contours, target_contours, inside, edge, v, sigma):
    """Transfer luminance texture only where both open mouths show a tooth surface."""
    src_gap = source_contours[2] - source_contours[1]
    top, upper, lower, bottom = target_contours
    dst_gap = lower - upper
    # Work in normalized mouth coordinates (corner distance 78). Suppress
    # stretched texture when one mouth is shut or the two openings disagree.
    smaller = np.minimum(src_gap, dst_gap)
    ratio = smaller / np.maximum(1., np.maximum(src_gap, dst_gap))
    weight = smoothstep((smaller - 4) / 5) * smoothstep((ratio - .45) / .35)
    weight *= smoothstep(inside / 2) * smoothstep(edge / 8)
    if not weight.any():
        return predicted

    lip = (edge > 8) & (((v > top) & (v < upper)) | ((v > lower) & (v < bottom)))
    if not lip.any():
        return predicted
    # Teeth are typically brighter and less red than the adjacent lip in
    # the same frame. Compare locally so skin tone and exposure can vary.
    luminance = cv.cvtColor(transported, cv.COLOR_BGR2GRAY)
    for image, light in ((transported, luminance), (predicted, cv.cvtColor(predicted, cv.COLOR_BGR2GRAY))):
        tooth = light - (image[..., 2] - image[..., 1])
        weight *= smoothstep((tooth - np.median(tooth[lip]) - 8) / 28)

    detail = luminance - cv.GaussianBlur(luminance, (0, 0), sigma)
    return predicted + (weight * np.clip(detail, -18, 18))[..., None]


def align_lip_texture(image, points, target, u, v, target_contours):
    geometry = mouth_geometry(points)
    if geometry is None:
        return None
    corners = np.linalg.norm(target[[48, 54]] - points[[48, 54]], axis=1)
    if corners.max() > .35 * np.linalg.norm(points[54] - points[48]):
        return None
    _, mat = geometry
    contours = lip_contours(cv.transform(points[None], mat)[0], u)
    if contours is None:
        return None
    source_y = v + lip_offsets(v, contours, target_contours)
    inv = cv.invertAffineTransform(mat)
    xmap = inv[0, 0] * u + inv[0, 1] * source_y + inv[0, 2]
    ymap = inv[1, 0] * u + inv[1, 1] * source_y + inv[1, 2]
    aligned = cv.remap(image, xmap, ymap, cv.INTER_LINEAR, borderMode=cv.BORDER_REPLICATE)
    return aligned.astype(np.float32), contours


def separate_upper_lip(composite, native, predicted, contours, delta, edge, xx, yy, normal, closed):
    """Resolve the occluding upper lip only where a closed source opens onto visible teeth."""
    top, upper, lower, _ = contours
    gap = lower - upper
    band = smoothstep((delta + 7) / 4) * (1 - smoothstep((delta - 2) / 4))
    gate = closed * smoothstep((gap - 3.5) / 6) * smoothstep(edge / 7)
    gate *= band * smoothstep((upper - top - 2) / 4)
    if not gate.any():
        return composite

    # Offsets follow the mouth normal, in the same normalized units as the lip contours.
    def sample(image, offset):
        return cv.remap(image, xx + normal[0] * offset, yy + normal[1] * offset,
                        cv.INTER_LINEAR, borderMode=cv.BORDER_REPLICATE)

    def dental_tone(image):
        blue, green, red = cv.split(image)
        return (green + blue) * .5 - (red - green)

    depth = np.clip(.43 * gap, 0, 5)
    inner = sample(predicted, depth - delta)
    lip_probe = -np.clip((upper - top) * .46, 1, 4) - delta
    # During opening, the first visible tooth can sit below the upper-lip shadow.
    deeper = sample(predicted, np.clip(.76 * gap, 0, 16) - delta)
    tone = np.maximum(dental_tone(inner), dental_tone(deeper))
    confidence = smoothstep((tone - dental_tone(sample(native, lip_probe)) - 7) / 28)
    confidence *= smoothstep((tone - dental_tone(sample(predicted, lip_probe)) - 3) / 20)
    # Adjacent visible teeth support the lip edge across an interdental shadow.
    local_confidence = confidence
    reliable = (abs(delta) < 1.5) & (edge > 6) & (gap > 6)
    if reliable.any():
        support = np.percentile(confidence[reliable], 75)
        confidence = np.maximum(confidence, .76 * support)
    confidence = cv.GaussianBlur(confidence, (0, 0), max(1., 3.3 * np.linalg.norm(normal)))

    # Sample the native upper surface above the original contact line. Draw the
    # tooth side from inside the generated cavity, beyond its mixed edge pixels.
    lip = sample(native, np.minimum(0, -.85 - delta))
    inward = np.clip(depth - delta, 0, 2.7) * smoothstep((depth - delta) / 2)
    teeth = sample(composite, inward * local_confidence)
    coverage = smoothstep((delta + .8) / 1.75)[..., None]
    separated = lip + coverage * (teeth - lip)
    return composite + (gate * confidence)[..., None] * (separated - composite)


def restore_lip_surfaces(original, generated, source_points, target_points, detail_view=None):
    dst = mouth_geometry(target_points)
    if dst is None:
        return generated
    _, mat = dst
    target_lips = cv.transform(target_points[None], mat)[0]
    yy, xx = np.indices(original.shape[:2], dtype=np.float32)
    u = mat[0, 0] * xx + mat[0, 1] * yy + mat[0, 2]
    v = mat[1, 0] * xx + mat[1, 1] * yy + mat[1, 2]
    target_contours = lip_contours(target_lips, u)
    if target_contours is None:
        return generated
    aligned = align_lip_texture(original, source_points, target_points, u, v, target_contours)
    if aligned is None:
        return generated
    native, source_contours = aligned
    upper, lower = target_contours[1:3]
    edge = np.minimum(u - target_lips[48, 0], target_lips[54, 0] - u)
    inside = np.minimum(np.minimum(v - upper, lower - v), edge)
    cavity = smoothstep((inside + 2) / 4)[..., None]
    # Keep the model's volume and shading around the opening. Recover only
    # the fine surface texture there, so landmark noise cannot redraw a lip edge.
    sigma = max(1., np.linalg.norm(source_points[54] - source_points[48]) / 24)
    predicted = generated.astype(np.float32)
    residual = cv.GaussianBlur(predicted - native, (0, 0), sigma)
    top, bottom = target_contours[0], target_contours[3]
    rim = smoothstep((v - top + 5) / 7) * smoothstep((bottom + 5 - v) / 7)
    rim *= smoothstep((edge + 4) / 8)
    surface = native + (.70 * rim[..., None]) * residual
    interior = restore_tooth_detail(native, predicted, source_contours, target_contours, inside, edge, v, sigma)
    if detail_view is not None:
        detail, points, strength = detail_view
        aligned = align_lip_texture(detail, points, target_points, u, v, target_contours)
        if aligned is not None:
            texture, contours = aligned
            enhanced = restore_tooth_detail(texture, predicted, contours, target_contours, inside, edge, v, sigma)
            interior = interior + strength * (enhanced - predicted)
    composite = surface * (1 - cavity) + interior * cavity
    source_gap = mouth_geometry(source_points)[0]
    closed = smoothstep((.105 - source_gap) / .06)
    if closed > 0:
        inner_edge = np.minimum(u - target_lips[60, 0], target_lips[64, 0] - u)
        composite = separate_upper_lip(composite, native, predicted, target_contours, v - upper,
                                       inner_edge, xx, yy, cv.invertAffineTransform(mat)[:, 1], closed)
    return np.rint(composite).clip(0, 255).astype(np.uint8)


class EDTalkEngine(FaceLandmarks):
    def __init__(self, wav16):
        super().__init__()
        self.audio = mel_features(wav16)
        self.weight = np.array([.85], dtype=np.float32)
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = 4
        self.model = ort.InferenceSession(
            str(MODELS / EDTALK_FILE), opts, providers=["CPUExecutionProvider"]
        )

    def prepare(self, frame, pts, zoom=1.):
        # Map the eyes, nose and mouth corners to the model's FFHQ portrait crop.
        anchors = np.float32([pts[36:42].mean(0), pts[42:48].mean(0), pts[30], pts[48], pts[54]])
        template = np.float32([[.37692, .46865], [.62286, .46913], [.50124, .61332],
                               [.39309, .72541], [.61150, .72490]]) * 256
        matrix, _ = cv.estimateAffinePartial2D(anchors, template, method=cv.RANSAC, ransacReprojThreshold=50.0)
        if matrix is None or not np.isfinite(matrix).all():
            raise ValueError("EDTalk 无法对齐人脸，请选择五官清晰的近景")
        # Give lip edges more model pixels while retaining both eyes and the
        # nose as pose anchors. Keep the mouth at its trained FFHQ location.
        mouth = pts[48:60].mean(axis=0)
        pivot = matrix[:, :2] @ mouth + matrix[:, 2]
        matrix *= zoom
        matrix[:, 2] += (1 - zoom) * pivot
        crop = cv.warpAffine(frame, matrix * 2, (512, 512), borderMode=cv.BORDER_REPLICATE)
        crop = cv.resize(crop, (256, 256), interpolation=cv.INTER_AREA)
        rgb = cv.cvtColor(crop, cv.COLOR_BGR2RGB).transpose(2, 0, 1)[None].astype(np.float32) / 255
        lips = pts[48:60]
        width = max(8., float(np.ptp(lips[:, 0])))
        center = (lips.min(0) + lips.max(0)) / 2
        h, w = frame.shape[:2]
        x, y = np.maximum(0, np.floor(center - width)).astype(int)
        r, b = np.minimum([w, h], np.ceil(center + width)).astype(int)
        if r <= x or b <= y:
            raise ValueError("嘴部不在画面内")
        inverse = cv.invertAffineTransform(matrix)
        inverse[:, 2] -= (x, y)
        box = (x, y, r, b)
        return rgb, inverse, box, mouth_mask(lips, box), pts

    def predict(self, frame, geometry, mel):
        rgb, inverse, (x, y, r, b), alpha, _ = geometry
        result = self.model.run(None, {"source": mel, "target": rgb, "weight": self.weight})[0]
        rgb_patch = np.rint(result[0].transpose(1, 2, 0).clip(0, 1) * 255).astype(np.uint8)
        patch = cv.warpAffine(cv.cvtColor(rgb_patch, cv.COLOR_RGB2BGR), inverse, (r-x, b-y),
                              flags=cv.INTER_CUBIC, borderMode=cv.BORDER_REPLICATE)
        composite = frame.copy()
        base = composite[y:b, x:r]
        base[:] = np.rint(base * (1 - alpha) + patch * alpha).astype(np.uint8)
        try:
            points = self.landmarks(composite) - np.float32([x, y])
        except ValueError:
            points = None
        return patch, points

    def sync(self, frames, indexes, shift, fixed, state):
        for frame, index in zip(frames, indexes):
            if fixed and "geometry" in state:
                geometry = state["geometry"]
            else:
                geometry = self.prepare(frame, self.track(frame, state))
                if fixed:
                    state["geometry"] = geometry
            _, _, (x, y, r, b), alpha, points = geometry
            mel = audio_window(self.audio, index - shift - AUDIO_LOOKBACK_FRAMES)
            patch, predicted = self.predict(frame, geometry, mel)
            base = frame[y:b, x:r]
            if predicted is not None:
                source_points = points - np.float32([x, y])
                src, dst = mouth_geometry(source_points), mouth_geometry(predicted)
                detail_view = None
                if src is not None and dst is not None:
                    # For a closed source opening into a vowel, sample dental
                    # texture at a second scale. Both passes use the same mel.
                    strength = smoothstep((.11 - src[0]) / .06) * smoothstep((dst[0] - .06) / .06)
                    if strength > 0:
                        detail_geometry = state.get("detail_geometry") if fixed else None
                        if detail_geometry is None:
                            detail_geometry = self.prepare(frame, points, zoom=1.25)
                            if fixed:
                                state["detail_geometry"] = detail_geometry
                        detail, detail_points = self.predict(frame, detail_geometry, mel)
                        if detail_points is not None:
                            detail_view = detail, detail_points, strength
                patch = restore_lip_surfaces(base, patch, source_points, predicted, detail_view)
            base[:] = np.rint(base * (1 - alpha) + patch * alpha).astype(np.uint8)

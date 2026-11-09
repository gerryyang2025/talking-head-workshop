"""Audio-conditioned face crops at the source resolution. Imported only for speaking shots."""

import cv2 as cv
import numpy as np
import onnxruntime as ort

from .media import MODELS, FPS


class FaceLandmarks:
    def __init__(self):
        self.detector = cv.FaceDetectorYN.create(
            str(MODELS / "studio/yunet.onnx"), "", (512, 512), 0.82
        )
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = 2
        ort.disable_telemetry_events()
        self.fan = ort.InferenceSession(
            str(MODELS / "studio/2dfan4.onnx"), opts, providers=["CPUExecutionProvider"]
        )

    def landmarks(self, frame):
        h, w = frame.shape[:2]
        scale = 512 / max(h, w)
        rw, rh = max(1, round(w * scale)), max(1, round(h * scale))
        small = np.zeros((512, 512, 3), np.uint8)
        small[:rh, :rw] = cv.resize(frame, (rw, rh))
        faces = self.detector.detect(small)[1]
        if faces is None or len(faces) != 1:
            raise ValueError(
                "镜头需要一张清晰、未遮挡的人脸，请检查多人、侧身或无脸的切片。"
            )
        x, y, fw, fh = faces[0, :4] / scale
        k = 195 / max(fw, fh)
        mat = np.float32(
            [[k, 0, 128 - (x + fw / 2) * k], [0, k, 128 - (y + fh / 2) * k]]
        )
        sample = (
            cv.warpAffine(frame, mat, (256, 256))
            .transpose(2, 0, 1)[None]
            .astype(np.float32)
            / 255
        )
        raw = self.fan.run(None, {self.fan.get_inputs()[0].name: sample})
        pts = next(o for o in raw if o.ndim == 3)[0, :, :2] * 4
        return cv.transform(pts[None], cv.invertAffineTransform(mat))[0]

    def track(self, frame, state):
        pts = self.landmarks(frame)
        if "pts" in state and np.mean(np.abs(pts - state["pts"])) < 3:
            pts = 0.72 * pts + 0.28 * state["pts"]
        state["pts"] = pts
        return pts


def mouth_mask(lips, box):
    x, y, r, b = box
    cx, cy = (lips.max(0) + lips.min(0)) / 2
    width = max(8.0, float(lips[:, 0].max() - lips[:, 0].min()))
    yy, xx = np.ogrid[y:b, x:r]
    distance = np.sqrt(
        ((xx - cx) / (0.88 * width)) ** 2
        + ((yy - cy - width * 0.09) / (0.78 * width)) ** 2
    )
    mask = np.clip((1 - distance) / 0.32, 0, 1).astype(np.float32)
    return (mask * mask * (3 - 2 * mask))[..., None]


class MouthEngine(FaceLandmarks):
    def __init__(self, wav16):
        import mlx.core as mx
        from musetalk_mlx.pipeline_mlx import MuseTalkPipeline
        from musetalk_mlx.whisper.log_mel import log_mel_spectrogram, N_SAMPLES
        from musetalk_mlx.whisper.audio2feature import get_whisper_chunk

        super().__init__()
        self.mx = mx
        self.pipe = MuseTalkPipeline.from_pretrained_mlx(MODELS / "musetalk-1.5-fp16")
        embeddings = [
            self.pipe.whisper_encoder(
                log_mel_spectrogram(mx.array(wav16[i : i + N_SAMPLES])).astype(
                    mx.float16
                )
            )
            for i in range(0, len(wav16), N_SAMPLES)
        ]
        self.audio = get_whisper_chunk(
            mx.concatenate(embeddings, axis=1), len(wav16), fps=FPS
        ).astype(mx.float16)
        mx.eval(self.audio)

    def face(self, frame, pts):
        h, w = frame.shape[:2]
        lo, hi = pts.min(0), pts.max(0)
        x, y = max(0, round(float(lo[0]))), max(0, round(float(2 * pts[29, 1] - hi[1])))
        r, b = (
            min(w, round(float(hi[0]))),
            min(h, round(float(hi[1] + (hi[1] - lo[1]) * 0.03))),
        )
        if min(r - x, b - y) < 32:
            raise ValueError("人脸有效区域过小，请选择近一些的镜头")
        crop = cv.resize(frame[y:b, x:r], (256, 256), interpolation=cv.INTER_AREA)
        box = (x, y, r, b)
        return crop, box, mouth_mask(pts[48:60], box)

    def sync(self, frames, indexes, shift, fixed, state):
        latents, regions = [], []
        for f in frames:
            if fixed and "geometry" in state:
                latent, region = state["geometry"]
            else:
                # Track on each moving frame so a different speaker is never silently selected.
                pts = self.track(f, state)
                crop, box, alpha = self.face(f, pts)
                latent = self.pipe.get_latents_for_unet(crop).astype(self.mx.float16)
                region = box, alpha
                if fixed:
                    state["geometry"] = latent, region
            regions.append(region)
            latents.append(latent)
        ix = self.mx.array(
            [max(0, min(len(self.audio) - 1, i - shift)) for i in indexes]
        )
        pred = self.pipe.generate_faces(self.mx.concatenate(latents), self.audio[ix])
        for frame, generated, ((x, y, r, b), alpha) in zip(frames, pred, regions):
            patch = cv.resize(
                generated, (r - x, b - y), interpolation=cv.INTER_CUBIC
            ).astype(np.float32)
            base = frame[y:b, x:r]
            base[:] = (
                np.rint(patch * alpha + base * (1 - alpha))
                .clip(0, 255)
                .astype(np.uint8)
            )

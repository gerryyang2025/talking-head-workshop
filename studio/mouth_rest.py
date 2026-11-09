"""Settle the current lips and jaw during sustained quiet in the locked narration."""
import cv2 as cv
import numpy as np

from .media import FPS


def smoothstep(t):
    t = np.clip(t, 0., 1.)
    return t * t * (3 - 2 * t)


def rest_weights(samples, frames, fps, rate, spans):
    per_frame = rate // fps
    samples = np.pad(samples[:frames * per_frame], (0, max(0, frames * per_frame - len(samples))))
    rms = np.sqrt(np.mean(samples.reshape(frames, per_frame) ** 2, axis=1))
    threshold = min(.0025, max(.0001, np.percentile(rms, 95) * .04))
    quiet = rms <= threshold
    gaps = np.zeros(frames, dtype=bool)
    for span in spans:
        if not span["voiced"]:
            gaps[span["first"]:span["stop"]] = True

    # A faint breath or recording noise between two stretches of genuine silence
    # at a sentence boundary should not restart the mouth for one or two frames.
    for first, stop in np.flatnonzero(np.diff(~quiet, prepend=False, append=False)).reshape(-1, 2):
        if (stop - first <= 2 and first >= 3 and stop + 3 <= frames
                and quiet[first-3:first].all() and quiet[stop:stop+3].all()
                and gaps[max(0, first-5):min(frames, stop+5)].any()
                and rms[first:stop].max() <= threshold * 3.2):
            quiet[first:stop] = True

    weights = np.zeros(frames, dtype=np.float32)
    for first, stop in np.flatnonzero(np.diff(quiet, prepend=False, append=False)).reshape(-1, 2):
        if stop - first < 6 and not gaps[first:stop].any():
            continue
        # Start settling in the falling tail only if it is already very soft.
        start = first
        while start > max(0, first - 3) and rms[start] <= rms[start-1] <= threshold * 6:
            start -= 1
        i = np.arange(start, stop)
        attack = (i - start + 1) / 6 if start else 1.
        release = (stop - i) / 4 if stop < frames else 1.
        weights[start:stop] = smoothstep(np.minimum(attack, release))
    return weights


CENTER = np.float32([72, 46])


def mouth_geometry(points):
    axis = points[54] - points[48]
    width = np.linalg.norm(axis)
    if width < 8:
        return None
    unit = axis / width
    normal = np.array([-unit[1], unit[0]])
    gap = np.mean((points[[67, 66, 65]] - points[[61, 62, 63]]) @ normal) / width
    transform = np.stack([unit, normal]) * (78 / width)
    offset = CENTER - transform @ ((points[48] + points[54]) / 2)
    return float(gap), np.column_stack([transform, offset]).astype(np.float32)


def lip_contours(points, x):
    contours = []
    for indices in ([48, 49, 50, 51, 52, 53, 54], [60, 61, 62, 63, 64],
                    [60, 67, 66, 65, 64], [48, 59, 58, 57, 56, 55, 54]):
        line = points[indices]
        if np.any(np.diff(line[:, 0]) <= 0):
            return None
        contours.append(np.interp(x, line[:, 0], line[:, 1]).astype(np.float32))
    return np.stack(contours)


def lip_offsets(y, src, dst):
    # Sample the lip surfaces and oral cavity separately. This lets the lips
    # meet without fading teeth into a closed mouth or stretching the lower lip.
    top, _, _, bottom = dst
    offset = (src[0] - top) * smoothstep(1 - (top - y) / 19)
    for k in range(3):
        a, b = dst[k:k+2]
        t = np.clip((y - a) / np.maximum(.001, b-a), 0., 1.)
        offset = np.where(y >= a, src[k] + t * (src[k+1] - src[k]) - y, offset)
    return np.where(y >= bottom, (src[3] - bottom) * smoothstep(1 - (y - bottom) / 34), offset)


def settle_lips(frame, points, amount, rest=None):
    geometry = mouth_geometry(points)
    if geometry is None or geometry[0] <= .025 or amount <= 0:
        return frame
    gap, mat = geometry
    lips = cv.transform(points[None], mat)[0]
    inverse = cv.invertAffineTransform(mat)
    corners = cv.transform(np.float32([[[0, 0], [144, 0], [144, 96], [0, 96]]]), inverse)[0]
    x, y = np.maximum(0, np.floor(corners.min(axis=0)).astype(int))
    r, b = np.minimum(frame.shape[1::-1], np.ceil(corners.max(axis=0)).astype(int))
    if r <= x or b <= y:
        return frame
    yy, xx = np.mgrid[y:b, x:r].astype(np.float32)
    u = xx * mat[0, 0] + yy * mat[0, 1] + mat[0, 2]
    v = xx * mat[1, 0] + yy * mat[1, 1] + mat[1, 2]
    src = lip_contours(lips, u)
    if src is None:
        return frame
    top, upper, lower, bottom = src
    opening = np.maximum(0, lower - upper)
    contact = upper + .28 * opening
    # With no recorded rest pose, move the jaw farther than the upper lip.
    neutral = np.stack([contact - .86 * (upper-top), contact, contact,
                        contact + .80 * (bottom-lower)])
    reference = lip_contours(rest[0], u) if rest is not None else None
    if reference is not None:
        neutral = reference
    # Where the native mouth is already relaxed, preserve its movement.
    weight = float(amount * smoothstep((gap - .025) / .045))
    dst = src + weight * (neutral - src)
    rim = np.minimum(opening * .16, 1.8) * weight
    src = src.copy()
    src[1] -= rim
    src[2] += rim
    edge = np.minimum(u - lips[48, 0], lips[54, 0] - u)
    shift = lip_offsets(v, src, dst) * smoothstep(edge / 7)
    patch = cv.remap(frame, xx + shift * inverse[0, 1], yy + shift * inverse[1, 1],
                     cv.INTER_LINEAR, borderMode=cv.BORDER_REPLICATE)
    if reference is not None:
        # Restore fine lip creases only on the aligned lip surfaces. Leave the
        # remaining oral cavity entirely on the current performance until contact.
        ref_y = v + lip_offsets(v, reference, dst)
        detail = cv.remap(rest[1], u, ref_y, cv.INTER_LINEAR, borderMode=cv.BORDER_REPLICATE)
        mask = smoothstep(edge / 9) * smoothstep((v - dst[0] + 3) / 4)
        mask *= smoothstep((dst[3] + 3 - v) / 4)
        mask *= (v <= dst[1]) | (v >= dst[2])
        patch = np.clip(patch + (.85 * weight * mask)[..., None] * detail, 0, 255).astype(np.uint8)
    out = frame.copy()
    out[y:b, x:r] = patch
    return out


class RestMouth:
    def __init__(self):
        from .engine import FaceLandmarks

        self.tracker = FaceLandmarks()
        self.poses = {}

    def find_pose(self, source):
        # Use geometry and fine detail from a genuinely closed mouth in this
        # trim. Lighting, lip color and head motion come from the displayed frame.
        count = 1 if source.fixed else max(1, int(source.length * FPS / source.rate))
        best_gap, best = .05, None
        seen = set()
        for budget in (16, 64):
            for index in np.linspace(0, count - 1, min(budget, count), dtype=int):
                if index in seen:
                    continue
                seen.add(index)
                source.pos = int(index)
                frame = source.next()
                try:
                    points = self.tracker.landmarks(frame)
                except ValueError:
                    continue
                geometry = mouth_geometry(points)
                if geometry is None or geometry[0] >= best_gap:
                    continue
                gap, mat = geometry
                lips = cv.transform(points[None], mat)[0]
                if lip_contours(lips, CENTER[:1]) is None:
                    continue
                patch = cv.warpAffine(frame, mat, (144, 96), borderMode=cv.BORDER_REPLICATE).astype(np.float32)
                best = lips, patch - cv.GaussianBlur(patch, (0, 0), 2.2)
                best_gap = gap
                if gap <= .025:
                    return best
            if best is not None:
                break
        return best

    def points(self, frame):
        try:
            return self.tracker.landmarks(frame)
        except ValueError:
            return None

    def settled(self, frame, points, amount, key, open_source):
        if key not in self.poses:
            source = open_source()
            try:
                self.poses[key] = self.find_pose(source)
            finally:
                source.close()
        return settle_lips(frame, points, amount, self.poses[key])


def head_transform(points):
    """Normalize head roll and scale using the eyes, with the nose as origin."""
    axis = points[45] - points[36]
    den = np.dot(axis, axis)
    if den < 64:
        return None
    linear = np.float32([[axis[0], axis[1]], [-axis[1], axis[0]]]) / den
    return np.column_stack([linear, -linear @ points[30]])


class LipPose:
    """A single performance frame in mouth coordinates, attached to the head."""
    def __init__(self, frame, points, mat, head):
        self.lips = cv.transform(points[None], mat)[0]
        self.corners = cv.transform(points[[48, 54]][None], head)[0]
        # Oversample the local patch so a second mapping does not soften a close-up.
        self.patch = cv.warpAffine(frame, 2 * mat, (288, 192), borderMode=cv.BORDER_REPLICATE)
        self.gap = float(np.mean(self.lips[[67, 66, 65], 1] - self.lips[[61, 62, 63], 1]))

    @classmethod
    def capture(cls, frame, points):
        if points is None:
            return None
        geom, head = mouth_geometry(points), head_transform(points)
        if geom is None or head is None:
            return None
        pose = cls(frame, points, geom[1], head)
        return pose if lip_contours(pose.lips, CENTER[:1]) is not None else None


def blend_poses(frame, points, a, b, t):
    """Move both lip surfaces to a common contour; keep just one view of the teeth."""
    head = head_transform(points)
    if head is None:
        return frame
    corners = cv.transform(((1-t)*a.corners + t*b.corners)[None], cv.invertAffineTransform(head))[0]
    anchors = points.copy()
    anchors[[48, 54]] = corners
    geom = mouth_geometry(anchors)
    if geom is None:
        return frame
    mat = geom[1]
    # Do not propagate a pose across a track discontinuity or a large turn.
    if np.max(np.linalg.norm(corners - points[[48, 54]], axis=1)) > .32*np.linalg.norm(corners[1]-corners[0]):
        return frame
    box = cv.transform(np.float32([[[0, 0], [144, 0], [144, 96], [0, 96]]]), cv.invertAffineTransform(mat))[0]
    x, y = np.maximum(0, np.floor(box.min(axis=0)).astype(int))
    r, d = np.minimum(frame.shape[1::-1], np.ceil(box.max(axis=0)).astype(int))
    if r <= x or d <= y:
        return frame
    yy, xx = np.mgrid[y:d, x:r].astype(np.float32)
    u = xx * mat[0, 0] + yy * mat[0, 1] + mat[0, 2]
    v = xx * mat[1, 0] + yy * mat[1, 1] + mat[1, 2]
    if a is b:
        patch = cv.remap(a.patch, 2*u, 2*v, cv.INTER_LINEAR, borderMode=cv.BORDER_REPLICATE)
    else:
        ca, cb = lip_contours(a.lips, u), lip_contours(b.lips, u)
        dst = (1-t)*ca + t*cb
        pa = cv.remap(a.patch, 2*u, 2*(v + lip_offsets(v, ca, dst)), cv.INTER_LINEAR, borderMode=cv.BORDER_REPLICATE)
        pb = cv.remap(b.patch, 2*u, 2*(v + lip_offsets(v, cb, dst)), cv.INTER_LINEAR, borderMode=cv.BORDER_REPLICATE)
        # Inside the opening, sample the performance that actually shows the
        # oral cavity. Once in contact, use both aligned lip surfaces normally.
        interior = np.clip(np.minimum(v-dst[1], dst[2]-v), 0, 1)
        mix = t + ((1 if b.gap > a.gap else 0)-t)*interior
        patch = (1-mix[..., None])*pa + mix[..., None]*pb
    radius = np.sqrt(((u-72)/68)**2 + ((v-47)/42)**2)
    mask = smoothstep((1-radius)/.33)[..., None]
    out = frame.copy()
    out[y:d, x:r] = np.rint(frame[y:d, x:r]*(1-mask) + patch*mask).astype(np.uint8)
    return out


class PausePerformance:
    """Independent, seekable gestures for sustained pauses inside one shot."""
    def __init__(self, weights, first, stop, tracker, clip, open_source):
        self.tracker, self.clip, self.open_source = tracker, clip, open_source
        self.weights = weights
        self.runs = {}
        self.active = self.poses = None
        # An edit can cut a gesture just before contact. Look outside the shot
        # for audio evidence only; every captured image stays on this side of the cut.
        offset = max(0, first - 6)
        nearby = weights[offset:stop+6]
        for begin, end in np.flatnonzero(np.diff(nearby > 0, prepend=False, append=False)).reshape(-1, 2):
            begin, end = begin + offset, end + offset
            begin_visible, end_visible = max(first, begin), min(stop, end)
            if begin_visible >= end_visible:
                continue
            plateau = np.flatnonzero(weights[begin:end] >= .999)
            if not len(plateau):
                continue
            enter, leave = np.clip(begin + plateau[[0, -1]], first, stop-1)
            run = (max(first, begin-1), enter, leave, min(stop-1, end))
            self.runs.update((i, run) for i in range(begin_visible, end_visible))

    def capture(self, index, read):
        frame = read(index)
        return frame, self.tracker.points(frame)

    def anchors(self, run, read):
        start, enter, leave, end = run
        # A relaxed generated frame from this pause best matches the lighting,
        # expression and lip texture of the last syllable.
        candidates = []
        for index in sorted({enter, (enter+leave)//2, leave}):
            frame, pts = self.capture(index, read)
            geom = mouth_geometry(pts) if pts is not None else None
            if geom is not None:
                candidates.append((abs(geom[0]-.028), geom[0], frame, pts))
        if not candidates:
            return None
        _, gap, frame, pts = min(candidates, key=lambda candidate: candidate[0])
        if gap > .045:
            frame = self.tracker.settled(frame, pts, 1., self.clip, self.open_source)
            pts = self.tracker.points(frame)
        neutral = LipPose.capture(frame, pts)
        if neutral is None:
            return None
        before = LipPose.capture(*self.capture(start, read)) if start < enter else neutral
        after = LipPose.capture(*self.capture(end, read)) if leave < end else neutral
        return (before, neutral, after) if before and after else None

    def apply(self, frame, index, read):
        weight = float(self.weights[index])
        if weight <= 0:
            return frame
        run = self.runs.get(index)
        if run != self.active:
            self.active = run
            self.poses = self.anchors(run, read) if run else None
        pts = self.tracker.points(frame)
        if pts is None:
            return frame
        if not self.poses:
            return self.tracker.settled(frame, pts, weight, self.clip, self.open_source)
        before, neutral, after = self.poses
        start, enter, leave, end = run
        if start < enter and index <= enter and weight < 1.:
            return blend_poses(frame, pts, before, neutral, weight)
        if leave < end and index >= leave and weight < 1.:
            return blend_poses(frame, pts, after, neutral, weight)
        return blend_poses(frame, pts, neutral, neutral, 1.)

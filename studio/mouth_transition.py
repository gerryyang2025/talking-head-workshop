"""Ease pose jumps when a speaking take must loop, keeping the current speech frame."""
import cv2 as cv
import numpy as np

from .media import FPS
from .mouth_rest import head_transform, mouth_geometry


def loop_windows(span, start, stop, length, rate, delay, radius=7):
    """Frames near an actual wrap in Frames.next(), in master time even for previews."""
    first, end = span["first"], span["stop"]
    radius = min(radius, int(length * FPS / rate) // 2)
    if radius < 2:
        return {}
    # Limit to this continuous speaking interval; never warp across a planned edit.
    def cycle(index):
        pos = span["offset"] + max(0, index - first - delay)
        return int(pos * rate / FPS) // length

    windows = {}
    for cut in range(max(first + 1, start - radius + 1), min(end, stop + radius)):
        if cycle(cut) == cycle(cut - 1):
            continue
        r = min(radius, cut - first, end - cut)
        if r >= 2:
            windows.update((i, (cut, r)) for i in range(max(start, cut-r), min(stop, cut+r)))
    return windows


class PoseTransition:
    """Move each side toward the other's pose, without mixing teeth from two frames."""

    def __init__(self, before, after):
        h, w = before.shape[:2]
        shrink = min(1., 384 / max(h, w))
        sw, sh = max(1, round(w * shrink)), max(1, round(h * shrink))
        a, b = [cv.cvtColor(cv.resize(f, (sw, sh), interpolation=cv.INTER_AREA),
                            cv.COLOR_BGR2GRAY) for f in (before, after)]
        self.fields = None
        if min(sh, sw) < 32:
            return
        dis = cv.DISOpticalFlow_create(cv.DISOPTICAL_FLOW_PRESET_MEDIUM)
        f, g = [cv.GaussianBlur(dis.calc(x, y, None), (0, 0), 2.5) for x, y in ((a, b), (b, a))]
        grid = self.grid(sw, sh)

        def reliable(flow, reverse):
            back = cv.remap(reverse, grid + flow, None, cv.INTER_LINEAR, borderMode=cv.BORDER_REPLICATE)
            error = np.linalg.norm(flow + back, axis=-1)
            return flow * np.clip((8 - error) / 5, 0, 1)[..., None]

        # Skip unrelated views rather than deform an unmatched subject or background.
        aligned = cv.remap(b, grid + f, None, cv.INTER_LINEAR, borderMode=cv.BORDER_REPLICATE)
        if cv.absdiff(a, aligned).mean() >= .85 * cv.absdiff(a, b).mean():
            return
        scale = np.float32([w/sw, h/sh])
        self.fields = tuple(cv.resize(reliable(v, rev) * scale, (w, h)) for v, rev in ((f, g), (g, f)))
        self.coords = self.grid(w, h)

    @staticmethod
    def grid(w, h):
        return np.dstack(np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32)))

    def apply(self, frame, offset, radius):
        if self.fields is None:
            return frame
        t = (offset + radius + .5) / (2 * radius)
        ease = t*t*(3-2*t)
        side = int(offset >= 0)
        amount = 1-ease if side else ease
        return cv.remap(frame, self.coords - self.fields[side] * amount, None,
                        cv.INTER_LINEAR, borderMode=cv.BORDER_REPLICATE)


class MovingTail:
    """Follow the outgoing plate for a short pause using its last synced face."""
    def __init__(self, source, pos, synced, tracker):
        self.source, self.pos, self.synced, self.tracker = source, pos, synced, tracker
        self.frames = {0: synced}
        self.head = None
        pts = tracker.points(synced)
        if pts is None:
            return
        geom = mouth_geometry(pts)
        self.head = head_transform(pts) if geom is not None else None
        if self.head is None:
            return
        # The surrounding plate supplies the actual eye, head and body motion.
        yy, xx = np.indices(synced.shape[:2], dtype=np.float32)
        mat = geom[1]
        u = mat[0, 0]*xx + mat[0, 1]*yy + mat[0, 2]
        v = mat[1, 0]*xx + mat[1, 1]*yy + mat[1, 2]
        distance = np.sqrt(((u-72)/84)**2 + ((v-52)/70)**2)
        alpha = np.clip((1-distance)/.3, 0, 1)
        self.mask = alpha*alpha*(3-2*alpha)

    def read(self, ahead):
        if ahead in self.frames:
            return self.frames[ahead]
        if self.head is None:
            return self.synced
        # Hold at the trim boundary if the plate would wrap to its first pose.
        cycle = int(self.pos * self.source.rate / FPS) // self.source.length
        limit = int(np.ceil((cycle+1) * self.source.length * FPS / self.source.rate)) - 1
        self.source.pos = min(self.pos + ahead, limit)
        frame = self.source.next()
        points = self.tracker.points(frame)
        head = head_transform(points) if points is not None else None
        if head is None:
            return self.synced
        mat = cv.invertAffineTransform(head) @ np.vstack((self.head, [0, 0, 1]))
        size = frame.shape[1::-1]
        face = cv.warpAffine(self.synced, mat, size, borderMode=cv.BORDER_REPLICATE)
        alpha = cv.warpAffine(self.mask, mat, size)[..., None]
        self.frames[ahead] = np.rint(face*alpha + frame*(1-alpha)).astype(np.uint8)
        return self.frames[ahead]

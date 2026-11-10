import collections
import json
import math
import re
import shutil
import subprocess
import time
import textwrap
from contextlib import contextmanager

import cv2 as cv
import numpy as np
from istream.lipsync import zh_mouth_risk
from .setup_models import NATIVE_WEIGHTS
from .mouth_transition import MovingTail, PoseTransition, loop_windows
from .media import (
    STORE,
    FPS,
    LAYOUTS,
    asset,
    db,
    english_sentences,
    ff,
    inspect_file,
    number,
    shots_for,
    signature,
)

STYLES = {
    "studio": ["full"],
    "editorial": ["full", "split", "card"],
    "lecture": ["full", "pip", "split"],
}
SIZES = {"16:9": (1280, 720), "9:16": (720, 1280)}
CAPTION_BAND = 104  # pixels at both supported export resolutions
SPLIT_FRACTION = 0.54
# SyncNet measured a 1–2 frame lead in MuseTalk 1.5's native 25 fps output.
# Apply the baseline when reading a synced clip so existing inference is reusable.
MOUTH_DELAY_FRAMES = 1
MODEL_NAMES = {"musetalk": "MuseTalk 1.5", "edtalk": "EDTalk 256",
               "soulx_flashhead": "SoulX-FlashHead Lite", "latentsync": "LatentSync 1.6"}
SYNC_VERSIONS = {"musetalk": "musetalk-v1", "edtalk": "edtalk-v5",
                 "soulx_flashhead": "soulx-lite-q8-v2", "latentsync": "latentsync-1.6-q8-v1"}


def selected_model(config):
    model = config.get("lipModel", "musetalk")
    if not isinstance(model, str) or model not in MODEL_NAMES:
        raise ValueError("请选择工作台支持的口型模型")
    return model


def load_voice(vid):
    if not isinstance(vid, str) or not re.fullmatch("[a-f0-9]{64}", vid):
        raise ValueError("请先生成或载入配音")
    path = STORE / "voices" / vid / "voice.json"
    if not path.is_file():
        raise ValueError("配音已失效，请重新生成")
    return json.loads(path.read_text())


def insert_options(config):
    ident = config.get("insert")
    speaking = config.get("insertSpeaking", False)
    if type(speaking) is not bool:
        raise ValueError("无效的补充素材口播设置")
    if speaking and not ident:
        raise ValueError("请先选择用于口播的补充素材")
    if ident and asset(ident)["role"] not in ("host", "insert"):
        raise ValueError("补充画面需要照片或视频")
    return ident, speaking


def project_inserts(config):
    if "inserts" not in config:
        ident, speaking = insert_options(config)
        return {ident: speaking} if ident else {}
    entries = config["inserts"]
    if not isinstance(entries, list):
        raise ValueError("项目补充素材列表无效")
    options = {}
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("id"), str) or not entry["id"]:
            raise ValueError("项目补充素材无效")
        ident, speaking = insert_options({"insert": entry["id"], "insertSpeaking": entry.get("speaking", False)})
        options[ident] = speaking
    return options


def line_insert(line, options, layout, index):
    if layout not in ("card", "insert"):
        return None, False
    ident = line.get("insert")
    if ident is None:
        if len(options) > 1:
            raise ValueError(f"请在「选镜与口型」为第 {index + 1} 句选择补充素材")
        ident = next(iter(options), None)
    if not ident:
        if layout == "insert":
            raise ValueError(f"第 {index + 1} 句需要补充素材，请先从素材库选取，再到「选镜与口型」指定")
        return None, False
    if ident not in options:
        raise ValueError(f"第 {index + 1} 句引用的素材未加入当前项目")
    speaking = line.get("insertSpeaking", options[ident])
    if type(speaking) is not bool:
        raise ValueError("无效的补充素材口播设置")
    return ident, speaking


def timed_cutaways(config, options, frames):
    entries = config.get("cutaways", [])
    if not isinstance(entries, list):
        raise ValueError("补充镜头列表无效")
    cuts = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("补充镜头无效")
        first, stop = entry.get("first"), entry.get("stop")
        if type(first) is not int or type(stop) is not int or not 0 <= first < stop <= frames:
            raise ValueError("补充镜头须位于配音范围内，且至少持续一帧")
        ident, speaking = entry.get("insert"), entry.get("insertSpeaking", False)
        if not ident or ident not in options or type(speaking) is not bool:
            raise ValueError("请为补充镜头选择项目素材和有效的用途")
        cuts.append(dict(first=first, stop=stop, insert=ident, insertSpeaking=speaking))
    cuts.sort(key=lambda cut: cut["first"])
    if any(left["stop"] > right["first"] for left, right in zip(cuts, cuts[1:])):
        raise ValueError("补充镜头不能重叠，可以首尾相接")
    return cuts


def base_visible(cuts, first, stop):
    cursor = first
    for cut in cuts:
        if cut["first"] > cursor:
            break
        cursor = max(cursor, cut["stop"])
        if cursor >= stop:
            return False
    return cursor < stop


def plan(config):
    vid = config.get("voiceId", "")
    voice = load_voice(vid)
    inputs = config.get("lines")
    if not isinstance(inputs, list) or len(inputs) != len(voice["lines"]):
        raise ValueError("文案已变更，请先更新配音")
    aspect, style = config.get("aspect"), config.get("style")
    if aspect not in SIZES or style not in STYLES:
        raise ValueError("无效的画幅或版式")
    framing = config.get("framing", "cover")
    if framing not in ("cover", "contain"):
        raise ValueError("无效的全屏镜头取景方式")
    ids = config.get("hosts", [])
    if not isinstance(ids, list) or len(ids) > 30:
        raise ValueError("母片选择无效")
    # Older drafts sent an ordered list of hosts. Its first item is the presenter.
    primary = ids[0] if ids else None
    pool = []
    if primary is not None:
        a = asset(primary)
        if a["role"] not in ("host", "insert"):
            raise ValueError("所选素材不能用作人物母片")
        pool = [s for s in shots_for(a) if s["enabled"]]
    inserts = project_inserts(config)
    frames = math.ceil(voice["duration"] * FPS - 1e-8)
    cutaways = timed_cutaways(config, inserts, frames)
    with db() as con:
        uses = collections.Counter(
            dict(
                con.execute(
                    "SELECT shot,sum(times) FROM usage GROUP BY shot"
                ).fetchall()
            )
        )
    rows = []
    last = 0
    for i, (line, original) in enumerate(zip(inputs, voice["lines"])):
        if line.get("text") != original["text"]:
            raise ValueError("文案与配音不匹配，请重新生成配音")
        start = number(
            line.get("start"), last, voice["duration"] + 0.001, "句子开始时间重叠或越界"
        )
        end = number(
            line.get("end"), start, voice["duration"] + 0.001, "句子结束时间无效"
        )
        first, stop = round(start * FPS), round(end * FPS)
        if stop <= first:
            raise ValueError("每句话至少需要一帧")
        last = end
        layout = line.get("layout", "auto")
        if layout == "auto":
            pattern = STYLES[style]
            layout = pattern[i % len(pattern)]
        if layout not in LAYOUTS:
            raise ValueError("无效的镜头版式")
        # The following line supplies the picture in the pause before it.
        picture_first = rows[-1]["stop"] if rows else 0
        picture_stop = frames if i == len(inputs) - 1 else stop
        visible = base_visible(cutaways, picture_first, picture_stop)
        insert, insert_speaking = line_insert(line, inserts, layout, i) if visible else (None, False)
        shot = None
        if visible and layout not in ("card", "insert"):
            if not pool:
                raise ValueError("出镜句需要主讲母片和可用切片，请在「准备母片」选择主讲，再到「切片打标」启用镜头")
            candidates = (
                pool
                if not line.get("shot")
                else [s for s in pool if s["id"] == line["shot"]]
            )
            if not candidates:
                raise ValueError("指定的切片不属于当前主讲母片或已停用，请在「选镜与口型」重新选镜")
            shot = min(
                candidates,
                key=lambda s: (
                    0 if s["end"] == 0 or s["end"] - s["start"] >= end - start else 1,
                    uses[s["id"]],
                ),
            )
            uses[shot["id"]] += 1
        rows.append(
            dict(
                first=first,
                stop=stop,
                text=line["text"],
                start=start,
                end=end,
                layout=layout,
                shot=shot,
                insert=insert,
                insertSpeaking=insert_speaking,
                risk=zh_mouth_risk(line["text"], end - start)["level"],
            )
        )
    return dict(
        title=str(config.get("title", "未命名口播"))[:80],
        aspect=aspect,
        framing=framing,
        style=style,
        primaryHost=primary,
        lipModel=selected_model(config),
        voice=vid,
        frames=frames,
        cutaways=cutaways,
        duration=voice["duration"],
        rows=rows,
        inserts=[{"id": ident, "speaking": mode} for ident, mode in inserts.items()],
        insert=next(iter(inserts)) if len(inserts) == 1 else None,
        shift=int(number(config.get("shift", 0), -8, 8, "口型时移限于正负 8 帧")),
        subtitles=config.get("subtitles", True) is True,
    )


class Frames:
    def __init__(self, info, start=0, end=0):
        self.fixed = info["kind"] == "photo"
        self.image = None
        self.cap = None
        self.pos = 0
        if self.fixed:
            self.image = cv.imread(info["path"])
            if self.image is None:
                raise ValueError("图片解码失败")
            h, w = self.image.shape[:2]
            ratio = min(1, 1280 / max(h, w))
            self.image = cv.resize(
                self.image,
                (max(2, round(w * ratio / 2) * 2), max(2, round(h * ratio / 2) * 2)),
                interpolation=cv.INTER_AREA,
            )
        else:
            self.cap = cv.VideoCapture(info["path"])
            self.rate = self.cap.get(cv.CAP_PROP_FPS) or FPS
            self.start = round(start * self.rate)
            self.length = max(
                1, round((end - start if end else info["duration"] - start) * self.rate)
            )
            self.last = -2
            self.image = None

    def next(self):
        if self.fixed:
            return self.image.copy()
        target = self.start + int(self.pos * self.rate / FPS) % self.length
        if target != self.last:
            if target != self.last + 1:
                self.cap.set(cv.CAP_PROP_POS_FRAMES, target)
            ok, frame = self.cap.read()
            if not ok:
                raise ValueError("母片无法读取所选帧，请复核入出点")
            h, w = frame.shape[:2]
            ratio = min(1, 1280 / max(h, w))
            self.image = cv.resize(
                frame,
                (max(2, round(w * ratio / 2) * 2), max(2, round(h * ratio / 2) * 2)),
                interpolation=cv.INTER_AREA,
            )
            self.last = target
        self.pos += 1
        return self.image.copy()

    def close(self):
        if self.cap:
            self.cap.release()


@contextmanager
def encoder(path, size, *extra):
    w, h = size
    args = [
        "ffmpeg",
        "-y",
        "-v",
        "error",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "bgr24",
        "-s",
        f"{w}x{h}",
        "-r",
        str(FPS),
        "-i",
        "pipe:0",
        *map(str, extra),
        "-c:v",
        "libx264",
        "-threads",
        "4",
        "-preset",
        "veryfast",
        "-crf",
        "17",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(path),
    ]
    with subprocess.Popen(args, stdin=subprocess.PIPE) as p:
        try:
            yield p.stdin
        finally:
            p.stdin.close()
        if p.wait():
            raise ValueError("FFmpeg 编码失败")


def fit(frame, w, h, cover=True, vertical_anchor=0.12):
    fh, fw = frame.shape[:2]
    scale = (max if cover else min)(w / fw, h / fh)
    ww, hh = max(1, round(fw * scale)), max(1, round(fh * scale))
    image = cv.resize(
        frame, (ww, hh), interpolation=cv.INTER_AREA if scale < 1 else cv.INTER_CUBIC
    )
    if cover:
        x, y = (ww - w) // 2, max(0, round((hh - h) * vertical_anchor))
        return image[y : y + h, x : x + w]
    return image


def compose(frame, layout, size, subtitles=False, framing="cover", progress=0):
    w, h = size
    canvas = np.full((h, w, 3), (33, 33, 28), np.uint8)
    if frame is None:
        return canvas
    if layout == "card":
        draw_card(canvas, frame, progress)
        return canvas
    if layout in ("full", "insert"):
        picture_h = h - CAPTION_BAND if subtitles else h
        picture_w = round(w * picture_h / h)
        image = fit(
            frame, picture_w, picture_h, cover=framing == "cover", vertical_anchor=0.5
        )
        ih, iw = image.shape[:2]
        x, y = (w - iw) // 2, (picture_h - ih) // 2
        canvas[y : y + ih, x : x + iw] = image
        return canvas
    if layout == "split":
        if w > h:
            cw = round(w * SPLIT_FRACTION)
            canvas[:, :cw] = fit(frame, cw, h)
        else:
            ch = round(h * SPLIT_FRACTION)
            canvas[:ch] = fit(frame, w, ch)
    else:
        radius = round(min(w, h) * 0.20)
        x, y = round(w * 0.70), round(h * 0.34)
        square = fit(frame, 2 * radius, 2 * radius)
        yy, xx = np.ogrid[-radius:radius, -radius:radius]
        mask = xx * xx + yy * yy < radius * radius
        canvas[y - radius : y + radius, x - radius : x + radius][mask] = square[mask]
        cv.circle(canvas, (x, y), radius, (106, 233, 197), 2, cv.LINE_AA)
    return canvas


def ass_time(frame):
    cs = round(frame * 100 / FPS)
    return f"{cs // 360000}:{cs // 6000 % 60:02}:{cs // 100 % 60:02}.{cs % 100:02}"


def card_visual_size(w, h):
    return (round(w * 0.54), h) if w > h else (w, round(h * 0.62))


def caption_box(layout, w, h, card_image=False):
    pad = round(w * 0.05)
    if layout in ("full", "insert"):
        return pad, h - CAPTION_BAND, w - pad, h
    if layout == "split":
        if w > h:
            return round(w * SPLIT_FRACTION) + pad, 0, w - pad, h
        return pad, round(h * SPLIT_FRACTION), w - pad, h
    if layout == "pip":
        circle_bottom = round(h * 0.34) + round(min(w, h) * 0.20)
        return pad, circle_bottom + 12, w - pad, h - 24
    if layout == "card" and card_image:
        box_w, box_h = card_visual_size(w, h)
        if w > h:
            return box_w + pad, 0, w - pad, h
        return pad, box_h, w - pad, h
    return pad, 0, w - pad, h


def draw_card(canvas, frame, progress):
    h, w = canvas.shape[:2]
    # Fit the whole visual as it slowly grows inside its reserved area.
    box_w, box_h = card_visual_size(w, h)
    margin = round(min(w, h) * 0.05)
    zoom = 0.94 + 0.06 * progress
    image = fit(
        frame, round((box_w - 2 * margin) * zoom),
        round((box_h - 2 * margin) * zoom), cover=False,
    )
    ih, iw = image.shape[:2]
    ix, iy = (box_w - iw) // 2, (box_h - ih) // 2
    canvas[iy : iy + ih, ix : ix + iw] = image


def synced_frames(path, count):
    return Frames(dict(kind="video", path=str(path), duration=count / FPS))


def visual_spans(tl):
    """Resolve the visible source at each audio or cut boundary, in master frames."""
    delay = MOUTH_DELAY_FRAMES if selected_model(tl) == "musetalk" else 0
    rows, cuts = tl["rows"], tl.get("cutaways", [])
    boundaries = {0, tl["frames"]}
    for item in [*rows, *cuts]:
        boundaries.update((item["first"], item["stop"]))
    ordered = sorted(boundaries)
    spans = []
    ri = ci = 0
    for first, stop in zip(ordered, ordered[1:]):
        while ri + 1 < len(rows) and first >= rows[ri]["stop"]:
            ri += 1
        while ci < len(cuts) and first >= cuts[ci]["stop"]:
            ci += 1
        row = rows[ri]
        voiced = row["first"] <= first < row["stop"]
        covered = ci < len(cuts) and cuts[ci]["first"] <= first
        source = cuts[ci] if covered else row
        layout = "insert" if covered else row["layout"]
        hold = not covered and not voiced and (layout == "card" or row["insertSpeaking"])
        offset = max(0, first - source["first"])
        if hold:
            offset = min(offset, source["stop"] - source["first"] - 1)
        elif not covered and not voiced:
            pause_start = rows[ri - 1]["stop"] if ri else 0
            if first >= row["stop"] and row["shot"]:
                # Continue from the last displayed source time in the tail.
                offset = max(0, first - row["first"] - delay)
            elif row["shot"] and 0 < row["first"] - pause_start <= 6:
                # A brief lead-in shows the incoming speaker. Do not play the
                # first few head movements twice when the synced take starts.
                hold = True
                offset = 0
            else:
                offset = first - (row["stop"] if first >= row["stop"] else pause_start)
        span = dict(
            first=first, stop=stop, layout=layout, delay=delay, shot=source.get("shot"),
            insert=source["insert"], insertSpeaking=source["insertSpeaking"],
            voiced=voiced, offset=offset, hold=hold, origin=source["first"],
            length=source["stop"] - source["first"], owner=("cut", ci) if covered else ("line", ri),
        )
        # Give the outgoing speaker a few frames to finish closing before the
        # next host shot. A timed cutaway always retains its exact in/out points.
        if (spans and not voiced and not covered and row["shot"] and stop-first <= 6
                and spans[-1]["voiced"] and spans[-1]["shot"] and spans[-1]["owner"][0] == "line"):
            previous = spans[-1]
            span = dict(previous, first=first, stop=stop, voiced=False, hold=True,
                        rest_from=previous["first"])
        spans.append(span)
    return spans


def draw_span(sink, span, part, size, start, stop, subtitles, framing, performance=None,
              cycle=None, open_tail=None, on_frame=None):
    source = tail = tail_source = None
    delay = span.get("delay", MOUTH_DELAY_FRAMES)
    windows = loop_windows(span, start, stop, *cycle, delay) if part and cycle else {}
    count = span["stop"] - span["first"]
    if part:
        source = synced_frames(part, count)
    elif span["shot"]:
        shot = span["shot"]
        source = Frames(asset(shot["asset"]), shot["start"], shot["end"])
    elif span["insert"]:
        source = Frames(asset(span["insert"]))

    def read_frame(index):
        nonlocal tail, tail_source
        if source is None:
            return None
        local = index - span["first"]
        if part:
            last = max(0, count - 1 - delay)
            source.pos = min(last, max(0, local - delay))
            if local >= count and open_tail and performance:
                if tail is None:
                    tail_source = open_tail()
                    tail = MovingTail(tail_source, span["offset"] + last, source.next(), performance.tracker)
                return tail.read(local - count + 1)
        else:
            source.pos = span["offset"] + (0 if span["hold"] else local)
        return source.next()

    try:
        seam = active_cut = None
        for index in range(start, stop):
            frame = read_frame(index)
            progress = min(1, max(0, (index - span["origin"]) / max(1, span["length"] - 1)))
            picture = performance.apply(frame, index, read_frame) if performance else frame
            if index in windows:
                cut, radius = windows[index]
                if cut != active_cut:
                    saved = source.pos
                    source.pos = cut - span["first"] - delay - 1
                    seam = PoseTransition(source.next(), source.next())
                    source.pos = saved
                    active_cut = cut
                picture = seam.apply(picture, index - cut, radius)
            sink.write(compose(picture, span["layout"], size, subtitles, framing, progress).tobytes())
            if on_frame and ((index + 1) % FPS == 0 or index + 1 == stop):
                on_frame(index + 1)
    finally:
        if tail_source:
            tail_source.close()
        if source:
            source.close()


def caption_cues(row, columns):
    # Older voice files can contain an entire paragraph in a single timed row.
    pages = []
    for sentence in english_sentences(row["text"]):
        lines = textwrap.wrap(sentence, width=columns, break_on_hyphens=False)
        pages.extend(lines[i : i + 2] for i in range(0, len(lines), 2))
    frames = row["stop"] - row["first"]
    if len(pages) > frames:
        raise ValueError("字幕页数超过句段帧数，请延长该句或缩短文案。")
    weights = [sum(map(len, page)) for page in pages]
    total = sum(weights)
    cursor = row["first"]
    used = 0
    for i, (page, weight) in enumerate(zip(pages, weights), 1):
        used += weight
        # Assign at least one frame per page, with no gaps or overlaps.
        end = row["first"] + i + round((frames - len(pages)) * used / total)
        yield cursor, end, page
        cursor = end


def write_ass(tl, path, origin=0):
    w, h = SIZES[tl["aspect"]]
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
WrapStyle: 2
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Main,Heiti SC,38,&H00FFFFFF,&H00FFFFFF,&H00201C18,&H50201C18,0,0,0,0,100,100,0,0,1,2,1,2,26,26,40,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    for row in tl["rows"]:
        layout = row["layout"]
        caption = layout in ("full", "insert")
        if caption and not tl["subtitles"]:
            continue
        left, top, right, bottom = caption_box(layout, w, h, bool(row.get("insert")))
        font = 32 if caption else 40
        # Budget one em per character so CJK and mixed-script lines also fit.
        columns = min(48, (right - left - 16) // font)
        # Paginate the spoken sentence once. Only the caption position changes on a cut.
        areas = []
        cursor = row["first"]
        if not caption:
            for cut in tl.get("cutaways", []):
                enter, leave = max(cut["first"], row["first"]), min(cut["stop"], row["stop"])
                if enter >= leave:
                    continue
                if cursor < enter:
                    areas.append((cursor, enter, layout))
                areas.append((enter, leave, "insert"))
                cursor = leave
        if cursor < row["stop"]:
            areas.append((cursor, row["stop"], layout))
        area_index = 0
        for start, stop, lines in caption_cues(row, columns):
            text = r"\N".join(
                line.replace("\\", "＼").replace("{", "｛").replace("}", "｝")
                for line in lines
            )
            while area_index < len(areas):
                enter, leave, visible = areas[area_index]
                begin, end = max(start, enter, origin), min(stop, leave)
                is_caption = visible in ("full", "insert")
                if begin < end and (tl["subtitles"] or not is_caption):
                    x1, y1, x2, y2 = caption_box(visible, w, h, bool(row.get("insert")))
                    x, y = (x1 + x2) // 2, (y1 + y2) // 2
                    position = rf"\an5\fs{32 if is_caption else 40}\pos({x},{y})\clip({x1},{y1},{x2},{y2})"
                    fade = ""
                    if not is_caption:
                        half_ms = (end - begin) * 500 // FPS
                        fade_in = min(160, half_ms) if begin == row["first"] else 0
                        fade_out = min(110, half_ms) if end == row["stop"] else 0
                        fade = rf"\fad({fade_in},{fade_out})"
                    events.append(
                        f"Dialogue: 0,{ass_time(begin-origin)},{ass_time(end-origin)},Main,,0,0,0,,{{{position}{fade}}}{text}"
                    )
                if leave > stop:
                    break
                area_index += 1
                if leave == stop:
                    break
    path.write_text(header + "\n".join(events) + "\n")


def render_card_preview(config, folder):
    voice_id, aspect = config.get("voiceId"), config.get("aspect")
    voice = load_voice(voice_id)
    line = config.get("line")
    if aspect not in SIZES or type(line) is not int or not 0 <= line < len(voice["lines"]):
        raise ValueError("请选择有效的图文句段和画幅")
    start = number(config.get("start"), 0, voice["duration"] + 0.001, "句段入点越界")
    end = number(config.get("end"), start, voice["duration"] + 0.001, "句段出点越界")
    first = round(start * FPS)
    count = round(end * FPS) - first
    if count < 1:
        raise ValueError("每句话至少需要一帧")
    insert, speaking = insert_options(config)
    layout = config.get("layout", "card")
    if layout not in ("card", "insert") or (layout == "insert" and not insert):
        raise ValueError("请选择有效的补充素材和镜头版式")
    subtitles, framing = config.get("subtitles", True) is True, config.get("framing", "cover")
    if framing not in ("contain", "cover"):
        raise ValueError("无效的全屏镜头取景方式")
    row = dict(layout=layout, first=first, stop=first + count, text=voice["lines"][line]["text"],
               insert=insert, insertSpeaking=speaking, shot=None)
    tl = dict(rows=[row], lipModel=selected_model(config), aspect=aspect, subtitles=subtitles, framing=framing, voice=voice_id,
              shift=int(number(config.get("shift", 0), -8, 8, "口型时移限于正负 8 帧")),
              frames=math.ceil(voice["duration"] * FPS - 1e-8))
    return render(tl, folder, lambda *_: None, window=(first, first + count))


def speaker_clip(span):
    shot = span["shot"]
    if shot:
        return shot["asset"], shot["start"], shot["end"]
    if span.get("insertSpeaking") and span["insert"]:
        return span["insert"], 0, 0
    return None


def sync_parts(rows, voice_id, shift, total, folder, notify, model, check_cancel, checkpoints):
    cache = STORE / "synced"
    cache.mkdir(exist_ok=True)
    voice = STORE / "voices" / voice_id / "voice.wav"
    parts = []
    engine = None
    inferred = cached = 0
    measured_seconds = 0.0
    spoken = [row for row in rows if row.get("voiced", True) and speaker_clip(row)]
    speech_frames = sum(row["stop"] - row["first"] for row in spoken)
    segment = 0
    for row in rows:
        check_cancel()
        count = row["stop"] - row["first"]
        clip = speaker_clip(row)
        if not row.get("voiced", True) or not clip:
            parts.append(None)
            continue
        segment += 1

        last_done = 0
        last_reused = 0
        sampled_at = time.monotonic()

        def report(done, detail="", reused=0):
            nonlocal measured_seconds, sampled_at, last_done, last_reused
            if done > last_done:
                now = time.monotonic()
                if done - last_done > reused - last_reused:
                    measured_seconds += now - sampled_at
                sampled_at, last_done, last_reused = now, done, reused
            new_frames = inferred + done - reused
            processed = inferred + cached + done
            metrics = dict(total=speech_frames, inferred=new_frames, cached=cached + reused,
                           fps=round(new_frames / measured_seconds, 4) if measured_seconds else None)
            message = f"口型推理 · 第 {segment}/{len(spoken)} 段"
            notify(10 + 62 * processed // speech_frames, message + (f" · {detail}" if detail else ""), metrics)

        ident, start, end = clip
        offset_key = (row["offset"],) if row.get("offset") else ()
        key = signature(
            SYNC_VERSIONS[model],
            voice_id,
            row["first"],
            row["stop"],
            shift,
            ident,
            start,
            end,
            *offset_key,
        )
        path = cache / (key + ".mp4")
        if path.exists():
            parts.append(path)
            report(count, "已复用", count)
            cached += count
            continue
        if engine is None:
            report(0, "正在载入口型模型")
            raw = ff("-i", voice, "-ar", "16000", "-ac", "1", "-f", "f32le", "pipe:1")
            samples = np.frombuffer(raw, "<f4")
            samples = np.pad(samples, (0, max(0, total * 640 - len(samples))))
            if model in NATIVE_WEIGHTS:
                from .native_lipsync import NativeLipEngine
                engine = NativeLipEngine(model, samples)
            elif model == "edtalk":
                from .edtalk import EDTalkEngine
                engine = EDTalkEngine(samples)
            else:
                from .engine import MouthEngine
                engine = MouthEngine(samples)
        src = Frames(asset(ident), start, end)
        src.pos = row.get("offset", 0)
        tmp = folder / (key + ".mp4")
        state = {}
        sampled_at = time.monotonic()
        reused = 0
        batch_folder = None
        try:
            if model == "latentsync" and checkpoints:
                from .native_lipsync import LATENTSYNC_BATCH
                if count > LATENTSYNC_BATCH:
                    batch_folder = checkpoints / key
            if batch_folder:
                reused = engine.render_checkpointed(src, row["first"] - shift, count, tmp, encoder,
                                                    report, check_cancel, batch_folder)
            elif model in NATIVE_WEIGHTS:
                engine.render(src, row["first"] - shift, count, tmp, encoder, report, check_cancel)
            else:
                first_frame = src.next()
                with encoder(tmp, first_frame.shape[1::-1]) as sink:
                    for j in range(0, count, 4):
                        check_cancel()
                        ix = list(range(j, min(count, j + 4)))
                        frames = [first_frame.copy() if k == 0 else src.next() for k in ix]
                        engine.sync(
                            frames,
                            [row["first"] + k for k in ix],
                            shift,
                            src.fixed,
                            state,
                        )
                        for f in frames:
                            sink.write(f.tobytes())
                        report(ix[-1] + 1)
        except ValueError as exc:
            if row.get("insertSpeaking"):
                raise ValueError(f"补充素材口播失败：{exc} 可更换清晰的单人素材，或把用途改为「配图」。") from exc
            raise
        finally:
            src.close()
        tmp.replace(path)
        parts.append(path)
        inferred += count - reused
        cached += reused
        if batch_folder:
            shutil.rmtree(batch_folder, ignore_errors=True)
    return parts, inferred, cached


def render(tl, folder, notify, window=None, *, check_cancel=lambda: None, checkpoints=None, on_inference=None):
    from istream.render import _esc

    size = SIZES[tl["aspect"]]
    total = tl["frames"]
    first, stop = window or (0, total)
    voice = STORE / "voices" / tl["voice"] / "voice.wav"
    ass = folder / "captions.ass"
    write_ass(tl, ass, origin=first)
    all_spans = visual_spans(tl)
    # Render the synced line and its short trailing pause as one performance.
    # Keep the inference interval itself unchanged so the same audio frames and
    # cached take are used when a preview starts inside that pause.
    tails = {s["rest_from"]: s["stop"] for s in all_spans if "rest_from" in s}
    spans = [s for s in all_spans if "rest_from" not in s and s["first"] < stop
             and tails.get(s["first"], s["stop"]) > first]
    report = on_inference or (lambda progress, message, metrics: notify(progress, message))
    parts, inferred, cached = sync_parts(spans, tl["voice"], tl["shift"], total, folder, report,
                                         selected_model(tl), check_cancel, checkpoints)
    weights = rest_mouth = None
    clips = [speaker_clip(span) for span in spans]
    actors = {ident: asset(ident) for ident in {clip[0] for clip in clips if clip}}
    cycles = {}
    tracks_source_motion = selected_model(tl) != "soulx_flashhead"
    for clip in {c for c, part in zip(clips, parts) if c and part and tracks_source_motion and actors[c[0]]["kind"] == "video"}:
        source = Frames(actors[clip[0]], *clip[1:])
        try:
            cycles[clip] = (source.length, source.rate)
        finally:
            source.close()
    if any(parts) or any(a["kind"] == "video" for a in actors.values()):
        from .mouth_rest import PausePerformance, RestMouth, rest_weights
        raw = ff("-i", voice, "-ar", "16000", "-ac", "1", "-f", "f32le", "pipe:1")
        weights = rest_weights(np.frombuffer(raw, "<f4"), total, FPS, 16000, all_spans)
        video_tail = tracks_source_motion and any(clip and actors[clip[0]]["kind"] == "video" and
                         s["stop"] < min(stop, tails.get(s["first"], s["stop"]))
                         for s, clip in zip(spans, clips))
        if video_tail or np.any(weights[first:stop]):
            rest_mouth = RestMouth()
    def composition_progress(end):
        check_cancel()
        notify(76 + 18 * (end - first) // (stop - first), f"正在合成画面 · {end - first}/{stop - first} 帧")

    composition_progress(first)
    output = folder / "film.mp4"
    filters = "subtitles='" + _esc(str(ass)) + "'"
    audio_trim = []
    if window:
        audio_trim = ["-ss", first / FPS, "-t", (stop - first) / FPS]
        filters += ",scale=iw/2:ih/2"
    with encoder(
        output, size, *audio_trim, "-i", voice, "-map", "0:v:0", "-map", "1:a:0",
        "-vf", filters, "-c:a", "aac", "-b:a", "160k",
    ) as sink:
        for span, part, clip in zip(spans, parts, clips):
            display_stop = tails.get(span["first"], span["stop"])
            performance = open_tail = None
            if rest_mouth and clip and (part or actors[clip[0]]["kind"] == "video"):
                def open_source(key=clip):
                    ident, begin, end = key
                    return Frames(actors[ident], begin, end)
                performance = PausePerformance(weights, span["first"], display_stop, rest_mouth, clip, open_source)
                if tracks_source_motion and display_stop > span["stop"] and actors[clip[0]]["kind"] == "video":
                    open_tail = open_source
            draw_span(sink, span, part, size, max(span["first"], first), min(display_stop, stop),
                      tl["subtitles"], tl.get("framing", "cover"), performance,
                      cycles.get(clip) if span["voiced"] else None, open_tail, composition_progress)
    if window:
        return output
    notify(95, "正在逐帧解码并核对音画时长")
    ff("-xerror", "-i", output, "-map", "0:v:0", "-map", "0:a:0", "-f", "null", "-")
    info = inspect_file(output)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    a = next(s for s in info["streams"] if s["codec_type"] == "audio")
    if (
        int(v["nb_frames"]) != total
        or abs(float(a["duration"]) - tl["duration"]) > 0.06
    ):
        raise ValueError("导出帧数或音轨时长与时间轴不一致")
    return dict(
        frames=total,
        duration=tl["duration"],
        size=list(size),
        inferred=inferred,
        cached=cached,
        skipped=total - inferred - cached,
        video=v["codec_name"],
        audio=a["codec_name"],
    )

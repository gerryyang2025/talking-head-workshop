import collections
import json
import math
import re
import subprocess
import textwrap
from contextlib import contextmanager

import cv2 as cv
import numpy as np
from istream.lipsync import zh_mouth_risk
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
        insert, insert_speaking = line_insert(line, inserts, layout, i)
        shot = None
        if layout not in ("card", "insert"):
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
                    uses[s["id"]],
                    0 if s["end"] == 0 or s["end"] - s["start"] >= end - start else 1,
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
        voice=vid,
        frames=math.ceil(voice["duration"] * FPS - 1e-8),
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


def write_insert_frames(sink, row, size, start, stop, part=None, *, subtitles=True, framing="cover"):
    source = Frames(asset(row["insert"])) if row.get("insert") else None
    count = row["stop"] - row["first"]
    synced = synced_frames(part, count) if part else None
    span = max(1, count - 1)
    frame = None
    try:
        for index in range(start, stop):
            progress = min(1, max(0, (index - row["first"]) / span))
            if synced and row["first"] <= index < row["stop"]:
                frame = synced.next()
            elif synced and index == row["stop"]:
                # Return to the corresponding original frame during the trailing pause.
                source.pos = count - 1
                frame = source.next()
            elif source and (frame is None or row["first"] < index < row["stop"]):
                frame = source.next()
            sink.write(compose(frame, row["layout"], size, subtitles, framing, progress).tobytes())
    finally:
        if synced:
            synced.close()
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


def write_ass(tl, path):
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
        x, y = (left + right) // 2, (top + bottom) // 2
        position = rf"\an5\fs{font}\pos({x},{y})\clip({left},{top},{right},{bottom})"
        for start, stop, lines in caption_cues(row, columns):
            fade = ""
            if not caption:
                half_ms = (stop - start) * 500 // FPS
                fade_in = min(160, half_ms) if start == row["first"] else 0
                fade_out = min(110, half_ms) if stop == row["stop"] else 0
                fade = rf"\fad({fade_in},{fade_out})"
            text = r"\N".join(
                line.replace("\\", "＼").replace("{", "｛").replace("}", "｝")
                for line in lines
            )
            events.append(
                f"Dialogue: 0,{ass_time(start)},{ass_time(stop)},Main,,0,0,0,,{{{position}{fade}}}{text}"
            )
    path.write_text(header + "\n".join(events) + "\n")


def render_card_preview(config, folder):
    from istream.render import _esc

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
    row = dict(layout=layout, first=0, stop=count, text=voice["lines"][line]["text"], insert=insert)
    part = None
    if speaking:
        shift = int(number(config.get("shift", 0), -8, 8, "口型时移限于正负 8 帧"))
        timed = dict(row, first=first, stop=first + count, insertSpeaking=True, shot=None)
        total = math.ceil(voice["duration"] * FPS - 1e-8)
        parts, _, _ = sync_parts([timed], voice_id, shift, total, folder, lambda *_: None)
        part = parts[0]
    ass = folder / "card.ass"
    write_ass(dict(aspect=aspect, rows=[row], subtitles=subtitles), ass)
    size = SIZES[aspect]
    output = folder / "card.mp4"
    with encoder(
        output, size, "-ss", first / FPS, "-t", count / FPS,
        "-i", STORE / "voices" / voice_id / "voice.wav", "-map", "0:v:0", "-map", "1:a:0",
        "-vf", "subtitles='" + _esc(str(ass)) + "',scale=iw/2:ih/2", "-c:a", "aac",
    ) as sink:
        write_insert_frames(sink, row, size, 0, count, part, subtitles=subtitles, framing=framing)
    return output


def sync_parts(rows, voice_id, shift, total, folder, notify):
    cache = STORE / "synced"
    cache.mkdir(exist_ok=True)
    voice = STORE / "voices" / voice_id / "voice.wav"
    parts = []
    engine = None
    inferred = cached = 0
    for index, row in enumerate(rows):
        count = row["stop"] - row["first"]
        shot = row["shot"]
        if shot:
            ident, start, end = shot["asset"], shot["start"], shot["end"]
        elif row.get("insertSpeaking"):
            ident, start, end = row["insert"], 0, 0
        else:
            parts.append(None)
            continue
        key = signature(
            "musetalk-v1",
            voice_id,
            row["first"],
            row["stop"],
            shift,
            ident,
            start,
            end,
        )
        path = cache / (key + ".mp4")
        if path.exists():
            parts.append(path)
            cached += count
            continue
        if engine is None:
            from .engine import MouthEngine

            notify(8, "正在载入本机 MuseTalk 口型模型")
            # Decode a band-limited inference copy of the final audio.
            raw = ff("-i", voice, "-ar", "16000", "-ac", "1", "-f", "f32le", "pipe:1")
            samples = np.frombuffer(raw, "<f4")
            samples = np.pad(samples, (0, max(0, total * 640 - len(samples))))
            engine = MouthEngine(samples)
        src = Frames(asset(ident), start, end)
        tmp = folder / (key + ".mp4")
        state = {}
        try:
            first_frame = src.next()
            with encoder(tmp, first_frame.shape[1::-1]) as sink:
                for j in range(0, count, 4):
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
                    notify(
                        10 + int(62 * (row["first"] + ix[-1]) / total),
                        f"口型推理 · 第 {index + 1} 句",
                    )
        except ValueError as exc:
            if row.get("insertSpeaking"):
                raise ValueError(f"补充素材口播失败：{exc} 可更换清晰的单人素材，或把用途改为「配图」。") from exc
            raise
        finally:
            src.close()
        tmp.replace(path)
        parts.append(path)
        inferred += count
    return parts, inferred, cached


def render(tl, folder, notify):
    size = SIZES[tl["aspect"]]
    voice = STORE / "voices" / tl["voice"] / "voice.wav"
    ass = folder / "captions.ass"
    write_ass(tl, ass)
    rows, total = tl["rows"], tl["frames"]
    parts, inferred, cached = sync_parts(rows, tl["voice"], tl["shift"], total, folder, notify)
    notify(76, "正在组合镜头、动态图文和字幕")
    output = folder / "film.mp4"
    from istream.render import _esc

    with encoder(
        output,
        size,
        "-i",
        voice,
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-vf",
        "subtitles='" + _esc(str(ass)) + "'",
        "-c:a",
        "aac",
        "-b:a",
        "160k",
    ) as sink:

        def section(row, part, n, talking):
            if n <= 0:
                return
            source = None
            try:
                if talking and part:
                    source = synced_frames(part, n)
                elif row["layout"] == "insert":
                    source = Frames(asset(row.get("insert") or tl["insert"]))
                elif row["shot"]:
                    s = row["shot"]
                    source = Frames(asset(s["asset"]), s["start"], s["end"])
                for _ in range(n):
                    f = source.next() if source else None
                    frame = compose(
                        f, row["layout"], size, tl["subtitles"], tl.get("framing", "cover")
                    )
                    sink.write(frame.tobytes())
            finally:
                if source:
                    source.close()

        cursor = 0
        for i, (row, part) in enumerate(zip(rows, parts)):
            if row["layout"] == "card" or row.get("insertSpeaking"):
                stop = total if i == len(rows) - 1 else row["stop"]
                write_insert_frames(sink, row, size, cursor, stop, part,
                                    subtitles=tl["subtitles"], framing=tl.get("framing", "cover"))
                cursor = stop
                continue
            section(row, None, row["first"] - cursor, False)
            section(row, part, row["stop"] - row["first"], True)
            cursor = row["stop"]
        section(rows[-1], None, total - cursor, False)
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

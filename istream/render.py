"""ffmpeg renderer in two stages around the lip-sync engine.

Stage A  lipsync-inputs : each visible run → host video at SOURCE resolution with temporal ops only (trim/reverse/speed) + VO slice
Stage B  lipsync        : engine adapters (lipsync.py) write lipsync/out/NN_synced.mp4 (passthrough = unsynced preview)
Stage C  composite      : synced runs → spatial ops (crop / punch / PiP / hide) → B-roll fades → MG overlays → captions → VO

Segments are content-hashed and cached, so re-rendering after an edit rebuilds only what changed (a build system for video).
Spec plates without footage render as labelled placeholder proxies (`placeholders/`), so plans can be watched before plates exist.
"""
import concurrent.futures as cf
import filecmp
import hashlib
import json
import math
import os
import shutil
import subprocess
import threading

from .lipsync import resolve_job_path

# Accept an explicit CJK font and native macOS locations as well as Linux Noto.
# The override also lets libass scan a small, project-owned font directory.
_FONT_CANDIDATES = (
    os.environ.get("ISTREAM_FONT"),
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Supplemental/Songti.ttc",
)
FONT = next((f for f in _FONT_CANDIDATES if f and os.path.isfile(f)), None)
NAVY, CYAN, WHITE, AMBER = "0x0C1424", "0x5FD4FF", "0xEAF4FF", "0xE8A86A"
_LOCK = threading.Lock()


def ff(args, cwd=None):
    p = subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-y"] + args, capture_output=True, text=True, cwd=cwd)
    if p.returncode and "Unrecognized option '/filter_complex'" in p.stderr and "-/filter_complex" in args:
        # Older FFmpeg releases load filter graphs with a dedicated script option.
        legacy_args = ["-filter_complex_script" if arg == "-/filter_complex" else arg for arg in args]
        return ff(legacy_args, cwd=cwd)
    if p.returncode != 0:
        raise RuntimeError("ffmpeg failed: " + " ".join(args[:12]) + " …\n" + p.stderr[-2000:])


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,r_frame_rate:format=duration", "-of", "json", path],
                         capture_output=True, text=True, check=True).stdout
    j = json.loads(out)
    n, d = j["streams"][0]["r_frame_rate"].split("/")
    fps = float(n) / float(d) if float(d) else 25.0
    return int(j["streams"][0]["width"]), int(j["streams"][0]["height"]), fps, float(j.get("format", {}).get("duration", 0.0) or 0.0)


def even(x):
    return int(round(x / 2.0)) * 2


def _h(*parts):
    return hashlib.sha1(json.dumps(parts, sort_keys=True, default=str).encode()).hexdigest()[:12]


def _esc(path):
    return path.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


class Renderer:
    def __init__(self, tl, cat, workdir, scale=1.0, base_dir=".", workers=4, crf=20):
        self.tl, self.cat, self.wd = tl, cat, workdir
        m = tl["meta"]
        self.W, self.H = even(m["size"][0] * scale), even(m["size"][1] * scale)
        self.fps = m["fps"]
        self.base = base_dir
        self.workers = workers
        self.crf = crf
        self._probe = {}
        for d in ("segments", "lipsync/in", "lipsync/out", "placeholders", "overlays"):
            os.makedirs(os.path.join(workdir, d), exist_ok=True)

    # ------------------------------------------------------------------ helpers
    def fr(self, t):
        return int(round(t * self.fps))

    def plate_path(self, pid):
        f = self.cat.plate_file(pid)
        if f and os.path.exists(f):
            return f
        return self.make_placeholder(pid)

    def psize(self, path):
        if path not in self._probe:
            self._probe[path] = probe(path)
        return self._probe[path]

    def make_placeholder(self, pid):
        """Labelled proxy for a plate that has not been generated yet (spec catalog)."""
        with _LOCK:              # workers share placeholders: build each once, atomically
            return self._make_placeholder(pid)

    def _make_placeholder(self, pid):
        p = self.cat.plates[pid]
        out = os.path.join(self.wd, "placeholders", f"{pid}.mp4")
        if os.path.exists(out):
            return out
        w, h = (even(p["size"][0] * 0.5), even(p["size"][1] * 0.5))
        dur = p["duration"]
        shots = [s for s in self.cat.shots.values() if s["plate"] == pid]
        fb = shots[0]["camera"].get("face_box") if shots else [0.4, 0.2, 0.2, 0.2]
        fx, fy, fw, fh = fb
        vf = [f"drawbox=x={fx * w - fw * w * 0.35:.0f}:y={(fy + fh) * h:.0f}:w={fw * w * 1.7:.0f}:h={h:.0f}:color=0x2E4468@1:t=fill",
              f"drawbox=x={fx * w:.0f}:y={fy * h:.0f}:w={fw * w:.0f}:h={fh * h:.0f}:color=0x9FB3D1@0.85:t=fill",
              f"drawbox=x={(fx + fw * 0.3) * w:.0f}:y={(fy + fh * 0.72) * h:.0f}:w={fw * w * 0.4:.0f}:h={fh * h * 0.08:.0f}:color=0x1C2A44@1:t=fill"]
        tf = os.path.join(self.wd, "placeholders", f"{pid}_title.txt")
        with open(tf, "w", encoding="utf-8") as f:
            f.write(f"SPEC PLACEHOLDER · {pid}")
        vf.append(f"drawtext=fontfile={FONT}:textfile={_esc(tf)}:fontcolor={WHITE}:fontsize={h * 0.028:.0f}:x=(w-text_w)/2:y=h*0.04")
        vf.append(f"drawtext=fontfile={FONT}:text='%{{pts\\:hms}}':fontcolor={CYAN}:fontsize={h * 0.024:.0f}:x=(w-text_w)/2:y=h*0.08")
        for s in shots:
            lf = os.path.join(self.wd, "placeholders", f"{s['id']}.txt")
            with open(lf, "w", encoding="utf-8") as f:
                f.write(f"{s['id']} · {'/'.join(s['edit']['roles'][:2])} · {s['performance']['emotion']}")
            vf.append(f"drawtext=fontfile={FONT}:textfile={_esc(lf)}:fontcolor={AMBER}:fontsize={h * 0.026:.0f}:x=(w-text_w)/2:y=h*0.9:"
                      f"enable='between(t,{s['src']['in']},{s['src']['out']})'")
        tmp = out[:-4] + ".tmp.mp4"
        ff(["-f", "lavfi", "-i", f"color=c=0x1C2A44:s={w}x{h}:r=25:d={dur}", "-vf", ",".join(vf), "-c:v", "libx264", "-preset", "ultrafast", "-crf", "26",
            "-pix_fmt", "yuv420p", tmp])
        os.replace(tmp, out)
        return out

    def vo_path(self):
        v = self.tl["meta"].get("vo")
        if not v:
            return None
        p = v if os.path.isabs(v) else os.path.normpath(os.path.join(self.base, v))
        return p if os.path.exists(p) else None

    # ------------------------------------------------------------------ stage A
    def _temporal_seg(self, c):
        """one clip, temporal ops only, at source resolution and timeline fps"""
        ops = {o["op"]: o for o in c.get("ops", [])}
        rate = ops.get("speed", {}).get("rate", 1.0)
        if isinstance(rate, bool) or not isinstance(rate, (int, float)) or not 0.85 <= rate <= 1.15:
            raise ValueError("speed rate must be a number between 0.85 and 1.15")
        rate = float(rate)
        src = self.plate_path(c["plate"])
        n = self.fr(c["rec"]["out"]) - self.fr(c["rec"]["in"])
        key = _h("tseg", src, c["src"], n, rate, "reverse" in ops, self.fps)
        out = os.path.join(self.wd, "segments", f"t_{key}.mp4")
        if os.path.exists(out):
            return out
        vf = []
        if rate != 1.0:
            vf.append(f"setpts=PTS/{rate}")
        vf.append(f"fps={self.fps}")
        if "reverse" in ops:
            vf.append("reverse")
        vf.append("setsar=1")
        dur = (c["src"]["out"] - c["src"]["in"]) + 0.5
        ff(["-ss", f"{c['src']['in']:.3f}", "-t", f"{dur:.3f}", "-i", src, "-vf", ",".join(vf), "-frames:v", str(n), "-an",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", out])
        return out

    def stage_lipsync_inputs(self, jobs):
        for job in jobs["jobs"]:
            for path in (job["inputs"]["video"], job["inputs"]["audio"], job["output"]):
                resolve_job_path(self.wd, path)
        clips = {c["id"]: c for c in self.tl["host"]}
        vo = self.vo_path()
        with cf.ThreadPoolExecutor(self.workers) as ex:
            segmap = dict(zip([cid for j in jobs["jobs"] for cid in j["clips"]],
                              ex.map(self._temporal_seg, [clips[cid] for j in jobs["jobs"] for cid in j["clips"]])))
        for j in jobs["jobs"]:
            vin = resolve_job_path(self.wd, j["inputs"]["video"])
            lst = resolve_job_path(self.wd, os.path.join("lipsync", "in", f"{j['id']}.txt"))
            with open(lst, "w") as f:
                for cid in j["clips"]:
                    f.write(f"file '{os.path.abspath(segmap[cid])}'\n")
            # different plates may differ in size: normalise to the first clip's size
            sizes = {self.psize(segmap[cid])[:2] for cid in j["clips"]}
            if len(sizes) == 1:
                ff(["-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", vin])
            else:
                w, h = self.psize(segmap[j["clips"][0]])[:2]
                ff(["-f", "concat", "-safe", "0", "-i", lst, "-vf", f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setsar=1",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", vin])
            ain = resolve_job_path(self.wd, j["inputs"]["audio"])
            off = self.tl["meta"].get("vo_offset", 0.0)
            if vo:
                ff(["-ss", f"{max(0.0, j['rec']['in'] - off):.3f}", "-t", f"{j['seconds']:.3f}", "-i", vo, "-ac", "1", "-ar", "48000", ain])
            else:
                ff(["-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono", "-t", f"{j['seconds']:.3f}", ain])
        return jobs

    # ------------------------------------------------------------------ stage C
    def _region(self, sw, sh, ops, face):
        fx, fy = face
        rx, ry, rw, rh = 0.0, 0.0, float(sw), float(sh)
        out_aspect = self.W / self.H
        crop = ops.get("crop")
        if crop or abs(rw / rh - out_aspect) > 0.01:
            cx = crop["cx"] if crop else fx
            if rw / rh > out_aspect:
                nw = rh * out_aspect
                rx = min(max(cx * sw - nw / 2, 0), sw - nw)
                rw = nw
            else:
                nh = rw / out_aspect
                ry = min(max(fy * sh - nh * 0.35, 0), sh - nh)
                rh = nh
        s = ops.get("scale", {}).get("s", 1.0)
        if s > 1.0:
            ax = min(max((fx * sw - rx) / rw, 0), 1)
            ay = min(max((fy * sh - ry) / rh, 0), 1)
            zw, zh = rw / s, rh / s
            rx, ry, rw, rh = rx + ax * (rw - zw), ry + ay * (rh - zh), zw, zh
        return [int(round(v)) for v in (rw, rh, rx, ry)]

    def _mask(self, d, ring=False):
        out = os.path.join(self.wd, "overlays", f"{'ring' if ring else 'mask'}_{d}.png")
        if not os.path.exists(out):
            r = d / 2
            if ring:
                expr = f"format=rgba,geq=r=95:g=212:b=255:a='255*between(hypot(X-{r},Y-{r}),{r - 4},{r - 1})'"
                ff(["-f", "lavfi", "-i", f"color=c=black:s={d}x{d}", "-vf", expr, "-frames:v", "1", out])
            else:
                ff(["-f", "lavfi", "-i", f"color=c=black:s={d}x{d}", "-vf", f"format=gray,geq=lum='255*lte(hypot(X-{r},Y-{r}),{r - 2})'", "-frames:v", "1", out])
        return out

    def _visible_seg(self, c, job, synced):
        n = self.fr(c["rec"]["out"]) - self.fr(c["rec"]["in"])
        a = self.fr(c["rec"]["in"]) - self.fr(job["rec"]["in"])
        sw, sh, _, _ = self.psize(synced)
        shot = self.cat.shots[c["shot"]]
        face = shot.face_center()
        ops = {o["op"]: o for o in c.get("ops", [])}
        hm = {x["id"]: x for x in self.tl["host"]}
        jsig = [(hm[cid]["src"], [o for o in hm[cid].get("ops", []) if o["op"] in ("reverse", "speed")], hm[cid]["rec"]) for cid in job["clips"] if cid in hm]
        key = _h("vseg", jsig, os.path.getsize(synced), a, n, ops, self.W, self.H, c["layout"])   # content-keyed: survives job renumbering
        out = os.path.join(self.wd, "segments", f"v_{key}.mp4")
        if os.path.exists(out):
            return out, 0, 0
        trim = f"trim=start_frame={a}:end_frame={a + n},setpts=PTS-STARTPTS"
        rw, rh, rx, ry = self._region(sw, sh, ops, face)
        if "pip" in ops:
            pip = ops["pip"]
            D = even(pip["size"] * min(self.W, self.H))
            side = int(min(rw, rh) * 0.62)
            fxp, fyp = face[0] * sw, face[1] * sh
            px = int(min(max(fxp - side / 2, 0), sw - side))
            py = int(min(max(fyp - side * 0.42, 0), sh - side))
            m = int(0.045 * min(self.W, self.H))
            corner = pip["corner"]
            ox = m if corner in ("bl", "tl") else self.W - D - m
            if self.H > self.W:
                oy = int(self.H * 0.60 - D) if corner in ("bl", "br") else int(self.H * 0.12)
            else:
                oy = self.H - D - m - int(self.H * 0.12) if corner in ("bl", "br") else m
            fc = (f"[0:v]{trim},split[a][b];"
                  f"[a]crop={rw}:{rh}:{rx}:{ry},scale={self.W}:{self.H}:flags=bicubic,gblur=sigma={0.022 * self.W:.1f},eq=brightness=-0.07:saturation=0.85[bg];"
                  f"[b]crop={side}:{side}:{px}:{py},scale={D}:{D}:flags=lanczos,format=rgba[h];[1:v]format=gray,scale={D}:{D}[mk];[h][mk]alphamerge[hm];"
                  f"[bg][hm]overlay={ox}:{oy}[o1];[o1][2:v]overlay={ox}:{oy},setsar=1[v]")
            ff(["-i", synced, "-loop", "1", "-i", self._mask(D), "-loop", "1", "-i", self._mask(D, ring=True), "-filter_complex", fc, "-map", "[v]", "-frames:v", str(n), "-r", str(self.fps),
                "-c:v", "libx264", "-preset", "veryfast", "-crf", str(self.crf), "-pix_fmt", "yuv420p", out])
        else:
            vf = f"{trim},crop={rw}:{rh}:{rx}:{ry},scale={self.W}:{self.H}:flags=lanczos,setsar=1"
            ff(["-i", synced, "-vf", vf, "-frames:v", str(n), "-r", str(self.fps), "-c:v", "libx264", "-preset", "veryfast", "-crf", str(self.crf), "-pix_fmt", "yuv420p", out])
        return out, 0, 0

    def _hidden_seg(self, c, ref, h_in, h_out):
        """B-roll / card span: the studio defocuses behind the content (blurred plate of the neighbouring shot)."""
        n = self.fr(c["rec"]["out"]) - self.fr(c["rec"]["in"]) + h_in + h_out
        by = next((o["by"] for o in c.get("ops", []) if o["op"] == "hide"), "card")
        if ref is None:
            ff_in = ["-f", "lavfi", "-i", f"color=c=0x1C2A44:s={self.W}x{self.H}:r={self.fps}"]
            vf = "null"
            key = _h("hseg-solid", n, by, self.W, self.H)
        else:
            shot = self.cat.shots[ref["shot"]]
            src = self.plate_path(ref["plate"])
            sw, sh, pfps, pdur = self.psize(src)
            L = n / self.fps
            t0 = min(max(0.0, ref["src"]["out"]), max(0.0, pdur - L - 0.1))
            ops = {o["op"]: o for o in ref.get("ops", []) if o["op"] == "crop"}
            rw, rh, rx, ry = self._region(sw, sh, ops, shot.face_center())
            ff_in = ["-ss", f"{t0:.3f}", "-t", f"{L + 0.5:.3f}", "-i", src]
            vf = (f"fps={self.fps},crop={rw}:{rh}:{rx}:{ry},scale={self.W}:{self.H}:flags=bicubic,gblur=sigma={0.03 * self.W:.1f},"
                  f"eq=brightness=-0.10:saturation=0.85")
            key = _h("hseg", src, t0, n, rw, rh, rx, ry, self.W, self.H, by)
        if by.startswith("broll:"):
            tf = os.path.join(self.wd, "overlays", f"broll_{key}.txt")
            with open(tf, "w", encoding="utf-8") as f:
                f.write("B-ROLL 待替换 · " + by.split(":", 1)[1])
            vert = self.H > self.W
            fsz = "h*0.018" if vert else "h*0.03"
            vf += (f",drawbox=x=iw*0.04:y=ih*0.05:w=iw*{0.92 if vert else 0.5}:h=ih*{0.04 if vert else 0.055}:color={NAVY}@0.6:t=fill,"
                   f"drawtext=fontfile={FONT}:textfile={_esc(tf)}:fontcolor={AMBER}:fontsize={fsz}:x=w*0.06:y=h*{0.06 if vert else 0.063}")
        out = os.path.join(self.wd, "segments", f"h_{key}.mp4")
        if not os.path.exists(out):
            ff(ff_in + ["-vf", vf + ",setsar=1", "-frames:v", str(n), "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", str(self.crf), "-pix_fmt", "yuv420p", out])
        return out, h_in, h_out

    def _mg_filters(self, items, base_label, next_input):
        """MG overlay chain. Asset PNGs (full-frame, same aspect) are overlaid with alpha fades; templates without assets
        render as flat preview cards (production MG goes through the Glass Protocol compositor)."""
        fc, inputs, cur, k = [], [], base_label, next_input
        placed = []          # (zone, a, b, slot) — simultaneous flat cards in one zone stack instead of overlapping
        for m in items:
            a, b = m["rec"]["in"], m["rec"]["out"]
            D = b - a
            asset = m.get("asset")
            if asset and not os.path.isabs(asset):
                asset = os.path.normpath(os.path.join(self.base, asset))
            if asset and os.path.exists(asset):
                aw, ah, _, _ = self.psize(asset)
                if abs(aw / ah - self.W / self.H) < 0.02:
                    inputs += ["-loop", "1", "-framerate", str(self.fps), "-t", f"{D + 0.1:.3f}", "-i", asset]
                    fc.append(f"[{k}:v]scale={self.W}:{self.H},format=rgba,fade=t=in:st=0:d=0.25:alpha=1,fade=t=out:st={max(0.0, D - 0.3):.3f}:d=0.3:alpha=1,"
                              f"setpts=PTS-STARTPTS+{a:.3f}/TB[mg{k}]")
                    fc.append(f"[{cur}][mg{k}]overlay=0:0:eof_action=pass:enable='between(t,{a:.3f},{b:.3f})'[o{k}]")
                    cur = f"o{k}"
                    k += 1
                    continue
            text = (m.get("text") or "").strip()
            if not text and m["template"] not in ("follow_pill",):
                continue
            if m["template"] == "follow_pill":
                text = text or "＋ 关注"
            tf = os.path.join(self.wd, "overlays", f"mg_{m['id']}.txt")
            with open(tf, "w", encoding="utf-8") as f:
                f.write(text)
            W, H = self.W, self.H
            fs = int(min(W, H) * (0.06 if m["zone"] == "full" else 0.042))
            boxw = min(W * 0.86, fs * (len(text) * 1.05 + 1.6))
            boxh = fs * 1.9
            z = m["zone"]
            if z == "right_half":
                x, y = W * 0.56, H * 0.36
            elif z == "left_half":
                x, y = W * 0.06, H * 0.36
            elif z == "upper_band":
                x, y = (W - boxw) / 2, H * 0.10
            elif z == "full":
                x, y = (W - boxw) / 2, (H - boxh) / 2
            else:
                x, y = (W - boxw) / 2, H * (0.62 if H > W else 0.70)
            slot = 0
            while any(z0 == z and a0 < b and b0 > a and s0 == slot for z0, a0, b0, s0 in placed):
                slot += 1
            placed.append((z, a, b, slot))
            y += slot * (boxh + fs * 0.4) * (-1 if z in ("lower_third",) else 1)
            en = f"enable='between(t,{a:.3f},{b:.3f})'"
            fc.append(f"[{cur}]drawbox=x={x:.0f}:y={y:.0f}:w={boxw:.0f}:h={boxh:.0f}:color={NAVY}@0.62:t=fill:{en},"
                      f"drawbox=x={x:.0f}:y={y:.0f}:w={boxw:.0f}:h={boxh:.0f}:color={CYAN}@0.85:t=2:{en},"
                      f"drawtext=fontfile={FONT}:textfile={_esc(tf)}:fontcolor={WHITE}:fontsize={fs}:x={x:.0f}+({boxw:.0f}-text_w)/2:y={y:.0f}+({boxh:.0f}-text_h)/2:{en}[t{m['id']}]")
            cur = f"t{m['id']}"
        return fc, inputs, cur, k

    def _ass(self, path):
        W, H = self.W, self.H
        vertical = H > W
        fs = int(H * (0.034 if vertical else 0.05))
        mv = int(H * (0.22 if vertical else 0.06))
        off = 0.0

        def ts(t):
            t = max(0.0, t + off)
            return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"
        lines = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "WrapStyle: 2", "",
                 "[V4+ Styles]",
                 "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
                 f"Style: Cap,Noto Sans CJK SC,{fs},&H00FFF4EA,&H00FFFFFF,&H00241410,&H80241410,-1,0,0,0,100,100,1,0,1,{max(2, fs // 14)},{max(1, fs // 28)},2,40,40,{mv},1",
                 "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
        for cpt in self.tl.get("captions", []):
            lines.append(f"Dialogue: 0,{ts(cpt['rec']['in'])},{ts(cpt['rec']['out'])},Cap,,0,0,0,,{cpt['text']}")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        return path

    def stage_composite(self, jobs, out_path, captions=True, mg=True, fade_frames=6, grain=0):
        host = self.tl["host"]
        jobmap = {cid: j for j in jobs["jobs"] for cid in j["clips"]}
        tasks = []
        last_vis = None
        for i, c in enumerate(host):
            if c["layout"] != "hidden" and c.get("shot"):
                j = jobmap[c["id"]]
                vin = resolve_job_path(self.wd, j["inputs"]["video"])
                synced = resolve_job_path(self.wd, j["output"])
                if not os.path.exists(synced) or filecmp.cmp(vin, synced, shallow=False):
                    # not lip-synced (preview / passthrough): pixels depend only on the clip → read its cached temporal
                    # segment so an edit rebuilds only the clips it touched
                    tasks.append(("v", c, {"rec": c["rec"], "clips": [c["id"]]}, self._temporal_seg(c)))
                else:
                    tasks.append(("v", c, j, synced))
                last_vis = c
            else:
                ref = last_vis or next((x for x in host[i + 1:] if x.get("shot")), None)
                vis = lambda x: x is not None and x["layout"] != "hidden" and x.get("shot")
                prv = host[i - 1] if i > 0 else None
                nxt = host[i + 1] if i + 1 < len(host) else None
                # handles only on sides that touch a visible host clip (hidden→hidden joins are cuts)
                h_in = fade_frames if (vis(prv) and c.get("transition_in") == "broll_fade") else 0
                h_out = fade_frames if (vis(nxt) and nxt.get("transition_in") == "broll_fade") else 0
                tasks.append(("h", c, ref, h_in, h_out))

        def run(t):
            return self._visible_seg(t[1], t[2], t[3]) if t[0] == "v" else self._hidden_seg(t[1], t[2], t[3], t[4])
        with cf.ThreadPoolExecutor(self.workers) as ex:
            segs = list(ex.map(run, tasks))
        # assemble: concat for cuts, xfade (fade) where a hidden span meets the host
        args, fc = [], []
        TB = f"settb=1/{self.fps * 1000},fps={self.fps}"
        for i, (p, _, _) in enumerate(segs):
            args += ["-i", p]
            fc.append(f"[{i}:v]setpts=PTS-STARTPTS,{TB}[n{i}]")
        cur, running = "n0", 0.0
        d = fade_frames / self.fps
        prev_hout = segs[0][2]
        running = (self.fr(host[0]["rec"]["out"]) - self.fr(host[0]["rec"]["in"])) / self.fps + segs[0][1] / self.fps + prev_hout / self.fps
        if segs[0][1]:
            fc.append(f"[n0]trim=start_frame={segs[0][1]},setpts=PTS-STARTPTS[s0]")
            cur = "s0"
            running -= segs[0][1] / self.fps
        for i in range(1, len(segs)):
            p, h_in, h_out = segs[i]
            c = host[i]
            L = (self.fr(c["rec"]["out"]) - self.fr(c["rec"]["in"])) / self.fps
            fade = c.get("transition_in") == "broll_fade" and (h_in or prev_hout)
            if fade:
                fc.append(f"[{cur}][n{i}]xfade=transition=fade:duration={d:.4f}:offset={running - d:.4f},{TB}[x{i}]")
                running += L + (h_in + h_out) / self.fps - d
            else:
                fc.append(f"[{cur}][n{i}]concat=n=2:v=1:a=0,{TB}[x{i}]")
                running += L + (h_in + h_out) / self.fps
            cur = f"x{i}"
            prev_hout = h_out
        k = len(segs)
        if grain and grain > 0:
            # one uniform fine grain over the host layer (after lip-sync, before MG/captions): unifies the smoother
            # lip-sync mouth patch with the rest of the face — see docs/HUMAN_PREMIUM.md P1-10
            fc.append(f"[{cur}]noise=alls={int(grain)}:allf=t+u[grn]")
            cur = "grn"
        if mg and self.tl.get("mg"):
            mfc, minputs, cur, k = self._mg_filters(self.tl["mg"], cur, k)
            fc += mfc
            args += minputs
        if captions and self.tl.get("captions"):
            ass = self._ass(os.path.join(self.wd, "captions.ass"))
            fc.append(f"[{cur}]subtitles=filename='{_esc(os.path.abspath(ass))}':fontsdir='{_esc(os.path.dirname(FONT))}'[vcap]")
            cur = "vcap"
        fc.append(f"[{cur}]format=yuv420p[vout]")
        vo = self.vo_path()
        dur = self.tl["meta"]["duration"]
        if vo:
            args += ["-i", vo]
            off = self.tl["meta"].get("vo_offset", 0.0)
            fc.append(f"[{k}:a]adelay={int(off * 1000)}:all=1,apad[aout]" if off > 0 else f"[{k}:a]apad[aout]")
        else:
            args += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
            fc.append(f"[{k}:a]anull[aout]")
        script = os.path.join(self.wd, "composite.filtergraph")
        with open(script, "w", encoding="utf-8") as f:
            f.write(";\n".join(fc))
        ff(args + ["-/filter_complex", script, "-map", "[vout]", "-map", "[aout]", "-t", f"{dur:.3f}", "-r", str(self.fps),
                   "-c:v", "libx264", "-preset", "medium", "-crf", str(self.crf), "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out_path])
        return out_path

"""Regressions for the website's audio-locked timeline and visible-only rendering."""

import io
import importlib.util
import json
import shutil
import tempfile
import types
import unittest
import wave
from pathlib import Path
from unittest.mock import patch


@unittest.skipUnless(
    all(importlib.util.find_spec(x) for x in ("flask", "numpy", "cv2")),
    "install studio/requirements.txt for website tests",
)
class StudioWorkflow(unittest.TestCase):
    def setUp(self):
        from studio import media, production
        from studio import __main__ as server

        tmp = (
            self.enterContext(tempfile.TemporaryDirectory())
            if hasattr(self, "enterContext")
            else None
        )
        if tmp is None:
            temp = tempfile.TemporaryDirectory()
            self.addCleanup(temp.cleanup)
            tmp = temp.name
        store = Path(tmp) / "store"
        for mod in (media, production, server):
            ctx = patch.object(mod, "STORE", store)
            ctx.start()
            self.addCleanup(ctx.stop)
        ctx = patch.object(media, "ROOT", Path(tmp))
        ctx.start()
        self.addCleanup(ctx.stop)
        media.init()
        self.server = server
        self.media = media
        self.production = production
        self.client = server.app.test_client()
        self.headers = {"X-Studio-Request": "1"}

    def test_studio_deep_links_load_the_workbench(self):
        stages = ("materials", "clips", "voice", "shots", "style", "review")
        paths = ["/studio", "/studio/library", "/studio/exports", *("/studio/steps/" + s for s in stages)]
        for path in paths:
            for suffix in ("", "/"):
                with self.subTest(path=path + suffix), self.client.get(path + suffix) as response:
                    self.assertEqual(response.status_code, 200)
                    self.assertIn(b'id="inspector"', response.data)
        for path in ("/studio/unknown", "/studio/steps/unknown"):
            self.assertEqual(self.client.get(path).status_code, 404)

    def test_system_voice_catalog_and_synthesis_keep_locale_and_saved_ids(self):
        listing = "\n".join((
            "Reed (中文（中国大陆）)    zh_CN    # 你好。",
            "Tingting    zh_CN    # 你好。",
            "Reed (中文（台湾）)    zh_TW    # 你好。",
            "Bad News    en_US    # Hello!",
        ))
        media = self.media
        with patch.object(media.shutil, "which", return_value="/usr/bin/say"), patch.object(
            media.subprocess, "run", return_value=types.SimpleNamespace(stdout=listing)
        ):
            session = self.client.get("/api/session").json
            self.assertTrue(session["engine"]["tts"])
            voices = {v["id"]: v for v in session["systemVoices"]}
            self.assertEqual(set(voices), {"reed", "tingting", "system:zh-TW:Reed (中文（台湾）)", "system:en-US:Bad News"})
            taiwan = next(v for v in voices.values() if v["locale"] == "zh-TW")
            with patch.object(media, "run") as say, patch.object(
                media, "read_pcm", return_value=media.np.ones(4800, dtype="<i2")
            ):
                def synth(voice):
                    return media.prepare_voice({"voice": voice, "text": "这是第一句。这是第二句。"})
                result = synth(taiwan["id"])
                self.assertEqual([c.args[0][2] for c in say.call_args_list], [taiwan["name"]] * 2)
                self.assertEqual(len(result["lines"]), 2)
                self.assertNotEqual(synth("reed")["id"], result["id"])
        with patch.object(media.shutil, "which", return_value=None):
            session = self.client.get("/api/session").json
            self.assertFalse(session["engine"]["tts"])
            self.assertEqual(session["systemVoices"], [])
            self.assertEqual(synth(taiwan["id"]), result)
            with self.assertRaisesRegex(ValueError, "本机找不到"):
                media.prepare_voice({"voice": taiwan["id"], "text": "新的台词。"})

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg required")
    def test_reference_upload_is_a_reusable_voice_and_never_replays_the_sample(self):
        import numpy as np
        media = self.media
        def upload_reference(transcript, silent=False):
            file = io.BytesIO()
            with wave.open(file, "wb") as wav:
                wav.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
                pcm = np.sin(np.arange(32000) * .2) * (0 if silent else 5000)
                wav.writeframes(pcm.astype("<i2").tobytes())
            file.seek(0)
            return self.client.post("/api/assets", headers=self.headers, data={
                "file": (file, "sample.wav"), "name": " 我的音色 ", "role": "personal_voice",
                "transcript": transcript,
            })

        for response in (upload_reference(" "), upload_reference("参考句。", silent=True),
                         upload_reference("参考录音只读了一句话。" * 12)):
            self.assertEqual(response.status_code, 400)
        self.assertFalse(list((media.STORE / "assets").glob("personal-*")))
        src = upload_reference("参考句。")
        self.assertEqual(src.status_code, 201, src.json)
        profile = src.json
        self.assertEqual(profile["name"], "我的音色")
        self.assertEqual(profile["role"], "personal_voice")
        self.assertEqual(profile["transcript"], "参考句。")
        self.assertIn(profile, self.client.get("/api/session").json["assets"])
        ref = self.client.get(f"/api/assets/{profile['id']}/reference")
        with ref, wave.open(io.BytesIO(ref.data), "rb") as wav:
            self.assertEqual((wav.getframerate(), wav.getnframes()), (24000, 48000))

        cfg = {"voice": profile["id"], "text": "今天下雨。明天放晴。"}
        original_run = media.subprocess.run
        def fake_worker(args, **kwargs):
            if args[0] != media.VOICE_PYTHON:
                return original_run(args, **kwargs)
            request = json.loads(kwargs["input"])
            self.assertEqual(request["transcript"], "参考句。")
            self.assertEqual(request["lines"], ["今天下雨。", "明天放晴。"])
            self.assertEqual(request["maxSeconds"], self.media.MAX_NARRATION_SECONDS)
            for i in range(2):
                media.write_wav(args[-1] / f"{i}.wav", np.ones(4800, dtype="<i2"))
            return types.SimpleNamespace(returncode=0)

        with patch.object(media, "personal_voice_ready", return_value=False):
            lookup = self.client.post("/api/voice?cached=1", headers=self.headers, json=cfg)
            self.assertEqual(lookup.status_code, 200)
            self.assertIsNone(lookup.json)
            unavailable = self.client.post("/api/voice", headers=self.headers, json=cfg)
            self.assertEqual(unavailable.status_code, 400)
            self.assertIn("缺少", unavailable.json["error"])
        with patch.object(media, "personal_voice_ready", return_value=True), patch.object(
            media.subprocess, "run", side_effect=fake_worker
        ):
            generated = self.client.post("/api/voice", headers=self.headers, json=cfg)
        self.assertEqual(generated.status_code, 200, generated.json)
        self.assertEqual(generated.json["method"], "个人音色逐句合成")
        self.assertAlmostEqual(generated.json["duration"], 0.48)
        with patch.object(self.server.executor, "submit", side_effect=AssertionError("cached voice queued for synthesis")):
            self.assertEqual(self.client.post("/api/voice", headers=self.headers, json=cfg).json, generated.json)
            self.assertEqual(self.client.post("/api/voice?cached=1", headers=self.headers, json=cfg).json, generated.json)
        with patch.object(media, "personal_voice_ready", return_value=False):
            self.assertEqual(media.prepare_voice(cfg), generated.json)
        edit_url = f"/api/assets/{profile['id']}/transcript"
        def edit(text):
            return self.client.post(edit_url, headers=self.headers, json={"transcript": text})
        self.assertEqual(edit("过长" * 80).status_code, 400)
        self.assertEqual(media.asset(profile["id"])["transcript"], "参考句。")
        self.assertEqual(edit("真实参考句。").status_code, 200)
        with patch.object(media, "personal_voice_ready", return_value=False):
            with self.assertRaisesRegex(ValueError, "缺少"):
                media.prepare_voice(cfg)  # A correction must not replay cached audio from the old transcript.
        self.assertEqual(edit("参考句。").status_code, 200)
        self.assertEqual(media.prepare_voice(cfg), generated.json)

    def test_long_narration_keeps_the_last_sentence_on_the_export_timeline(self):
        media = self.media
        text = "前面的句子。" * 16 + "最后一句要读完。"
        cfg = {"voice": "reed", "text": text}
        with patch.object(media, "RATE", 1000):
            clips = [media.np.ones(7330, dtype="<i2")] * 16 + [media.np.ones(5000, dtype="<i2")]
            with patch.object(media, "synthesized_lines", return_value=clips):
                voice = media.prepare_voice(cfg)
            self.assertAlmostEqual(voice["lines"][-1]["start"], 119.52)
            self.assertAlmostEqual(voice["lines"][-1]["end"], 124.52)
            self.assertAlmostEqual(voice["duration"], 124.66)
            with wave.open(str(media.STORE / "voices" / voice["id"] / "voice.wav")) as wav:
                self.assertEqual(wav.getnframes(), 124660)
            plan = self.production.plan(dict(voiceId=voice["id"], style="editorial", aspect="16:9",
                                             lines=[dict(line, layout="card") for line in voice["lines"]]))
            self.assertEqual(len(plan["rows"]), 17)
            self.assertEqual(plan["frames"], 3117)
            self.assertEqual(plan["rows"][-1]["text"], "最后一句要读完。")
            with patch.object(media, "MAX_NARRATION_SECONDS", 120), patch.object(
                media, "synthesized_lines", return_value=clips
            ), self.assertRaisesRegex(ValueError, "第 17 句.*120 秒"):
                media.prepare_voice(dict(cfg, text=text + "再加一句。"))

    def test_long_recording_has_a_separate_limit_from_source_clips(self):
        media = self.media
        info = {"format": {"duration": "125"}, "streams": [{"codec_type": "audio"}]}
        with patch.object(media, "inspect_file", return_value=info):
            asset = media.build_asset(Path("long.wav"), "audio", "audio", "整篇录音", "long")
            self.assertEqual(asset["duration"], 125)
            with self.assertRaisesRegex(ValueError, "120 秒"):
                media.build_asset(Path("ref.wav"), "audio", "personal_voice", "参考音色", "ref")
            info["format"]["duration"] = "600.01"
            with self.assertRaisesRegex(ValueError, "600 秒"):
                media.build_asset(Path("long.wav"), "audio", "audio", "整篇录音", "long")

    def test_lipsync_dependencies_follow_the_selected_model(self):
        from studio.setup_models import EDTALK_FILE
        with tempfile.TemporaryDirectory() as tmp, patch.object(self.server, "MODELS", Path(tmp)), patch(
            "importlib.util.find_spec", return_value=True
        ):
            for name in ("studio/yunet.onnx", "studio/2dfan4.onnx", EDTALK_FILE):
                path = Path(tmp) / name
                path.parent.mkdir(exist_ok=True)
                path.touch()
            self.server.require_lipsync("edtalk")
            with self.assertRaisesRegex(ValueError, "MuseTalk"):
                self.server.require_lipsync("musetalk")
        self.assertEqual(self.production.selected_model({}), "musetalk")
        for invalid in (None, [], "unknown"):
            with self.assertRaisesRegex(ValueError, "口型模型"):
                self.production.selected_model({"lipModel": invalid})

    def test_model_list_reports_missing_components_separately(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(self.server, "MODELS", Path(tmp)), patch.object(
            self.media, "personal_voice_missing", return_value=[]
        ):
            (Path(tmp) / "studio").mkdir()
            (Path(tmp) / "studio/yunet.onnx").touch()
            engine = self.client.get("/api/session").json["engine"]
        models = {m["name"]: m["missing"] for m in engine["models"]}
        self.assertTrue(engine["personalVoice"])
        self.assertFalse(engine["ready"])
        self.assertFalse(models["YuNet"])
        self.assertFalse(models["Qwen3-TTS 0.6B Base · 4-bit"])
        self.assertIn("studio/2dfan4.onnx", models["2DFAN4"])
        self.assertIn("musetalk-1.5-fp16/whisper_encoder.safetensors", models["Whisper 音频编码器"])

    def test_hidden_clip_and_alignment(self):
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            self.skipTest("ffmpeg + ffprobe required")
        wav = io.BytesIO()
        with wave.open(wav, "wb") as f:
            f.setparams((1, 2, 48000, 0, "NONE", "not compressed"))
            f.writeframes(bytes(96000))
        wav.seek(0)
        src = self.client.post(
            "/api/assets",
            data={"file": (wav, "voice.wav"), "role": "audio"},
            headers=self.headers,
        )
        self.assertEqual(src.status_code, 201, src.json)
        voice = self.client.post(
            "/api/voice",
            json={"voice": src.json["id"], "text": "第一句。第二句。"},
            headers=self.headers,
        ).json
        self.assertEqual(voice["duration"], 1)
        lines = [dict(l, layout="card") for l in voice["lines"]]
        cfg = dict(
            voiceId=voice["id"], lines=lines, hosts=[], style="editorial", aspect="16:9"
        )
        tl = self.production.plan(cfg)
        self.assertTrue(all(row["shot"] is None for row in tl["rows"]))
        folder = self.media.STORE / "job"
        folder.mkdir()
        with patch.dict("sys.modules", {"studio.engine": None}):
            result = self.production.render(tl, folder, lambda *_: None)
        self.assertEqual(
            (result["frames"], result["inferred"], result["skipped"]), (25, 0, 25)
        )
        # The selected visual must reach the encoded card even when ordinary captions are off.
        import cv2 as cv
        import numpy as np

        photo = np.full((96, 72, 3), (220, 30, 200), np.uint8)
        uploaded = self.client.post(
            "/api/assets", data={"file": (io.BytesIO(cv.imencode(".png", photo)[1]), "card.png"),
                                 "role": "insert"}, headers=self.headers,
        )
        self.assertEqual(uploaded.status_code, 201)
        for aspect, size in self.production.SIZES.items():
            cfg.update(insert=uploaded.json["id"], aspect=aspect, subtitles=False)
            tl = self.production.plan(cfg)
            self.assertEqual(tl["rows"][0]["insert"], uploaded.json["id"])
            with patch.dict("sys.modules", {"studio.engine": None}):
                self.production.render(tl, folder, lambda *_: None)
            video = cv.VideoCapture(str(folder / "film.mp4"))
            try:
                video.set(cv.CAP_PROP_POS_FRAMES, 6)
                ok, frame = video.read()
            finally:
                video.release()
            self.assertTrue(ok)
            w, h = self.production.card_visual_size(*size)
            self.assertGreater(int(frame[h // 2, w // 2, 0]), 180)
            x1, y1, x2, y2 = self.production.caption_box("card", *size, card_image=True)
            self.assertGreater(np.count_nonzero(np.all(frame[y1:y2, x1:x2] > 215, axis=2)), 10)
        lines[1]["start"] = 0
        with self.assertRaisesRegex(ValueError, "重叠"):
            self.production.plan(cfg)

    def test_first_host_is_the_only_speaker_even_in_old_multi_host_drafts(self):
        for ident, role in (("video", "host"), ("beach", "host"), ("beach-insert", "insert")):
            self.media.save_asset(dict(id=ident, role=role, shots=[
                dict(asset=ident, id=f"{ident}-{i}", enabled=True, start=0, end=3)
                for i in (1, 2)
            ]))
        layouts = ["full", "split", "pip", "card", "insert"]
        lines = [dict(text=k, layout=k, start=i, end=i + 1) for i, k in enumerate(layouts)]
        cfg = dict(voiceId="voice", style="studio", aspect="16:9", hosts=["video", "beach"],
                   insert="beach-insert", lines=lines)
        with patch.object(self.production, "load_voice", return_value=dict(duration=5, lines=lines)):
            tl = self.production.plan(cfg)
            self.assertEqual(tl["primaryHost"], "video")
            self.assertEqual([r["shot"] and r["shot"]["asset"] for r in tl["rows"]],
                             ["video", "video", "video", None, None])
            self.assertEqual([r["insert"] for r in tl["rows"]], [None] * 3 + ["beach-insert"] * 2)
            self.assertNotEqual(tl["rows"][0]["shot"]["id"], tl["rows"][1]["shot"]["id"])
            lines[1]["shot"] = "beach-1"
            with self.assertRaisesRegex(ValueError, "不属于当前主讲母片"):
                self.production.plan(cfg)
            lines[1]["shot"] = ""
            self.media.save_asset(dict(id="video", role="host", shots=[]))
            with self.assertRaisesRegex(ValueError, "启用镜头"):
                self.production.plan(cfg)

    def test_library_visuals_are_assigned_per_line_without_rotating_the_speaker(self):
        self.media.save_asset(dict(id="lead", role="insert", shots=[
            dict(id="lead-1", asset="lead", enabled=True, start=0, end=1)
        ]))
        entries = [dict(id=f"visual-{i}") for i in range(40)]
        for entry in entries:
            self.media.save_asset(dict(id=entry["id"], role="host", kind="photo"))
        lines = [dict(text=str(i), start=i, end=i+1, layout=k)
                 for i, k in enumerate(("split", "card", "insert", "card", "card"))]
        lines[1].update(insert="visual-0", insertSpeaking=True)
        lines[2].update(insert="visual-39")
        lines[3].update(insert="visual-0", insertSpeaking=False)
        lines[4].update(insert="")
        cfg = dict(voiceId="voice", aspect="9:16", style="studio", hosts=["lead"], inserts=entries, lines=lines)
        with patch.object(self.production, "load_voice", return_value=dict(duration=5, lines=lines)):
            tl = self.production.plan(cfg)
            rows = tl["rows"]
            self.assertEqual(rows[0]["shot"]["asset"], "lead")
            self.assertEqual([(r["insert"], r["insertSpeaking"]) for r in rows],
                             [(None, False), ("visual-0", True), ("visual-39", False), ("visual-0", False), (None, False)])
            self.assertEqual(len(tl["inserts"]), 40)
            del lines[2]["insert"]
            with self.assertRaisesRegex(ValueError, "第 3 句"):
                self.production.plan(cfg)
            lines[2]["insert"] = "outside-project"
            with self.assertRaisesRegex(ValueError, "未加入当前项目"):
                self.production.plan(cfg)
            self.media.save_asset(dict(id="audio", role="audio", kind="audio"))
            cfg["inserts"] = [dict(id="audio")]
            with self.assertRaisesRegex(ValueError, "照片或视频"):
                self.production.plan(cfg)

    def test_automatic_pick_prefers_a_full_take_but_preserves_an_explicit_short_cut(self):
        self.media.save_asset(dict(id="lead", role="host", shots=[
            dict(id=name, asset="lead", enabled=True, start=0, end=duration)
            for name, duration in [("short", 1.), ("long", 4.)]
        ]))
        lines = [dict(text="一句", start=i*3, end=i*3+3, layout="full") for i in range(3)]
        lines[2]["shot"] = "short"
        cfg = dict(voiceId="voice", aspect="9:16", style="studio", hosts=["lead"], lines=lines)
        with patch.object(self.production, "load_voice", return_value=dict(duration=9, lines=lines)):
            timeline = self.production.plan(cfg)
        self.assertEqual([row["shot"]["id"] for row in timeline["rows"]], ["long", "long", "short"])

    def test_rest_pose_only_uses_confirmed_silence(self):
        import numpy as np
        from studio.mouth_rest import rest_weights

        envelope = np.full(40, .08, dtype=np.float32)
        envelope[3:7] = .001       # Brief low-energy sound inside speech.
        envelope[10:19] = .0005    # Sustained near-silence inside a timed sentence.
        envelope[24:27] = 0        # Short gap between two timed sentences.
        gaps = [dict(first=24, stop=27, voiced=False), dict(first=32, stop=35, voiced=False)]
        weights = rest_weights(np.repeat(envelope, 640), len(envelope), 25, 16000, gaps)
        self.assertFalse(weights[3:7].any())
        self.assertTrue(0 < weights[10] < .1)
        self.assertEqual(weights[15], 1)
        self.assertTrue(np.all(np.diff(weights[10:16]) >= 0))
        self.assertLess(np.max(np.abs(np.diff(weights[10:19]))), .5)
        self.assertTrue(np.all((weights[24:27] > 0) & (weights[24:27] < .5)))
        self.assertFalse(weights[32:35].any())  # A timing gap alone cannot mute a visible word.

        # A breath at a sentence boundary used to release a nearly closed mouth twice.
        envelope[10:27] = .0005
        envelope[20:22] = .007
        def sampled():
            return rest_weights(np.repeat(envelope, 640), len(envelope), 25, 16000, gaps)
        self.assertEqual(sampled()[20:22].tolist(), [1, 1])
        envelope[20:22] = .06
        self.assertFalse(sampled()[20:22].any())  # Protect an actual soft-to-loud restart.

    def test_lips_settle_in_the_current_frame(self):
        import numpy as np
        from studio.mouth_rest import settle_lips

        pts = np.zeros((68, 2), dtype=np.float32)
        pts[48:60] = [[33, 46], [43, 39], [54, 34], [72, 32], [90, 34], [99, 39],
                      [111, 46], [99, 56], [90, 60], [72, 62], [54, 60], [43, 56]]
        pts[60:68] = [[34, 46], [54, 40], [72, 39], [91, 40], [110, 46],
                      [91, 53], [72, 55], [54, 53]]
        frame = np.full((96, 144, 3), 80, dtype=np.uint8)
        frame[40:55, 60:84] = 240  # Exposed teeth between distinct lip and chin textures.
        frame[55:61, 60:84] = 120
        frame[66:68, 60:84] = 150
        counts = []
        for amount in (0, .25, .5, .75, 1):
            result = settle_lips(frame, pts, amount)
            counts.append(int((result[:, 72, 0] > 190).sum()))
            np.testing.assert_array_equal(result[:, :25], frame[:, :25])
        self.assertEqual(counts[0], 15)
        self.assertTrue(all(a > b for a, b in zip(counts, counts[1:])))
        self.assertEqual(counts[-1], 0)
        self.assertLess(np.where(result[:, 72, 0] == 150)[0].min(), 66)
        self.assertIs(settle_lips(frame, np.zeros_like(pts), 1), frame)

    def test_sustained_pause_uses_a_continuous_gesture_when_raw_lips_reopen(self):
        import cv2 as cv
        import numpy as np
        from studio.mouth_rest import PausePerformance

        gaps = [16, 16, 2, 18, 2, 16, 2, 18, 16, 2, 15, 2, 14, 16]
        weights = np.array([0, .07, .26, .5, .74, .93, 1, 1, 1, 1, .84, .5, .16, 0])
        frames, landmarks = [], []
        for index, gap in enumerate(gaps):
            points = np.zeros((68, 2), np.float32)
            points[[36, 45, 30]] = [[34, 15], [110, 15], [72, 25]]
            points[48:60] = [[33,46], [43,38], [54,35], [72,33], [90,35], [99,38],
                             [111,46], [99,52], [90,56], [72,57+gap/2], [54,56], [43,52]]
            points[60:68] = [[34,46], [54,45-gap/4], [72,45-gap/2], [90,45-gap/4],
                             [110,46], [90,45+gap/4], [72,45+gap/2], [54,45+gap/4]]
            frame = np.full((96, 144, 3), 105, np.uint8)
            cv.fillConvexPoly(frame, points[48:60].astype(int), (80, 80, 150))
            cv.fillConvexPoly(frame, points[60:68].astype(int), (245, 245, 245))
            frame[0, 0] = index
            frames.append(frame)
            landmarks.append(points)
        tracker = types.SimpleNamespace(points=lambda f: landmarks[int(f[0, 0, 0])])

        def render(first, stop, indices):
            def read(index):
                self.assertIn(index, range(first, stop))  # No cross-shot donor frames.
                return frames[index]
            gesture = PausePerformance(weights, first, stop, tracker, None, None)
            return [gesture.apply(read(i), i, read) for i in indices]

        result = render(0, len(frames), range(len(frames)))
        openings = [int((frame[:, 72, 0] > 190).sum()) for frame in result]
        self.assertTrue(np.all(np.diff(openings[:7]) <= 0), openings)
        self.assertTrue(np.all(np.diff(openings[9:]) >= 0), openings)
        self.assertEqual(len(set(openings[6:10])), 1)
        self.assertIs(result[0], frames[0])
        for index in (2, 7, 11):
            np.testing.assert_array_equal(render(0, len(frames), [index])[0], result[index])
        # This cut interrupts the closing ramp. It must stop partway to contact.
        truncated = render(0, 5, range(5))
        openings = [int((frame[:, 72, 0] > 190).sum()) for frame in truncated]
        self.assertTrue(3 < openings[-1] < openings[0], openings)

    def test_short_video_pause_follows_the_plate_without_restarting_its_mouth_or_loop(self):
        import numpy as np
        from studio.mouth_transition import MovingTail

        base = np.zeros((68, 2), np.float32)
        base[[36, 45, 30, 48, 54]] = [[34, 15], [110, 15], [72, 25], [42, 54], [102, 54]]
        def frame(shift, speaking=False):
            image = np.full((120, 156, 3), 25+shift, np.uint8)
            image[50:58, 65+shift:80+shift] = 150 if speaking else 240
            image[0, 0] = shift
            return image
        source = types.SimpleNamespace(pos=2, rate=25, length=5)
        source.next = lambda: frame(source.pos)
        tracker = types.SimpleNamespace(points=lambda f: base + np.float32([f[0, 0, 0], 0]))
        tail = MovingTail(source, 2, frame(2, speaking=True), tracker)
        later, earlier = tail.read(2), tail.read(1)
        self.assertEqual(earlier[0, -1, 0], 28)
        self.assertEqual(later[0, -1, 0], 29)
        self.assertEqual(later[54, 83, 0], 150)
        np.testing.assert_array_equal(tail.read(3), later)

    def test_speaking_insert_preview_and_export_share_absolute_audio_frames(self):
        import cv2 as cv
        import numpy as np

        ident = "e" * 64
        folder = self.media.STORE / "voices" / ident
        folder.mkdir(parents=True)
        lines = [dict(text="你好", start=.2, end=.6, layout="card"),
                 dict(text="再见", start=.72, end=.96, layout="insert")]
        (folder / "voice.json").write_text(json.dumps(dict(duration=1, lines=lines)))
        with wave.open(str(folder / "voice.wav"), "wb") as wav:
            wav.setparams((1, 2, 48000, 0, "NONE", "not compressed"))
            wav.writeframes(bytes(96000))
        path = folder / "photo.png"
        cv.imwrite(str(path), np.full((120, 90, 3), (180, 20, 30), np.uint8))
        self.media.save_asset(dict(id="photo", role="insert", kind="photo", path=str(path)))
        calls = []

        class MarkMouth:
            def __init__(self, _samples):
                pass

            def sync(self, frames, indexes, shift, fixed, state):
                calls.extend(indexes)
                for frame, index in zip(frames, indexes):
                    frame[:] = (15, 240, index * 8)

        class NoFace:
            def landmarks(self, _frame):
                raise ValueError("No face in the synthetic solid-color test image")

        def pixel(movie, index, x, y):
            video = cv.VideoCapture(str(movie))
            try:
                video.set(cv.CAP_PROP_POS_FRAMES, index)
                ok, frame = video.read()
                self.assertTrue(ok)
                return frame[y, x]
            finally:
                video.release()

        config = dict(voiceId=ident, aspect="16:9", style="editorial", hosts=[],
                      lines=lines, insert="photo", insertSpeaking=True)
        with patch.dict("sys.modules", {"studio.engine": types.SimpleNamespace(MouthEngine=MarkMouth, FaceLandmarks=NoFace)}):
            preview = self.production.render_card_preview(
                dict(config, line=0, start=.2, end=.6), folder)
            self.assertEqual(calls, list(range(5, 15)))
            self.assertGreater(pixel(preview, 0, 160, 160)[1], 200)
            tl = self.production.plan(config)
            result = self.production.render(tl, folder, lambda *_: None)
        self.assertEqual(calls, list(range(5, 15)) + list(range(18, 24)))
        self.assertEqual((result["inferred"], result["cached"], result["skipped"]), (6, 10, 9))
        film = folder / "film.mp4"
        self.assertGreater(pixel(film, 3, 320, 320)[0], 150)  # Original photo in the pause.
        self.assertGreater(pixel(film, 6, 320, 320)[1], 200)  # Mouth result reaches the card.
        self.assertGreater(pixel(film, 20, 640, 320)[1], 200)  # And the full-screen insert.
        self.assertGreater(pixel(film, 24, 640, 320)[0], 150)
        # Red encodes source time: the first image holds, then follows the calibrated clock.
        for first in (5, 18):
            start_red = int(pixel(film, first, 320, 320)[2])
            self.assertAlmostEqual(int(pixel(film, first+1, 320, 320)[2]), start_red, delta=2)
            self.assertAlmostEqual(int(pixel(film, first+4, 320, 320)[2]), start_red+24, delta=5)

        # Switching models must recompute the same frames; an EDTalk preview
        # can then reuse the EDTalk take without MuseTalk's one-frame delay.
        calls.clear()
        with patch.dict("sys.modules", {"studio.edtalk": types.SimpleNamespace(EDTalkEngine=MarkMouth),
                                       "studio.engine": types.SimpleNamespace(FaceLandmarks=NoFace)}):
            comparison_tl = self.production.plan(dict(config, lipModel="edtalk"))
            result = self.production.render(comparison_tl, folder, lambda *_: None)
            self.assertEqual((result["inferred"], result["cached"]), (16, 0))
            preview = self.production.render_card_preview(
                dict(config, line=0, start=.2, end=.6, lipModel="edtalk"), folder)
            self.assertEqual(calls, list(range(5, 15)) + list(range(18, 24)))
            self.assertAlmostEqual(int(pixel(preview, 3, 160, 160)[2]) -
                                   int(pixel(preview, 0, 160, 160)[2]), 24, delta=5)

        # A speaking cut crosses a pause. Only its two voiced ranges reach the model.
        calls.clear()
        config.update(insertSpeaking=False, cutaways=[dict(first=10, stop=21, insert="photo", insertSpeaking=True)])
        tl = self.production.plan(config)
        with patch.dict("sys.modules", {"studio.engine": types.SimpleNamespace(MouthEngine=MarkMouth, FaceLandmarks=NoFace)}):
            preview = self.production.render(tl, folder, lambda *_: None, window=(12, 21))
            preview_red = int(pixel(preview, 0, 160, 160)[2])
            self.assertGreater(pixel(preview, 0, 160, 160)[1], 200)
            self.assertGreater(pixel(preview, 4, 160, 160)[0], 150)
            self.assertGreater(pixel(preview, 7, 160, 160)[1], 200)
            result = self.production.render(tl, folder, lambda *_: None)
            self.assertAlmostEqual(int(pixel(film, 12, 320, 320)[2]), preview_red, delta=4)
        self.assertEqual(calls, list(range(10, 15)) + list(range(18, 21)))
        self.assertEqual((result["cached"], result["skipped"]), (8, 17))

    def test_looped_speaker_moves_continuously_and_preview_matches_export(self):
        import cv2 as cv
        import numpy as np

        p = self.production
        w, h = 160, 96
        path = self.media.STORE / "synced.mp4"
        # A synthetic head pans right, then jumps back to the trim in-point.
        texture = np.full((h, w, 3), (35, 35, 40), dtype=np.uint8)
        cv.ellipse(texture, (80, 47), (24, 38), 0, 0, 360, (130, 165, 205), -1)
        for x in (70, 90):
            cv.circle(texture, (x, 36), 5, (35, 45, 55), -1, cv.LINE_AA)
        cv.ellipse(texture, (80, 61), (10, 3), 0, 0, 360, (45, 50, 90), -1)
        with p.encoder(path, (w, h)) as sink:
            for i in range(21):
                frame = np.roll(texture, (i+3) % 10, axis=1)
                sink.write(frame.tobytes())
        span = dict(first=12, stop=33, offset=3, hold=False, origin=12, length=21, layout="full")

        def read(first, stop, cycle):
            sink = io.BytesIO()
            with patch.object(p, "compose", side_effect=lambda frame, *_: frame):
                p.draw_span(sink, span, path, (w,h), first, stop, False, "cover", cycle=cycle)
            return np.frombuffer(sink.getvalue(), dtype=np.uint8).reshape((-1, h, w, 3))

        raw = read(12, 33, None)
        fixed = read(12, 33, (10, 25))
        # Absolute frame 20 is the first wrap (including time calibration).
        def jump(frames):
            return cv.absdiff(frames[7], frames[8])[:, 22:-22].mean()
        self.assertLess(jump(fixed), .65 * jump(raw))
        np.testing.assert_array_equal(read(19, 23, (10, 25)), fixed[7:11])
        np.testing.assert_array_equal(raw[:2], fixed[:2])  # No warp outside the seam.

    def test_short_host_pause_uses_last_synced_frame_even_when_preview_starts_in_the_gap(self):
        import cv2 as cv
        import numpy as np
        p = self.production
        host = dict(shot=dict(asset="lead", start=0, end=1), insert=None, insertSpeaking=False)
        tl = dict(frames=25, voice="v", shift=0, duration=1., aspect="16:9", subtitles=False, rows=[
            dict(host, layout="full", text="上句", first=0, stop=10),
            dict(host, layout="split", text="下句", first=14, stop=25)])
        folder = self.media.STORE
        wav = folder / "voices/v/voice.wav"
        wav.parent.mkdir(parents=True)
        with wave.open(str(wav), "wb") as handle:
            handle.setparams((1, 2, 16000, 0, "NONE", ""))
            handle.writeframes(np.full(16000, 3000, dtype="<i2").tobytes())
        self.media.save_asset(dict(id="lead", role="host", kind="photo"))
        synced = folder / "take.mp4"
        with p.encoder(synced, (80, 96)) as sink:
            for index in range(10):
                sink.write(np.full((96, 80, 3), index * 20, np.uint8).tobytes())
        gap = p.visual_spans(tl)[1]
        self.assertEqual((gap["layout"], gap["rest_from"], gap["voiced"]), ("full", 0, False))
        self.assertTrue(self.server.visible_speech([gap]))
        with patch.object(p, "sync_parts", return_value=([synced], 0, 10)) as sync:
            preview = p.render(tl, folder, lambda *_: None, window=(11, 14))
        self.assertEqual([s["first"] for s in sync.call_args.args[0]], [0])
        cap = cv.VideoCapture(str(preview))
        try:
            for _ in range(3):
                ok, frame = cap.read()
                self.assertTrue(ok)
                self.assertAlmostEqual(int(frame[180, 320, 0]), 160, delta=5)
        finally:
            cap.release()

    def test_timed_cutaways_resume_source_and_keep_speech_and_captions_on_the_master_clock(self):
        p = self.production
        options = {"shot-a": False, "shot-b": False}
        placements = [
            dict(first=4, stop=8, insert="shot-a"),
            dict(first=8, stop=17, insert="shot-b", insertSpeaking=True),
            dict(first=18, stop=19, insert="shot-a"),
        ]
        cuts = p.timed_cutaways({"cutaways": list(reversed(placements))}, options, 25)
        for invalid in ([dict(placements[0], first=-1)], [dict(placements[0], stop=26)],
                        [dict(placements[0], first=8)], [dict(placements[0], insert="audio")],
                        [placements[0], dict(placements[1], first=7)]):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                p.timed_cutaways({"cutaways": invalid}, options, 25)
        one_frame = [dict(first=i, stop=i + 1, insert="shot-a") for i in range(250)]
        self.assertEqual(len(p.timed_cutaways({"cutaways": one_frame}, options, 250)), 250)
        self.assertFalse(p.base_visible(cuts, 4, 17))
        self.assertTrue(p.base_visible(cuts, 4, 18))
        host = dict(layout="split", shot=dict(asset="lead", id="lead-1", start=0, end=1),
                    insert=None, insertSpeaking=False)
        tl = dict(frames=25, cutaways=cuts, aspect="16:9", subtitles=True, rows=[
            dict(host, first=1, stop=12, text="第一句。"), dict(host, first=15, stop=24, text="第二句。")
        ])
        spans = p.visual_spans(tl)
        self.assertEqual([(s["first"], s["stop"], s["voiced"], s["offset"])
                          for s in spans if s["insert"] == "shot-b"],
                         [(8, 12, True, 0), (12, 15, False, 4), (15, 17, True, 7)])
        self.assertEqual([(s["first"], s["offset"]) for s in spans if s["shot"] and s["voiced"]],
                         [(1, 0), (17, 2), (19, 4)])
        self.assertEqual(sum(s["stop"]-s["first"] for s in spans), 25)
        ass = self.media.STORE / "cutaways.ass"
        p.write_ass(tl, ass)
        events = [line for line in ass.read_text().splitlines() if line.startswith("Dialogue:")]
        self.assertTrue(any("0:00:00.04,0:00:00.16" in e and "第一句。" in e and r"\fs40" in e for e in events))
        self.assertTrue(any("0:00:00.16,0:00:00.32" in e and "第一句。" in e and r"\fs32" in e for e in events))
        self.assertTrue(any("0:00:00.76,0:00:00.96" in e and "第二句。" in e and r"\fs40" in e for e in events))
        tl["subtitles"] = False
        p.write_ass(tl, ass)
        self.assertNotIn(r"\fs32", ass.read_text())
        self.assertIn("第二句。", ass.read_text())

    def test_normalized_trim_and_review(self):
        a = {"kind": "video", "duration": 3.0, "id": "plate"}
        clean = self.media.clean_shots(
            a, [{"start": 1, "end": 2, "enabled": False, "emotion": "平静"}]
        )
        self.assertFalse(clean[0]["enabled"])
        self.assertEqual(clean[0]["emotion"], "平静")
        with self.assertRaisesRegex(ValueError, "出点"):
            self.media.clean_shots(a, [{"start": 2, "end": 1}])

    def test_review_belongs_to_a_finished_film_and_merges_legacy_checks(self):
        def save(items, **options):
            return self.client.post(
                "/api/jobs/a/review", json=dict(items=items, **options), headers=self.headers
            )

        self.server.put_job(dict(id="a", status="running"))
        self.assertEqual(save({"mouth": {"status": "passed"}}).status_code, 409)
        for ident in ("a", "b"):
            self.server.put_job(dict(id=ident, status="done", qc={"duration": 5}))
        issue = {"status": "issue", "time": 2.56, "note": "句末没有闭嘴"}
        self.assertEqual(save({"mouth": issue}).json["review"]["mouth"], issue)
        saved = save({k: {"status": "passed"} for k in ("playback", "mouth")}, onlyMissing=True)
        self.assertEqual(saved.json["review"], {"playback": {"status": "passed"}, "mouth": issue})
        self.assertEqual(save({"mouth": dict(issue, time=6)}).status_code, 400)
        self.assertEqual(self.client.get("/api/jobs/a").json["review"]["mouth"], issue)
        self.assertNotIn("review", self.client.get("/api/jobs/b").json)
        cleared = save({"mouth": {"status": "pending"}}).json["review"]
        self.assertEqual(cleared["mouth"], {"status": "pending"})
        self.assertEqual(save({"mouth": {"status": "passed"}}, onlyMissing=True).json["review"], cleared)

    def test_paragraph_from_an_existing_voice_is_paged_inside_its_timing(self):
        sentence = "Dr. Wu uses version 1.5 and writes about it on example.com."
        text = " ".join([sentence] * 5)
        self.assertEqual(self.media.sentences(text), [sentence] * 5)
        row = dict(text=text, first=13, stop=255)
        pages = list(self.production.caption_cues(row, 28))
        self.assertGreater(len(pages), 1)
        self.assertEqual((pages[0][0], pages[-1][1]), (13, 255))
        self.assertEqual(" ".join(line for _, _, lines in pages for line in lines), text)
        for i, (start, stop, lines) in enumerate(pages):
            self.assertLess(start, stop)
            self.assertLessEqual(len(lines), 2)
            if i:
                self.assertEqual(start, pages[i - 1][1])

    def test_caption_area_contains_no_picture_in_either_aspect(self):
        import numpy as np

        p = self.production
        image = np.full((120, 100, 3), 240, dtype=np.uint8)
        for size in p.SIZES.values():
            for layout in ("full", "insert", "split", "pip"):
                with self.subTest(size=size, layout=layout):
                    frame = p.compose(image, layout, size, subtitles=True)
                    left, top, right, bottom = p.caption_box(layout, *size)
                    self.assertTrue(np.all(frame[top:bottom, left:right] == (33, 33, 28)))
                    self.assertTrue(np.any(frame == 240))
            self.assertTrue(np.all(p.compose(image, "full", size, subtitles=False) == 240))

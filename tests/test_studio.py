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
                for frame in frames:
                    frame[:] = (15, 240, 15)

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
        with patch.dict("sys.modules", {"studio.engine": types.SimpleNamespace(MouthEngine=MarkMouth)}):
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

        # A speaking cut crosses a pause. Only its two voiced ranges reach the model.
        calls.clear()
        config.update(insertSpeaking=False, cutaways=[dict(first=10, stop=21, insert="photo", insertSpeaking=True)])
        tl = self.production.plan(config)
        with patch.dict("sys.modules", {"studio.engine": types.SimpleNamespace(MouthEngine=MarkMouth)}):
            preview = self.production.render(tl, folder, lambda *_: None, window=(12, 21))
            self.assertGreater(pixel(preview, 0, 160, 160)[1], 200)
            self.assertGreater(pixel(preview, 4, 160, 160)[0], 150)
            self.assertGreater(pixel(preview, 7, 160, 160)[1], 200)
            result = self.production.render(tl, folder, lambda *_: None)
        self.assertEqual(calls, list(range(10, 15)) + list(range(18, 21)))
        self.assertEqual((result["cached"], result["skipped"]), (8, 17))

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

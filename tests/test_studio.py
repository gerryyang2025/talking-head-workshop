"""Regressions for the website's audio-locked timeline and visible-only rendering."""

import io
import importlib.util
import shutil
import tempfile
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
        lines[1]["start"] = 0
        with self.assertRaisesRegex(ValueError, "重叠"):
            self.production.plan(cfg)

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

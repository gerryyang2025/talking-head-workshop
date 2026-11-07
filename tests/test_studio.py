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

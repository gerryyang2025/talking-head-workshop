"""EDTalk's converted model has its own audio and face-compositing contract."""
import importlib.util
import unittest


@unittest.skipUnless(all(importlib.util.find_spec(name) for name in
                         ("numpy", "scipy", "cv2", "onnxruntime")), "studio dependencies required")
class EDTalkInputTests(unittest.TestCase):
    def test_model_bands_normalization_and_silence(self):
        import numpy as np
        from studio.edtalk import mel_features

        t = np.arange(16000) / 16000
        # Three tones cover low, mid and high bands of the ONNX reference frontend.
        signal = (.7 * np.cos(2*np.pi*320*t) + .2 * np.sin(2*np.pi*1200*t)
                  + .1 * np.sin(2*np.pi*2800*t)).astype(np.float32)
        features = mel_features(signal)
        np.testing.assert_allclose(features[[10, 11, 31, 51, 52], 35],
                                   [.8382, .5564, 1.3434, .5303, -.1064], atol=.001)
        np.testing.assert_allclose(features, mel_features(signal * .125), atol=.001)
        self.assertTrue((mel_features(np.zeros(16)) == -4).all())

    def test_window_uses_video_clock_and_silence_outside_track(self):
        import numpy as np
        from studio.edtalk import audio_window

        bands = np.broadcast_to(np.arange(40), (80, 40))
        np.testing.assert_array_equal(audio_window(bands, 5)[0, 0], bands[:, 16:32])
        np.testing.assert_array_equal(audio_window(bands, -1)[0, 0, 0], [-4]*4 + list(range(12)))
        np.testing.assert_array_equal(audio_window(bands, 12)[0, 0, 0], [38, 39] + [-4]*14)

    def test_preserves_lip_texture_and_predicts_newly_visible_interior(self):
        import numpy as np
        from studio.edtalk import restore_lip_surfaces

        points = np.zeros((68, 2), dtype=np.float32)
        points[48:60] = [(26, 44), (36, 41), (45, 39), (54, 38), (63, 39), (72, 41),
                         (82, 44), (72, 48), (63, 50), (54, 51), (45, 50), (36, 48)]
        points[60:68] = [(29, 44), (38, 44), (54, 44), (70, 44),
                         (79, 44), (70, 45), (54, 45), (38, 45)]
        target = points.copy()
        target[[55, 56, 57, 58, 59, 65, 66, 67], 1] += 13
        original = np.full((96, 108, 3), 70, np.uint8)
        original[49:51, 50:59] = 190
        prediction = np.full_like(original, 230)
        restored = restore_lip_surfaces(original, prediction, points, target)
        np.testing.assert_array_equal(restored[51, 54], [230]*3)  # Mouth interior.
        # The crease moves from rows 49–50 onto the lowered lip and keeps contrast.
        self.assertGreater(int(restored[63, 54, 0]) - int(restored[60, 54, 0]), 70)
        np.testing.assert_array_equal(restored[20, 54], [70]*3)
        self.assertIs(restore_lip_surfaces(original, prediction, points, points * 0), prediction)

        prediction[:] = [80, 87, 145]
        prediction[45:56] = 185
        detail_view = prediction.copy()
        detail_view[45:56, 54:56] = 155
        baseline = restore_lip_surfaces(original, prediction, points, target)
        refined = restore_lip_surfaces(original, prediction, points, target, (detail_view, target, 1.))
        self.assertLess(int(refined[50, 54, 0]), int(baseline[50, 54, 0]) - 4)
        np.testing.assert_array_equal(refined[:44], baseline[:44])
        np.testing.assert_array_equal(refined[59:], baseline[59:])
        rejected = restore_lip_surfaces(original, prediction, points, target, (detail_view, target + 32, 1.))
        np.testing.assert_array_equal(rejected, baseline)

    def test_tooth_detail_requires_two_matching_visible_surfaces(self):
        import numpy as np
        from studio.edtalk import restore_tooth_detail

        v, u = np.indices((32, 40), dtype=np.float32)
        contours = np.stack([np.full_like(v, k) for k in (4, 12, 23, 29)])
        edge = np.minimum(u, 39-u)
        inside = np.minimum(v - 12, 23 - v)
        native = np.full((32, 40, 3), [92, 96, 148], np.float32)
        native[12:24] = 187
        native[12:24, 20:22] = 164
        generated = native.copy()
        generated[12:24] = 184

        def restore(source, prediction, source_shape):
            return restore_tooth_detail(source, prediction, source_shape, contours, inside, edge, v, 2.)

        result = restore(native, generated, contours)
        self.assertLess(result[17, 20, 0], generated[17, 20, 0] - 4)
        np.testing.assert_array_equal(result[inside <= 0], generated[inside <= 0])
        shut = contours.copy()
        shut[2] = shut[1]
        np.testing.assert_array_equal(restore(native, generated, shut), generated)
        # A dark cavity or red tongue on either side must not gain tooth grooves.
        for color in ([22, 22, 22], [78, 87, 170]):
            blocked = generated.copy()
            blocked[12:24] = color
            np.testing.assert_array_equal(restore(native, blocked, contours), blocked)
            blocked[12:24, 20:22] -= 15
            np.testing.assert_array_equal(restore(blocked, generated, contours), generated)

    def test_closed_source_upper_lip_meets_teeth_without_bleeding_into_the_cavity(self):
        import numpy as np
        from studio.edtalk import separate_upper_lip

        yy, xx = np.indices((36, 48), np.float32)
        contours = np.stack([np.full_like(yy, i) for i in (6, 14, 27, 33)])
        delta = yy - contours[1]
        edge = np.minimum(xx - 2, 45 - xx)
        normal = np.float32([0, 1])
        lip = np.float32([69, 74, 129])
        native = np.broadcast_to(lip, (*yy.shape, 3)).copy()
        blend = np.clip((delta + 3) / 8, 0, 1)[..., None]

        def apply(prediction, closed):
            return separate_upper_lip(prediction, native, prediction, contours, delta,
                                      edge, xx, yy, normal, closed)

        teeth = np.float32([176, 181, 188])
        soft = lip + blend * (teeth - lip)
        result = apply(soft, 1.)
        # Increase separation across the observed boundary without painting a darker outline.
        self.assertGreater(result[15, 24, 1] - result[13, 24, 1],
                           2 * (soft[15, 24, 1] - soft[13, 24, 1]))
        self.assertGreaterEqual(result[13:16, 24, 1].min(), lip[1])
        np.testing.assert_array_equal(result[21:], soft[21:])
        np.testing.assert_array_equal(result[:, :3], soft[:, :3])
        np.testing.assert_array_equal(apply(soft, 0.), soft)
        for color in ([24, 23, 30], [60, 76, 175], lip):
            dark_or_red = lip + blend * (np.float32(color) - lip)
            np.testing.assert_array_equal(apply(dark_or_red, 1.), dark_or_red)

        # At the start of opening the tooth can appear below a band of shadow.
        shadow = np.float32([67, 69, 85])
        lit_lip = np.float32([105, 109, 146])
        shaded = lit_lip + blend * (shadow - lit_lip)
        shaded[22:27] = teeth
        rim = apply(shaded, 1.)
        self.assertLess(rim[13, 24, 1], shaded[13, 24, 1] - 5)
        self.assertLess(rim[16, 24, 1], 95)
        np.testing.assert_array_equal(rim[22:27], shaded[22:27])

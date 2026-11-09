# 生成包 · GENERATE_PACK — 无遮挡元视频底板

> 当前模板：`reference`。在仓库根目录运行 `python3 -m istream identity set --photo ./me.jpg` 可生成自己的版本。

## 生成母片

- 人物：参考照中的人物。参考照：请使用自己的单人参考照。
- 为同一批母片使用相同参考照、模型与版本。先生成首帧，再生成近景、中景或开场动作。
- 建议使用 1080p 或更高分辨率、25 fps。保留嘴部清晰、手势避开脸、切点处姿势稳定的片段。剪辑时沿用最终配音。

## 负面提示词 / Negative (all starter plates)

```text
Negative: hands touching face, hand covering mouth, profile view, head turned away, looking away, hair over face, jewelry, earrings, glasses, patterned clothing, logo, text, subtitles, watermark, camera movement, zoom, cut, jump cut, flicker, lighting change, extra people, extra fingers, deformed hands, distorted face, plastic skin, hands in frame, laughing, wide open mouth, talking in the last section
```

## 无遮挡提醒 / No-occlusion (from Avoid lines)

Avoid 段已写明：hands touching or covering the face or mouth · 手不碰脸不挡嘴 · 无道具挡嘴 · 干净背景。
生成时若模型爱把手抬起来，加重负面里的 `hands touching face, hand covering mouth`，或在提示词 Timeline 里强调 hands stay below frame。

## 当前身份块 / Current identity block

**EN**

```text
Identity: exactly the same person as in the attached reference image (same face, hair, skin tone, age appearance). clothing matches the reference image unless an outfit lock is given. No jewelry, no glasses unless visible in the reference.
```

**中文**

```text
人物：与所附参考图中为同一人（脸型、发型、肤色、年龄感一致）。服装与参考图一致（除非另行指定服装锁定）。不戴首饰；除非参考图中可见，否则不戴眼镜。
```

> 外貌细节来自你提供的 `--describe` / `--outfit` / `--name`，**不会**自动读图分析脸。
> Appearance locks come only from flags you pass — there is no automatic face analysis.

## 首帧图提示词 / First-frame prompts

### IMG-A

**EN**

```text
Photorealistic 9:16 vertical portrait photo, medium close-up from mid-chest up, subject centered, eyes on the upper third line, a little headroom. Subject: exactly the same person as in the attached reference image (same face, hair, skin tone, age appearance). clothing matches the reference image unless an outfit lock is given. No jewelry, no glasses unless visible in the reference. She faces the lens directly with a relaxed neutral expression, lips relaxed and gently closed, shoulders relaxed and level, hands out of view below the frame. Background: plain warm light-grey seamless wall. Large soft key light 45 degrees from camera left, soft fill from camera right, subtle hair rim light, neutral 5600K. True-to-life skin texture, sharp focus on the eyes, natural color. No text, no logo.
```

**中文**

```text
写实 9:16 竖幅人像照片，胸部以上近景，人物居中，眼睛位于画面上三分之一线，头顶略留空间。人物：与所附参考图中为同一人（脸型、发型、肤色、年龄感一致）。服装与参考图一致（除非另行指定服装锁定）。不戴首饰；除非参考图中可见，否则不戴眼镜。她正对镜头，表情放松中性，嘴唇放松、轻轻闭合，双肩放松、水平，双手在画面以下不入画。背景：纯净的浅暖灰无缝墙。镜头左侧 45 度大面积柔光主光，镜头右侧柔和补光，细微发丝轮廓光，5600K 中性色温。真实皮肤纹理，眼睛焦点清晰，自然色彩。无文字，无 logo。
```

### IMG-B

**EN**

```text
Photorealistic 9:16 vertical portrait photo, medium shot from the waist up, subject centered, eyes on the upper third line, room on both sides of the body. Subject: exactly the same person as in the attached reference image (same face, hair, skin tone, age appearance). clothing matches the reference image unless an outfit lock is given. No jewelry, no glasses unless visible in the reference. She faces the lens directly with a relaxed neutral expression, lips relaxed and gently closed, shoulders relaxed and level, hands loosely clasped in front of the waist, all fingers natural. Background: plain warm light-grey seamless wall. Large soft key light 45 degrees from camera left, soft fill from camera right, subtle hair rim light, neutral 5600K. True-to-life skin texture, sharp focus on the eyes, natural color. No text, no logo.
```

**中文**

```text
写实 9:16 竖幅人像照片，腰部以上中景，人物居中，眼睛位于画面上三分之一线，身体两侧留有空间。人物：与所附参考图中为同一人（脸型、发型、肤色、年龄感一致）。服装与参考图一致（除非另行指定服装锁定）。不戴首饰；除非参考图中可见，否则不戴眼镜。她正对镜头，表情放松中性，嘴唇放松、轻轻闭合，双肩放松、水平，双手在腰前轻握，手指自然。背景：纯净的浅暖灰无缝墙。镜头左侧 45 度大面积柔光主光，镜头右侧柔和补光，细微发丝轮廓光，5600K 中性色温。真实皮肤纹理，眼睛焦点清晰，自然色彩。无文字，无 logo。
```

### IMG-A169

**EN**

```text
Photorealistic 16:9 horizontal photo, medium close-up from mid-chest up, subject on the left third facing the lens, eyes on the upper third line, a little headroom, the right half of the frame clean softly lit wall. Subject: exactly the same person as in the attached reference image (same face, hair, skin tone, age appearance). clothing matches the reference image unless an outfit lock is given. No jewelry, no glasses unless visible in the reference. She faces the lens directly with a relaxed neutral expression, lips relaxed and gently closed, shoulders relaxed and level, hands out of view below the frame. Background: plain warm light-grey seamless wall. Large soft key light 45 degrees from camera left, soft fill from camera right, subtle hair rim light, neutral 5600K. True-to-life skin texture, sharp focus on the eyes, natural color. No text, no logo.
```

**中文**

```text
写实 16:9 横幅照片，胸部以上近景，人物位于左三分之一处、正对镜头，眼睛位于画面上三分之一线，头顶略留空间，画面右半边是干净、柔和受光的墙面。人物：与所附参考图中为同一人（脸型、发型、肤色、年龄感一致）。服装与参考图一致（除非另行指定服装锁定）。不戴首饰；除非参考图中可见，否则不戴眼镜。她正对镜头，表情放松中性，嘴唇放松、轻轻闭合，双肩放松、水平，双手在画面以下不入画。背景：纯净的浅暖灰无缝墙。镜头左侧 45 度大面积柔光主光，镜头右侧柔和补光，细微发丝轮廓光，5600K 中性色温。真实皮肤纹理，眼睛焦点清晰，自然色彩。无文字，无 logo。
```

## 起步套装提示词 / Starter plate prompts（先生成这三条）

推荐 Phase 0 / 标准档先跑 **K01 + K02 + O01**（近景主力 · 中景手势 · 开场入镜）。

### K01 · 近景口播主底板 · Main close-up talking plate

- 文件名：`liz01_o1_mcu_916_koubo-main_mid_30s_v01.mov` ｜ MCU · 9:16 · 30s · 首帧 IMG-A
- 切点：0.5s / 7.5s / 14.5s / 21.5s / 29.0s

**EN Master Prompt**

```text
30-second single continuous shot, locked-off camera on a tripod, no camera movement, no zoom, no cuts. 9:16 vertical. Medium close-up from mid-chest up, subject centered, eyes on the upper third line, a little headroom.
Identity: exactly the same person as in the attached reference image (same face, hair, skin tone, age appearance). clothing matches the reference image unless an outfit lock is given. No jewelry, no glasses unless visible in the reference.
Setting and light: plain warm light-grey seamless wall behind her, evenly lit, nothing else in frame. Large soft key light 45 degrees from camera left, soft fill from camera right, subtle hair rim light from behind, neutral 5600K white balance, constant exposure for the whole shot. Photorealistic, true-to-life skin texture, sharp focus on the face, natural color, fine film grain, no flicker. Quiet room tone, no music.
Performance: In the first three sections she speaks to the camera calmly and naturally as if mid-conversation, with natural jaw and lip movement and a relaxed rhythm; in the last section she stops speaking and listens with her lips gently closed. Her eyes stay on the lens, she blinks naturally, head turns stay within 20 degrees, and her hands stay out of view below the frame the whole time. Home pose: head centered and facing the lens, shoulders relaxed and level, hands resting together low and out of view below the bottom edge of the frame, lips relaxed. Energy: low to medium — only small, subtle, natural movements, so that every section can be reused many times and even played in reverse without looking odd.
Timeline:
0–1s: She holds the home pose, then begins speaking.
1–7s: Calm, neutral narration with small, slow nods on stressed words; shoulders almost still.
7–8s: She returns to the home pose and holds it still for one second.
8–14s: She keeps speaking with a very slight head tilt to the left and one small eyebrow raise on a key word, then straightens.
14–15s: She returns to the home pose and holds it still for one second.
15–21s: She looks into the lens with a bright, warm smile and a small welcoming nod, then keeps speaking warmly with a soft smile.
21–22s: She returns to the home pose and holds it still for one second.
22–28s: She stops speaking; with her lips gently closed she listens attentively, gives two small slow nods with a soft closed-lip smile, and blinks once naturally.
28–30s: She relaxes back into the home pose with a calm, faint closed-lip smile and holds it still until the end, the final frame matching the first frame as closely as possible.
Avoid: hands touching or covering the face or mouth, head turned more than 20 degrees, hair crossing the face, jewelry, glasses, patterned clothing, logos, text, subtitles, camera movement, zoom, cuts, lighting changes, extra people, objects in the background, hands entering the frame, laughing, opening the mouth in the last section.
```

**中文 Master Prompt**

```text
30 秒单个连续镜头，三脚架固定机位，无运镜、无变焦、无剪辑。9:16 竖屏。胸部以上近景，人物居中，眼睛位于画面上三分之一线，头顶略留空间。
人物：与所附参考图中为同一人（脸型、发型、肤色、年龄感一致）。服装与参考图一致（除非另行指定服装锁定）。不戴首饰；除非参考图中可见，否则不戴眼镜。
场景与光线：身后是纯净的浅暖灰无缝墙，照明均匀，画面中没有其他物体。镜头左侧 45 度大面积柔光主光，镜头右侧柔和补光，身后细微的发丝轮廓光，5600K 中性白平衡，整个镜头曝光恒定。写实，真实皮肤纹理，脸部焦点清晰，自然色彩，细腻胶片颗粒，无闪烁。安静的室内环境声，无音乐。
表演：前三段她像正在对话一样，平静自然地对着镜头说话，下颌与嘴唇自然运动，节奏放松；最后一段她停止说话，双唇轻轻闭合地倾听。视线始终看镜头，自然眨眼，头部转动不超过 20 度，双手全程在画面底边以下不入画。回位姿势：头部居中面向镜头，双肩放松、水平，双手放低并拢在画面底边以下（不入画），嘴唇放松。能量：低到中——只有细小、自然的动作，让每一段都能被反复使用，甚至倒放也不显得奇怪。
时间线：
0–1 秒：保持回位姿势，然后开始说话。
1–7 秒：平静、中性地叙述，在重音处缓慢地小幅点头，肩部几乎不动。
7–8 秒：回到回位姿势，静止保持一秒。
8–14 秒：继续说话，头部极轻微地向左倾斜，在关键词处轻扬一次眉毛，然后回正。
14–15 秒：回到回位姿势，静止保持一秒。
15–21 秒：她看向镜头，露出明亮温暖的笑容，轻轻点头表示欢迎，然后带着浅笑温暖地继续说。
21–22 秒：回到回位姿势，静止保持一秒。
22–28 秒：她停止说话，双唇轻闭，专注倾听，带着闭唇浅笑缓慢地小幅点头两次，自然眨眼一次。
28–30 秒：放松回到回位姿势，只留一丝平静的闭唇笑意，静止保持到结束，最后一帧尽量与第一帧一致。
避免：手触碰或遮挡脸和嘴，头部转动超过 20 度，头发遮挡脸部，首饰，眼镜，有图案的服装，logo，文字，字幕，镜头运动，变焦，剪辑，光线变化，其他人物，背景杂物，手进入画面，大笑，最后一段张嘴。
```

**Avoid EN：** Avoid: hands touching or covering the face or mouth, head turned more than 20 degrees, hair crossing the face, jewelry, glasses, patterned clothing, logos, text, subtitles, camera movement, zoom, cuts, lighting changes, extra people, objects in the background, hands entering the frame, laughing, opening the mouth in the last section.

**避免（中文）：** 避免：手触碰或遮挡脸和嘴，头部转动超过 20 度，头发遮挡脸部，首饰，眼镜，有图案的服装，logo，文字，字幕，镜头运动，变焦，剪辑，光线变化，其他人物，背景杂物，手进入画面，大笑，最后一段张嘴。

### K02 · 中景口播底板（自然手势） · Medium-shot talking plate with natural hands

- 文件名：`liz01_o1_ms_916_koubo-hands_mid_30s_v01.mov` ｜ MS · 9:16 · 30s · 首帧 IMG-B
- 切点：0.5s / 7.5s / 14.5s / 21.5s / 29.0s

**EN Master Prompt**

```text
30-second single continuous shot, locked-off camera on a tripod, no camera movement, no zoom, no cuts. 9:16 vertical. Medium shot from the waist up, subject centered, eyes on the upper third line, with enough room on both sides that her hands stay fully inside the frame when she gestures.
Identity: exactly the same person as in the attached reference image (same face, hair, skin tone, age appearance). clothing matches the reference image unless an outfit lock is given. No jewelry, no glasses unless visible in the reference.
Setting and light: plain warm light-grey seamless wall behind her, evenly lit, nothing else in frame. Large soft key light 45 degrees from camera left, soft fill from camera right, subtle hair rim light from behind, neutral 5600K white balance, constant exposure for the whole shot. Photorealistic, true-to-life skin texture, sharp focus on the face, natural color, fine film grain, no flicker. Quiet room tone, no music.
Performance: She speaks to the camera calmly and naturally as if mid-conversation, with natural jaw and lip movement and a relaxed rhythm. Her eyes stay on the lens, she blinks naturally, head turns stay within 20 degrees, and her hands stay between waist and chest height and never touch or cover the face or mouth. Home pose: head centered and facing the lens, shoulders relaxed and level, hands loosely clasped in front of the waist, lips relaxed. Energy: medium — natural conversational nods and small eyebrow movements; hand movements are small and relaxed, and every gesture starts from and returns to the home pose.
Timeline:
0–1s: She holds the home pose, then begins speaking.
1–7s: Natural conversational talking with her hands loosely clasped at the waist and small nods.
7–8s: She returns to the home pose and holds it still for one second.
8–14s: Both palms open outward at chest height in a relaxed explaining gesture, then come back together at the waist.
14–15s: She returns to the home pose and holds it still for one second.
15–21s: She keeps talking with a light smile while her right hand makes one small, relaxed open-palm movement at waist height, then rejoins the other hand.
21–22s: She returns to the home pose and holds it still for one second.
22–28s: To sum up, both hands come loosely together in front of her chest, then lower back to the waist as she gives one firm, confident nod.
28–30s: She finishes her sentence, returns to the home pose and holds it still until the end, the final frame matching the first frame as closely as possible.
Avoid: hands touching or covering the face or mouth, head turned more than 20 degrees, hair crossing the face, jewelry, glasses, patterned clothing, logos, text, subtitles, camera movement, zoom, cuts, lighting changes, extra people, objects in the background, counting on fingers, pointing, waving, hands rising above chest height, deformed fingers.
```

**中文 Master Prompt**

```text
30 秒单个连续镜头，三脚架固定机位，无运镜、无变焦、无剪辑。9:16 竖屏。腰部以上中景，人物居中，眼睛位于画面上三分之一线，两侧留足空间，做手势时双手完整留在画面内。
人物：与所附参考图中为同一人（脸型、发型、肤色、年龄感一致）。服装与参考图一致（除非另行指定服装锁定）。不戴首饰；除非参考图中可见，否则不戴眼镜。
场景与光线：身后是纯净的浅暖灰无缝墙，照明均匀，画面中没有其他物体。镜头左侧 45 度大面积柔光主光，镜头右侧柔和补光，身后细微的发丝轮廓光，5600K 中性白平衡，整个镜头曝光恒定。写实，真实皮肤纹理，脸部焦点清晰，自然色彩，细腻胶片颗粒，无闪烁。安静的室内环境声，无音乐。
表演：她像正在对话一样，平静自然地对着镜头说话，下颌与嘴唇自然运动，节奏放松。视线始终看镜头，自然眨眼，头部转动不超过 20 度，双手始终在腰部到胸口之间活动，绝不触碰或遮挡脸部和嘴。回位姿势：头部居中面向镜头，双肩放松、水平，双手在腰前轻握，嘴唇放松。能量：中——自然的对话式点头和细微的眉毛动作；手部动作小而放松，每个手势都从回位姿势开始，并回到回位姿势。
时间线：
0–1 秒：保持回位姿势，然后开始说话。
1–7 秒：自然的对话式说话，双手在腰前轻握，小幅点头。
7–8 秒：回到回位姿势，静止保持一秒。
8–14 秒：双手在胸口高度向外摊开，做一个放松的讲解手势，然后回到腰前合拢。
14–15 秒：回到回位姿势，静止保持一秒。
15–21 秒：带着浅笑继续说话，右手在腰部高度做一个小幅、放松的摊掌动作，然后与另一只手重新合拢。
21–22 秒：回到回位姿势，静止保持一秒。
22–28 秒：总结时双手在胸前轻轻合拢，再放回腰前，同时自信有力地点头一次。
28–30 秒：说完这句话，回到回位姿势，静止保持到结束，最后一帧尽量与第一帧一致。
避免：手触碰或遮挡脸和嘴，头部转动超过 20 度，头发遮挡脸部，首饰，眼镜，有图案的服装，logo，文字，字幕，镜头运动，变焦，剪辑，光线变化，其他人物，背景杂物，数手指，指向，挥手，手抬到胸口以上，手指畸形。
```

**Avoid EN：** Avoid: hands touching or covering the face or mouth, head turned more than 20 degrees, hair crossing the face, jewelry, glasses, patterned clothing, logos, text, subtitles, camera movement, zoom, cuts, lighting changes, extra people, objects in the background, counting on fingers, pointing, waving, hands rising above chest height, deformed fingers.

**避免（中文）：** 避免：手触碰或遮挡脸和嘴，头部转动超过 20 度，头发遮挡脸部，首饰，眼镜，有图案的服装，logo，文字，字幕，镜头运动，变焦，剪辑，光线变化，其他人物，背景杂物，数手指，指向，挥手，手抬到胸口以上，手指畸形。

### O01 · 开场入镜底板（4 种自然开场） · Opening plate — four natural ways to arrive on camera

- 文件名：`liz01_o1_mcu_916_opening-set_mid_30s_v01.mov` ｜ MCU · 9:16 · 30s · 首帧 IMG-A
- 切点：0.5s / 7.5s / 14.5s / 21.5s / 29.0s

**EN Master Prompt**

```text
30-second single continuous shot, locked-off camera on a tripod, no camera movement, no zoom, no cuts. 9:16 vertical. Medium close-up from mid-chest up, subject centered, eyes on the upper third line, a little headroom.
Identity: exactly the same person as in the attached reference image (same face, hair, skin tone, age appearance). clothing matches the reference image unless an outfit lock is given. No jewelry, no glasses unless visible in the reference.
Setting and light: plain warm light-grey seamless wall behind her, evenly lit, nothing else in frame. Large soft key light 45 degrees from camera left, soft fill from camera right, subtle hair rim light from behind, neutral 5600K white balance, constant exposure for the whole shot. Photorealistic, true-to-life skin texture, sharp focus on the face, natural color, fine film grain, no flicker. Quiet room tone, no music.
Performance: This plate holds four different natural ways of starting a video, separated by returns to the home pose. When she speaks, she is calm and natural with natural jaw and lip movement. Her hands stay out of view below the frame the whole time; head turns up to 30 degrees happen only in the short set-up moments before she starts speaking. Home pose: head centered and facing the lens, shoulders relaxed and level, hands resting together low and out of view below the bottom edge of the frame, lips relaxed. Energy: medium — unforced, like a real presenter settling in, never performed or theatrical.
Timeline:
0–1s: She holds the home pose.
1–2.5s: Her eyes drop down and slightly to her left as if glancing at notes below the frame, lips closed.
2.5–7s: She lifts her eyes to the lens, takes a small natural breath, breaks into a warm smile and begins speaking.
7–8s: She returns to the home pose and holds it still for one second.
8–9.5s: She turns her head about 25 degrees to her right as if finishing a word with someone off camera, lips closed.
9.5–14s: She turns back to the lens with a bright, easy smile and begins speaking.
14–15s: She returns to the home pose and holds it still for one second.
15–16.5s: She sits back slightly and relaxes her shoulders.
16.5–21s: She leans in toward the lens into the home framing, eyebrows lifting with friendly energy, and begins speaking.
21–22s: She returns to the home pose and holds it still for one second.
22–28s: From complete stillness she takes a visible, calm breath with her shoulders rising slightly, gives a small smile and begins speaking calmly.
28–30s: She relaxes back into the home pose and holds it still until the end, the final frame matching the first frame as closely as possible.
Avoid: hands touching or covering the face or mouth, head turned more than 30 degrees, hair crossing the face, jewelry, glasses, patterned clothing, logos, text, subtitles, camera movement, zoom, cuts, lighting changes, extra people, objects in the background, hands entering the frame, props, waving, laughing.
```

**中文 Master Prompt**

```text
30 秒单个连续镜头，三脚架固定机位，无运镜、无变焦、无剪辑。9:16 竖屏。胸部以上近景，人物居中，眼睛位于画面上三分之一线，头顶略留空间。
人物：与所附参考图中为同一人（脸型、发型、肤色、年龄感一致）。服装与参考图一致（除非另行指定服装锁定）。不戴首饰；除非参考图中可见，否则不戴眼镜。
场景与光线：身后是纯净的浅暖灰无缝墙，照明均匀，画面中没有其他物体。镜头左侧 45 度大面积柔光主光，镜头右侧柔和补光，身后细微的发丝轮廓光，5600K 中性白平衡，整个镜头曝光恒定。写实，真实皮肤纹理，脸部焦点清晰，自然色彩，细腻胶片颗粒，无闪烁。安静的室内环境声，无音乐。
表演：这条底板包含四种不同的自然开场方式，之间都回到回位姿势。她说话时平静自然，下颌与嘴唇自然运动。双手全程在画面底边以下不入画；最多 30 度的转头只出现在开口前的短暂准备动作里。回位姿势：头部居中面向镜头，双肩放松、水平，双手放低并拢在画面底边以下（不入画），嘴唇放松。能量：中——不刻意，像真实主播坐定开讲，绝不表演化、戏剧化。
时间线：
0–1 秒：保持回位姿势。
1–2.5 秒：她的目光向下、略偏左，像在看画面下方的提纲，嘴唇闭合。
2.5–7 秒：她抬眼看向镜头，自然地吸一小口气，绽开温暖的笑容，开始说话。
7–8 秒：回到回位姿势，静止保持一秒。
8–9.5 秒：她把头向自己的右侧转约 25 度，像刚和镜头外的人说完一句话，嘴唇闭合。
9.5–14 秒：她转回镜头，带着明亮、轻松的笑容开始说话。
14–15 秒：回到回位姿势，静止保持一秒。
15–16.5 秒：她身体略向后靠，放松双肩。
16.5–21 秒：她向镜头前倾回到回位构图，眉毛带着友好的劲头微微上扬，开始说话。
21–22 秒：回到回位姿势，静止保持一秒。
22–28 秒：从完全静止开始，她平静地吸一口气，双肩微微抬起，露出一个小小的笑容，然后平静地开始说话。
28–30 秒：放松回到回位姿势，静止保持到结束，最后一帧尽量与第一帧一致。
避免：手触碰或遮挡脸和嘴，头部转动超过 30 度，头发遮挡脸部，首饰，眼镜，有图案的服装，logo，文字，字幕，镜头运动，变焦，剪辑，光线变化，其他人物，背景杂物，手进入画面，道具，挥手，大笑。
```

**Avoid EN：** Avoid: hands touching or covering the face or mouth, head turned more than 30 degrees, hair crossing the face, jewelry, glasses, patterned clothing, logos, text, subtitles, camera movement, zoom, cuts, lighting changes, extra people, objects in the background, hands entering the frame, props, waving, laughing.

**避免（中文）：** 避免：手触碰或遮挡脸和嘴，头部转动超过 30 度，头发遮挡脸部，首饰，眼镜，有图案的服装，logo，文字，字幕，镜头运动，变焦，剪辑，光线变化，其他人物，背景杂物，手进入画面，道具，挥手，大笑。

## 更多底板 / More plates

完整中英提示词（含 L01/L02 60s 接力、K01H 横屏孪生、K03 近景变体）见：

- `prompts/PROMPT_LIBRARY.md`
- `prompts/prompts-only.txt`（纯提示词，方便复制）

- **K01H** · 近景口播主底板 · 横屏左三分之一 · MCU · 16:9 · 30s · 首帧 IMG-A169
- **K03** · 近景口播变体（可选） · MCU · 9:16 · 30s · 首帧 IMG-A
- **L01** · 近景 60 秒长底板（8 段不重样） · MCU · 9:16 · 60s · 首帧 IMG-A
- **L02** · 中景 60 秒长底板（含左右托举位） · MS · 9:16 · 60s · 首帧 IMG-B

## 生成之后 / After generation

```bash
# 1) 切片（无遮挡元视频 → 可复用镜头）
python3 -m istream slice path/to/K01.mp4 --id K01 --out drafts/K01.json --sheet drafts/K01_sheet.jpg
python3 -m istream slice path/to/K02.mp4 --id K02 --out drafts/K02.json --sheet drafts/K02_sheet.jpg
python3 -m istream slice path/to/O01.mp4 --id O01 --out drafts/O01.json --sheet drafts/O01_sheet.jpg
# 2) 人工/VLM 复核 → catalog merge-review
# 3) 写稿 → plan → edit → lipsync → render（见 SKILL.md）
```

## 恢复默认形象 / Restore default persona

换回包内定稿东亚女性形象（并让 `prompts verify` 再次对上 frozen_check）：

```bash
python3 -m istream identity restore
```

换过身份后，`istream prompts verify` 会报 MISMATCH，这是预期行为；只有默认形象才与 K01–K03 定稿逐字一致。

## 真人感 / 去 AI 味（P0）

> 状态：推测性方案：还没有在真实视频模型上做 A/B；按 docs/HUMAN_PREMIUM.md §8 的 Phase 0 A/B 跑完之前，不要当成已验证
> 完整原理、参考照规则、选片与后期：`docs/HUMAN_PREMIUM.md`。这里只放 P0 补丁、负面补充和入库评分卡。
> 叠加层只在复制时生效，**不改** `library.json`，所以 K01–K03 定稿的逐字校验（`prompts verify`）不受影响。

**一键拿到已叠加的完整提示词 / Get the patched prompts:**

```bash
python3 -m istream prompts overlay --plate K01 --lang both --negative           # 完整版
python3 -m istream prompts overlay --plate K02 --lang en --compact --negative   # 提示词字数受限的工具
python3 -m istream prompts overlay --first-frame IMG-A --lang both               # 首帧图
```

### 1) 句子替换 / Line swaps（叠加时自动完成）

| 原句 | 改为 | 为什么 |
|---|---|---|
| 照明均匀，画面中没有其他物体 · *evenly lit, nothing else in frame* | 柔和受光，从主光一侧向外自然减光，画面中没有其他物体 · *softly lit with a gentle natural falloff away from the key side, nothing else in frame* | 均匀平光的背景 = 空洞影棚，是 AI 味来源之一 |
| 脸部焦点清晰 · *sharp focus on the face* | 眼睛焦点精准 · *critical focus on the eyes* | “脸部锐利”容易引出过度锐化的皮肤；真实人像对焦在眼睛 |
| 静止保持一秒 · *holds it still for one second* | 稳稳停留约一秒，仍在呼吸、眨眼，不是定格 · *settles there for about one second, still breathing and blinking, never frozen* | 定格式静止像人体模特；切点只需要“低运动”，不需要“零运动” |
| 静止保持两秒 · *holds it still for two seconds* | 稳稳停留约两秒，仍在呼吸、眨眼，不是定格 · *settles there for about two seconds, still breathing and blinking, never frozen* | 同上，用于 60 秒接力点 |
| 静止保持到结束 · *holds it still until the end* | 安静地保持到结束（仍有呼吸和眨眼） · *holds it calmly until the end, still breathing and blinking* | 结尾静止也要有呼吸 |
| 在重音处缓慢地小幅点头 · *small, slow nods on stressed words* | 跟着重音偶尔小幅点头一两次，绝不按固定节拍 · *one or two small nods driven by the stressed words, never in a steady rhythm* | 节拍器式点头是最明显的动作 AI 痕迹 |
| 露出明亮温暖的笑容 · *bright, warm smile* | 露出先从眼睛里出来的温暖笑容 · *warm smile that starts in her eyes* | “明亮的笑”容易露出一整排牙（蜡像牙）；从眼睛开始的笑才像真的 |
| 明亮、轻松的笑容 · *bright, easy smile* | 轻松、真实、笑到眼睛里的笑容 · *easy, genuine smile that reaches her eyes* | 同上，O01 开场 |

### 2) 场景与光线补丁 · Setting patch（接在 Setting / 场景与光线 句末）

```text
Shot like a premium documentary interview on a cinema camera with an 85mm-equivalent portrait lens from a few metres away at about f/2.8: the eyes are critically sharp, the ears and the back of the hair fall off gently, and the wall behind her is softly out of focus. Key-to-fill ratio about 3:1, so the shadow side of the face keeps soft modelling, with one soft catchlight in each eye on the key side. Real skin: visible pores, fine vellus hair caught by the rim light, subtle unevenness of tone and a natural sheen on the high points, never glossy and never airbrushed. Restrained, natural film-like grade: true skin hue, soft highlight roll-off, gentle contrast; no beauty filter, no HDR look, no over-sharpening.
```

```text
按高端纪录片访谈的方式拍摄：电影摄影机，等效 85mm 人像镜头，从几米外拍，光圈约 f/2.8；眼睛焦点锐利，耳朵和脑后头发自然虚化，身后墙面柔和失焦。主光与补光约 3:1，脸部暗面保留柔和的立体感；双眼各有一个位于主光一侧的柔和眼神光。皮肤是真实的皮肤：可见毛孔、轮廓光下细小的绒毛、轻微不均匀的肤色，高光处是自然光泽，绝不油亮，绝不磨皮。克制自然的胶片感调色：肤色真实，高光过渡柔和，反差温和；不要美颜滤镜，不要 HDR 质感，不要过度锐化。
```

### 3) 表演微行为补丁 · Performance patch（接在 Performance / 表演 句末）

```text
Alive at rest: she is never frozen — her breathing shows softly in her chest and shoulders, she makes tiny weight shifts, and her eyes stay alive with small natural movements. Blinks are irregular (now and then a double blink, sometimes a longer gap), often at the end of a phrase or when her gaze shifts. Expressions are slightly asymmetric and driven by what she says: a brow lifts on a stressed word, a smile starts in the eyes and fades on its own. Between sentences her lips close fully and she takes a small breath. No movement repeats in a regular rhythm. Her hands stay exactly where described above, and nothing ever touches or covers the face.
```

```text
静止时也是活人：她从不定格——胸口和肩膀有柔和可见的呼吸起伏，身体有极轻微的重心移动，眼神有细小的自然转动。眨眼不规律（偶尔连眨两下，偶尔隔得久一点），多出现在一句话结尾或视线移动时。表情略带不对称，并跟着说话内容走：重音处眉毛微抬，笑意先出现在眼睛里，再自己慢慢退去。句与句之间双唇完全闭合，轻轻吸一口气。任何动作都不按固定节拍重复。双手的位置严格按上文描述，任何东西都不碰脸、不挡脸。
```

### 4) 首帧图补丁 · First-frame patch（放在 “No text, no logo.” 之前）

```text
Captured like an editorial portrait on a full-frame camera with an 85mm lens at f/2.8: natural skin with pores and fine vellus hair, a few fine flyaway hairs at the crown and along the parting, well away from the face, the subtle natural asymmetry of a real face, matte natural makeup, lips with natural texture, one soft catchlight in each eye, a relaxed and present expression. Not a beauty retouch, not a 3D render.
```

```text
像全画幅相机、85mm 镜头、f/2.8 拍下的杂志人像：真实皮肤，看得到毛孔和细小绒毛；头顶和发缝处有几根细碎发丝，远离脸部；保留真人脸自然的细微不对称；哑光自然妆；嘴唇有真实纹理；双眼各一个柔和眼神光；表情放松、在场。不是美颜精修，不是三维渲染。
```

### 5) 可选气质句 · Optional style line（`--style`，单独成行放在场景之后）

```text
Overall feel: a calm, premium interview — natural, intimate and quietly confident, like a carefully lit documentary, not an advertisement and not an avatar.
```

```text
整体气质：沉静、高级的访谈感——自然、亲近、从容自信，像布光讲究的纪录片，而不是广告，也不是虚拟形象。
```

### 6) 负面补充 / Negative extras（追加到每条底板的负面框）

```text
airbrushed skin, beauty filter, porcelain skin, waxy skin, glossy oily skin, over-smoothed face, CGI, 3D render, video game character, uncanny valley, doll-like face, mannequin, perfectly symmetrical face, dead eyes, vacant stare, unblinking, rhythmic blinking, metronomic nodding, robotic movement, frozen pose, floating head, stiff shoulders, constant smile, frozen smile, wax lips, glossy lipstick, fused teeth, blurry teeth, mouth smear, morphing face, identity drift, texture flicker, boiling noise, warping background, shimmering edges, helmet hair, rigid hair, over-sharpened, HDR, halo, bloom glow, oversaturated, teal and orange grade, studio void, flat lighting, everything in focus, AI-generated look
```

```text
磨皮，美颜滤镜，瓷娃娃皮肤，蜡像质感，油光皮肤，过度平滑的脸，CG，三维渲染，游戏角色，恐怖谷，娃娃脸，人体模特，完全对称的脸，眼神空洞，呆滞凝视，不眨眼，节拍式眨眼，机械点头，机器人般的动作，定格姿势，脑袋漂浮感，肩膀僵硬，一直在笑，僵住的笑容，蜡像嘴唇，亮面唇膏，牙齿粘成一片，牙齿模糊，嘴部糊成一团，脸部变形，身份漂移，纹理闪烁，噪点翻滚，背景扭曲，边缘闪烁，头盔式头发，头发僵硬成块，过度锐化，HDR，光晕，泛光，过饱和，青橙调色，空洞影棚，平光，全部清晰无景深，AI 生成感
```

负面框字数受限时只用短版 / short list: `airbrushed skin, beauty filter, waxy skin, CGI, uncanny valley, dead eyes, unblinking, metronomic nodding, frozen pose, constant smile, fused teeth, mouth smear, morphing face, texture flicker, over-sharpened`

### 7) 入库评分卡 / Take scorecard（每条底板抽 4–5 次后逐条打勾）

| # | 检查（是 / 否） | Check (yes / no) |
|---|---|---|
| 1 | 皮肤：100% 放大看鼻翼和脸颊，毛孔和细纹理清楚，而且帧与帧之间稳定（不磨皮，不“翻滚”） | Skin: at 100% on nose/cheeks, pores and fine texture are visible and stable frame to frame (no airbrush, no boiling) |
| 2 | 眼睛：眨眼不规律（30 秒至少约 6 次、间隔不均），眼神有细小移动，眼神光和主光方向一致 | Eyes: irregular blinks (≈6+ per 30 s, uneven gaps), small eye movements, catchlight matches the key side |
| 3 | 呼吸：回位静止段肩膀和胸口有轻微起伏，不是定格画面 | Breathing: during home-pose holds the shoulders/chest move slightly — not a freeze-frame |
| 4 | 节奏：2 倍速看一遍，没有重复的点头或摇摆循环 | Rhythm: watched at 2×, no repeating nod or sway loop |
| 5 | 嘴：嘴唇有纹理，牙齿颗颗分明、不是一整块白，停顿时嘴完全闭合，没有糊嘴 | Mouth: textured lips, individually defined teeth (not a white block), full closure at pauses, no smear |
| 6 | 身份（一票否决）：0 / 10 / 20 / 30 秒四帧与参考图并排，是同一个人，无漂移 | Identity (veto): frames at 0/10/20/30 s side by side with the reference are the same person, no drift |
| 7 | 头发与边缘：头顶和发缝处有少量自然碎发（远离脸），发丝和耳朵边缘稳定不闪，不是头盔头 | Hair & edges: a few natural flyaways at the crown/parting (off the face), stable hair/ear edges, no helmet hair |
| 8 | 光与景深：脸的暗面有柔和立体感（不是平光），背景有减光和虚化，没有光晕或 HDR 感 | Light & depth: soft modelling on the shadow side (not flat), background falloff and defocus, no glow or HDR |
| 9 | 表情：笑容会出现也会自然退去，中性脸不呆，左右有细微不对称 | Expression: smiles arrive and fade, neutral face is not dead, slight left-right asymmetry |
| 10 | 底板纪律（一票否决）：手不过胸、不碰脸，切点处回位，嘴始终无遮挡，无字幕水印，曝光恒定 | Plate rules (veto): hands below chest and off the face, home pose at cut points, mouth never covered, no text/watermark, constant exposure |

**规则：** 10 项里至少 9 个“是”才入库；第 6 项（身份）或第 10 项（底板纪律）任何一个“否”直接淘汰。
**Rule:** Enter the library only with ≥ 9 of 10 YES; a NO on #6 (identity) or #10 (plate rules) rejects the take regardless.

## 手势与表情（P0）

> 状态：待验证：还没有在真实视频模型上跑过；手势 / 表情补丁和 K04 / K05 都按推测方案处理，跑完 docs/GESTURE_EXPRESSION.md §I 的 Phase 0 A/B 之前不要当成已验证
> 词表、诊断、例时间线和脚本映射见 `docs/GESTURE_EXPRESSION.md`；这里只放 P0 补丁、新底板 K04 / K05、负面补充和评分卡。
> 硬规则不变：嘴永远不被挡、手不碰脸、切点在回位、头部 ±20°、无首饰 / 眼镜 / logo、机位锁死；手势像访谈主持人，不是短视频舞蹈或舞台表演。
> 同样是复制时叠加，**不改** `library.json`，`prompts verify` 照常通过。

**一键拿到已叠加的完整提示词 / Get the patched prompts:**

```bash
python3 -m istream prompts overlay --plate K02 --lang both --negative --gesture            # 真人感 + 手势表情（叠加）
python3 -m istream prompts overlay --overlay gesture_expression --plate K02 --negative     # 只叠手势表情
python3 -m istream prompts overlay --plate K04 --lang zh --negative --gesture              # 新：中景手势密集底板
python3 -m istream prompts overlay --plate K05 --lang en --compact --negative --gesture    # 新：近景表情密集底板（字数受限）
python3 -m istream catalog build-spec --overlay gesture_expression --out catalog/gesture  # 预期标签目录（含 K04 / K05）
```

### 1) 近景规则 / MCU rule

- 近景（MCU：K01 / K03 / K05 / O01 / K01H）双手永远不入画——只靠表情、眼神、呼吸和肩膀；手势只属于腰部以上的中景（MS：K02 / K04 / L02）。近景里一旦手进画面，这一段只能裁掉或淘汰。
- Close-ups (MCU: K01 / K03 / K05 / O01 / K01H) keep the hands out of frame for good — life comes from expression, eyes, breath and shoulders only. Hand gestures belong to waist-up medium shots (MS: K02 / K04 / L02). If a hand enters an MCU take, crop that span or reject it.

### 2) 表情词表 / Expression lexicon（近景、中景都可用）

| # | 表情 | 标签 | 什么时候用 | 表演提示（EN） |
|---|---|---|---|---|
| E01 | 浅笑承接 · Soft smile | `soft_smile` | 开场、话题落地后、亲和的过渡句 | A soft smile rises in her eyes first while her lips stay relaxed or just part, then it fades back to neutral within about a second. |
| E02 | 认同点头 · Agreeing nod | `nod` | “对 / 没错 / 确实”、反问之后、肯定自己的观点 | One or two small nods at uneven moments with a slight lift of the brows, as if agreeing with what she just said. |
| E03 | 思考一瞥 · Thinking glance | `think_glance` | “其实……”、设问之前、要说出一个洞察之前 | Before the key phrase her eyes drift briefly up and to the side as if finding the right word, then come back to the lens with a small nod. |
| E04 | 扬眉点题 · Brow lift on the key word | `brow_raise` | 重音词、意外的数据、列点里的每一项 | Her brows lift briefly on the stressed word and her eyes open a touch, then everything relaxes again. |
| E05 | 轻皱眉（难点 / 提醒） · Concerned furrow | `brow_furrow` | “但是 / 注意 / 坑 / 风险”、说到难点 | On the hard word her brows draw slightly together with a small concerned head tilt and a softer voice, then they release. |
| E06 | 轻笑后收 · Soft laugh, then settle | `soft_laugh` | 轻松自嘲、“我们都这样”、俏皮的插话 | A short soft laugh through the nose with a small lift of the shoulders, then she settles straight back into calm speaking. |
| E07 | 倾听脸 · Listening face | `head_tilt` | 停顿、抛出问题之后、“你可能会问”的反应镜头 | Lips closed, a slight head tilt and engaged eyes, two small nods at uneven moments and a brief quiet half smile. |
| E08 | 笃定收句 · Confident close | `nod` | 总结、结论、行动号召的最后一个字 | Her chin stays level, she gives one small downward nod on the last word and her lips close into a calm, settled half smile. |
| E09 | 共情柔和 · Empathetic softening | `soft_eyes` | “我知道这很难”、说到观众的痛点 | Her eyes soften, the inner corners of her brows lift slightly, her head tilts a little and a gentle half smile appears. |
| E10 | 会心一笑（“你懂的”） · Knowing look | `knowing_look` | “对吧？”、“你懂的”、分享一个内行人的小观察 | A slightly one-sided half smile with a tiny brow lift and a small nod toward the lens, like sharing an insider point. |

### 3) 手势词表 / Gesture lexicon（只用于中景 MS，手在画内）

| # | 手势 | 标签 | 路径（回位 → 手势 → 回位） | 幅度上限 | 时长 | 风险 |
|---|---|---|---|---|---|---|
| G01 | 摊手讲解 · Open-palm explain | `palms_open` | 腰前轻握 → 双手在胸口略低处向外摊开（一只手略早、略高）→ 回到腰前合拢 | 手不高过胸口；左右各不超过身体外侧一拳 | 1.5–2 s | low |
| G02 | 单手递出（“就是这个”） · Palm-up offer | `palm_single` | 腰前 → 一只手掌心向上，向镜头方向前送约 10 厘米 → 停半拍 → 回到腰前 | 腰到胸口之间；不伸直手臂，不伸到镜头前 | 1–1.5 s | low |
| G03 | 两手对比（“一方面……另一方面”） · Contrast hands | `contrast_hands` | 腰前 → 左手掌心向上移到身体左侧 → 右手移到身体右侧（略晚半拍）→ 两手回到腰前 | 腰部高度；每只手离身体不超过一个前臂 | 2–2.5 s | mid |
| G04 | 计数 1-2-3（高风险） · Counting 1-2-3 (high risk) | `count` | 腰前 → 一只手抬到胸口略低处，掌心略朝向自己，依次伸出食指、中指、无名指 → 回到腰前 | 只用一只手；手指放松微弯；不高过胸口 | 2–3 s | high |
| G05 | 节拍点（安全版列点） · Beat marks | `hand_beat` | 腰前 → 一只手侧掌（掌心朝侧面）在腰部高度做两三下轻微的向下点 → 回到腰前 | 幅度一拳以内；点与点间隔不均匀 | 1.5–2.5 s | low |
| G06 | 合手收束 · Hands together to sum up | `hands_together` | 腰前 → 双手在胸口略低处轻轻合拢（一只手搭在另一只上）→ 放回腰前 | 不高过胸口；不握拳 | 1.5–2 s | low |
| G07 | 轻耸肩 · Small shrug | `shrug` | 腰前 → 双肩轻抬约 2 厘米，掌心在腰前微微翻向上，眉毛一抬 → 落回回位 | 肩膀小幅；手不离开腰部高度 | 1–1.5 s | low |
| G08 | 比划大小 · Size frame | `size_frame` | 腰前 → 两只平展的手掌在胸口略低处相对，间距约 30 厘米，表示“这么大一块”→ 回到腰前 | 用平展手掌，不用拇指食指捏出“一点点”；不高过胸口 | 1–1.5 s | mid |
| G09 | 手按胸口（真诚） · Hand on chest | `hand_on_chest` | 腰前 → 一只手平放在锁骨以下的胸口中间 → 轻轻一点头 → 回到腰前 | 手必须在锁骨以下，远离下巴和脸 | 1–1.5 s | low |
| G10 | 侧向引导（给图形让位） · Open-palm guide to the side | `palm_present` | 腰前 → 画面一侧的那只手掌心向上，朝画面空的一侧轻轻打开（像在介绍旁边的图）→ 停一拍 → 回到腰前 | 胸口略低处；用整只手掌引导，不用食指指 | 1.5–2 s | low |
| G11 | 指尖相触（思考 / 笃定） · Steepled fingertips | `steeple` | 腰前 → 两手指尖在腰到胸口之间轻轻相触成“尖塔” → 散开回到腰前 | 腰到胸口之间；不抵下巴 | 1.5–2.5 s | mid |

### 4) 句子替换 / Line swaps（只作用于标注的底板，叠加时自动完成）

| 底板 | 原句 | 改为 | 为什么 |
|---|---|---|---|
| K02 | 自然的对话式说话，双手在腰前轻握，小幅点头。 · *Natural conversational talking with her hands loosely clasped at the waist and small nods.* | 自然的对话式说话，双手在腰前轻握；说话间手指自然松开又重新握一次，带着浅笑，认同地小幅点头一次。 · *Natural conversational talking with her hands loosely clasped at the waist; once, her fingers loosen and re-clasp as she speaks, with a soft smile and one small agreeing nod.* | 回位手不是“焊死”的：手指一次松开再握，加 E01 浅笑和 E02 认同点头 |
| K02 | 双手在胸口高度向外摊开，做一个放松的讲解手势，然后回到腰前合拢。 · *Both palms open outward at chest height in a relaxed explaining gesture, then come back together at the waist.* | 双手在胸口略低处向外摊开，做一个放松的讲解手势，一只手略早于另一只，关键词上眉毛微微上扬，然后双手回到腰前合拢。 · *Both palms open outward at lower-chest height in a relaxed explaining gesture, one hand slightly ahead of the other, her eyebrows lifting a little on the key word, then the hands come back together at the waist.* | G01 两手错开（去镜像）+ E04 扬眉 |
| K02 | 带着浅笑继续说话，右手在腰部高度做一个小幅、放松的摊掌动作，然后与另一只手重新合拢。 · *She keeps talking with a light smile while her right hand makes one small, relaxed open-palm movement at waist height, then rejoins the other hand.* | 带着浅笑继续说话，右手在腰部高度掌心向上、把观点轻轻往前“递”一下，双肩随之轻松地微微一耸，然后与另一只手重新合拢。 · *She keeps talking with a light smile while her right hand turns palm-up and offers the point a little forward at waist height, her shoulders lifting in a tiny easy shrug, then the hand rejoins the other.* | G02 单手递出 + G07 轻耸肩 |
| K02 | 总结时双手在胸前轻轻合拢，再放回腰前，同时自信有力地点头一次。 · *To sum up, both hands come loosely together in front of her chest, then lower back to the waist as she gives one firm, confident nod.* | 总结时双手在胸前略低处轻轻合拢，表情落定为平静笃定的浅笑，然后双手放回腰前，有力地点头一次。 · *To sum up, both hands come loosely together in front of her lower chest as her expression settles into a calm, confident half smile, then they lower back to the waist with one firm nod.* | G06 合手 + E08 笃定收句 |
| K01 / K01H | 继续说话，头部极轻微地向左倾斜，在关键词处轻扬一次眉毛，然后回正。 · *She keeps speaking with a very slight head tilt to the left and one small eyebrow raise on a key word, then straightens.* | 继续说话，头部极轻微地向左倾斜；说到关键词前，目光短暂地向斜上方一瞥，像在找合适的词，随即回到镜头，轻扬一次眉毛，然后回正。 · *She keeps speaking with a very slight head tilt to the left; before the key word her eyes flick briefly up and to the side as if finding the right word, then come back to the lens with one small eyebrow raise, and she straightens.* | 近景只加表情：E03 思考一瞥 + E04 扬眉 |
| K01 / K01H | 带着闭唇浅笑缓慢地小幅点头两次，自然眨眼一次。 · *gives two small slow nods with a soft closed-lip smile, and blinks once naturally.* | 带着闭唇浅笑，在不规律的时刻小幅点头两次，脸上有安静的回应，像听到了一个好观点，自然眨眼。 · *gives two small nods at uneven moments with a soft closed-lip smile, her face quietly responsive as if hearing a good point, and blinks naturally.* | E07 倾听脸：不规律点头 + 有回应 |
| K03 | 连续三个快速的小点头，像在肯定自己的观点。 · *Three quick small nods in a row as if agreeing with her own point.* | 两三个时机不均的小幅认同点头，眉毛微抬，带一点会心的浅笑，像在肯定自己的观点。 · *Two or three small agreeing nods at uneven moments, with a slight brow lift and a knowing half smile, as if agreeing with her own point.* | E02 + E10：去掉等间隔三连点 |
| K03 | 眉头因专注而极轻微地收拢（不是皱眉），缓慢点头一次 · *eyebrows drawn very slightly together in concentration (not frowning), and one slow nod* | 说到难点时眉头轻轻收拢、头微微一侧，带一点关切（不是生气、不是皱眉），随即舒展，缓慢点头一次 · *eyebrows drawn slightly together on the hard word with a small concerned head tilt (not angry, not frowning), then they release, and one slow nod* | E05 轻皱眉：有起有落 |
| K03 | 说话时短暂地温暖一笑，然后身体略微后靠，放松而自信地把话说完。 · *A brief warm smile while speaking, then a slight lean back, relaxed and confident, as she finishes the thought.* | 说话时短暂地温暖一笑，笑意先从眼睛里升起、又自然退去，然后身体略微后靠，放松而自信地把话说完。 · *A brief warm smile that rises in her eyes first and fades naturally while she speaks, then a slight lean back, relaxed and confident, as she finishes the thought.* | E01 浅笑承接：笑意由眼睛带出、有起有落（K03 的避免词禁止大笑，所以这里不用 E06） |

### 5) 中景表演补丁 · MS performance patch（K02 / K04 / L02，接在 Performance / 表演 句末）

```text
Gesture grammar: like a real interview host, her hands help her think — every gesture starts from the home pose, lands on a stressed word and settles back to the waist within about two seconds. Gestures stay between the waist and the lower chest, never above the chest and never near the face, chin or hair. Mostly one hand at a time; when both hands move they are slightly out of sync, never mirrored. Fingers stay relaxed and natural, with no posed hand signs. Small and conversational, never stage acting.
```

```text
手势语法：像真实的访谈主持人，手是在帮她思考——每个手势都从回位姿势出发，落在重音词上，约两秒内回到腰前。手势只在腰部到胸口略低处之间，绝不高过胸口，绝不靠近脸、下巴和头发。大多一次只动一只手；两只手同时动时前后略有错开，绝不镜像同步。手指放松自然，不摆任何手势符号。幅度小、像聊天，绝不是舞台表演。
```

避免补丁 / Avoid add-on：`hands coming near the face, chin or hair, hand signs such as OK, peace or thumbs-up, perfectly mirrored two-hand movements, the same gesture repeated in a rhythm, exaggerated stage acting` · `手靠近脸、下巴或头发，比 OK、比耶、点赞等手势符号，两手完全镜像同步，同一个手势按节拍重复，夸张的舞台表演`

### 6) 近景表演补丁 · MCU performance patch（K01 / K03 / K05 / O01 / K01H）

```text
Expression grammar: her hands never enter the frame — all the life comes from her face, eyes, breath and shoulders. Expressions are small, brief and slightly asymmetric: a soft smile that rises in the eyes and fades, a quick brow lift on a key word, a short thinking glance away and back, a slight concerned furrow on a hard word. Each expression peaks with the words and returns to a relaxed neutral before the next home pose; nothing is held like a mask.
```

```text
表情语法：双手绝不入画——所有生气都来自脸、眼睛、呼吸和肩膀。表情小、短、略带不对称：从眼睛里升起又退去的浅笑，关键词上快速一扬眉，短暂地移开视线思考再回来，说到难点时眉头轻轻一收。每个表情都随着话语到达峰值，在下一个回位前回到放松的中性脸；没有任何表情像面具一样挂着。
```

避免补丁 / Avoid add-on：`exaggerated or held expressions, cartoon surprise, winking or smirking, eyebrows stuck raised` · `夸张或一直挂着的表情，卡通式惊讶，眨单眼或坏笑，眉毛一直扬着`

### 7) 负面补充 / Negative extras

所有底板 / all plates:

```text
touching face, hand on chin, touching hair, overacting, theatrical expression, exaggerated surprise, cartoon expression, wink, smirk, frozen grin, eyebrows stuck raised, tongue out, pout
```

```text
摸脸，手托下巴，摸头发，过度表演，舞台腔表情，夸张惊讶，卡通表情，眨单眼，坏笑，僵住的笑，眉毛一直扬着，吐舌头，嘟嘴
```

中景再加 / MS plates also:

```text
pointing at camera, index finger pointing, finger guns, OK sign, peace sign, thumbs up, finger heart, jazz hands, waving, clapping, fist pump, crossed arms, hands in pockets, hands behind back, hands above shoulders, mirrored symmetric gestures, synchronized hands, repetitive gestures, metronomic hand beats, robotic gestures, frozen hands, floating hands, extra fingers, missing fingers, fused fingers, twisted wrist, props in hands, exaggerated gestures
```

```text
指向镜头，食指指人，手枪手势，OK 手势，比耶，点赞，比心，爵士手，挥手，鼓掌，握拳庆祝，抱臂，手插兜，手背在身后，手高过肩膀，两手镜像对称，两手同步，重复的手势，节拍器式点手，机械手势，僵住的手，悬空不自然的手，多手指，少手指，手指粘连，手腕扭曲，手里拿道具，夸张手势
```

- K01 / K01H 去掉 `looking away`：K01 第 2 段加入了 E03 思考一瞥（≤1 秒、回到镜头）；负面词里的 looking away 会把它压掉。“head turned away / profile view” 仍保留

### 8) 新底板 K04 / K05（叠加层定义，不进 `library.json`，待验证）

#### K04 · 中景手势底板（手势密集） · MS · 9:16 · 30s · 首帧 IMG-B

```text
30-second single continuous shot, locked-off camera on a tripod, no camera movement, no zoom, no cuts. 9:16 vertical. Medium shot from the waist up, subject centered, eyes on the upper third line, with enough room on both sides that her hands stay fully inside the frame when she gestures.
Identity: exactly the same person as in the attached reference image (same face, hair, skin tone, age appearance). clothing matches the reference image unless an outfit lock is given. No jewelry, no glasses unless visible in the reference.
Setting and light: plain warm light-grey seamless wall behind her, evenly lit, nothing else in frame. Large soft key light 45 degrees from camera left, soft fill from camera right, subtle hair rim light from behind, neutral 5600K white balance, constant exposure for the whole shot. Photorealistic, true-to-life skin texture, sharp focus on the face, natural color, fine film grain, no flicker. Quiet room tone, no music.
Performance: She speaks to the camera calmly and naturally as if mid-conversation, with natural jaw and lip movement and a relaxed rhythm. Her eyes stay on the lens, she blinks naturally, head turns stay within 20 degrees, and her hands stay between waist and chest height and never touch or cover the face or mouth. Home pose: head centered and facing the lens, shoulders relaxed and level, hands loosely clasped in front of the waist, lips relaxed. Energy: medium — this plate carries the conversational gestures of a real interview host; every gesture is small, lands on a stressed word, starts from the home pose and returns to it, and no two sections use the same gesture. Gesture grammar: like a real interview host, her hands help her think — every gesture starts from the home pose, lands on a stressed word and settles back to the waist within about two seconds. Gestures stay between the waist and the lower chest, never above the chest and never near the face, chin or hair. Mostly one hand at a time; when both hands move they are slightly out of sync, never mirrored. Fingers stay relaxed and natural, with no posed hand signs. Small and conversational, never stage acting.
Timeline:
0–1s: She holds the home pose, then begins speaking.
1–7s: Talking naturally, she turns her right hand palm-up and offers the idea a little forward at waist height, with a soft smile that rises in her eyes, then the hand returns to the waist.
7–8s: She returns to the home pose and holds it still for one second.
8–14s: Comparing two options, one hand opens palm-up to one side at waist height and the other hand to the other side half a beat later, her brows lifting a little on the second option; both hands return to the waist.
14–15s: She returns to the home pose and holds it still for one second.
15–21s: Listing three short points, her right hand makes three small downward beats at waist height, palm turned sideways, each landing on a stressed word at uneven intervals, with a small nod on the last one; then the hand returns.
21–22s: She returns to the home pose and holds it still for one second.
22–28s: With a light, easy tone she gives a small shrug, palms turning slightly up at the waist, and a soft half-laugh through the nose, then settles into a calm, confident look as the hands return to the waist.
28–30s: She finishes her sentence, returns to the home pose and holds it still until the end, the final frame matching the first frame as closely as possible.
Avoid: hands touching or covering the face or mouth, head turned more than 20 degrees, hair crossing the face, jewelry, glasses, patterned clothing, logos, text, subtitles, camera movement, zoom, cuts, lighting changes, extra people, objects in the background, counting on fingers, pointing, waving, hands rising above chest height, deformed fingers, hands coming near the face, chin or hair, hand signs such as OK, peace or thumbs-up, perfectly mirrored two-hand movements, the same gesture repeated in a rhythm, exaggerated stage acting.
```

```text
30 秒单个连续镜头，三脚架固定机位，无运镜、无变焦、无剪辑。9:16 竖屏。腰部以上中景，人物居中，眼睛位于画面上三分之一线，两侧留足空间，做手势时双手完整留在画面内。
人物：与所附参考图中为同一人（脸型、发型、肤色、年龄感一致）。服装与参考图一致（除非另行指定服装锁定）。不戴首饰；除非参考图中可见，否则不戴眼镜。
场景与光线：身后是纯净的浅暖灰无缝墙，照明均匀，画面中没有其他物体。镜头左侧 45 度大面积柔光主光，镜头右侧柔和补光，身后细微的发丝轮廓光，5600K 中性白平衡，整个镜头曝光恒定。写实，真实皮肤纹理，脸部焦点清晰，自然色彩，细腻胶片颗粒，无闪烁。安静的室内环境声，无音乐。
表演：她像正在对话一样，平静自然地对着镜头说话，下颌与嘴唇自然运动，节奏放松。视线始终看镜头，自然眨眼，头部转动不超过 20 度，双手始终在腰部到胸口之间活动，绝不触碰或遮挡脸部和嘴。回位姿势：头部居中面向镜头，双肩放松、水平，双手在腰前轻握，嘴唇放松。能量：中——这条底板承载真实访谈主持人的对话手势；每个手势都很小、落在重音词上、从回位姿势出发并回到回位姿势，任意两段不用同一个手势。手势语法：像真实的访谈主持人，手是在帮她思考——每个手势都从回位姿势出发，落在重音词上，约两秒内回到腰前。手势只在腰部到胸口略低处之间，绝不高过胸口，绝不靠近脸、下巴和头发。大多一次只动一只手；两只手同时动时前后略有错开，绝不镜像同步。手指放松自然，不摆任何手势符号。幅度小、像聊天，绝不是舞台表演。
时间线：
0–1 秒：保持回位姿势，然后开始说话。
1–7 秒：自然地说着话，右手在腰部高度掌心向上，把想法轻轻往前“递”一下，笑意先从眼睛里升起，然后手回到腰前。
7–8 秒：回到回位姿势，静止保持一秒。
8–14 秒：比较两个选项时，一只手在腰部高度掌心向上移到一侧，另一只手晚半拍移到另一侧，说到第二个选项时眉毛微微上扬；然后两手回到腰前。
14–15 秒：回到回位姿势，静止保持一秒。
15–21 秒：列举三个短点时，右手侧掌在腰部高度轻轻向下点三下，每一下落在一个重音词上，间隔不均匀，最后一下配一个小点头；然后手回到腰前。
21–22 秒：回到回位姿势，静止保持一秒。
22–28 秒：用轻松的语气小小地耸一下肩，掌心在腰前微微翻向上，从鼻子里轻笑一声，然后落定为平静笃定的神情，双手回到腰前。
28–30 秒：说完这句话，回到回位姿势，静止保持到结束，最后一帧尽量与第一帧一致。
避免：手触碰或遮挡脸和嘴，头部转动超过 20 度，头发遮挡脸部，首饰，眼镜，有图案的服装，logo，文字，字幕，镜头运动，变焦，剪辑，光线变化，其他人物，背景杂物，数手指，指向，挥手，手抬到胸口以上，手指畸形，手靠近脸、下巴或头发，比 OK、比耶、点赞等手势符号，两手完全镜像同步，同一个手势按节拍重复，夸张的舞台表演。
```

```text
Negative: hands touching face, hand covering mouth, profile view, head turned away, looking away, hair over face, jewelry, earrings, glasses, patterned clothing, logo, text, subtitles, watermark, camera movement, zoom, cut, jump cut, flicker, lighting change, extra people, extra fingers, deformed hands, distorted face, plastic skin, counting fingers, pointing, waving, fused fingers, touching face, hand on chin, touching hair, overacting, theatrical expression, exaggerated surprise, cartoon expression, wink, smirk, frozen grin, eyebrows stuck raised, tongue out, pout, pointing at camera, index finger pointing, finger guns, OK sign, peace sign, thumbs up, finger heart, jazz hands, clapping, fist pump, crossed arms, hands in pockets, hands behind back, hands above shoulders, mirrored symmetric gestures, synchronized hands, repetitive gestures, metronomic hand beats, robotic gestures, frozen hands, floating hands, missing fingers, twisted wrist, props in hands, exaggerated gestures
```

#### K05 · 近景表情底板（表情密集） · MCU · 9:16 · 30s · 首帧 IMG-A

```text
30-second single continuous shot, locked-off camera on a tripod, no camera movement, no zoom, no cuts. 9:16 vertical. Medium close-up from mid-chest up, subject centered, eyes on the upper third line, a little headroom.
Identity: exactly the same person as in the attached reference image (same face, hair, skin tone, age appearance). clothing matches the reference image unless an outfit lock is given. No jewelry, no glasses unless visible in the reference.
Setting and light: plain warm light-grey seamless wall behind her, evenly lit, nothing else in frame. Large soft key light 45 degrees from camera left, soft fill from camera right, subtle hair rim light from behind, neutral 5600K white balance, constant exposure for the whole shot. Photorealistic, true-to-life skin texture, sharp focus on the face, natural color, fine film grain, no flicker. Quiet room tone, no music.
Performance: In the first three sections she speaks to the camera calmly and naturally as if mid-conversation, with natural jaw and lip movement and a relaxed rhythm; in the last section she stops speaking and listens with her lips gently closed. Her eyes stay on the lens apart from one brief thinking glance, she blinks naturally, head turns stay within 20 degrees, and her hands stay out of view below the frame the whole time. Home pose: head centered and facing the lens, shoulders relaxed and level, hands resting together low and out of view below the bottom edge of the frame, lips relaxed. Energy: low to medium — this plate carries the small facial expressions of a real host; each expression is brief, slightly asymmetric, peaks with the words and returns to a relaxed neutral before the home pose. Expression grammar: her hands never enter the frame — all the life comes from her face, eyes, breath and shoulders. Expressions are small, brief and slightly asymmetric: a soft smile that rises in the eyes and fades, a quick brow lift on a key word, a short thinking glance away and back, a slight concerned furrow on a hard word. Each expression peaks with the words and returns to a relaxed neutral before the next home pose; nothing is held like a mask.
Timeline:
0–1s: She holds the home pose, then begins speaking.
1–7s: She begins a thought, her eyes drift briefly up and to the side as if finding the right word, then come back to the lens and her brows lift on the key word.
7–8s: She returns to the home pose and holds it still for one second.
8–14s: On a cautionary point her brows draw slightly together with a small head tilt and a softer voice, then her eyes soften with empathy as she finishes the sentence.
14–15s: She returns to the home pose and holds it still for one second.
15–21s: A light, relatable aside: a short soft laugh through the nose with a small lift of the shoulders, then she settles straight back into calm speaking with a lingering soft smile.
21–22s: She returns to the home pose and holds it still for one second.
22–28s: She stops speaking and listens with her lips closed, a slight head tilt, two small nods at uneven moments and a brief knowing half smile.
28–30s: She relaxes back into the home pose with a calm, faint closed-lip smile and holds it still until the end, the final frame matching the first frame as closely as possible.
Avoid: hands touching or covering the face or mouth, head turned more than 20 degrees, hair crossing the face, jewelry, glasses, patterned clothing, logos, text, subtitles, camera movement, zoom, cuts, lighting changes, extra people, objects in the background, hands entering the frame, open-mouthed laughing, looking away from the lens for more than a second, opening the mouth in the last section, exaggerated or held expressions, cartoon surprise, winking or smirking, eyebrows stuck raised.
```

```text
30 秒单个连续镜头，三脚架固定机位，无运镜、无变焦、无剪辑。9:16 竖屏。胸部以上近景，人物居中，眼睛位于画面上三分之一线，头顶略留空间。
人物：与所附参考图中为同一人（脸型、发型、肤色、年龄感一致）。服装与参考图一致（除非另行指定服装锁定）。不戴首饰；除非参考图中可见，否则不戴眼镜。
场景与光线：身后是纯净的浅暖灰无缝墙，照明均匀，画面中没有其他物体。镜头左侧 45 度大面积柔光主光，镜头右侧柔和补光，身后细微的发丝轮廓光，5600K 中性白平衡，整个镜头曝光恒定。写实，真实皮肤纹理，脸部焦点清晰，自然色彩，细腻胶片颗粒，无闪烁。安静的室内环境声，无音乐。
表演：前三段她像正在对话一样，平静自然地对着镜头说话，下颌与嘴唇自然运动，节奏放松；最后一段她停止说话，双唇轻轻闭合地倾听。除了一次短暂的思考式目光，视线始终看镜头，自然眨眼，头部转动不超过 20 度，双手全程在画面底边以下不入画。回位姿势：头部居中面向镜头，双肩放松、水平，双手放低并拢在画面底边以下（不入画），嘴唇放松。能量：低到中——这条底板承载真实主持人的细微表情；每个表情都短、略带不对称，随话语到达峰值，在回位前回到放松的中性脸。表情语法：双手绝不入画——所有生气都来自脸、眼睛、呼吸和肩膀。表情小、短、略带不对称：从眼睛里升起又退去的浅笑，关键词上快速一扬眉，短暂地移开视线思考再回来，说到难点时眉头轻轻一收。每个表情都随着话语到达峰值，在下一个回位前回到放松的中性脸；没有任何表情像面具一样挂着。
时间线：
0–1 秒：保持回位姿势，然后开始说话。
1–7 秒：她开始讲一个想法，目光短暂地向斜上方飘一下，像在找合适的词，随即回到镜头，在关键词上扬起眉毛。
7–8 秒：回到回位姿势，静止保持一秒。
8–14 秒：说到需要提醒的地方，眉头轻轻收拢，头微微一侧，语气放软，然后在说完这句话时眼神柔和下来，带着共情。
14–15 秒：回到回位姿势，静止保持一秒。
15–21 秒：一句轻松、让人有共鸣的插话：从鼻子里短促地轻笑一声，肩膀微微一抬，然后立刻回到平静的说话状态，嘴角留着一点浅笑。
21–22 秒：回到回位姿势，静止保持一秒。
22–28 秒：她停止说话，双唇闭合地倾听，头微微一侧，在不规律的时刻小幅点头两次，浮现一个短暂的会心浅笑。
28–30 秒：放松回到回位姿势，只留一丝平静的闭唇笑意，静止保持到结束，最后一帧尽量与第一帧一致。
避免：手触碰或遮挡脸和嘴，头部转动超过 20 度，头发遮挡脸部，首饰，眼镜，有图案的服装，logo，文字，字幕，镜头运动，变焦，剪辑，光线变化，其他人物，背景杂物，手进入画面，张嘴大笑，视线离开镜头超过一秒，最后一段张嘴，夸张或一直挂着的表情，卡通式惊讶，眨单眼或坏笑，眉毛一直扬着。
```

```text
Negative: hands touching face, hand covering mouth, profile view, head turned away, hair over face, jewelry, earrings, glasses, patterned clothing, logo, text, subtitles, watermark, camera movement, zoom, cut, jump cut, flicker, lighting change, extra people, extra fingers, deformed hands, distorted face, plastic skin, hands in frame, open-mouth laughter, wide open mouth, talking in the last section, touching face, hand on chin, touching hair, overacting, theatrical expression, exaggerated surprise, cartoon expression, wink, smirk, frozen grin, eyebrows stuck raised, tongue out, pout
```

### 9) 入库评分卡（加项）/ Scorecard add-ons

| # | 检查（是 / 否） | Check (yes / no) |
|---|---|---|
| GE1 | 回位：每个手势都从腰前回位出发，约 2.5 秒内回到回位；每个切点处双手都在回位 | Return: every gesture starts from the home pose and is back within ~2.5 s; hands are at home at every cut point |
| GE2 | 高度（一票否决）：没有任何一帧手高过胸口或靠近脸、下巴、头发、嘴 | Height (veto): no frame has a hand above the chest or near the face, chin, hair or mouth |
| GE3 | 手指：手势峰值帧 100% 放大，五指数量和形状正常，无粘连、无多指、无扭腕（G04 计数至少抽 6 次） | Fingers: at 100% on gesture peaks, five normal fingers, no fusion, extras or twisted wrists (G04 needs ≥ 6 draws) |
| GE4 | 不像节拍器：2 倍速看，手势和点头不是等间隔重复，两手没有镜像同步 | Not metronomic: at 2×, gestures and nods do not repeat at even intervals and the hands are never mirrored |
| GE5 | 词势对齐：手势和表情的峰值落在重音附近（约 ±0.3 秒），不是乱挥 | Word-gesture sync: gesture/expression peaks land near the stressed word (≈ ±0.3 s), not random waving |
| GE6 | 表情有起有落：笑、扬眉、皱眉都会退回中性，峰值 ≤ 1.5 秒，左右脸有细微不对称 | Expressions rise and fall: smiles, brow lifts and furrows return to neutral, peaks ≤ 1.5 s, slight left-right asymmetry |
| GE7 | 没有手势梗（一票否决）：没有 OK、比耶、点赞、比心、指镜头、挥手、抱臂、插兜、道具 | No meme gestures (veto): no OK, peace, thumbs-up, finger heart, pointing at camera, waving, crossed arms, pockets or props |
| GE8 | 近景纪律：近景底板手完全不入画；表情不夸张，不像舞台表演；倾听段嘴始终闭合 | MCU discipline: hands never enter close-ups; expressions are not theatrical; the mouth stays closed in listening spans |

**规则：** 和 HUMAN_PREMIUM 的 10 项一起用。8 项全部为“是”，这一段才打手势 / 表情标签；有“否”但 GE2、GE7 通过时，这一段仍可入库，但只打基础标签。GE2 或 GE7 任何一个“否”，整段不可用（手挡脸或手势梗）。
**Rule:** Use together with the HUMAN_PREMIUM 10. Tag a span with gesture/expression tags only if all 8 are YES; with a NO elsewhere but GE2 and GE7 passing, keep the span with basic tags only. A NO on GE2 or GE7 makes the span unusable.


# 高级无限流 · 底板提示词库 · Prompt Library

> 本文件由 `python -m istream prompts build` 从 `prompts/library.json` 生成，请改 JSON，不要改这里。
> K01–K03 的默认形象提示词取自 [plates-source.md](plates-source.md)（原稿名 `dh-plates-final-koubo.md`），可用 `python -m istream prompts verify` 校验。
> 提示词校验只检查文本。生成实际母片后，按[制作 Skill](../SKILL.md)复核人物、动作与切点。

## 0. 怎么用

1. **拼装公式：** `锁定行(画幅/景别/时长) + 身份 + 场景与光线 + 表演 + 时间线 + 避免`。身份和场景两块是全库共享的，**一字不改**；需要更换形象时用 `python -m istream identity set --photo ./me.jpg` 同步身份块和首帧提示词。
2. **首帧图：** 先用 IMG-A（近景）/ IMG-B（中景）/ IMG-A169（横屏左三分之一）生成首帧图，生成底板时设为首帧；支持尾帧的工具，尾帧也用同一张图，保证所有底板首尾一致、可以互拼。
3. **30 秒底板：** 直接粘贴完整提示词。每条抽 4–5 次，挑最好的一条入库。
4. **60 秒底板（L01 / L02）：** 工具支持 60 秒就用完整版；不支持就用「接力 A / 接力 B」两段各 30 秒生成：B 段用 A 段尾帧作首帧（或用延长功能），开头已带“从上一段的回位姿势无缝接续”。接力点在 28–31 秒的回位静止段里，切点 29.5 秒。
5. **开场底板（O01）：** 4 个开场镜头都从“准备动作”的中间切入，所以第一帧主播就已经“在场”（低头看提纲 / 刚转回来 / 正在前倾 / 静场吸气），而不是突然出现。这 4 段只能做全片第一个镜头（O01_s4 例外，也可做章节开场）。
6. **生成设置（沿用定稿）：** 同一模型和版本；1080p 起，能更高就更高；统一帧率（优先 25fps）；每次挂同一张身份参考图；模型自带的音频一律静音；单次上限不足 30 秒时在 14–15 秒的回位处拆两段。

## 1. 首帧图

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

## 2. 30 秒底板（定稿 + 横屏孪生）

### K01 · 近景口播主底板 · Main close-up talking plate

- 文件名：`liz01_o1_mcu_916_koubo-main_mid_30s_v01.mov` ｜ MCU · 9:16 · 30 秒 · 首帧图 IMG-A ｜ 状态：frozen (dh-plates-final-koubo.md)
- 切点（回位静止中点）：0.5s / 7.5s / 14.5s / 21.5s / 29s

| 时间 | 段 | 动作 | 角色 roles | 能量 | 情绪 | 嘴 | 倒放 |
|---|---|---|---|---|---|---|---|
| 1–7s | s1 | 平静、中性地叙述，在重音处缓慢地小幅点头，肩部几乎不动。 | narrate, explain | 2 | neutral | talking | good |
| 8–14s | s2 | 继续说话，头部极轻微地向左倾斜，在关键词处轻扬一次眉毛，然后回正。 | narrate, question | 3 | curious | talking | good |
| 15–21s | s3 | 她看向镜头，露出明亮温暖的笑容，轻轻点头表示欢迎，然后带着浅笑温暖地继续说。 | open, hook, close | 3 | warm | talking | no |
| 22–28s | s4 | 她停止说话，双唇轻闭，专注倾听，带着闭唇浅笑缓慢地小幅点头两次，自然眨眼一次。 | pause, listen, close, cta | 1 | warm | smile_closed | good |

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

**负面提示词（支持负面框的工具）：** `Negative: hands touching face, hand covering mouth, profile view, head turned away, looking away, hair over face, jewelry, earrings, glasses, patterned clothing, logo, text, subtitles, watermark, camera movement, zoom, cut, jump cut, flicker, lighting change, extra people, extra fingers, deformed hands, distorted face, plastic skin, hands in frame, laughing, wide open mouth, talking in the last section`

### K02 · 中景口播底板（自然手势） · Medium-shot talking plate with natural hands

- 文件名：`liz01_o1_ms_916_koubo-hands_mid_30s_v01.mov` ｜ MS · 9:16 · 30 秒 · 首帧图 IMG-B ｜ 状态：frozen (dh-plates-final-koubo.md)
- 切点（回位静止中点）：0.5s / 7.5s / 14.5s / 21.5s / 29s

| 时间 | 段 | 动作 | 角色 roles | 能量 | 情绪 | 嘴 | 倒放 |
|---|---|---|---|---|---|---|---|
| 1–7s | s1 | 自然的对话式说话，双手在腰前轻握，小幅点头。 | narrate | 3 | neutral | talking | ok |
| 8–14s | s2 | 双手在胸口高度向外摊开，做一个放松的讲解手势，然后回到腰前合拢。 | explain | 3 | neutral | talking | no |
| 15–21s | s3 | 带着浅笑继续说话，右手在腰部高度做一个小幅、放松的摊掌动作，然后与另一只手重新合拢。 | narrate, story | 3 | warm | talking | no |
| 22–28s | s4 | 总结时双手在胸前轻轻合拢，再放回腰前，同时自信有力地点头一次。 | summary, emphasis | 3 | confident | talking | no |

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

**负面提示词（支持负面框的工具）：** `Negative: hands touching face, hand covering mouth, profile view, head turned away, looking away, hair over face, jewelry, earrings, glasses, patterned clothing, logo, text, subtitles, watermark, camera movement, zoom, cut, jump cut, flicker, lighting change, extra people, extra fingers, deformed hands, distorted face, plastic skin, counting fingers, pointing, waving, fused fingers`

### K03 · 近景口播变体（可选） · Alternate close-up talking plate

- 文件名：`liz01_o1_mcu_916_koubo-alt_mid_30s_v01.mov` ｜ MCU · 9:16 · 30 秒 · 首帧图 IMG-A ｜ 状态：frozen (dh-plates-final-koubo.md)
- 切点（回位静止中点）：0.5s / 7.5s / 14.5s / 21.5s / 29s

| 时间 | 段 | 动作 | 角色 roles | 能量 | 情绪 | 嘴 | 倒放 |
|---|---|---|---|---|---|---|---|
| 1–7s | s1 | 对话式讲述，头部随着语言节奏轻微地左右摆动。 | narrate, story | 3 | warm | talking | good |
| 8–14s | s2 | 连续三个快速的小点头，像在肯定自己的观点。 | summary, emphasis | 3 | confident | talking | ok |
| 15–21s | s3 | 讲严肃观点时平静专注：目光坚定，眉头因专注而极轻微地收拢（不是皱眉），缓慢点头一次。 | data, emphasis, explain | 2 | serious | talking | no |
| 22–28s | s4 | 说话时短暂地温暖一笑，然后身体略微后靠，放松而自信地把话说完。 | close, cta, summary | 3 | warm | talking | no |

**EN Master Prompt**

```text
30-second single continuous shot, locked-off camera on a tripod, no camera movement, no zoom, no cuts. 9:16 vertical. Medium close-up from mid-chest up, subject centered, eyes on the upper third line, a little headroom.
Identity: exactly the same person as in the attached reference image (same face, hair, skin tone, age appearance). clothing matches the reference image unless an outfit lock is given. No jewelry, no glasses unless visible in the reference.
Setting and light: plain warm light-grey seamless wall behind her, evenly lit, nothing else in frame. Large soft key light 45 degrees from camera left, soft fill from camera right, subtle hair rim light from behind, neutral 5600K white balance, constant exposure for the whole shot. Photorealistic, true-to-life skin texture, sharp focus on the face, natural color, fine film grain, no flicker. Quiet room tone, no music.
Performance: She speaks to the camera calmly and naturally as if mid-conversation, with natural jaw and lip movement and a relaxed rhythm. Her eyes stay on the lens, she blinks naturally, head turns stay within 20 degrees, and her hands stay out of view below the frame the whole time. Home pose: head centered and facing the lens, shoulders relaxed and level, hands resting together low and out of view below the bottom edge of the frame, lips relaxed. Energy: medium — natural conversational nods and small eyebrow movements.
Timeline:
0–1s: She holds the home pose, then begins speaking.
1–7s: Conversational delivery with her head moving slightly side to side in rhythm with the words.
7–8s: She returns to the home pose and holds it still for one second.
8–14s: Three quick small nods in a row as if agreeing with her own point.
14–15s: She returns to the home pose and holds it still for one second.
15–21s: Calm and focused for a serious point: steady gaze, eyebrows drawn very slightly together in concentration (not frowning), and one slow nod.
21–22s: She returns to the home pose and holds it still for one second.
22–28s: A brief warm smile while speaking, then a slight lean back, relaxed and confident, as she finishes the thought.
28–30s: She finishes her sentence, returns to the home pose and holds it still until the end, the final frame matching the first frame as closely as possible.
Avoid: hands touching or covering the face or mouth, head turned more than 20 degrees, hair crossing the face, jewelry, glasses, patterned clothing, logos, text, subtitles, camera movement, zoom, cuts, lighting changes, extra people, objects in the background, hands entering the frame, frowning, laughing.
```

**中文 Master Prompt**

```text
30 秒单个连续镜头，三脚架固定机位，无运镜、无变焦、无剪辑。9:16 竖屏。胸部以上近景，人物居中，眼睛位于画面上三分之一线，头顶略留空间。
人物：与所附参考图中为同一人（脸型、发型、肤色、年龄感一致）。服装与参考图一致（除非另行指定服装锁定）。不戴首饰；除非参考图中可见，否则不戴眼镜。
场景与光线：身后是纯净的浅暖灰无缝墙，照明均匀，画面中没有其他物体。镜头左侧 45 度大面积柔光主光，镜头右侧柔和补光，身后细微的发丝轮廓光，5600K 中性白平衡，整个镜头曝光恒定。写实，真实皮肤纹理，脸部焦点清晰，自然色彩，细腻胶片颗粒，无闪烁。安静的室内环境声，无音乐。
表演：她像正在对话一样，平静自然地对着镜头说话，下颌与嘴唇自然运动，节奏放松。视线始终看镜头，自然眨眼，头部转动不超过 20 度，双手全程在画面底边以下不入画。回位姿势：头部居中面向镜头，双肩放松、水平，双手放低并拢在画面底边以下（不入画），嘴唇放松。能量：中——自然的对话式点头和细微的眉毛动作。
时间线：
0–1 秒：保持回位姿势，然后开始说话。
1–7 秒：对话式讲述，头部随着语言节奏轻微地左右摆动。
7–8 秒：回到回位姿势，静止保持一秒。
8–14 秒：连续三个快速的小点头，像在肯定自己的观点。
14–15 秒：回到回位姿势，静止保持一秒。
15–21 秒：讲严肃观点时平静专注：目光坚定，眉头因专注而极轻微地收拢（不是皱眉），缓慢点头一次。
21–22 秒：回到回位姿势，静止保持一秒。
22–28 秒：说话时短暂地温暖一笑，然后身体略微后靠，放松而自信地把话说完。
28–30 秒：说完这句话，回到回位姿势，静止保持到结束，最后一帧尽量与第一帧一致。
避免：手触碰或遮挡脸和嘴，头部转动超过 20 度，头发遮挡脸部，首饰，眼镜，有图案的服装，logo，文字，字幕，镜头运动，变焦，剪辑，光线变化，其他人物，背景杂物，手进入画面，皱眉，大笑。
```

**负面提示词（支持负面框的工具）：** `Negative: hands touching face, hand covering mouth, profile view, head turned away, looking away, hair over face, jewelry, earrings, glasses, patterned clothing, logo, text, subtitles, watermark, camera movement, zoom, cut, jump cut, flicker, lighting change, extra people, extra fingers, deformed hands, distorted face, plastic skin, hands in frame, frowning, angry, laughing, wide open mouth`

### K01H · 近景口播主底板 · 横屏左三分之一 · Main close-up talking plate · 16:9 left third

- 文件名：`liz01_o1_mcu_169_koubo-main-left_mid_30s_v01.mov` ｜ MCU · 16:9 · 30 秒 · 首帧图 IMG-A169 ｜ 状态：new (lock-line swap of K01)
- 切点（回位静止中点）：0.5s / 7.5s / 14.5s / 21.5s / 29s

| 时间 | 段 | 动作 | 角色 roles | 能量 | 情绪 | 嘴 | 倒放 |
|---|---|---|---|---|---|---|---|
| 1–7s | s1 | 平静、中性地叙述，在重音处缓慢地小幅点头，肩部几乎不动。 | narrate, explain | 2 | neutral | talking | good |
| 8–14s | s2 | 继续说话，头部极轻微地向左倾斜，在关键词处轻扬一次眉毛，然后回正。 | narrate, question | 3 | curious | talking | good |
| 15–21s | s3 | 她看向镜头，露出明亮温暖的笑容，轻轻点头表示欢迎，然后带着浅笑温暖地继续说。 | open, hook, close | 3 | warm | talking | no |
| 22–28s | s4 | 她停止说话，双唇轻闭，专注倾听，带着闭唇浅笑缓慢地小幅点头两次，自然眨眼一次。 | pause, listen, close, cta | 1 | warm | smile_closed | good |

**EN Master Prompt**

```text
30-second single continuous shot, locked-off camera on a tripod, no camera movement, no zoom, no cuts. 16:9 horizontal. Medium close-up from mid-chest up, subject on the left third of the frame facing the lens, eyes on the upper third line, a little headroom; the right half of the frame is clean, softly lit wall left free for graphics.
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
30 秒单个连续镜头，三脚架固定机位，无运镜、无变焦、无剪辑。16:9 横屏。胸部以上近景，人物位于画面左三分之一处、正对镜头，眼睛位于画面上三分之一线，头顶略留空间；画面右半边是干净、柔和受光的墙面，留给后期放图形。
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

**负面提示词（支持负面框的工具）：** `Negative: hands touching face, hand covering mouth, profile view, head turned away, looking away, hair over face, jewelry, earrings, glasses, patterned clothing, logo, text, subtitles, watermark, camera movement, zoom, cut, jump cut, flicker, lighting change, extra people, extra fingers, deformed hands, distorted face, plastic skin, hands in frame, laughing, wide open mouth, talking in the last section`

## 3. 60 秒长底板

### L01 · 近景 60 秒长底板（8 段不重样） · 60-second close-up plate, eight distinct sections

- 文件名：`liz01_o1_mcu_916_koubo-long_mid_60s_v01.mov` ｜ MCU · 9:16 · 60 秒 · 首帧图 IMG-A ｜ 状态：new
- 切点（回位静止中点）：0.5s / 7.5s / 14.5s / 21.5s / 29.5s / 37.5s / 44.5s / 51.5s / 59s

| 时间 | 段 | 动作 | 角色 roles | 能量 | 情绪 | 嘴 | 倒放 |
|---|---|---|---|---|---|---|---|
| 1–7s | s1 | 平稳、从容地叙述，每句话末尾缓慢点头一次，肩部保持不动。 | narrate, explain | 2 | neutral | talking | good |
| 8–14s | s2 | 讲到重点时身体极轻微地向镜头前倾，眉毛微微上扬，然后坐回。 | emphasis, explain | 3 | confident | talking | no |
| 15–21s | s3 | 像在回想什么，目光短暂地向左上方看一下，随即回到镜头，带着心中有数的小点头继续说。 | question, story | 3 | curious | talking | no |
| 22–28s | s4 | 带着浅笑，头部轻微向右侧倾，亲切放松。 | narrate, open | 3 | warm | talking | ok |
| 31–37s | s5 | 讲关键事实时严肃专注：目光稳定，几乎不动，缓慢点头一次。 | data, emphasis | 2 | serious | talking | good |
| 38–44s | s6 | 连续两个快速的小点头，像在说“对吧？”，带一点笃定的浅笑。 | summary, emphasis | 3 | confident | talking | ok |
| 45–51s | s7 | 语气更柔和、带共情：语速略慢，眼神温暖，轻轻点头一次。 | explain, narrate | 2 | empathetic | talking | good |
| 52–58s | s8 | 她停止说话，双唇轻闭地倾听，带着闭唇浅笑缓慢点头一次，自然眨眼。 | pause, listen, close | 1 | warm | smile_closed | good |

**EN Master Prompt**

```text
60-second single continuous shot, locked-off camera on a tripod, no camera movement, no zoom, no cuts. 9:16 vertical. Medium close-up from mid-chest up, subject centered, eyes on the upper third line, a little headroom.
Identity: exactly the same person as in the attached reference image (same face, hair, skin tone, age appearance). clothing matches the reference image unless an outfit lock is given. No jewelry, no glasses unless visible in the reference.
Setting and light: plain warm light-grey seamless wall behind her, evenly lit, nothing else in frame. Large soft key light 45 degrees from camera left, soft fill from camera right, subtle hair rim light from behind, neutral 5600K white balance, constant exposure for the whole shot. Photorealistic, true-to-life skin texture, sharp focus on the face, natural color, fine film grain, no flicker. Quiet room tone, no music.
Performance: She speaks to the camera calmly and naturally as if mid-conversation, with natural jaw and lip movement and a relaxed rhythm; whenever the timeline says she listens, she stops speaking and keeps her lips gently closed. Her eyes stay on the lens except for one brief thoughtful glance, she blinks naturally, head turns stay within 20 degrees, and her hands stay out of view below the frame the whole time. Home pose: head centered and facing the lens, shoulders relaxed and level, hands resting together low and out of view below the bottom edge of the frame, lips relaxed. Energy: low to medium — small, natural movements only, and every section looks different from the others so the sections can be reused in any order.
Timeline:
0–1s: She holds the home pose, then begins speaking.
1–7s: Calm, measured narration with one slow nod at the end of each phrase; shoulders still.
7–8s: She returns to the home pose and holds it still for one second.
8–14s: She leans in very slightly toward the lens for an important point, eyebrows lifting a little, then settles back.
14–15s: She returns to the home pose and holds it still for one second.
15–21s: A brief thoughtful glance up and to the left as if recalling something, then her eyes come back to the lens and she continues with a small knowing nod.
21–22s: She returns to the home pose and holds it still for one second.
22–28s: A light smile with a slight head tilt to the right, friendly and relaxed.
28–30s: She returns to the home pose and holds it still for two seconds.
30–31s: She holds the home pose, then begins speaking again.
31–37s: Serious and focused for a key fact: steady gaze, almost no movement, one slow nod.
37–38s: She returns to the home pose and holds it still for one second.
38–44s: Two quick small nods as if saying "right?", with a small confident smile.
44–45s: She returns to the home pose and holds it still for one second.
45–51s: Softer, empathetic delivery: slightly slower, warm eyes, one gentle nod.
51–52s: She returns to the home pose and holds it still for one second.
52–58s: She stops speaking and listens with her lips gently closed, a soft closed-lip smile, one slow nod and a natural blink.
58–60s: She relaxes into the home pose and holds it still until the end, the final frame matching the first frame as closely as possible.
Avoid: hands touching or covering the face or mouth, head turned more than 20 degrees, hair crossing the face, jewelry, glasses, patterned clothing, logos, text, subtitles, camera movement, zoom, cuts, lighting changes, extra people, objects in the background, hands entering the frame, frowning, laughing.
```

**中文 Master Prompt**

```text
60 秒单个连续镜头，三脚架固定机位，无运镜、无变焦、无剪辑。9:16 竖屏。胸部以上近景，人物居中，眼睛位于画面上三分之一线，头顶略留空间。
人物：与所附参考图中为同一人（脸型、发型、肤色、年龄感一致）。服装与参考图一致（除非另行指定服装锁定）。不戴首饰；除非参考图中可见，否则不戴眼镜。
场景与光线：身后是纯净的浅暖灰无缝墙，照明均匀，画面中没有其他物体。镜头左侧 45 度大面积柔光主光，镜头右侧柔和补光，身后细微的发丝轮廓光，5600K 中性白平衡，整个镜头曝光恒定。写实，真实皮肤纹理，脸部焦点清晰，自然色彩，细腻胶片颗粒，无闪烁。安静的室内环境声，无音乐。
表演：她像正在对话一样，平静自然地对着镜头说话，下颌与嘴唇自然运动，节奏放松；时间线写到“倾听”时，她停止说话，双唇轻轻闭合。除了一次短暂的思考式目光，视线始终看镜头，自然眨眼，头部转动不超过 20 度，双手全程在画面底边以下不入画。回位姿势：头部居中面向镜头，双肩放松、水平，双手放低并拢在画面底边以下（不入画），嘴唇放松。能量：低到中——只有细小、自然的动作，而且每一段都和其他段不一样，方便以任意顺序复用。
时间线：
0–1 秒：保持回位姿势，然后开始说话。
1–7 秒：平稳、从容地叙述，每句话末尾缓慢点头一次，肩部保持不动。
7–8 秒：回到回位姿势，静止保持一秒。
8–14 秒：讲到重点时身体极轻微地向镜头前倾，眉毛微微上扬，然后坐回。
14–15 秒：回到回位姿势，静止保持一秒。
15–21 秒：像在回想什么，目光短暂地向左上方看一下，随即回到镜头，带着心中有数的小点头继续说。
21–22 秒：回到回位姿势，静止保持一秒。
22–28 秒：带着浅笑，头部轻微向右侧倾，亲切放松。
28–30 秒：回到回位姿势，静止保持两秒。
30–31 秒：保持回位姿势，然后重新开始说话。
31–37 秒：讲关键事实时严肃专注：目光稳定，几乎不动，缓慢点头一次。
37–38 秒：回到回位姿势，静止保持一秒。
38–44 秒：连续两个快速的小点头，像在说“对吧？”，带一点笃定的浅笑。
44–45 秒：回到回位姿势，静止保持一秒。
45–51 秒：语气更柔和、带共情：语速略慢，眼神温暖，轻轻点头一次。
51–52 秒：回到回位姿势，静止保持一秒。
52–58 秒：她停止说话，双唇轻闭地倾听，带着闭唇浅笑缓慢点头一次，自然眨眼。
58–60 秒：放松回到回位姿势，静止保持到结束，最后一帧尽量与第一帧一致。
避免：手触碰或遮挡脸和嘴，头部转动超过 20 度，头发遮挡脸部，首饰，眼镜，有图案的服装，logo，文字，字幕，镜头运动，变焦，剪辑，光线变化，其他人物，背景杂物，手进入画面，皱眉，大笑。
```

**接力 A（30 秒）· EN**

```text
30-second single continuous shot, locked-off camera on a tripod, no camera movement, no zoom, no cuts. 9:16 vertical. Medium close-up from mid-chest up, subject centered, eyes on the upper third line, a little headroom.
Identity: exactly the same person as in the attached reference image (same face, hair, skin tone, age appearance). clothing matches the reference image unless an outfit lock is given. No jewelry, no glasses unless visible in the reference.
Setting and light: plain warm light-grey seamless wall behind her, evenly lit, nothing else in frame. Large soft key light 45 degrees from camera left, soft fill from camera right, subtle hair rim light from behind, neutral 5600K white balance, constant exposure for the whole shot. Photorealistic, true-to-life skin texture, sharp focus on the face, natural color, fine film grain, no flicker. Quiet room tone, no music.
Performance: She speaks to the camera calmly and naturally as if mid-conversation, with natural jaw and lip movement and a relaxed rhythm; whenever the timeline says she listens, she stops speaking and keeps her lips gently closed. Her eyes stay on the lens except for one brief thoughtful glance, she blinks naturally, head turns stay within 20 degrees, and her hands stay out of view below the frame the whole time. Home pose: head centered and facing the lens, shoulders relaxed and level, hands resting together low and out of view below the bottom edge of the frame, lips relaxed. Energy: low to medium — small, natural movements only, and every section looks different from the others so the sections can be reused in any order.
Timeline:
0–1s: She holds the home pose, then begins speaking.
1–7s: Calm, measured narration with one slow nod at the end of each phrase; shoulders still.
7–8s: She returns to the home pose and holds it still for one second.
8–14s: She leans in very slightly toward the lens for an important point, eyebrows lifting a little, then settles back.
14–15s: She returns to the home pose and holds it still for one second.
15–21s: A brief thoughtful glance up and to the left as if recalling something, then her eyes come back to the lens and she continues with a small knowing nod.
21–22s: She returns to the home pose and holds it still for one second.
22–28s: A light smile with a slight head tilt to the right, friendly and relaxed.
28–30s: She returns to the home pose and holds it still for two seconds.
Avoid: hands touching or covering the face or mouth, head turned more than 20 degrees, hair crossing the face, jewelry, glasses, patterned clothing, logos, text, subtitles, camera movement, zoom, cuts, lighting changes, extra people, objects in the background, hands entering the frame, frowning, laughing.
```

**接力 A（30 秒）· 中文**

```text
30 秒单个连续镜头，三脚架固定机位，无运镜、无变焦、无剪辑。9:16 竖屏。胸部以上近景，人物居中，眼睛位于画面上三分之一线，头顶略留空间。
人物：与所附参考图中为同一人（脸型、发型、肤色、年龄感一致）。服装与参考图一致（除非另行指定服装锁定）。不戴首饰；除非参考图中可见，否则不戴眼镜。
场景与光线：身后是纯净的浅暖灰无缝墙，照明均匀，画面中没有其他物体。镜头左侧 45 度大面积柔光主光，镜头右侧柔和补光，身后细微的发丝轮廓光，5600K 中性白平衡，整个镜头曝光恒定。写实，真实皮肤纹理，脸部焦点清晰，自然色彩，细腻胶片颗粒，无闪烁。安静的室内环境声，无音乐。
表演：她像正在对话一样，平静自然地对着镜头说话，下颌与嘴唇自然运动，节奏放松；时间线写到“倾听”时，她停止说话，双唇轻轻闭合。除了一次短暂的思考式目光，视线始终看镜头，自然眨眼，头部转动不超过 20 度，双手全程在画面底边以下不入画。回位姿势：头部居中面向镜头，双肩放松、水平，双手放低并拢在画面底边以下（不入画），嘴唇放松。能量：低到中——只有细小、自然的动作，而且每一段都和其他段不一样，方便以任意顺序复用。
时间线：
0–1 秒：保持回位姿势，然后开始说话。
1–7 秒：平稳、从容地叙述，每句话末尾缓慢点头一次，肩部保持不动。
7–8 秒：回到回位姿势，静止保持一秒。
8–14 秒：讲到重点时身体极轻微地向镜头前倾，眉毛微微上扬，然后坐回。
14–15 秒：回到回位姿势，静止保持一秒。
15–21 秒：像在回想什么，目光短暂地向左上方看一下，随即回到镜头，带着心中有数的小点头继续说。
21–22 秒：回到回位姿势，静止保持一秒。
22–28 秒：带着浅笑，头部轻微向右侧倾，亲切放松。
28–30 秒：回到回位姿势，静止保持两秒。
避免：手触碰或遮挡脸和嘴，头部转动超过 20 度，头发遮挡脸部，首饰，眼镜，有图案的服装，logo，文字，字幕，镜头运动，变焦，剪辑，光线变化，其他人物，背景杂物，手进入画面，皱眉，大笑。
```

**接力 B（30 秒）· EN**

```text
30-second single continuous shot, locked-off camera on a tripod, no camera movement, no zoom, no cuts. 9:16 vertical. Medium close-up from mid-chest up, subject centered, eyes on the upper third line, a little headroom.
Continue seamlessly from the previous shot, starting from the home pose.
Identity: exactly the same person as in the attached reference image (same face, hair, skin tone, age appearance). clothing matches the reference image unless an outfit lock is given. No jewelry, no glasses unless visible in the reference.
Setting and light: plain warm light-grey seamless wall behind her, evenly lit, nothing else in frame. Large soft key light 45 degrees from camera left, soft fill from camera right, subtle hair rim light from behind, neutral 5600K white balance, constant exposure for the whole shot. Photorealistic, true-to-life skin texture, sharp focus on the face, natural color, fine film grain, no flicker. Quiet room tone, no music.
Performance: She speaks to the camera calmly and naturally as if mid-conversation, with natural jaw and lip movement and a relaxed rhythm; whenever the timeline says she listens, she stops speaking and keeps her lips gently closed. Her eyes stay on the lens except for one brief thoughtful glance, she blinks naturally, head turns stay within 20 degrees, and her hands stay out of view below the frame the whole time. Home pose: head centered and facing the lens, shoulders relaxed and level, hands resting together low and out of view below the bottom edge of the frame, lips relaxed. Energy: low to medium — small, natural movements only, and every section looks different from the others so the sections can be reused in any order.
Timeline:
0–1s: She holds the home pose, then begins speaking again.
1–7s: Serious and focused for a key fact: steady gaze, almost no movement, one slow nod.
7–8s: She returns to the home pose and holds it still for one second.
8–14s: Two quick small nods as if saying "right?", with a small confident smile.
14–15s: She returns to the home pose and holds it still for one second.
15–21s: Softer, empathetic delivery: slightly slower, warm eyes, one gentle nod.
21–22s: She returns to the home pose and holds it still for one second.
22–28s: She stops speaking and listens with her lips gently closed, a soft closed-lip smile, one slow nod and a natural blink.
28–30s: She relaxes into the home pose and holds it still until the end, the final frame matching the first frame as closely as possible.
Avoid: hands touching or covering the face or mouth, head turned more than 20 degrees, hair crossing the face, jewelry, glasses, patterned clothing, logos, text, subtitles, camera movement, zoom, cuts, lighting changes, extra people, objects in the background, hands entering the frame, frowning, laughing.
```

**接力 B（30 秒）· 中文**

```text
30 秒单个连续镜头，三脚架固定机位，无运镜、无变焦、无剪辑。9:16 竖屏。胸部以上近景，人物居中，眼睛位于画面上三分之一线，头顶略留空间。
从上一段的回位姿势无缝接续。
人物：与所附参考图中为同一人（脸型、发型、肤色、年龄感一致）。服装与参考图一致（除非另行指定服装锁定）。不戴首饰；除非参考图中可见，否则不戴眼镜。
场景与光线：身后是纯净的浅暖灰无缝墙，照明均匀，画面中没有其他物体。镜头左侧 45 度大面积柔光主光，镜头右侧柔和补光，身后细微的发丝轮廓光，5600K 中性白平衡，整个镜头曝光恒定。写实，真实皮肤纹理，脸部焦点清晰，自然色彩，细腻胶片颗粒，无闪烁。安静的室内环境声，无音乐。
表演：她像正在对话一样，平静自然地对着镜头说话，下颌与嘴唇自然运动，节奏放松；时间线写到“倾听”时，她停止说话，双唇轻轻闭合。除了一次短暂的思考式目光，视线始终看镜头，自然眨眼，头部转动不超过 20 度，双手全程在画面底边以下不入画。回位姿势：头部居中面向镜头，双肩放松、水平，双手放低并拢在画面底边以下（不入画），嘴唇放松。能量：低到中——只有细小、自然的动作，而且每一段都和其他段不一样，方便以任意顺序复用。
时间线：
0–1 秒：保持回位姿势，然后重新开始说话。
1–7 秒：讲关键事实时严肃专注：目光稳定，几乎不动，缓慢点头一次。
7–8 秒：回到回位姿势，静止保持一秒。
8–14 秒：连续两个快速的小点头，像在说“对吧？”，带一点笃定的浅笑。
14–15 秒：回到回位姿势，静止保持一秒。
15–21 秒：语气更柔和、带共情：语速略慢，眼神温暖，轻轻点头一次。
21–22 秒：回到回位姿势，静止保持一秒。
22–28 秒：她停止说话，双唇轻闭地倾听，带着闭唇浅笑缓慢点头一次，自然眨眼。
28–30 秒：放松回到回位姿势，静止保持到结束，最后一帧尽量与第一帧一致。
避免：手触碰或遮挡脸和嘴，头部转动超过 20 度，头发遮挡脸部，首饰，眼镜，有图案的服装，logo，文字，字幕，镜头运动，变焦，剪辑，光线变化，其他人物，背景杂物，手进入画面，皱眉，大笑。
```

**负面提示词（支持负面框的工具）：** `Negative: hands touching face, hand covering mouth, profile view, head turned away, looking away, hair over face, jewelry, earrings, glasses, patterned clothing, logo, text, subtitles, watermark, camera movement, zoom, cut, jump cut, flicker, lighting change, extra people, extra fingers, deformed hands, distorted face, plastic skin, hands in frame, frowning, angry, laughing, wide open mouth`

### L02 · 中景 60 秒长底板（含左右托举位） · 60-second medium plate with left/right present beats

- 文件名：`liz01_o1_ms_916_koubo-hands-long_mid_60s_v01.mov` ｜ MS · 9:16 · 60 秒 · 首帧图 IMG-B ｜ 状态：new
- 切点（回位静止中点）：0.5s / 7.5s / 14.5s / 21.5s / 29.5s / 37.5s / 44.5s / 51.5s / 59s

| 时间 | 段 | 动作 | 角色 roles | 能量 | 情绪 | 嘴 | 倒放 |
|---|---|---|---|---|---|---|---|
| 1–7s | s1 | 自然的对话式说话，双手在腰前轻握，小幅点头。 | narrate | 3 | neutral | talking | ok |
| 8–14s | s2 | 画面右侧的那只手在胸口高度掌心向上，轻轻向画面右侧呈现，像托着一个小东西，停一拍，然后回到腰前。 | emphasis, data, explain | 3 | confident | talking | no |
| 15–21s | s3 | 双手在胸口高度向外摊开，做一个放松的讲解手势，然后回到腰前合拢。 | explain | 3 | neutral | talking | no |
| 22–28s | s4 | 总结时双手在胸前轻轻合拢，自信地点头一次，再放回腰前。 | summary | 3 | confident | talking | no |
| 31–37s | s5 | 她身体极轻微地前倾，双手放在腰前，用严肃专注的语气说话。 | data, emphasis | 2 | serious | talking | ok |
| 38–44s | s6 | 画面左侧的那只手在胸口高度掌心向上，轻轻向画面左侧呈现，停一拍，然后回到腰前。 | emphasis, data, explain | 3 | confident | talking | no |
| 45–51s | s7 | 双手轻握，用三个小点头标出三个短句，不数手指。 | list | 3 | neutral | talking | ok |
| 52–58s | s8 | 温暖收尾：说完这句话时露出亲切的笑容，然后双手在腰前合拢，温暖地轻轻点头。 | close, cta | 2 | warm | talking | no |

**EN Master Prompt**

```text
60-second single continuous shot, locked-off camera on a tripod, no camera movement, no zoom, no cuts. 9:16 vertical. Medium shot from the waist up, subject centered, eyes on the upper third line, with enough room on both sides that her hands stay fully inside the frame when she gestures.
Identity: exactly the same person as in the attached reference image (same face, hair, skin tone, age appearance). clothing matches the reference image unless an outfit lock is given. No jewelry, no glasses unless visible in the reference.
Setting and light: plain warm light-grey seamless wall behind her, evenly lit, nothing else in frame. Large soft key light 45 degrees from camera left, soft fill from camera right, subtle hair rim light from behind, neutral 5600K white balance, constant exposure for the whole shot. Photorealistic, true-to-life skin texture, sharp focus on the face, natural color, fine film grain, no flicker. Quiet room tone, no music.
Performance: She speaks to the camera calmly and naturally as if mid-conversation, with natural jaw and lip movement and a relaxed rhythm. Her eyes stay on the lens, she blinks naturally, head turns stay within 20 degrees, and her hands stay between waist and chest height and never touch or cover the face or mouth. Home pose: head centered and facing the lens, shoulders relaxed and level, hands loosely clasped in front of the waist, lips relaxed. Energy: medium — natural conversational nods; hand movements are small and relaxed, every gesture starts from and returns to the home pose, and no two sections use the same gesture.
Timeline:
0–1s: She holds the home pose, then begins speaking.
1–7s: Natural conversational talking with her hands loosely clasped at the waist and small nods.
7–8s: She returns to the home pose and holds it still for one second.
8–14s: Her hand on the screen-right side turns palm-up at chest height and gently presents toward screen-right as if holding something small on her palm, holds for a beat, then returns to the waist.
14–15s: She returns to the home pose and holds it still for one second.
15–21s: Both palms open outward at chest height in a relaxed explaining gesture, then come back together at the waist.
21–22s: She returns to the home pose and holds it still for one second.
22–28s: To sum up, both hands come loosely together in front of her chest with one confident nod, then lower back to the waist.
28–30s: She returns to the home pose and holds it still for two seconds.
30–31s: She holds the home pose, then begins speaking again.
31–37s: She leans forward very slightly with her hands resting at the waist and speaks in a serious, focused tone.
37–38s: She returns to the home pose and holds it still for one second.
38–44s: Her hand on the screen-left side turns palm-up at chest height and gently presents toward screen-left, holds for a beat, then returns to the waist.
44–45s: She returns to the home pose and holds it still for one second.
45–51s: Hands loosely clasped, she marks three short phrases with three small nods, without counting on her fingers.
51–52s: She returns to the home pose and holds it still for one second.
52–58s: A warm close: a friendly smile while finishing her sentence, then her hands rest together at the waist and she gives a small, warm nod.
58–60s: She returns to the home pose and holds it still until the end, the final frame matching the first frame as closely as possible.
Avoid: hands touching or covering the face or mouth, head turned more than 20 degrees, hair crossing the face, jewelry, glasses, patterned clothing, logos, text, subtitles, camera movement, zoom, cuts, lighting changes, extra people, objects in the background, counting on fingers, pointing, waving, hands rising above chest height, deformed fingers.
```

**中文 Master Prompt**

```text
60 秒单个连续镜头，三脚架固定机位，无运镜、无变焦、无剪辑。9:16 竖屏。腰部以上中景，人物居中，眼睛位于画面上三分之一线，两侧留足空间，做手势时双手完整留在画面内。
人物：与所附参考图中为同一人（脸型、发型、肤色、年龄感一致）。服装与参考图一致（除非另行指定服装锁定）。不戴首饰；除非参考图中可见，否则不戴眼镜。
场景与光线：身后是纯净的浅暖灰无缝墙，照明均匀，画面中没有其他物体。镜头左侧 45 度大面积柔光主光，镜头右侧柔和补光，身后细微的发丝轮廓光，5600K 中性白平衡，整个镜头曝光恒定。写实，真实皮肤纹理，脸部焦点清晰，自然色彩，细腻胶片颗粒，无闪烁。安静的室内环境声，无音乐。
表演：她像正在对话一样，平静自然地对着镜头说话，下颌与嘴唇自然运动，节奏放松。视线始终看镜头，自然眨眼，头部转动不超过 20 度，双手始终在腰部到胸口之间活动，绝不触碰或遮挡脸部和嘴。回位姿势：头部居中面向镜头，双肩放松、水平，双手在腰前轻握，嘴唇放松。能量：中——自然的对话式点头；手部动作小而放松，每个手势都从回位姿势开始并回到回位姿势，任意两段不用同一个手势。
时间线：
0–1 秒：保持回位姿势，然后开始说话。
1–7 秒：自然的对话式说话，双手在腰前轻握，小幅点头。
7–8 秒：回到回位姿势，静止保持一秒。
8–14 秒：画面右侧的那只手在胸口高度掌心向上，轻轻向画面右侧呈现，像托着一个小东西，停一拍，然后回到腰前。
14–15 秒：回到回位姿势，静止保持一秒。
15–21 秒：双手在胸口高度向外摊开，做一个放松的讲解手势，然后回到腰前合拢。
21–22 秒：回到回位姿势，静止保持一秒。
22–28 秒：总结时双手在胸前轻轻合拢，自信地点头一次，再放回腰前。
28–30 秒：回到回位姿势，静止保持两秒。
30–31 秒：保持回位姿势，然后重新开始说话。
31–37 秒：她身体极轻微地前倾，双手放在腰前，用严肃专注的语气说话。
37–38 秒：回到回位姿势，静止保持一秒。
38–44 秒：画面左侧的那只手在胸口高度掌心向上，轻轻向画面左侧呈现，停一拍，然后回到腰前。
44–45 秒：回到回位姿势，静止保持一秒。
45–51 秒：双手轻握，用三个小点头标出三个短句，不数手指。
51–52 秒：回到回位姿势，静止保持一秒。
52–58 秒：温暖收尾：说完这句话时露出亲切的笑容，然后双手在腰前合拢，温暖地轻轻点头。
58–60 秒：回到回位姿势，静止保持到结束，最后一帧尽量与第一帧一致。
避免：手触碰或遮挡脸和嘴，头部转动超过 20 度，头发遮挡脸部，首饰，眼镜，有图案的服装，logo，文字，字幕，镜头运动，变焦，剪辑，光线变化，其他人物，背景杂物，数手指，指向，挥手，手抬到胸口以上，手指畸形。
```

**接力 A（30 秒）· EN**

```text
30-second single continuous shot, locked-off camera on a tripod, no camera movement, no zoom, no cuts. 9:16 vertical. Medium shot from the waist up, subject centered, eyes on the upper third line, with enough room on both sides that her hands stay fully inside the frame when she gestures.
Identity: exactly the same person as in the attached reference image (same face, hair, skin tone, age appearance). clothing matches the reference image unless an outfit lock is given. No jewelry, no glasses unless visible in the reference.
Setting and light: plain warm light-grey seamless wall behind her, evenly lit, nothing else in frame. Large soft key light 45 degrees from camera left, soft fill from camera right, subtle hair rim light from behind, neutral 5600K white balance, constant exposure for the whole shot. Photorealistic, true-to-life skin texture, sharp focus on the face, natural color, fine film grain, no flicker. Quiet room tone, no music.
Performance: She speaks to the camera calmly and naturally as if mid-conversation, with natural jaw and lip movement and a relaxed rhythm. Her eyes stay on the lens, she blinks naturally, head turns stay within 20 degrees, and her hands stay between waist and chest height and never touch or cover the face or mouth. Home pose: head centered and facing the lens, shoulders relaxed and level, hands loosely clasped in front of the waist, lips relaxed. Energy: medium — natural conversational nods; hand movements are small and relaxed, every gesture starts from and returns to the home pose, and no two sections use the same gesture.
Timeline:
0–1s: She holds the home pose, then begins speaking.
1–7s: Natural conversational talking with her hands loosely clasped at the waist and small nods.
7–8s: She returns to the home pose and holds it still for one second.
8–14s: Her hand on the screen-right side turns palm-up at chest height and gently presents toward screen-right as if holding something small on her palm, holds for a beat, then returns to the waist.
14–15s: She returns to the home pose and holds it still for one second.
15–21s: Both palms open outward at chest height in a relaxed explaining gesture, then come back together at the waist.
21–22s: She returns to the home pose and holds it still for one second.
22–28s: To sum up, both hands come loosely together in front of her chest with one confident nod, then lower back to the waist.
28–30s: She returns to the home pose and holds it still for two seconds.
Avoid: hands touching or covering the face or mouth, head turned more than 20 degrees, hair crossing the face, jewelry, glasses, patterned clothing, logos, text, subtitles, camera movement, zoom, cuts, lighting changes, extra people, objects in the background, counting on fingers, pointing, waving, hands rising above chest height, deformed fingers.
```

**接力 A（30 秒）· 中文**

```text
30 秒单个连续镜头，三脚架固定机位，无运镜、无变焦、无剪辑。9:16 竖屏。腰部以上中景，人物居中，眼睛位于画面上三分之一线，两侧留足空间，做手势时双手完整留在画面内。
人物：与所附参考图中为同一人（脸型、发型、肤色、年龄感一致）。服装与参考图一致（除非另行指定服装锁定）。不戴首饰；除非参考图中可见，否则不戴眼镜。
场景与光线：身后是纯净的浅暖灰无缝墙，照明均匀，画面中没有其他物体。镜头左侧 45 度大面积柔光主光，镜头右侧柔和补光，身后细微的发丝轮廓光，5600K 中性白平衡，整个镜头曝光恒定。写实，真实皮肤纹理，脸部焦点清晰，自然色彩，细腻胶片颗粒，无闪烁。安静的室内环境声，无音乐。
表演：她像正在对话一样，平静自然地对着镜头说话，下颌与嘴唇自然运动，节奏放松。视线始终看镜头，自然眨眼，头部转动不超过 20 度，双手始终在腰部到胸口之间活动，绝不触碰或遮挡脸部和嘴。回位姿势：头部居中面向镜头，双肩放松、水平，双手在腰前轻握，嘴唇放松。能量：中——自然的对话式点头；手部动作小而放松，每个手势都从回位姿势开始并回到回位姿势，任意两段不用同一个手势。
时间线：
0–1 秒：保持回位姿势，然后开始说话。
1–7 秒：自然的对话式说话，双手在腰前轻握，小幅点头。
7–8 秒：回到回位姿势，静止保持一秒。
8–14 秒：画面右侧的那只手在胸口高度掌心向上，轻轻向画面右侧呈现，像托着一个小东西，停一拍，然后回到腰前。
14–15 秒：回到回位姿势，静止保持一秒。
15–21 秒：双手在胸口高度向外摊开，做一个放松的讲解手势，然后回到腰前合拢。
21–22 秒：回到回位姿势，静止保持一秒。
22–28 秒：总结时双手在胸前轻轻合拢，自信地点头一次，再放回腰前。
28–30 秒：回到回位姿势，静止保持两秒。
避免：手触碰或遮挡脸和嘴，头部转动超过 20 度，头发遮挡脸部，首饰，眼镜，有图案的服装，logo，文字，字幕，镜头运动，变焦，剪辑，光线变化，其他人物，背景杂物，数手指，指向，挥手，手抬到胸口以上，手指畸形。
```

**接力 B（30 秒）· EN**

```text
30-second single continuous shot, locked-off camera on a tripod, no camera movement, no zoom, no cuts. 9:16 vertical. Medium shot from the waist up, subject centered, eyes on the upper third line, with enough room on both sides that her hands stay fully inside the frame when she gestures.
Continue seamlessly from the previous shot, starting from the home pose.
Identity: exactly the same person as in the attached reference image (same face, hair, skin tone, age appearance). clothing matches the reference image unless an outfit lock is given. No jewelry, no glasses unless visible in the reference.
Setting and light: plain warm light-grey seamless wall behind her, evenly lit, nothing else in frame. Large soft key light 45 degrees from camera left, soft fill from camera right, subtle hair rim light from behind, neutral 5600K white balance, constant exposure for the whole shot. Photorealistic, true-to-life skin texture, sharp focus on the face, natural color, fine film grain, no flicker. Quiet room tone, no music.
Performance: She speaks to the camera calmly and naturally as if mid-conversation, with natural jaw and lip movement and a relaxed rhythm. Her eyes stay on the lens, she blinks naturally, head turns stay within 20 degrees, and her hands stay between waist and chest height and never touch or cover the face or mouth. Home pose: head centered and facing the lens, shoulders relaxed and level, hands loosely clasped in front of the waist, lips relaxed. Energy: medium — natural conversational nods; hand movements are small and relaxed, every gesture starts from and returns to the home pose, and no two sections use the same gesture.
Timeline:
0–1s: She holds the home pose, then begins speaking again.
1–7s: She leans forward very slightly with her hands resting at the waist and speaks in a serious, focused tone.
7–8s: She returns to the home pose and holds it still for one second.
8–14s: Her hand on the screen-left side turns palm-up at chest height and gently presents toward screen-left, holds for a beat, then returns to the waist.
14–15s: She returns to the home pose and holds it still for one second.
15–21s: Hands loosely clasped, she marks three short phrases with three small nods, without counting on her fingers.
21–22s: She returns to the home pose and holds it still for one second.
22–28s: A warm close: a friendly smile while finishing her sentence, then her hands rest together at the waist and she gives a small, warm nod.
28–30s: She returns to the home pose and holds it still until the end, the final frame matching the first frame as closely as possible.
Avoid: hands touching or covering the face or mouth, head turned more than 20 degrees, hair crossing the face, jewelry, glasses, patterned clothing, logos, text, subtitles, camera movement, zoom, cuts, lighting changes, extra people, objects in the background, counting on fingers, pointing, waving, hands rising above chest height, deformed fingers.
```

**接力 B（30 秒）· 中文**

```text
30 秒单个连续镜头，三脚架固定机位，无运镜、无变焦、无剪辑。9:16 竖屏。腰部以上中景，人物居中，眼睛位于画面上三分之一线，两侧留足空间，做手势时双手完整留在画面内。
从上一段的回位姿势无缝接续。
人物：与所附参考图中为同一人（脸型、发型、肤色、年龄感一致）。服装与参考图一致（除非另行指定服装锁定）。不戴首饰；除非参考图中可见，否则不戴眼镜。
场景与光线：身后是纯净的浅暖灰无缝墙，照明均匀，画面中没有其他物体。镜头左侧 45 度大面积柔光主光，镜头右侧柔和补光，身后细微的发丝轮廓光，5600K 中性白平衡，整个镜头曝光恒定。写实，真实皮肤纹理，脸部焦点清晰，自然色彩，细腻胶片颗粒，无闪烁。安静的室内环境声，无音乐。
表演：她像正在对话一样，平静自然地对着镜头说话，下颌与嘴唇自然运动，节奏放松。视线始终看镜头，自然眨眼，头部转动不超过 20 度，双手始终在腰部到胸口之间活动，绝不触碰或遮挡脸部和嘴。回位姿势：头部居中面向镜头，双肩放松、水平，双手在腰前轻握，嘴唇放松。能量：中——自然的对话式点头；手部动作小而放松，每个手势都从回位姿势开始并回到回位姿势，任意两段不用同一个手势。
时间线：
0–1 秒：保持回位姿势，然后重新开始说话。
1–7 秒：她身体极轻微地前倾，双手放在腰前，用严肃专注的语气说话。
7–8 秒：回到回位姿势，静止保持一秒。
8–14 秒：画面左侧的那只手在胸口高度掌心向上，轻轻向画面左侧呈现，停一拍，然后回到腰前。
14–15 秒：回到回位姿势，静止保持一秒。
15–21 秒：双手轻握，用三个小点头标出三个短句，不数手指。
21–22 秒：回到回位姿势，静止保持一秒。
22–28 秒：温暖收尾：说完这句话时露出亲切的笑容，然后双手在腰前合拢，温暖地轻轻点头。
28–30 秒：回到回位姿势，静止保持到结束，最后一帧尽量与第一帧一致。
避免：手触碰或遮挡脸和嘴，头部转动超过 20 度，头发遮挡脸部，首饰，眼镜，有图案的服装，logo，文字，字幕，镜头运动，变焦，剪辑，光线变化，其他人物，背景杂物，数手指，指向，挥手，手抬到胸口以上，手指畸形。
```

**负面提示词（支持负面框的工具）：** `Negative: hands touching face, hand covering mouth, profile view, head turned away, looking away, hair over face, jewelry, earrings, glasses, patterned clothing, logo, text, subtitles, watermark, camera movement, zoom, cut, jump cut, flicker, lighting change, extra people, extra fingers, deformed hands, distorted face, plastic skin, counting fingers, pointing, waving, fused fingers`

## 4. 开场入镜底板

### O01 · 开场入镜底板（4 种自然开场） · Opening plate — four natural ways to arrive on camera

- 文件名：`liz01_o1_mcu_916_opening-set_mid_30s_v01.mov` ｜ MCU · 9:16 · 30 秒 · 首帧图 IMG-A ｜ 状态：new
- 切点（回位静止中点）：0.5s / 7.5s / 14.5s / 21.5s / 29s

| 时间 | 段 | 动作 | 角色 roles | 能量 | 情绪 | 嘴 | 倒放 |
|---|---|---|---|---|---|---|---|
| 1–2.5s | 准备 | 她的目光向下、略偏左，像在看画面下方的提纲，嘴唇闭合。（不单独使用，作为开场镜头的入点） | — | — | — | closed | — |
| 2.5–7s | s1 | 她抬眼看向镜头，自然地吸一小口气，绽开温暖的笑容，开始说话。 | open | 3 | warm | talking | no |
| 8–9.5s | 准备 | 她把头向自己的右侧转约 25 度，像刚和镜头外的人说完一句话，嘴唇闭合。（不单独使用，作为开场镜头的入点） | — | — | — | closed | — |
| 9.5–14s | s2 | 她转回镜头，带着明亮、轻松的笑容开始说话。 | open | 3 | warm | talking | no |
| 15–16.5s | 准备 | 她身体略向后靠，放松双肩。（不单独使用，作为开场镜头的入点） | — | — | — | closed | — |
| 16.5–21s | s3 | 她向镜头前倾回到回位构图，眉毛带着友好的劲头微微上扬，开始说话。 | open, hook | 4 | curious | talking | no |
| 22–28s | s4 | 从完全静止开始，她平静地吸一口气，双肩微微抬起，露出一个小小的笑容，然后平静地开始说话。 | open, transition | 2 | warm | talking | no |

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

**负面提示词（支持负面框的工具）：** `Negative: hands touching face, hand covering mouth, profile view, looking away, hair over face, jewelry, earrings, glasses, patterned clothing, logo, text, subtitles, watermark, camera movement, zoom, cut, jump cut, flicker, lighting change, extra people, extra fingers, deformed hands, distorted face, plastic skin, hands in frame, laughing, wide open mouth, talking in the last section`

## 5. 月度换新：用菜单组合新底板

“无限”不是一套底板永远用下去，而是**锁定段不变、动作段持续换新**。下面的微动作菜单来自已有底板加上 5 个新动作；`python -m istream prompts refresh --n 4 --framing mcu --seed 202611` 会从菜单里抽出没用过的组合，生成 R01… 新底板（锁定段相同，可直接混进旧库），同时生成它们的预期标签。

| id | 景别 | 动作 | roles | 能量 | 情绪 |
|---|---|---|---|---|---|
| K01.1 | mcu | 平静、中性地叙述，在重音处缓慢地小幅点头，肩部几乎不动。 | narrate, explain | 2 | neutral |
| K01.2 | mcu | 继续说话，头部极轻微地向左倾斜，在关键词处轻扬一次眉毛，然后回正。 | narrate, question | 3 | curious |
| K01.3 | mcu | 她停止说话，双唇轻闭，专注倾听，带着闭唇浅笑缓慢地小幅点头两次，自然眨眼一次。 | pause, listen, close, cta | 1 | warm |
| K02.4 | ms | 自然的对话式说话，双手在腰前轻握，小幅点头。 | narrate | 3 | neutral |
| K02.5 | ms | 双手在胸口高度向外摊开，做一个放松的讲解手势，然后回到腰前合拢。 | explain | 3 | neutral |
| K02.6 | ms | 带着浅笑继续说话，右手在腰部高度做一个小幅、放松的摊掌动作，然后与另一只手重新合拢。 | narrate, story | 3 | warm |
| K02.7 | ms | 总结时双手在胸前轻轻合拢，再放回腰前，同时自信有力地点头一次。 | summary, emphasis | 3 | confident |
| K03.8 | mcu | 对话式讲述，头部随着语言节奏轻微地左右摆动。 | narrate, story | 3 | warm |
| K03.9 | mcu | 连续三个快速的小点头，像在肯定自己的观点。 | summary, emphasis | 3 | confident |
| K03.10 | mcu | 讲严肃观点时平静专注：目光坚定，眉头因专注而极轻微地收拢（不是皱眉），缓慢点头一次。 | data, emphasis, explain | 2 | serious |
| K03.11 | mcu | 说话时短暂地温暖一笑，然后身体略微后靠，放松而自信地把话说完。 | close, cta, summary | 3 | warm |
| L01.12 | mcu | 平稳、从容地叙述，每句话末尾缓慢点头一次，肩部保持不动。 | narrate, explain | 2 | neutral |
| L01.13 | mcu | 讲到重点时身体极轻微地向镜头前倾，眉毛微微上扬，然后坐回。 | emphasis, explain | 3 | confident |
| L01.14 | mcu | 像在回想什么，目光短暂地向左上方看一下，随即回到镜头，带着心中有数的小点头继续说。 | question, story | 3 | curious |
| L01.15 | mcu | 讲关键事实时严肃专注：目光稳定，几乎不动，缓慢点头一次。 | data, emphasis | 2 | serious |
| L01.16 | mcu | 连续两个快速的小点头，像在说“对吧？”，带一点笃定的浅笑。 | summary, emphasis | 3 | confident |
| L01.17 | mcu | 语气更柔和、带共情：语速略慢，眼神温暖，轻轻点头一次。 | explain, narrate | 2 | empathetic |
| L01.18 | mcu | 她停止说话，双唇轻闭地倾听，带着闭唇浅笑缓慢点头一次，自然眨眼。 | pause, listen, close | 1 | warm |
| L02.19 | ms | 自然的对话式说话，双手在腰前轻握，小幅点头。 | narrate | 3 | neutral |
| L02.20 | ms | 画面右侧的那只手在胸口高度掌心向上，轻轻向画面右侧呈现，像托着一个小东西，停一拍，然后回到腰前。 | emphasis, data, explain | 3 | confident |
| L02.21 | ms | 双手在胸口高度向外摊开，做一个放松的讲解手势，然后回到腰前合拢。 | explain | 3 | neutral |
| L02.22 | ms | 总结时双手在胸前轻轻合拢，自信地点头一次，再放回腰前。 | summary | 3 | confident |
| L02.23 | ms | 她身体极轻微地前倾，双手放在腰前，用严肃专注的语气说话。 | data, emphasis | 2 | serious |
| L02.24 | ms | 画面左侧的那只手在胸口高度掌心向上，轻轻向画面左侧呈现，停一拍，然后回到腰前。 | emphasis, data, explain | 3 | confident |
| L02.25 | ms | 双手轻握，用三个小点头标出三个短句，不数手指。 | list | 3 | neutral |
| L02.26 | ms | 温暖收尾：说完这句话时露出亲切的笑容，然后双手在腰前合拢，温暖地轻轻点头。 | close, cta | 2 | warm |
| X.27 | mcu | 说到一半，双唇闭合停顿半拍，像在挑一个合适的词，然后轻轻点头继续说。 | question, narrate | 2 | curious |
| X.28 | mcu | 说到一半忍不住露出一个被逗乐的浅笑，然后温暖地继续说。 | story, narrate | 3 | playful |
| X.29 | mcu | 她稍稍收拢目光、压低一点声音，像在分享一件重要的事，缓慢点头一次。 | emphasis, data | 2 | serious |
| X.30 | ms | 带着轻松的笑容，双肩小幅耸一下，像在说“其实没那么难”。 | explain, narrate | 3 | playful |
| X.31 | ms | 一只手抬到胸口高度，缓慢地做一个小幅水平划动，像在摆出一条时间线，然后回到腰前。 | story, explain | 3 | neutral |

**示例：R01（seed 202611 抽出的组合）· EN**

```text
30-second single continuous shot, locked-off camera on a tripod, no camera movement, no zoom, no cuts. 9:16 vertical. Medium close-up from mid-chest up, subject centered, eyes on the upper third line, a little headroom.
Identity: exactly the same person as in the attached reference image (same face, hair, skin tone, age appearance). clothing matches the reference image unless an outfit lock is given. No jewelry, no glasses unless visible in the reference.
Setting and light: plain warm light-grey seamless wall behind her, evenly lit, nothing else in frame. Large soft key light 45 degrees from camera left, soft fill from camera right, subtle hair rim light from behind, neutral 5600K white balance, constant exposure for the whole shot. Photorealistic, true-to-life skin texture, sharp focus on the face, natural color, fine film grain, no flicker. Quiet room tone, no music.
Performance: She speaks to the camera calmly and naturally as if mid-conversation, with natural jaw and lip movement and a relaxed rhythm. Her eyes stay on the lens, she blinks naturally, head turns stay within 20 degrees, and her hands stay out of view below the frame the whole time. Home pose: head centered and facing the lens, shoulders relaxed and level, hands resting together low and out of view below the bottom edge of the frame, lips relaxed. Energy: medium — natural conversational nods and small eyebrow movements.
Timeline:
0–1s: She holds the home pose, then begins speaking.
1–7s: Mid-sentence she pauses for half a beat with her lips closed, as if choosing the right word, then continues with a small nod.
7–8s: She returns to the home pose and holds it still for one second.
8–14s: She stops speaking and listens with her lips gently closed, a soft closed-lip smile, one slow nod and a natural blink.
14–15s: She returns to the home pose and holds it still for one second.
15–21s: Calm and focused for a serious point: steady gaze, eyebrows drawn very slightly together in concentration (not frowning), and one slow nod.
21–22s: She returns to the home pose and holds it still for one second.
22–28s: Two quick small nods as if saying "right?", with a small confident smile.
28–30s: She finishes her sentence, returns to the home pose and holds it still until the end, the final frame matching the first frame as closely as possible.
Avoid: hands touching or covering the face or mouth, head turned more than 20 degrees, hair crossing the face, jewelry, glasses, patterned clothing, logos, text, subtitles, camera movement, zoom, cuts, lighting changes, extra people, objects in the background, hands entering the frame, frowning, laughing.
```

## 6. VLM 打标提示词（入库第 2 步）

切片工具只能测出“机器测得出来的”标签（切点、人脸、运动、静音、缺陷）。情绪、手势名称、角色用下面这段提示词交给多模态模型（每个镜头喂 3–5 帧 + 测量值），返回 JSON 直接合并进 `shots.json`，再人工抽查 20%。

```text
You are tagging one shot from a digital-human talking-head plate for an automatic editor.
Input: 3–5 frames from the shot (start, middle, end, plus any gesture peak), the shot duration, and measured metrics (face box, motion level, speech fraction). Look only at what is visible; do not guess intentions.
Return ONE JSON object, no prose, with exactly these keys:
{"emotion": <one of emotion>, "gestures": [{"g": <one of gesture>, "t": <seconds from shot start>}], "gaze": <gaze>, "mouth": <mouth>, "hands": <hands>, "head_motion": <head_motion>, "roles": [<1–3 of role, best first>], "reversible": <reversible>, "jaw": <jaw>, "energy": <1–5>, "defects": [<free text, e.g. "second face: glass reflection left half">], "notes": <≤20 words>}
Rules: hands anywhere near the mouth or chin → hands="near_face". A smile showing many teeth → mouth="open_smile". reversible="good" only if the motion is symmetric (nods, stillness) and nothing (blink, gesture) would look backwards. roles: open = the host arrives / greets; pause/listen = mouth closed; emphasis = a clear peak (lean-in, brow raise, firm nod).
Allowed values:
- emotion: neutral, warm, serious, curious, confident, empathetic, playful, surprised
- gesture: none, nod, nod_multi, head_tilt, brow_raise, soft_smile, think_glance, brow_furrow, soft_laugh, soft_eyes, knowing_look, sway, palms_open, palm_single, hands_together, palm_present, contrast_hands, hand_beat, shrug, size_frame, hand_on_chest, steeple, lean_in, lean_back, smile_greet, look_up_to_lens, turn_to_lens, settle_in, point_left, point_right, count
- gaze: lens, down, off_left, off_right, up
- mouth: talking, closed, smile_closed, open_smile
- hands: out_of_frame, low, chest, near_face
- head_motion: still, small, medium, large
- role: open, hook, narrate, explain, story, list, data, question, emphasis, agree, contrast, caveat, think, empathy, summary, pause, listen, transition, close, cta
- reversible: no, ok, good
- jaw: low, mid, high
- energy: 1, 2, 3, 4, 5
```

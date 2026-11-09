# 真人感母片的生成与验收

<!-- 本文由 tools/HUMAN_PREMIUM.template.md 与 prompts/overlays/human_premium.json 生成。 -->

选择五官、唇缘清晰的单人参考照，固定人物、服装和光源。同批母片先试一段近景，观察皮肤纹理、眨眼、呼吸和句间回位。若嘴被遮住、面部漂移或动作中途跳变，应换片重试。

## 使用提示词

在仓库根目录运行 `python3 -m istream prompts overlay --plate K01 --lang both --negative`，复制适合所用模型的版本。字数受限时加 `--compact`。以下摘出叠加层的主要字段，便于对照生成结果。

| 用途 | 中文 | English |
| --- | --- | --- |
| 光线与镜头 | 按高端纪录片访谈的方式拍摄：电影摄影机，等效 85mm 人像镜头，从几米外拍，光圈约 f/2.8；眼睛焦点锐利，耳朵和脑后头发自然虚化，身后墙面柔和失焦。主光与补光约 3:1，脸部暗面保留柔和的立体感；双眼各有一个位于主光一侧的柔和眼神光。皮肤是真实的皮肤：可见毛孔、轮廓光下细小的绒毛、轻微不均匀的肤色，高光处是自然光泽，绝不油亮，绝不磨皮。克制自然的胶片感调色：肤色真实，高光过渡柔和，反差温和；不要美颜滤镜，不要 HDR 质感，不要过度锐化。 | Shot like a premium documentary interview on a cinema camera with an 85mm-equivalent portrait lens from a few metres away at about f/2.8: the eyes are critically sharp, the ears and the back of the hair fall off gently, and the wall behind her is softly out of focus. Key-to-fill ratio about 3:1, so the shadow side of the face keeps soft modelling, with one soft catchlight in each eye on the key side. Real skin: visible pores, fine vellus hair caught by the rim light, subtle unevenness of tone and a natural sheen on the high points, never glossy and never airbrushed. Restrained, natural film-like grade: true skin hue, soft highlight roll-off, gentle contrast; no beauty filter, no HDR look, no over-sharpening. |
| 微表情与动作 | 静止时也是活人：她从不定格——胸口和肩膀有柔和可见的呼吸起伏，身体有极轻微的重心移动，眼神有细小的自然转动。眨眼不规律（偶尔连眨两下，偶尔隔得久一点），多出现在一句话结尾或视线移动时。表情略带不对称，并跟着说话内容走：重音处眉毛微抬，笑意先出现在眼睛里，再自己慢慢退去。句与句之间双唇完全闭合，轻轻吸一口气。任何动作都不按固定节拍重复。双手的位置严格按上文描述，任何东西都不碰脸、不挡脸。 | Alive at rest: she is never frozen — her breathing shows softly in her chest and shoulders, she makes tiny weight shifts, and her eyes stay alive with small natural movements. Blinks are irregular (now and then a double blink, sometimes a longer gap), often at the end of a phrase or when her gaze shifts. Expressions are slightly asymmetric and driven by what she says: a brow lifts on a stressed word, a smile starts in the eyes and fades on its own. Between sentences her lips close fully and she takes a small breath. No movement repeats in a regular rhythm. Her hands stay exactly where described above, and nothing ever touches or covers the face. |
| 首帧人物 | 像全画幅相机、85mm 镜头、f/2.8 拍下的杂志人像：真实皮肤，看得到毛孔和细小绒毛；头顶和发缝处有几根细碎发丝，远离脸部；保留真人脸自然的细微不对称；哑光自然妆；嘴唇有真实纹理；双眼各一个柔和眼神光；表情放松、在场。不是美颜精修，不是三维渲染。 | Captured like an editorial portrait on a full-frame camera with an 85mm lens at f/2.8: natural skin with pores and fine vellus hair, a few fine flyaway hairs at the crown and along the parting, well away from the face, the subtle natural asymmetry of a real face, matte natural makeup, lips with natural texture, one soft catchlight in each eye, a relaxed and present expression. Not a beauty retouch, not a 3D render. |
| 可选风格 | 整体气质：沉静、高级的访谈感——自然、亲近、从容自信，像布光讲究的纪录片，而不是广告，也不是虚拟形象。 | Overall feel: a calm, premium interview — natural, intimate and quietly confident, like a carefully lit documentary, not an advertisement and not an avatar. |

## 入库评分

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

10 项里至少 9 个“是”才入库；第 6 项（身份）或第 10 项（底板纪律）任何一个“否”直接淘汰。

后期若发现口型区域比周围皮肤更平滑，可在人物合成后统一施加细颗粒（P1-10），并以最终导出尺寸复查嘴唇和牙齿。[校准与复核](../skills/portrait-lipsync/SKILL.md)

## 8. 对照验证（Phase 0 A/B）

用同一参考照、模型、机位和生成设置分别生成基础版与叠加版。按上表评估每条实际母片，再决定是否入库；提示词能通过文本校验，只说明它按预期组成。

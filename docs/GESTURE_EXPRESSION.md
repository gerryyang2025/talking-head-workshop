# 手势与表情选用指南

<!-- 本文由 tools/GESTURE_EXPRESSION.template.md 与 prompts/overlays/gesture_expression.json 生成。 -->

用中景容纳手臂动作，用近景呈现眉眼和头部动作。近景（MCU：K01 / K03 / K05 / O01 / K01H）双手永远不入画——只靠表情、眼神、呼吸和肩膀；手势只属于腰部以上的中景（MS：K02 / K04 / L02）。近景里一旦手进画面，这一段只能裁掉或淘汰。 若生成画面像在反复点头，先减少同段动作；手靠近嘴或切点落在动作中间时，重选回位片段。

在仓库根目录运行 `python3 -m istream prompts overlay --plate K04 --lang zh --gesture --negative`，获取中景手势母片的完整提示词。K02 可叠加温和手势，K05 用于近景表情。下表描述预期动作，实际镜头需看片复核。

## E. 脚本与标签

CLI 稿件可在句首标注意图，或用 `[手势: 对比]`、`[表情: 浅笑+扬眉]` 指定动作。[脚本示例](../recipes/gesture/script.md)

| 意图 role | 标记 | 触发词 | 中景：表情 + 手势 | 近景替代 | 备注 |
|---|---|---|---|---|---|
| `open` | [开场] | 大家好、今天聊 | E01 浅笑承接 ＋ G02 单手递出（“就是这个”） | E01；开场优先用 O01 的开场专用镜头 |  |
| `agree` | [认同] / [肯定] | 对、没错、确实、是的 | E02 认同点头 / E10 会心一笑（“你懂的”） ＋ G06 合手收束 | E02 / E10 |  |
| `list` | [列点] / ①②③ | 第一、第二、三个 | E04 扬眉点题 ＋ G05 节拍点（安全版列点） / G04 计数 1-2-3（高风险） | E02 小点头 + 字幕 ①②③ | 默认 G05 节拍点；G04 计数是高风险，需要额外抽卡 |
| `contrast` | [对比] | 一方面……另一方面、不是……而是、A 还是 B | E04 扬眉点题 ＋ G03 两手对比（“一方面……另一方面”） | 头部轻轻左右一侧 + E04 |  |
| `caveat` | [提醒] / [转折] / [注意] | 但是、不过、注意、坑、风险 | E05 轻皱眉（难点 / 提醒） / E09 共情柔和 ＋ G07 轻耸肩 / G09 手按胸口（真诚） | E05 |  |
| `think` | [思考] | 其实、你有没有想过、我想了很久 | E03 思考一瞥 ＋ G11 指尖相触（思考 / 笃定） | E03 |  |
| `question` | [提问] | ？、为什么、怎么办 | E03 思考一瞥 / E04 扬眉点题 ＋ G02 单手递出（“就是这个”） | E04 + 推近 |  |
| `emphasis` | [强调] / [重音: 词] | 才叫、记住、关键 | E04 扬眉点题 ＋ G02 单手递出（“就是这个”） / G05 节拍点（安全版列点） | E04 + 推近 |  |
| `data` | [数据] | 数字、倍、百分之 | E04 扬眉点题 ＋ G08 比划大小 / G10 侧向引导（给图形让位） | E04 |  |
| `empathy` | [共情] | 我知道、很多人都、别担心 | E09 共情柔和 ＋ G09 手按胸口（真诚） | E09 |  |
| `story` | [故事]（轻松时加 [表情: 轻笑后收]） | 比如、有一次、我们都 | E06 轻笑后收 / E01 浅笑承接 ＋ G07 轻耸肩 / G02 单手递出（“就是这个”） | E06 |  |
| `summary` | [总结] | 总之、一句话、所以说 | E08 笃定收句 ＋ G06 合手收束 | E08 |  |
| `pause` | [停顿] / 倾听 | （静场、抛出问题后） | E07 倾听脸 ＋ — | E07（闭嘴段，不送口型） |  |
| `cta` | [关注] | 关注、下期 | E01 浅笑承接 / E08 笃定收句 ＋ G02 单手递出（“就是这个”） | E01 → E08 |  |

### K04 的动作与切点

| 时间 | 动作（ZH） | Action (EN) | 词表 / 标签 | 角色 |
|---|---|---|---|---|
| 0–1 s | 保持回位姿势，然后开始说话。 | She holds the home pose, then begins speaking. | 起始回位 | — |
| 1–7 s | 自然地说着话，右手在腰部高度掌心向上，把想法轻轻往前“递”一下，笑意先从眼睛里升起，然后手回到腰前。 | Talking naturally, she turns her right hand palm-up and offers the idea a little forward at waist height, with a soft smile that rises in her eyes, then the hand returns to the waist. | G02 `palm_single` + E01 `soft_smile` | explain, open, narrate |
| 7–8 s | 回到回位姿势，静止保持一秒。 | She returns to the home pose and holds it still for one second. | **回位 ✂** | — |
| 8–14 s | 比较两个选项时，一只手在腰部高度掌心向上移到一侧，另一只手晚半拍移到另一侧，说到第二个选项时眉毛微微上扬；然后两手回到腰前。 | Comparing two options, one hand opens palm-up to one side at waist height and the other hand to the other side half a beat later, her brows lifting a little on the second option; both hands return to the waist. | G03 `contrast_hands` + E04 `brow_raise` | contrast, explain |
| 14–15 s | 回到回位姿势，静止保持一秒。 | She returns to the home pose and holds it still for one second. | **回位 ✂** | — |
| 15–21 s | 列举三个短点时，右手侧掌在腰部高度轻轻向下点三下，每一下落在一个重音词上，间隔不均匀，最后一下配一个小点头；然后手回到腰前。 | Listing three short points, her right hand makes three small downward beats at waist height, palm turned sideways, each landing on a stressed word at uneven intervals, with a small nod on the last one; then the hand returns. | G05 `hand_beat` + E02 `nod` | list, data, emphasis |
| 21–22 s | 回到回位姿势，静止保持一秒。 | She returns to the home pose and holds it still for one second. | **回位 ✂** | — |
| 22–28 s | 用轻松的语气小小地耸一下肩，掌心在腰前微微翻向上，从鼻子里轻笑一声，然后落定为平静笃定的神情，双手回到腰前。 | With a light, easy tone she gives a small shrug, palms turning slightly up at the waist, and a soft half-laugh through the nose, then settles into a calm, confident look as the hands return to the waist. | G07 `shrug` + E06 `soft_laugh` | caveat, story, agree |
| 28–30 s | 说完这句话，回到回位姿势，静止保持到结束，最后一帧尽量与第一帧一致。 | She finishes her sentence, returns to the home pose and holds it still until the end, the final frame matching the first frame as closely as possible. | **回位 ✂（尾帧≈首帧）** | — |

## 入库复核

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

和 HUMAN_PREMIUM 的 10 项一起用。8 项全部为“是”，这一段才打手势 / 表情标签；有“否”但 GE2、GE7 通过时，这一段仍可入库，但只打基础标签。GE2 或 GE7 任何一个“否”，整段不可用（手挡脸或手势梗）。

## I. 对照验证（Phase 0 A/B）

固定参考照和生成设置，对比基础母片与叠加版。检查每个手势是否在画内完成、是否遮嘴、回位处能否接入下一句；记录通过复核的片段和实际出入点。

## 动作词表

### 表情与头部动作

| 表情 | 何时用 | 切片位置 |
|---|---|---|
| E01 浅笑承接 (`soft_smile`) | 开场、话题落地后、亲和的过渡句 | 等笑意退了再回位；不要在笑的峰值上切 |
| E02 认同点头 (`nod`) | “对 / 没错 / 确实”、反问之后、肯定自己的观点 | 点头之间可以切；不要切在头最低点 |
| E03 思考一瞥 (`think_glance`) | “其实……”、设问之前、要说出一个洞察之前 | 切点前视线至少回到镜头 0.5 秒；适合放在句首或停顿里，口型更安全 |
| E04 扬眉点题 (`brow_raise`) | 重音词、意外的数据、列点里的每一项 | 峰值 ≤ 0.5 秒；可以和推近一起用 |
| E05 轻皱眉（难点 / 提醒） (`brow_furrow`) | “但是 / 注意 / 坑 / 风险”、说到难点 | 回位前眉头必须完全舒展 |
| E06 轻笑后收 (`soft_laugh`) | 轻松自嘲、“我们都这样”、俏皮的插话 | 不放在切点；回位前嘴已闭合（大笑会让口型替换失效） |
| E07 倾听脸 (`head_tilt`) | 停顿、抛出问题之后、“你可能会问”的反应镜头 | 闭嘴段不送口型；可以整段用作停顿 / 反应镜头 |
| E08 笃定收句 (`nod`) | 总结、结论、行动号召的最后一个字 | 很适合直接接回位；是最安全的段尾 |
| E09 共情柔和 (`soft_eyes`) | “我知道这很难”、说到观众的痛点 | 适合配慢一点的语速 |
| E10 会心一笑（“你懂的”） (`knowing_look`) | “对吧？”、“你懂的”、分享一个内行人的小观察 | 峰值短；不要接在严肃句后面 |

### 中景手势

| 手势 | 动作路径 | 幅度上限 | 风险 |
|---|---|---|---|
| G01 摊手讲解 (`palms_open`) | 腰前轻握 → 双手在胸口略低处向外摊开（一只手略早、略高）→ 回到腰前合拢 | 手不高过胸口；左右各不超过身体外侧一拳 | low |
| G02 单手递出（“就是这个”） (`palm_single`) | 腰前 → 一只手掌心向上，向镜头方向前送约 10 厘米 → 停半拍 → 回到腰前 | 腰到胸口之间；不伸直手臂，不伸到镜头前 | low |
| G03 两手对比（“一方面……另一方面”） (`contrast_hands`) | 腰前 → 左手掌心向上移到身体左侧 → 右手移到身体右侧（略晚半拍）→ 两手回到腰前 | 腰部高度；每只手离身体不超过一个前臂 | mid |
| G04 计数 1-2-3（高风险） (`count`) | 腰前 → 一只手抬到胸口略低处，掌心略朝向自己，依次伸出食指、中指、无名指 → 回到腰前 | 只用一只手；手指放松微弯；不高过胸口 | high |
| G05 节拍点（安全版列点） (`hand_beat`) | 腰前 → 一只手侧掌（掌心朝侧面）在腰部高度做两三下轻微的向下点 → 回到腰前 | 幅度一拳以内；点与点间隔不均匀 | low |
| G06 合手收束 (`hands_together`) | 腰前 → 双手在胸口略低处轻轻合拢（一只手搭在另一只上）→ 放回腰前 | 不高过胸口；不握拳 | low |
| G07 轻耸肩 (`shrug`) | 腰前 → 双肩轻抬约 2 厘米，掌心在腰前微微翻向上，眉毛一抬 → 落回回位 | 肩膀小幅；手不离开腰部高度 | low |
| G08 比划大小 (`size_frame`) | 腰前 → 两只平展的手掌在胸口略低处相对，间距约 30 厘米，表示“这么大一块”→ 回到腰前 | 用平展手掌，不用拇指食指捏出“一点点”；不高过胸口 | mid |
| G09 手按胸口（真诚） (`hand_on_chest`) | 腰前 → 一只手平放在锁骨以下的胸口中间 → 轻轻一点头 → 回到腰前 | 手必须在锁骨以下，远离下巴和脸 | low |
| G10 侧向引导（给图形让位） (`palm_present`) | 腰前 → 画面一侧的那只手掌心向上，朝画面空的一侧轻轻打开（像在介绍旁边的图）→ 停一拍 → 回到腰前 | 胸口略低处；用整只手掌引导，不用食指指 | low |
| G11 指尖相触（思考 / 笃定） (`steeple`) | 腰前 → 两手指尖在腰到胸口之间轻轻相触成“尖塔” → 散开回到腰前 | 腰到胸口之间；不抵下巴 | mid |

# 真人感母片的生成与验收

<!-- 本文由 tools/HUMAN_PREMIUM.template.md 与 prompts/overlays/human_premium.json 生成。 -->

选择五官、唇缘清晰的单人参考照，固定人物、服装和光源。同批母片先试一段近景，观察皮肤纹理、眨眼、呼吸和句间回位。若嘴被遮住、面部漂移或动作中途跳变，应换片重试。

## 使用提示词

在仓库根目录运行 `python3 -m istream prompts overlay --plate K01 --lang both --negative`，复制适合所用模型的版本。字数受限时加 `--compact`。以下摘出叠加层的主要字段，便于对照生成结果。

| 用途 | 中文 | English |
| --- | --- | --- |
| 光线与镜头 | {{setting_append.zh}} | {{setting_append.en}} |
| 微表情与动作 | {{performance_append.zh}} | {{performance_append.en}} |
| 首帧人物 | {{first_frame_append.zh}} | {{first_frame_append.en}} |
| 可选风格 | {{style_line.zh}} | {{style_line.en}} |

## 入库评分

{{SCORECARD_TABLE}}

{{scorecard_rule.zh}}

后期若发现口型区域比周围皮肤更平滑，可在人物合成后统一施加细颗粒（P1-10），并以最终导出尺寸复查嘴唇和牙齿。[校准与复核](../skills/portrait-lipsync/SKILL.md)

## 8. 对照验证（Phase 0 A/B）

用同一参考照、模型、机位和生成设置分别生成基础版与叠加版。按上表评估每条实际母片，再决定是否入库；提示词能通过文本校验，只说明它按预期组成。

# 手势与表情选用指南

<!-- 本文由 tools/GESTURE_EXPRESSION.template.md 与 prompts/overlays/gesture_expression.json 生成。 -->

用中景容纳手臂动作，用近景呈现眉眼和头部动作。{{mcu_rule.zh}} 若生成画面像在反复点头，先减少同段动作；手靠近嘴或切点落在动作中间时，重选回位片段。

在仓库根目录运行 `python3 -m istream prompts overlay --plate K04 --lang zh --gesture --negative`，获取中景手势母片的完整提示词。K02 可叠加温和手势，K05 用于近景表情。下表描述预期动作，实际镜头需看片复核。

## E. 脚本与标签

CLI 稿件可在句首标注意图，或用 `[手势: 对比]`、`[表情: 浅笑+扬眉]` 指定动作。[脚本示例](../recipes/gesture/script.md)

{{INTENT_TABLE}}

### K04 的动作与切点

{{TIMELINE_K04}}

## 入库复核

{{SCORECARD_TABLE}}

{{scorecard_rule.zh}}

## I. 对照验证（Phase 0 A/B）

固定参考照和生成设置，对比基础母片与叠加版。检查每个手势是否在画内完成、是否遮嘴、回位处能否接入下一句；记录通过复核的片段和实际出入点。

## 动作词表

### 表情与头部动作

{{EXPR_LEXICON}}

### 中景手势

{{GESTURE_LEXICON}}

---
name: talking-head-workshop
description: 用可复用的人物照片或视频母片制作数字人口播。适用于准备人物提示词、切片打标、按配音选镜、安排补充画面、局部口型推理、横竖版导出与复核。
---

# 口播工坊制作流程

先确认出镜人物、最终台词或录音、目标画幅和交付物。用户已指定照片、视频或音色时，使用指定素材。修已有成片时记下问题时点，保留可供对比的原版。

## 1. 确定主讲与母片

已有单人照片或视频，可直接在工作台素材库设为主讲。照片适合固定构图；需要真实转头或手势时选视频。补充照片或视频可多选，按句或按秒插入。需要出镜说话的补充人物也可以作为该段口播素材。[工作台入口与安装](README.md)

若要用外部视频模型新做一批母片，在仓库根目录绑定参考照，然后打开生成包：

```sh
python3 -m istream identity set --photo ./me.jpg --id presenter
python3 -m istream identity show
```

`identity set` 会复制照片，更新本地提示词库、首帧提示词和生成包。个人生成包另存在 `prompts/identity/<id>/GENERATE_PACK.md`。需要锁定服装或外观时用 `--outfit` 和 `--describe` 写明。在视频生成工具中挂同一张参考照，按包内提示生成近景、中景和温和手势母片。只有要切回随仓库分发的默认模板时才运行 `python3 -m istream identity restore`。[生成包](prompts/GENERATE_PACK.md) · [真人感与选片](docs/HUMAN_PREMIUM.md) · [手势与表情](docs/GESTURE_EXPRESSION.md)

## 2. 切片与入库质检

按自然停顿、姿势回位和镜头变化定出入点。逐段检查人物一致性、嘴部可见性、表情、手势及可放字幕或图文的区域。手遮嘴、画面中有第二张脸或烧录叠化的片段应剔除或标出可用区间。

命令行用 `istream slice` 输出切片草稿和联系表，人工复核后用 `istream catalog merge-review` 合并。规格目录中的 `spec` 仅表示预计动作；实测切点和经过复核的标签才可作为实际选片依据。[标签说明](schema/TAGS.md) · [复核样例](catalog/standin/review.json)

## 3. 用最终配音锁定时间轴

给定整篇录音时核对逐字稿和句间停顿；需要读新稿时使用选定的系统音色或个人音色。听完整篇配音再定镜头、字幕和切点。CLI 规划可传逐句 `--align`；按字数估时的方案只用于预览节奏。[逐句时点样例](recipes/demo60/align.json)

## 4. 选镜与剪辑

### 4.1 稿件标记

CLI 稿件一行一段台词。可写 `[提问]`、`[强调]` 指定意图，`[B-roll: 描述]` 插画面，`[MG: id]` 选动态图文，`[重音: 词]` 指定强调时点。选镜优先保证镜头能连续覆盖台词，同时检查手势与语义、人物和图文位置。用 `istream plan` 产出时间轴；改片时用 `istream edit --ops-file` 另存版本，再用 `istream qc --strict` 检查。[完整可运行示例](DEMO.md)

## 5. 生成口型并合成

先完成裁时、变速和循环等时序调整。仅对可见且正在说话的人物片段推理，停顿时接续同一镜头的动作。纯图文或全屏配图沿用主音轨。最后处理画幅、分屏、小窗、字幕和叠图。检查横竖版时分别观看实际取景。

工作台可直接用本机 MuseTalk 推理。使用 CLI 对接引擎时，用 `istream lipsync plan` 生成任务，用 `render --stage inputs` 准备素材，真实引擎输出与各段帧数相符后再执行 `render --stage composite`。`passthrough` 预览保留原始嘴型。音画偏移、句尾闭唇、双层唇线和停顿衔接按 [portrait-lipsync](skills/portrait-lipsync/SKILL.md) 校准并复核。

## 6. 交付

带声完整播放最终 MP4，在句尾、切镜、字幕出现和补充画面进出时检查同步、遮挡及接缝。记录发现问题的具体时点。交付成片和对应时间轴，区分实际观看结果与自动质检提示。持续出片时用 `istream ledger record` 记录已用镜头；需评估 CLI 方案成本时用 `istream cost` 并附所用假设。

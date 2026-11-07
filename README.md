<p align="center">
  <img src="assets/cover-21x9.png" alt="岚叔无限流数字人口播：一套数字人，无限出片" width="100%">
</p>

<h1 align="center">lanshu-infinite-stream-koubo</h1>

<p align="center">
  <strong>岚叔 · 无限流数字人口播</strong><br>
  母片先做好，切片反复用。换文案、换镜头、换风格，持续出片。
</p>

<p align="center">
  <a href="https://github.com/cclank/lanshu-infinite-stream-koubo/actions/workflows/test.yml"><img src="https://github.com/cclank/lanshu-infinite-stream-koubo/actions/workflows/test.yml/badge.svg" alt="Tests"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-22C55E?style=flat-square" alt="MIT License"></a>
  <a href="SKILL.md"><img src="https://img.shields.io/badge/Agent-Skill-111827?style=flat-square" alt="Agent Skill"></a>
  <a href="#快速开始"><img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.10+"></a>
  <a href="#快速开始"><img src="https://img.shields.io/badge/FFmpeg-7%2B-007808?style=flat-square&logo=ffmpeg&logoColor=white" alt="FFmpeg 7+"></a>
  <a href="#核心流程"><img src="https://img.shields.io/badge/Timeline-Audio_Locked-0F766E?style=flat-square" alt="Audio-locked timeline"></a>
</p>
<p align="center">
  <a href="#怎么省成本"><img src="https://img.shields.io/badge/Footage-Reusable-0D9488?style=flat-square" alt="Reusable footage"></a>
  <a href="#核心流程"><img src="https://img.shields.io/badge/Lip--sync-Visible_Only-7C3AED?style=flat-square" alt="Lip-sync visible segments only"></a>
  <a href="SKILL.md"><img src="https://img.shields.io/badge/Output-16%3A9_%7C_9%3A16-0284C7?style=flat-square" alt="16:9 and 9:16"></a>
  <a href="SKILL.md"><img src="https://img.shields.io/badge/Quality-QC_Workflow-475569?style=flat-square" alt="Quality-control workflow"></a>
</p>
<p align="center">
  <a href="https://x.com/LufzzLiz"><img src="https://img.shields.io/badge/X-%E5%B2%9A%E5%8F%94_%40LufzzLiz-111111?style=for-the-badge&logo=x&logoColor=white" alt="在 X 上关注岚叔 @LufzzLiz"></a>
</p>

## 无限流怎么玩

先生成或拍摄一套人物、服装、光线一致的**母片**，切成带动作、表情、景别标签的镜头库。每次写新稿，就按内容选镜头、配音、处理口型，再用不同版式和动效组合成片。

适合课程、知识讲解、产品介绍等口播内容。素材库可以持续补新，镜头按使用情况轮换。

![同一套人物切片和音轨，组合成六种剪辑风格](assets/showcase.gif)

同一套人物切片和音轨，组合成六种剪辑风格。上图为现有成片节选。

## 本地口播工作台

在本机已配置的工程目录运行以下命令，然后打开 [帧间工作台](http://127.0.0.1:8765/)。

```bash
.venv/bin/python -m studio
```

在「准备母片」导入同一人物的照片或视频，在「切片打标」复核画面、调整入出点和标签。输入文案可用 macOS 普通话声音逐句合成，也可导入配音后手动校对句段。每句话都可选镜和版式，包括人物全屏、分屏、圆形小窗、动态图文、外部补充画面。生成时只对出镜句段运行本机 MuseTalk。导出记录提供播放器、MP4、时间轴和切片使用次数。

当前本机推理路径面向 Apple Silicon Mac，依赖支持 Metal 的 MLX、FFmpeg（含 libass）、FFprobe 和中文字体。首次配置新机器时使用工程虚拟环境执行以下命令。模型缓存约 2 GB，仅安装时需要下载；素材和导出保存在本机。

```bash
.venv/bin/python -m pip install -r studio/requirements.txt
.venv/bin/python -m studio.setup_models
.venv/bin/python -m studio
```

工作台支持单人、单条最多 120 秒、25 fps 的短片，可导出 1280 × 720 或 720 × 1280。单张照片可驱动口型；不同景别、转身和手势来自导入的母片。语义标签需人工复核。系统配音按实际逐句音频定时，上传录音的台词先按字数初排，可在「选镜与口型」调整时间。新工作区可直接上传素材，当前草稿保存在浏览器中，渲染历史、推理缓存和素材库保存在 `build/studio/`。

## 核心流程

| 阶段 | 做什么 |
| --- | --- |
| **① 准备母片** | 用参考图固定人物，准备近景、中景、温和手势等镜头，保持脸和嘴无遮挡。 |
| **② 切片打标** | 按自然停顿和动作切片，标注表情、视线、手势与入出点，筛掉异常片段。 |
| **③ 文案配音** | 校对配音、对齐台词，以声音锁定时间轴，字幕和镜头跟着声音走。 |
| **④ 选镜与口型** | 按句挑切片，只给人物可见且需要说话的片段做口型；时序调整先完成。 |
| **⑤ 多风格剪辑** | 组合全屏、分屏、圆形小窗、补充画面和动态图文，复用切片完成不同包装。 |
| **⑥ 检查导出** | 核查嘴型、接缝、字幕与遮挡，完整播放后导出横版或竖版，并记录素材使用。 |

## 怎么省成本

- **同稿换风格**：共用母片、配音和已对好的口型，继续剪辑、渲染。
- **新稿换内容**：母片继续用，重新配音，并处理新稿需要的口型。
- **按需处理**：人物被全屏图解或补充画面覆盖的时段，跳过口型任务。

“无限流”强调长期复用与重新组合；母片、模型调用及返修仍按实际使用计费。

## 快速开始

将本目录放进 Agent 的技能目录，例如项目下的 `.agents/skills/lanshu-infinite-stream-koubo/`，加载 [`SKILL.md`](SKILL.md)。提供人物参考图或已有切片库、文案和声音要求，即可让 Agent 按流程制作：

```text
使用 lanshu-infinite-stream-koubo。
优先复用我的人物切片，以确认后的配音锁定时间轴。
只对需要出镜说话的片段做口型。
制作一条 16:9 口播，人物主讲、圆形小窗与全屏图解交替。
输出成片、字幕和检查结果。
```

本地命令入口：

```bash
git clone https://github.com/cclank/lanshu-infinite-stream-koubo.git
cd lanshu-infinite-stream-koubo
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python tools/check_environment.py
python -m istream --help
python -m istream prompts build
```

核心规划模块使用 Python 3.10+；切片需要 NumPy。合成推荐 FFmpeg 7+，须包含 `drawtext`、`subtitles`、`libx264` 和中文字体。macOS 可安装完整版：

```bash
brew install ffmpeg-full
export PATH="$(brew --prefix ffmpeg-full)/bin:$PATH"
python tools/check_environment.py --render
```

视频、配音与真实口型服务需自行接入；包内口型适配器以模板为主，`passthrough` 用于预览，不会修改嘴型。以上环境检查和示例渲染均不调用生成模型。

```bash
python tools/build_library.py
python -m istream prompts verify
python -m unittest discover -s tests -v
bash tools/run_demo.sh
```

提示词源文件已随仓库提供。没有原始母片时，示例使用带标识的占位动画验证装配流程；原有预览和联系表可在 [`DEMO.md`](DEMO.md) 查看。要复现替身母片示例，将自己的两条原片放到 `source/original-koubo.mp4`、`source/ai-native-original.mp4`，重新切片并复核标签。

## 搭配不同剪辑风格

可以参考下面这些独立 Skill 的分镜、版式和动效，再接上同一套人物切片与音轨：

- **`talking-head-editor` · Renoise**：口播精剪、字幕花字、画中画。 [安装 Renoise](https://renoise.ai/mcp?utm_source=lufzzliz-aini-202610&utm_medium=xcom)
- **[`lanshu-create-ai-presenter-video`](https://github.com/cclank/lanshu-create-ai-presenter-video) · cclank**：纸艺立体书等讲解风格。
- **[`digital-human-koubo`](https://github.com/andyhuo520/digital-human-koubo) · andyhuo520**：发布解读、粒子文字、文档聚焦。

## 详细文档

| 文档 | 内容 |
| --- | --- |
| [`SKILL.md`](SKILL.md) | 完整流程、命令、剪辑规则与口型处理 |
| [`prompts/GENERATE_PACK.md`](prompts/GENERATE_PACK.md) | 参考图与母片生成提示词 |
| [`schema/TAGS.md`](schema/TAGS.md) | 切片标签与素材契约 |
| [`DEMO.md`](DEMO.md) | 装配、改片与多画幅示例 |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | 架构、接口与适配范围 |

## 许可证

项目代码采用 [MIT License](LICENSE)。第三方依赖、外部服务及人物、图片、音视频素材遵循各自的授权和使用条款。

---

由 **岚叔（Lanshu）** 整理与维护。[在 X 上关注 @LufzzLiz →](https://x.com/LufzzLiz)

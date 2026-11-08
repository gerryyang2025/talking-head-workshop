<h1 align="center">帧间 · 本地口播工作台</h1>

<p align="center">
  <strong>Gerry · 无限流数字人口播</strong><br>
  母片先做好，切片反复用。换文案、换镜头、换风格，持续出片。
</p>

<p align="center">
  <a href="https://github.com/gerryyang2025/lanshu-infinite-stream-koubo/actions/workflows/test.yml"><img src="https://github.com/gerryyang2025/lanshu-infinite-stream-koubo/actions/workflows/test.yml/badge.svg" alt="Tests"></a>
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

## 无限流怎么玩

先生成或拍摄一套人物、服装、光线一致的**母片**，切成带动作、表情、景别标签的镜头库。每次写新稿，就按内容选镜头、配音、处理口型，再用不同版式和动效组合成片。

适合课程、知识讲解、产品介绍等口播内容。素材库可以持续补新，镜头按使用情况轮换。

![同一套人物切片和音轨，组合成六种剪辑风格](assets/showcase.gif)

上图为原项目的剪辑示例，同一套人物切片和音轨组合成六种风格。

## 本地口播工作台

在本机已配置的工程目录运行 `./optools.sh start`，然后打开 [帧间工作台](http://127.0.0.1:8765/)。服务在后台运行，可以关闭终端。

```bash
./optools.sh status    # 显示 PID、网页就绪状态和访问地址
./optools.sh logs      # 查看最近 80 行后台日志
./optools.sh logs -f   # 持续查看日志，按 Ctrl+C 退出查看
./optools.sh restart   # 重启
./optools.sh stop      # 停止
```

脚本也能识别用 `.venv/bin/python -m studio` 手动启动的工作台。手动启动时日志在原终端，脚本启动时日志追加到 `build/studio/service.log`。停止或重启会中断正在生成的视频，请等渲染完成后再操作。需要换端口时可运行 `KOUBO_STUDIO_PORT=8766 ./optools.sh restart`。

照片、视频和配音统一导入「素材库」，支持一次选取多个文件。在「准备母片」打开素材库，选择一份主讲母片，再将需要的照片或视频逐个选为补充素材。素材可以跨项目复用，从项目中移出只会取消引用。

「全屏人物」「分屏讲解」和「圆形小窗」使用主讲母片的切片。在「选镜与口型」把一句设为「补充画面」或「动态图文」，即可为它选择项目中的素材，指定「配图」或「人物口播」，点击时间线上的镜头可带声预览。只有一份补充素材时自动选用，多份时逐句选择，同一份可重复使用。「动态图文」也支持纯文字卡。「多风格剪辑」负责风格、画幅、取景和字幕，切换风格只改变设为「跟随风格」的句子的版式。

要在一句话中切换多个画面，在「选镜与口型」的剪辑时间线播放或拖动「配音定位」，点击「插入补充画面」，从素材库选择照片或视频，设置起止秒数并保存。镜头按 25 FPS 对齐，可以首尾相接、跨句或重复使用同一素材；结束后接回该位置原有的镜头。点击补充轨上的镜头可移动时间、替换素材或删除。镜头列表中的「预览」可试听切换前后各一秒，「预览剪辑」可播放整条草稿。普通配图保留原配音，选择「人物口播」会为该镜头内的说话时段生成口型。

成片生成后，在「检查导出」带声播放，逐项确认「通过」。选择「有问题」会暂停成片并记下播放位置，填写说明后点「保存问题」。点击已保存的秒数可跳回复查。「导出记录」按成片保存复核进度，新生成的版本单独复核。渲染完成即可下载 MP4。

当前本机推理路径面向 Apple Silicon Mac，依赖支持 Metal 的 MLX、FFmpeg（含 libass）、FFprobe 和中文字体。首次配置新机器时使用工程虚拟环境执行以下命令。模型缓存约 2 GB，仅安装时需要下载；素材和导出保存在本机。

```bash
.venv/bin/python -m pip install -r studio/requirements.txt
.venv/bin/python -m studio.setup_models
./optools.sh start
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
git clone https://github.com/gerryyang2025/lanshu-infinite-stream-koubo.git
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

本项目的制作流程源自[岚叔的开源工程](https://github.com/cclank/lanshu-infinite-stream-koubo)。

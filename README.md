# 口播工坊 · Talking Head Workshop

**Gerry · 无限流数字人口播**。准备一张单人照片或一段人物视频，写下台词，在本机完成配音、口型、剪辑和 MP4 导出。下一篇稿子可以继续使用同一套人物素材。

![口播工坊首页：同一主题的横版与竖版口播画面](docs/talking-head-workshop.webp)

[打开本机首页](http://127.0.0.1:8765/) · [直接进入工作台](http://127.0.0.1:8765/studio) · [第一次出片](#核心流程) · [首次安装](#首次安装) · [命令行与 Agent Skill](#命令行与-agent-skill)

## 快速开始

第一次在本机启动，运行 `./optools.sh init` 安装工作台依赖和全部本地模型。[首次安装](#首次安装)

**已经配置过这台 Mac**：在工程目录运行 `./optools.sh start`，打开[首页](http://127.0.0.1:8765/)了解功能，或收藏[制作工作台](http://127.0.0.1:8765/studio)继续编辑。两个地址都由本机服务提供。服务启动后可以关闭终端。

素材库、导出记录和六个制作步骤各有独立地址。可以收藏常用页面，也可以用浏览器前进、后退切换。打开书签时会使用本浏览器的当前项目。[素材库](http://127.0.0.1:8765/studio/library) · [导出记录](http://127.0.0.1:8765/studio/exports) · [文案配音](http://127.0.0.1:8765/studio/steps/voice)

**第一次试做**：在工作台点「新建项目」，从「素材库」导入一张嘴部无遮挡的单人照片，在「准备母片」将它选为主讲。初次可以直接用一篇短测试文案和一个系统音色；确认整篇配音能播放后，再点「生成口播」。想使用自己的录音或音色，见下方配音说明。

## 核心流程

| 在工作台打开 | 怎么用 |
| --- | --- |
| ① 准备母片 | 指定一份主讲照片或视频；可以从同一个素材库选择多份补充照片或视频。素材可跨项目复用，从项目移出只会取消引用。 |
| ② 切片打标 | 查看建议切片，调整视频出入点，核对表情、视线和手势标签，剔除遮嘴或异常片段。 |
| ③ 文案配音 | 选择短稿、长稿或输入自己的台词。选音色准备整篇配音；「短句试听音色」只比较声音。整篇音频就绪后，时间线才显示镜头、配音波形和字幕。 |
| ④ 选镜与口型 | 逐句选切片、版式和出镜人物。可以在配音的指定秒数插入多个补充画面，也可按帧微调口型并预览剪辑。 |
| ⑤ 多风格剪辑 | 组合全屏人物、分屏讲解、圆形小窗、动态图文或补充画面；选择画幅、全屏取景和底部字幕。切换风格只影响「跟随风格」的句段。 |
| ⑥ 检查导出 | 点「生成口播」，完成后带声检查闭唇、接缝、字幕与遮挡。「有问题」可记录时间和说明，点时间即可跳回复查。从这里下载 MP4、时间轴 JSON，或在「导出记录」回看不同版本。 |

[![实际制作工作台：主讲监看、剪辑时间线与横竖版设置](studio/static/showcase/workbench.webp)](studio/static/showcase/workbench.webp)

上图是用仓库公开素材建立的演示项目，点击可看大图。首页的横竖版对照取自同一主题的[横版样片](recipes/demo60/out/demo60_preview_169.mp4)和[竖版样片](recipes/demo60/out/916/demo60_preview_916.mp4)。全新工作区可以从自己的素材开始。

### 配音：读新稿，还是用现成的录音？

| 已有资源 | 选择方式 | 时间线依据 |
| --- | --- | --- |
| 只有文案 | 在「文案配音」选 macOS 已安装的系统音色；可用短句试听比较。 | 根据每句实际合成的音频定时。 |
| 自己的音色样本 | 在「素材库 → 添加个人音色」保存参考录音和逐字稿。之后直接在「文案配音」选这个音色读新稿。 | 模型在本机逐句合成，根据新配音的实际时长定时。 |
| 录好了这篇台词 | 导入整篇音频，在素材库点「用作配音」，并填写对应台词。 | 按录音时长和台词字数初排，可在「选镜与口型」校正句段边界。 |

个人音色建议使用 10～20 秒清晰的单人录音（WAV、M4A、MP3、AIFF 或 AAC）。逐字稿填写**参考录音里实际说的话**，可以从 UTF-8 TXT 导入。在「核对参考录音与逐字稿」可回听、更正后重新生成。

### 主讲与补充素材

主讲母片用于全屏、分屏和圆形小窗。要插播照片或视频，在「选镜与口型」拖动「配音定位」，点「插入补充画面」，选素材、设起止时间。可以连续插入、跨句或重复用同一素材；结束后接回原镜头。「配图」保留原配音，不改嘴；「人物口播」只给该镜头中需要说话的时段做口型。「动态图文」可以将台词与配图排在一起，也支持纯文字卡。

检查句尾时先把「口型微调（帧）」留在 0：嘴先于声音试 +1，声音先到试 −1，每帧 40 毫秒。视频母片优先选能覆盖整句的连续切片，避免在句尾突然换头部姿势。详细校准、停顿闭唇和验证步骤见 [portrait-lipsync](skills/portrait-lipsync/SKILL.md)。

## 本地口播工作台

### 首次安装

在 **Apple Silicon Mac** 上装好 Homebrew，然后在工程根目录运行以下命令。首次初始化需要联网。

```bash
./optools.sh init
./optools.sh start
```

`init` 为工作台和个人音色各建一套 Python 3.12 环境，安装第三方库，配置 FFmpeg、FFprobe 并检查中文字体。它会下载并校验约 3.7 GB 的模型，包括 MuseTalk、Whisper 音频编码器、YuNet、2DFAN4 和 Qwen3-TTS。重复执行会复用已校验的模型，补齐缺失或损坏的文件。

启动后，在「本地模型与引擎」查看就绪状态，在「文案配音 → 配音来源」选择系统音色或已保存的个人音色。首次添加自己的音色，请到「素材库 → 添加个人音色」保存参考录音和逐字稿。[打开文案配音](http://127.0.0.1:8765/studio/steps/voice)

仅需浏览网页或管理素材时，可用 `./optools.sh init --web-only` 跳过模型安装。之后运行 `./optools.sh init` 即可补齐。

### 服务、数据与输出

```bash
./optools.sh status    # 查看网页是否就绪和访问地址
./optools.sh logs -f   # 跟踪日志；不加 -f 则显示最近 80 行
./optools.sh restart   # 重启；请等当前渲染完成
./optools.sh stop      # 停止服务
```

默认监听本机 `127.0.0.1:8765`。可用 `KOUBO_STUDIO_PORT=8766 ./optools.sh restart` 换端口；浏览器草稿按来源保存，继续原草稿时请用原浏览器和端口。

| 内容 | 默认位置或限制 |
| --- | --- |
| 项目草稿 | 当前浏览器的本地存储；清除站点数据会清除草稿。 |
| 上传素材、音色参考、配音 | `build/studio/assets/`、`build/studio/voices/`；索引在 `build/studio/studio.sqlite3`。 |
| 成片与缓存 | `build/studio/jobs/` 存放成片及时间轴；`build/studio/synced/` 复用已推理片段。后台日志为 `build/studio/service.log`。 |
| 素材与文案 | 单段视频不超过 120 秒；每篇文案最多 1500 字、60 个句段，整篇配音最长 10 分钟。单张照片能驱动口型；手势与转头需要视频母片。 |
| 网页导出 | 25 fps 的 MP4；横版 1280 × 720，竖版 720 × 1280。 |

## 怎么省成本

模型和依赖首次安装需要联网。安装完成后，网页的配音、口型和导出在本机执行，无需云端 API Key，也不产生云端 token 费用；仍会占用机器的计算时间、磁盘与电力。同一套母片可以反复用；同稿换版式可以复用符合条件的口型缓存。全屏配图、纯文字卡等没有人物说话的时段会跳过口型推理。

## 命令行与 Agent Skill

将本目录放进 Agent 的技能目录，例如项目下的 `.agents/skills/talking-head-workshop/`，加载 [`SKILL.md`](SKILL.md)。提供人物参考图或已有切片库、文案和声音要求，即可让 Agent 按流程制作：

```text
使用 talking-head-workshop。
优先复用我的人物切片，以确认后的配音锁定时间轴。
只对需要出镜说话的片段做口型。
制作一条 16:9 口播，人物主讲、圆形小窗与全屏图解交替。
输出成片、字幕和检查结果。
```

下面是独立的 `istream` 命令行工具，用于规划、切片、出提示词和装配示例：

```bash
git clone https://github.com/gerryyang2025/talking-head-workshop.git
cd talking-head-workshop
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

命令行示例的 `passthrough` 是装配预览，不修改嘴型；该适配器与上文网页工作台内置的 MuseTalk 推理是两条路径。以上环境检查和示例渲染均不调用生成模型。

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

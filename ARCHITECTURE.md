# 架构与维护入口

## 运行依赖

在仓库根目录运行 `./optools.sh init`，即可安装两个 Python 环境、配置媒体工具，并下载和校验全部模型。首次安装需要联网。原有依赖于 2026-11-09 在 macOS 15.5（arm64）上从空目录初始化。SoulX 和 LatentSync 于 2026-11-10 在同一台 Mac 上完成安装验证。再次安装时，pip 会按项目约束解析版本。[安装流程](tools/studio_setup.py)

### 系统工具

| 依赖 | 用途与本机版本 | 获取方式 |
| --- | --- | --- |
| Apple Silicon、macOS、Metal | 本地模型推理。本机为 macOS 15.5、arm64 | 使用 Apple Silicon Mac 的原生终端，Metal 随 macOS 提供。可用 `uname -m` 确认输出为 `arm64`。 |
| Homebrew | 缺少系统工具时用于补装。本机为 7.0.12 | 首次使用可从官网下载 macOS 的 `.pkg` 安装器，安装后用 `brew --version` 确认。[Homebrew 官网](https://brew.sh/) |
| Python 3.12 | 工作台和个人音色各用一个虚拟环境，本机均为 3.12.13 | `init` 复用已有的 Python 3.12 环境。新机缺少 Python 3.12 时会通过 Homebrew 安装；也可手动执行 `brew install python@3.12`。 |
| FFmpeg、FFprobe | 转码、探测和导出，本机均为 9.0.2 | `init` 检查已有安装是否支持 `drawtext`、`subtitles` 和 `libx264`，需要时通过 Homebrew 安装。手动执行 `brew install ffmpeg-full` 即可取得两个工具。 |
| audio.cpp 0.9.4 | SoulX-FlashHead 和 LatentSync 共用的原生 Metal 推理程序 | `init` 下载固定的 [macOS arm64 Metal 发行包](https://github.com/0xShug0/audio.cpp/releases/tag/v0.9.4)，校验归档和程序的 SHA-256，安装到 `build/models/native-lipsync/audio.cpp-0.9.4/audiocpp_cli`。 |
| 中文字体 | 渲染字幕和图文，本机使用 STHeiti Medium | 优先使用系统已有的中文字体。也可在 macOS「字体册」下载安装中文字体，将 `ISTREAM_FONT` 设为字体文件的绝对路径。 |
| macOS 系统语音 | 系统音色朗读，使用 `/usr/bin/say` | `say` 随 macOS 提供。更多音色可在「系统设置」中的朗读设置里下载，用 `say -v '?'` 列出可用音色。[Apple 声音下载说明](https://support.apple.com/zh-cn/guide/mac-help/mchlp2290/mac) |

### 本地模型

首次安装由 `init` 从 Hugging Face 下载 21 个模型文件（约 8.30 GiB），保存在 `build/models/`。已经建好工作台环境时，可以在仓库根目录用以下命令单独补齐或校验模型。

```sh
.venv/bin/python -m studio.setup_models
```

下载中断后重跑同一命令即可。脚本根据 SHA-256 跳过已校验的文件，重新下载缺失或校验失败的文件。中断的单个文件会从头下载，校验通过后才移入目标路径。[逐文件下载地址与 SHA-256 清单](studio/setup_models.py)

| 模型 | 用途 | 下载来源 | 保存位置（相对于 `build/models/`） |
| --- | --- | --- | --- |
| MuseTalk 1.5 FP16 | 根据配音生成嘴型 | [模型目录 · ad54104a](https://huggingface.co/mlx-community/MuseTalk-1.5-fp16/tree/ad54104a0129121fe2ea67471250c0656c985284) | `musetalk-1.5-fp16/` 下的 `config.json`、`unet.safetensors`、`vae.safetensors` |
| EDTalk 256 | 音频驱动嘴部，ONNX Runtime 在 CPU 推理 | [FaceFusion 转换权重 · 6271ab1c](https://huggingface.co/facefusion/models-3.3.0/blob/6271ab1c4619ceb2e534d65e0ec973f22a9aec38/edtalk_256.onnx) · [EDTalk 原项目](https://github.com/tanshuai0219/EDTalk) | `facefusion/edtalk_256.onnx` |
| SoulX-FlashHead Lite Q8 | 用人物照片和配音生成整帧动态肖像 | [原项目](https://github.com/Soul-AILab/SoulX-FlashHead) · [GGUF 下载](https://huggingface.co/audio-cpp/SoulX-FlashHead-GGUF/resolve/cc83157045008de647a4ba11ca5ed19e66caa575/SoulX-FlashHead-Lite-Q8_0.gguf) | `native-lipsync/SoulX-FlashHead-Lite-Q8_0.gguf` |
| LatentSync 1.6 Q8/F16 | 按音频同步视频人物口型，使用原视频姿态 | [原项目](https://github.com/bytedance/LatentSync) · [GGUF 下载](https://huggingface.co/audio-cpp/LatentSync-1.6-GGUF/resolve/937b95aa98518dff8728541a8a38b94985d90dd1/latentsync-1.6-q8_0-f16.gguf) | `native-lipsync/latentsync-1.6-q8_0-f16.gguf` |
| Whisper 音频编码器 | 为 MuseTalk 提取语音特征 | [下载编码器](https://huggingface.co/mlx-community/MuseTalk-1.5-fp16/resolve/ad54104a0129121fe2ea67471250c0656c985284/whisper_encoder.safetensors) | `musetalk-1.5-fp16/whisper_encoder.safetensors` |
| YuNet 2023mar | 检测人脸 | [下载 OpenCV 权重](https://huggingface.co/opencv/face_detection_yunet/resolve/main/face_detection_yunet_2023mar.onnx) | `studio/yunet.onnx`（按此文件名保存） |
| 2DFAN4 | 定位人脸与唇部关键点 | [下载 FaceFusion 权重](https://huggingface.co/facefusion/models-3.0.0/resolve/main/2dfan4.onnx) | `studio/2dfan4.onnx` |
| Qwen3-TTS 12Hz 0.6B Base 4-bit | 按参考录音和逐字稿合成个人音色 | [模型目录 · 0d6bb6fe](https://huggingface.co/mlx-community/Qwen3-TTS-12Hz-0.6B-Base-4bit/tree/0d6bb6fe33f92d47a507e23b9148940e8366ab5b) | `qwen3-tts-0.6b-base-4bit/`，保留根目录的 8 个模型与配置文件和 `speech_tokenizer/` 下的 4 个文件 |

本机 M1 Pro（32 GB）使用同一段真人视频和 1.92 秒配音，首次导出 48 帧竖版样片，SoulX Lite 用时约 1 分 08 秒，LatentSync 1.6 约 13 分 53 秒。句段缓存命中后可直接复用。

两个 GGUF 包分别包含所需的音频编码器、生成模型及视觉组件。LatentSync 包含 InsightFace 的预训练人脸模型，其条款限非商业研究使用。SoulX Lite 的 LTX VAE 另适用 OpenRAIL-M。[LatentSync 转换包说明](https://huggingface.co/audio-cpp/LatentSync-1.6-GGUF) · [SoulX 权重授权](https://huggingface.co/Soul-AILab/SoulX-FlashHead-1_3B)

<details>
<summary>手动下载 Qwen3-TTS 时需要的 12 个文件</summary>

- 模型根目录放置 `config.json`、`generation_config.json`、`merges.txt`、`model.safetensors`、`model.safetensors.index.json`、`preprocessor_config.json`、`tokenizer_config.json`、`vocab.json`。
- `speech_tokenizer/` 子目录放置 `config.json`、`configuration.json`、`model.safetensors`、`preprocessor_config.json`。

</details>

手动下载时，按表中的文件名和目录放置文件。也可从另一台已初始化的机器复制整个 `build/models/`，再运行上面的命令校验。工作台侧栏的「本地模型与引擎」可查看就绪状态。

### Python 第三方库

`init` 会用各虚拟环境自己的 pip 安装下列直接依赖。普通包及其间接依赖从 pip 配置的包索引下载（默认为 PyPI）。口型引擎使用仓库指定的 GitHub 源码提交。pip 随虚拟环境初始化，缺失时由 Python 的 `ensurepip` 补齐。

| 环境 | 直接依赖 | 项目安装约束 | 本机版本 | 下载来源 |
| --- | --- | --- | --- | --- |
| 工作台 | Flask | `>=3.1,<4` | 3.1.3 | [PyPI · Flask](https://pypi.org/project/Flask/) |
| 工作台、独立 CLI 切片 | NumPy | `>=1.23` | 2.5.4（工作台） | [PyPI · numpy](https://pypi.org/project/numpy/) |
| 工作台 | ONNX Runtime | `onnxruntime>=1.20` | 1.31.1 | [PyPI · onnxruntime](https://pypi.org/project/onnxruntime/) |
| 工作台 | OpenCV | `opencv-python>=4.10` | 5.0.0.93 | [PyPI · opencv-python](https://pypi.org/project/opencv-python/) |
| 工作台 | SciPy（EDTalk 音频特征） | `>=1.10,<2` | 1.18.1 | [PyPI · SciPy](https://pypi.org/project/scipy/) |
| 工作台 | MuseTalk MLX | `musetalk-mlx` 固定提交（macOS arm64） | 0.1.0 | [GitHub 源码归档 · c6eb30ebd1ed](https://codeload.github.com/xocialize/musetalk-mlx/tar.gz/c6eb30ebd1ed4d043983209813370153de9346bf) |
| 个人音色 | MLX-Audio | `mlx-audio==0.6.4` | 0.6.4 | [PyPI · mlx-audio](https://pypi.org/project/mlx-audio/) |
| 个人音色 | Transformers | `transformers==5.22.2` | 5.22.2 | [PyPI · transformers](https://pypi.org/project/transformers/) |

已有虚拟环境时，修复某个环境的 Python 包可选用对应的命令。工作台清单同时包含网页、媒体处理和口型引擎。

```sh
# 工作台
.venv/bin/python -m pip install -r studio/requirements.txt

# 个人音色
build/voice-env/bin/python -m pip install -r studio/voice-requirements.txt
```

只用独立 CLI 切片时，可在自己的虚拟环境执行 `python -m pip install -r requirements.txt`。CLI 规划与提示词拼装使用标准库。[CLI 依赖](requirements.txt) · [网页与媒体依赖](studio/web-requirements.txt) · [口型依赖](studio/requirements.txt) · [个人音色依赖](studio/voice-requirements.txt)

<details>
<summary>展开全新安装包清单（工作台 52 项，个人音色 39 项，含间接依赖和 pip）</summary>

| Python 包 | 工作台 `.venv` | 个人音色 `build/voice-env` |
| --- | --- | --- |
| `annotated-doc` | — | 0.0.5 |
| `anyio` | 4.16.0 | 4.16.0 |
| `blinker` | 1.9.0 | — |
| `certifi` | 2026.10.23 | — |
| `cffi` | 2.1.1 | 2.1.1 |
| `charset-normalizer` | 3.5.2 | — |
| `click` | 8.5.1 | 8.5.1 |
| `cloudpickle` | 3.1.2 | — |
| `decorator` | 5.3.1 | — |
| `filelock` | 4.2.9 | 4.2.9 |
| `Flask` | 3.1.3 | — |
| `flatbuffers` | 25.12.19 | — |
| `fsspec` | 2026.9.0 | 2026.9.0 |
| `h11` | 0.16.0 | 0.16.0 |
| `hf-xet` | 1.8.0 | 1.8.0 |
| `httpcore2` | 2.16.0 | 2.16.0 |
| `httpx2` | 2.16.0 | 2.16.0 |
| `huggingface_hub` | 2.4.0 | 2.4.0 |
| `idna` | 3.20 | 3.20 |
| `itsdangerous` | 2.2.0 | — |
| `Jinja2` | 3.1.6 | 3.1.6 |
| `joblib` | 1.6.0 | — |
| `lazy-loader` | 0.6 | — |
| `librosa` | 1.0.0 | — |
| `llvmlite` | 0.50.0 | — |
| `markdown-it-py` | — | 4.2.0 |
| `MarkupSafe` | 3.0.4 | 3.0.4 |
| `mdurl` | — | 0.1.2 |
| `miniaudio` | — | 1.72 |
| `mlx` | 0.32.4 | 0.32.4 |
| `mlx-audio` | — | 0.6.4 |
| `mlx-metal` | 0.32.4 | 0.32.4 |
| `msgpack` | 1.2.4 | — |
| `musetalk-mlx` | 0.1.0 | — |
| `narwhals` | 2.28.0 | — |
| `numba` | 0.68.1 | — |
| `numpy` | 2.5.4 | 2.5.4 |
| `onnxruntime` | 1.31.1 | — |
| `opencv-python` | 5.0.0.93 | — |
| `packaging` | 26.3 | 26.3 |
| `pip` | 26.0 | 26.0 |
| `platformdirs` | 4.14.5 | — |
| `pooch` | 1.9.0 | — |
| `protobuf` | 7.36.2 | — |
| `pycparser` | 3.12 | 3.12 |
| `Pygments` | — | 2.21.0 |
| `PyYAML` | 6.0.3 | 6.0.3 |
| `regex` | — | 2026.11.9 |
| `requests` | 2.34.2 | — |
| `rich` | — | 15.0.0 |
| `safetensors` | — | 0.8.0 |
| `scikit-learn` | 1.9.1 | — |
| `scipy` | 1.18.1 | 1.18.1 |
| `sentencepiece` | — | 0.2.3 |
| `shellingham` | — | 1.5.4 |
| `sounddevice` | — | 0.5.6 |
| `soundfile` | 0.14.0 | — |
| `soxr` | 1.1.0 | — |
| `threadpoolctl` | 3.8.0 | — |
| `tokenizers` | — | 0.23.3 |
| `tqdm` | 4.70.1 | 4.70.1 |
| `transformers` | — | 5.22.2 |
| `truststore` | 0.10.5 | 0.10.5 |
| `typer` | — | 0.28.0 |
| `typing_extensions` | 4.16.0 | 4.16.0 |
| `urllib3` | 2.8.0 | — |
| `Werkzeug` | 3.1.9 | — |

</details>

在仓库根目录用下列命令查看安装或升级后的实际版本，与上面的快照对照。

```sh
.venv/bin/python -m pip list
build/voice-env/bin/python -m pip list
```

## 工作台从文案到成片

网页由 Flask 提供。首页位于 `/`，工作台位于 `/studio`，素材库、导出记录和制作步骤支持子路径直达。浏览器保存当前项目草稿，服务端用 SQLite 索引本机素材、配音、渲染任务和复核结果。[网页入口与 API](studio/__main__.py) · [工作台交互](studio/static/studio.js)

| 修改目标 | 实现入口 |
| --- | --- |
| 服务启停、首次安装、模型就绪状态 | [optools.sh](optools.sh)、[安装流程](tools/studio_setup.py)、[模型清单与校验](studio/setup_models.py) |
| 素材与声音 | [媒体与配音](studio/media.py) 管理上传、系统音色和逐句时点；[个人音色](studio/personal_voice.py) 在独立 Python 环境运行 Qwen3-TTS。 |
| 选镜、补充画面和导出 | [制作流程](studio/production.py) 以确认的配音建立时间轴，只对可见的说话片段运行口型，再合成画幅、字幕和音轨。 |
| 口型与停顿 | [口型引擎](studio/engine.py) 跟踪人脸，MuseTalk 使用 Whisper 特征，[EDTalk](studio/edtalk.py) 使用与转换权重匹配的 80 带梅尔频谱，按预测唇形重映射母片唇纹和可见牙纹。闭唇母片遇到张口音时，会用同一配音额外推理放大的取景，仅补充露齿区域的亮度细节。[SoulX 和 LatentSync 适配器](studio/native_lipsync.py) 截取当前可见段的配音，按时间线接收 25 FPS 画面。四个模型独立缓存推理结果。[停顿闭唇](studio/mouth_rest.py) 和[镜头衔接](studio/mouth_transition.py) 处理收口及头姿连续性。 |

## 命令行装配

`python -m istream` 可独立读取标记脚本、素材目录和逐句时间戳，生成时间轴 JSON。[规划器](istream/planner.py) 选镜，[质检](istream/qc.py) 检查重复镜头、人物遮挡等问题，[口型任务](istream/lipsync.py) 按可见时段分配工作，[渲染器](istream/render.py) 装配输出。CLI 的 `passthrough` 用于预览剪辑；要生成真实嘴型可在工作台选择口型模型，或给 CLI 提供真实引擎处理过的片段。[可复跑的示例](DEMO.md)

## 提示词、标签和示例的维护位置

| 内容 | 维护源与生成方式（从仓库根目录执行） |
| --- | --- |
| 默认母片提示词库 | K01–K03 定稿在 [plates-source.md](prompts/plates-source.md)。`python tools/build_library.py` 构建默认 `library.json`，`python -m istream prompts build` 导出 Markdown 和纯文本，`python -m istream prompts verify` 校验定稿。重建默认库请使用干净检出，以免覆盖本地定制形象。 |
| 人物生成包 | `istream identity set` 根据参考照、当前身份与叠加配置生成 [GENERATE_PACK.md](prompts/GENERATE_PACK.md)；用户照片流程见 [制作 Skill](SKILL.md)。 |
| 真人感、手势与表情指南 | 提示词和评分项在 [overlays](prompts/overlays/)，说明文字在 [真人感模板](tools/HUMAN_PREMIUM.template.md) 和[手势模板](tools/GESTURE_EXPRESSION.template.md)。改动后分别运行 `python tools/build_human_premium_doc.py` 和 `python tools/build_gesture_expression_doc.py`。 |
| 切片标签 | [词表](istream/vocab.py) 和 [schema 定义](istream/schema.py) 通过 `python -m istream schema --write` 生成 [标签文档](schema/TAGS.md) 和 JSON Schema。 |
| 示例输入和结果 | [recipes](recipes/) 保留可执行的脚本、时间戳、编辑指令和预期输出。历史成本报告按示例参数估算；本地工作台的运行方式见 [README](README.md)。 |

在独立检出中按 CI 顺序运行 `python tools/build_library.py`、`python -m istream prompts verify` 和 `python -m unittest discover -s tests -v`。身份测试会在该副本内切换和恢复模板。涉及导出时，先用 `python tools/check_environment.py --render` 检查 FFmpeg 滤镜和字体。

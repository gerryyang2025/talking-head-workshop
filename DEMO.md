# 命令行示例与样片

这个示例把同一份台词、配音和切片排成横版或竖版，适合检验选镜、图文避让和字幕时点。样片使用 `passthrough` 装配，保留母片原有嘴型。想用自己的照片和配音生成同步口播，请从 [工作台快速开始](README.md#首次安装) 进入。

[横版样片](recipes/demo60/out/demo60_preview_169.mp4) · [竖版样片](recipes/demo60/out/916/demo60_preview_916.mp4) · [修改后的样片](recipes/demo60/edit/demo60_edited_169.mp4)

## 复跑一次规划

从仓库根目录执行。已初始化工作台可先运行 `source .venv/bin/activate`。单独使用规划器需要 Python 3.10+。仓库已包含[脚本](recipes/demo60/script.md)、[逐句时点](recipes/demo60/align.json)和[复核过的切片目录](catalog/standin/plates.json)，以下命令可直接运行。

```sh
mkdir -p build/demo
python3 -m istream plan recipes/demo60/script.md --cat catalog/standin/plates.json \
  --align recipes/demo60/align.json --aspect 16:9 --out build/demo/timeline.json
python3 -m istream qc build/demo/timeline.json --cat catalog/standin/plates.json --strict
python3 -m istream lipsync plan build/demo/timeline.json --cat catalog/standin/plates.json \
  --out build/demo/lipsync_jobs.json
```

打开 `timeline.json` 查看逐句字幕、镜头及图文时点，打开 `lipsync_jobs.json` 查看需要处理的人物片段。把 `--aspect` 改为 `9:16` 并另存时间轴，即可对比竖版规划。

## 看一次改片与复核

[第一次修改](recipes/demo60/edit/01_edit.ops) 引入了图文遮挡和重复镜头，[质检报告](recipes/demo60/edit/01_qc.txt) 列出具体时点。[第二次修改](recipes/demo60/edit/02_fix.ops) 调整选镜和版式后，重新检查[修复结果](recipes/demo60/edit/02_qc.txt)。报告里的 `RISK` 仍需结合成片带声复核。

需要批量重建仓库示例时，在单独的干净检出中运行 `bash tools/run_demo.sh`；脚本会更新示例文件，渲染需要 FFmpeg 和中文字体。重新渲染 demo60 还需要与切片目录匹配的两条原片，放在 `source/original-koubo.mp4` 和 `source/ai-native-original.mp4`。缺少原片时脚本会跳过这部分，仍可用[长稿动态分镜](recipes/longform/out/longform_animatic_916.mp4)检查占位镜头的节奏和版式。

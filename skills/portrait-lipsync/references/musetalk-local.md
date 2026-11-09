# 本机 MuseTalk 推理与复查

在工作台的「本地模型与引擎」确认口型模型和人脸模型就绪。排查已有成片时，从「导出记录」取得同一任务的 MP4 与时间轴，在「选镜与口型」定位有问题的句段。始终用相同的母片和配音做前后对比。

## 定位处理环节

1. YuNet 检查单人脸，2DFAN4 定位关键点。视频逐帧跟踪，照片可复用裁切和编码。遇到脸框错位、双人同框或嘴部太小，先检查实际选中的素材及入出点。[人脸与口型引擎](../../../studio/engine.py)
2. 工作台将配音的推理副本转为 16 kHz 单声道，用 Whisper 编码后按输出帧率取语音特征。MuseTalk 根据人脸和对应音频帧生成嘴型。时序微调从 0 开始，以清晰的起音和收口确定偏移方向。[口型任务与合成](../../../studio/production.py)
3. 如果说话时同步、停下来才跳嘴，比较原始生成帧和最终 MP4 的同一时点。先看停顿权重、唇形过渡与头姿连续性。实际步骤见[句尾闭唇与逐帧复核](pause-closure.md)。

工作台直接执行 MuseTalk 推理。用命令行制作时，确认真实引擎已写回对应片段；CLI 的 `passthrough` 仅供检查装配。

## 复查命令

在装有 FFmpeg 和 FFprobe 的环境中，把 `original`、`revised` 设为两部成片路径。在本项目的虚拟环境中，可先将 `.venv/bin` 加入 `PATH`。

```sh
ffprobe -v error -show_entries stream=codec_name,width,height,avg_frame_rate,nb_frames,start_time,duration:format=duration -of json "$revised"
ffmpeg -v error -xerror -i "$revised" -map 0:v:0 -map 0:a:0 -f null -

for movie in "$original" "$revised"; do
  ffmpeg -v error -i "$movie" -map 0:a:0 -c:a copy -f hash -hash sha256 -
done
```

音频包哈希适用于复用同一编码音轨的修订。重新编码过的音轨应核对解码后的时点与内容。

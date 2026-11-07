# Apple Silicon 本机案例

## 接回项目

在 `lanshu-infinite-stream-koubo` 中，先看 `prompts/identity/<人物ID>/ref.png` 和 `build/<人物ID>/talking-head/`。后者可能已有 `portrait-base.mp4`、`narration.wav`、`captions.srt` 和上一版成片。换人物时重新检测关键点和裁切范围。只修嘴型时从无字幕底板开始，最后叠一次字幕。

项目的 `istream/lipsync.py` 中，`passthrough` 只复制输入，返回 `synced: false`；当前 `musetalk` 适配器提供调用模板。先确认实际执行了推理，再把生成帧合成到画面。如果走项目的分镜流程，按作业清单写回对应片段，再执行合成。

## 本机推理路径

1. 本例在 M1 Pro 上使用 MuseTalk 1.5 的社区 MLX 移植和 FP16 权重。先检查当前 Python 能导入 `mlx.core`、`musetalk_mlx`，再运行一个很小的 Metal 运算确认 GPU 可用。上次运行留下的临时源码目录可能已被系统清理，复用前应验证实际安装。工程的模型缓存目录是 `build/models/musetalk-1.5-fp16/`，内有 `config.json`、`unet.safetensors`、`vae.safetensors` 和 `whisper_encoder.safetensors`。补下载时按选定版本核对权重校验值。[MLX 实现](https://github.com/xocialize/musetalk-mlx) · [本例权重版本](https://huggingface.co/mlx-community/MuseTalk-1.5-fp16/tree/ad54104a0129121fe2ea67471250c0656c985284)
2. 用鼻梁、左右脸缘和下巴定位裁切框，按后端要求将脸缩放为 256 × 256 的 BGR 图像。调用 `MuseTalkPipeline.from_pretrained_mlx` 载入模型，`get_latents_for_unet` 编码参考脸。单张照片产生的轻微头动可共用一份参考脸编码，再逐帧按跟踪变换回贴。真人视频有明显转头时，应为相应姿态重新取脸。
3. 将配音的推理副本转为 16 kHz 单声道，计算 log-mel 后用 `encode_audio` 按帧率取语音特征，并用 `generate_faces` 分批生成脸部帧。本例使用 25 fps；处理较长配音时，按所用语音编码器的窗口分段并核对跨段帧数。把语音特征、生成帧、回贴坐标和所用模型版本留在本次工作目录，方便调校。
4. 原分辨率下跟踪并合成脸部，最后缩放、加字幕并封装音轨。修订已有 MP4 且配音相同，可用 FFmpeg 的 `-map 1:a:0 -c:a copy` 复用第二个输入中的 AAC 音轨。

## 这次是怎样判定改善的

| 检查点 | 原片所见 | 调整及复查 |
| --- | --- | --- |
| 3.72 秒，两句之间 | 已经停声，画面仍有上下两层唇线 | 取消闭嘴照片与生成嘴型的音量混合，改用模型休止姿势。左右对比可见双唇合拢。 |
| 连续说话和露齿 | 开口集中在嘴周，下巴几乎静止 | 按下唇位移带动下巴，仅在唇表面回贴原照纹理。放大后部分露齿帧仍略软。 |
| 整段音画时序 | 同一 SyncNet 测法估计嘴部领先约 2 帧，25 fps 下约 80 毫秒 | 换模型后先单测新生成序列，再校该序列。最终成片的整段估计偏移为 0 帧。换照片、配音、模型或帧率后重新测量。 |

## 复查命令

在装有 FFmpeg 和 FFprobe 的环境中，把 `original`、`revised` 设为两部成片路径。在本项目的虚拟环境中，可先将 `.venv/bin` 加入 `PATH`。

```sh
ffprobe -v error -show_entries stream=codec_name,width,height,avg_frame_rate,nb_frames,start_time,duration:format=duration -of json "$revised"
ffmpeg -v error -xerror -i "$revised" -map 0:v:0 -map 0:a:0 -f null -

for movie in "$original" "$revised"; do
  ffmpeg -v error -i "$movie" -map 0:a:0 -c:a copy -f hash -hash sha256 -
done
```

本例成片为 1080 × 1080、25 fps、250 帧、10 秒，修订前后的 AAC 音频包哈希相同。哈希比较适用于直接复用同一编码音轨的修订；重新编码过的音轨应比较解码后的时点与内容。

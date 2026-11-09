# DEMO · 一份脚本 → 时间轴 → QC → 口型任务 → 成片 → 像改代码一样改

> **v1.1：** 新增 `istream identity set --photo` → `prompts/GENERATE_PACK.md`（用户照片锁定数字人 + 无遮挡元视频提示词一站包）。正确流程是先生成元视频底板再切片；本 DEMO 仍用替身底板演示装配侧，见 `docs/USER_PHOTO.md` / `SKILL.md` §2.0。

> 这里的数字、表格和画面来自实际运行的产物（`recipes/demo60/`、`recipes/longform/`）。运行 `bash tools/run_demo.sh` 可复现提示词、规划、QC 和占位动画；替身母片的重新切片与渲染需要自行提供下面两条原片，并复核标签。原片不随仓库发布。
> **先说清楚两件事：**
> 1. 演示的底板是本项目的两条真实数字人原片（替身底板，720p），不是按本技能提示词生成的生产底板。
> 2. 口型这一步用的是 `passthrough`（不改嘴）。所以预览片里主播的嘴在说原片的台词，和配音对不上，这正是口型引擎要修的地方（见第 5 步）。

---

## 0. 素材

| 底板 | 来源 | 实际情况 |
|---|---|---|
| P01 | `source/original-koubo.mp4`（MCP 口播原片，30 s） | 3 个机位：主播在左 / 主播在右且左侧有玻璃倒影 / 居中近景；15.47–15.83 s 烧录叠化，24.73 s 硬切 |
| P02 | `source/ai-native-original.mp4`（AI Native 口播原片，30 s） | 主播在左；14.53–25.83 s 右半区烧录了乱码图表 |

**配音：** AI Native 原声 0–25.75 s，加 0.30 s 静音，再接 MCP 原声 0–30.02 s，共 **56.07 s**（`recipes/demo60/vo.m4a`）。

**MG：** 直接复用本项目 Glass Protocol 动效包里的 PNG，按句拼成 16 张卡（`recipes/demo60/mg/`），每张卡标了它占用的半区。

---

## 1. 切片打标：机器测得 + 人工复核

```bash
python -m istream slice source/original-koubo.mp4 --id P01 --out catalog/standin/drafts/P01.json --sheet catalog/standin/drafts/P01_sheet.jpg
python -m istream slice source/ai-native-original.mp4 --id P02 --out catalog/standin/drafts/P02.json --sheet catalog/standin/drafts/P02_sheet.jpg
python3 -m istream catalog merge-review --draft catalog/standin/drafts/P01.json catalog/standin/drafts/P02.json --review catalog/standin/review.json --out catalog/standin
```

**P01 测得：**
- 叠化 15.47–15.83 s，硬切 24.73 s，自动分成 3 个机位。
- 8.10–10.53 s 右半区出现“边缘异常”，但那块区域大部分是皮肤 → 判为**手势**（掌心托举 `palm_present`），不是缺陷。
- 第一版切片器把它误判成烧录图形，靠“同一机位内的皮肤基线”修正。

**P02 测得：**
- 14.53–25.83 s 右半区烧录图形（`baked_overlay`，`zone: right_half`）。
- 20 s 附近的手挥动没有被误判成叠化：判叠化要求左右两半同时变化，而且边缘密度对调。

**复核（`review.json`）补上的：** 情绪、手势名、角色，以及 P01 机位 2 的 `second_face: true`（玻璃倒影里有第二张脸）。

**结果：** 12 个镜头、59.3 s 素材。联系表见 `docs/slicer_P01_sheet.jpg`、`docs/slicer_P02_sheet.jpg`。

---

## 2. 写稿

`recipes/demo60/script.md`（节选）：

```markdown
# 第一讲 · AI Native
[开场][钩子][MG: an_hook] 全员都开了AI账号，效率怎么还原地踏步？
[故事][B-roll: 车间按流程重排的俯拍][MG: an_flow] 直到有人给每台机器配上小电机……
[强调][重音: 打字机][MG: an_typewriter] AI也一样，塞进旧流程，它只是台更快的打字机。
# 第二讲 · MCP
[强调][主播][重音: USB-C][MG: mcp_usbc][MG: mcp_palm] MCP就是AI的USB-C。
[列点][MG: mcp_three] 接上之后，Agent能拿到三样东西：……
[关注][MG: mcp_cta] 关注我，明天讲Agent到底怎么用工具。
```

**时间来源：** `align.json` 给出 17 句和关键词的起止时间（从原声测得，误差约 ±0.1 s）。TTS 或 ASR 的逐句时间戳导出就是这个格式。

---

## 3. 规划（脚本驱动装配）

```bash
python3 -m istream plan recipes/demo60/script.md --cat catalog/standin/plates.json --align recipes/demo60/align.json --out recipes/demo60/out/timeline.json
```

```
planned 21 clips, 16 MG, 40 captions · 56.07s · profile short · 16:9
  c01   0.00-  3.37  full   P02_s1      0.05-  3.42  cut
  c02   3.37-  6.12  full   P01_s1      1.05-  3.80  zoomcut
  c03   6.12-  8.87  full   P02_s6     26.98- 29.73  zoomcut
  c04   8.87- 11.70  pip    P01_s5     20.48- 23.31  zoomcut    pip:bl0.3
  c05  11.70- 14.53  pip    P02_s3     11.22- 14.05  zoomcut    pip:bl0.3
  c06  14.53- 19.85  hidden —               —        broll_fade hide:broll:车间按流程重排的俯拍
  c07  19.85- 22.53  full   P01_s3     11.57- 14.25  broll_fade
  c08  22.53- 23.22  punch  P01_s2      5.75-  6.44  zoomcut    scale1.15
  c09  23.22- 26.10  full   P01_s1      1.05-  3.93  zoomcut    scale1.1
  c10  26.10- 28.73  full   P02_s1      0.05-  2.68  zoomcut    scale1.1
  c11  28.73- 30.57  full   P01_s5     20.48- 22.32  zoomcut
  c12  30.57- 32.97  split  P02_s2      5.82-  8.22  zoomcut
  c13  32.97- 34.41  full   P01_s4     18.63- 20.07  zoomcut
  c14  34.41- 36.45  full   P01_s2      6.75-  8.79  zoomcut    scale1.1
  c15  36.45- 40.21  full   P01_s1      0.05-  3.81  zoomcut    scale1.15
  c16  40.21- 41.75  split  P02_s3     11.47- 13.01  zoomcut
  c17  41.75- 44.37  split  P01_s4     15.88- 18.50  zoomcut
  c18  44.37- 46.99  split  P01_s5     20.48- 23.10  zoomcut    scale1.1
  c19  46.99- 50.89  pip    P02_s2      5.82-  9.72  zoomcut    pip:br0.3
  c20  50.89- 53.69  full   P01_s6     27.17- 29.97  zoomcut
  c21  53.69- 56.07  full   P02_s6     26.98- 29.36  zoomcut    scale1.1
planner warning: slot 46.99-50.89: relaxed to PiP (zone supply exhausted) — add plates with that side free
```

**读这张表（每个决定在 `timeline.json` 的 `why` 字段里都有原因）：**

1. **开场 c01：** 第一帧就是主播全画面，从 P02 的起点入。
2. **画中画 c04 / c05：** 覆盖率平衡把“讲解老厂房”这两句改成内容主导（老厂房蓝图卡在右半区）。主播缩成圆窗，放在**左下**，内容的对侧。
3. **B-roll c06：** 主播隐藏，演播室虚化，B-roll 位置打上“待替换”标签，配音照常。这 5.32 s **不送口型**。
4. **推近 c08：** 在“打字机”起点前 2 帧切进 1.15 倍推近。
5. **手势对关键词 c14：** “MCP 就是 AI 的 USB-C”这一槽选中了 P01_s2，掌心托举在成片 35.76 s 抬起，“USB-C”在 35.65 s，相差 **0.11 s**。`mcp_palm` 光柱卡用 `at_keyword` 在 35.60 s 出现，像是她托起来的。这一槽能拿到 P01_s2，是因为“最受约束的槽先选”；从左到右挑的旧版本里，这个镜头早被前面的句子用掉了。
6. **左半区三件套 c17 / c18：** 这几张 MG 卡在左半区，只有 P01 机位 2（主播在右，左边是玻璃倒影）让得出位置。规划器选了它们，MG 正好叠在倒影上。
7. **供给放宽 c19：** 下一句也要左半区，但能让出左半区的新素材用完了。规划器没有硬塞重复镜头，而是改成画中画（主播在右下），并提示“补一条那一侧空着的底板”。
8. **重复：** 56 秒的片子只有 59 秒素材。规划器保证 12 秒内不重复同一时刻，更远的重复全部换了变体（缩放 1.0 / 1.1 / 1.15），QC 逐条提示复核。

渲染联系表：`docs/demo60_169_sheet.jpg`。

---

## 4. QC

```
QC: PASS — 0 FAIL, 3 RISK (must review after lip-sync), 19 WARN
metrics: clips=21, host_shots=17, unique_shots=10, asl_s=2.42, longest_s=3.76, coverage=0.265, visible_talking_s=50.75
  [RISK] rate: @26.16s b07 6.7 字/s — high risk for Chinese lip-sync (b/p/m closures) …
  [RISK] rate: @28.79s b08 7.4 字/s …
  [RISK] rate: @33.03s b10 7.3 字/s …
  [WARN] upscale: P01: 5 clips upscaled up to 1.72× — generate this plate at higher resolution …
  [WARN] repeat: @23.22s c09 reuses P01_s1 as a variant (scale/reverse/PiP) 19.8s after 3.4s — check by eye
  [WARN] jumpcut: @23.22s c08→c09 same plate, same scale: reads as a skip …
  …
```

- **RISK：** MCP 段的真人原声每秒 7 字以上，是真实的口型风险，不是误报。正式出片时让 TTS 放慢 5–10%，或者逐帧复核这三段。
- **upscale：** 720p 替身底板放到 1080p 母版，QC 如实报出。生产底板请按 1080p 以上、目标画幅生成。

---

## 5. 口型任务（以及“接上真引擎”时会发生什么）

```bash
python3 -m istream lipsync plan recipes/demo60/out/timeline.json --cat catalog/standin/plates.json --out recipes/demo60/out/lipsync_jobs.json
```

```
lip-sync: 11 jobs, 50.75s sent, 5.32s skipped (host hidden)
  j01   0.00-  3.37 ( 3.37s) tier=hero     engine=sync-2-pro  face≈276px zh-risk=high (6.13 字/s, b/p/m×2, AI)
  j03   8.87- 14.53 ( 5.66s) tier=small    engine=musetalk    face≈85px  zh-risk=mid  …   ← 画中画小脸走快模型
  j06  34.41- 41.75 ( 7.34s) tier=hero     engine=sync-2-pro  face≈317px zh-risk=mid (3.68 字/s, b/p/m×6, AI/MCP/USB-C)
       · 唇齿音 f ×1：看上齿是否压下唇
       · 夹杂英文 / 缩写（AI、MCP、USB-C）：字母口型和中文不同，单独看一遍
  j08  44.37- 46.99 ( 2.62s) tier=hero     engine=sync-2-pro  face≈312px zh-risk=mid (7.23 字/s, b/p/m×2)
       · 语速 7.2 字/s 偏快：TTS 放慢 5–10% 或拆句
  …（完整清单见 recipes/demo60/out/lipsync.txt）
```

- **每个任务的输入**（`render` 阶段 A 生成）：
  - `build/lipsync/in/NN_video.mp4`：只做了时间裁切的**原分辨率**主播画面，没有字幕、没有 MG、没有推近。
  - `NN_audio.wav`：对应的配音切片。
- **含 P01 机位 2 镜头的任务**（j03、j04、j05、j07、j08）带 `face_lock`（主脸框），防止引擎锁到玻璃倒影上的那张脸。
- **接上真引擎：** 把 `--engine passthrough` 换成真实引擎，或者按 `istream lipsync run` 打印的模板命令手动跑。结果放到 `build/lipsync/out/NN_synced.mp4`，再执行：

  ```bash
  python3 -m istream render … --stage composite
  ```

  合成阶段会读取同步后的画面，再做推近、画中画和 MG。时间轴不用改一行。
- **口型后的复核顺序：**
  1. RISK 段（26.2–34.1 s）逐帧看 b/p/m 闭合；
  2. j06 的 “MCP / USB-C” 字母口型；
  3. 用评分卡打分（可行性报告 §7.1）。

---

## 6. 渲染（两阶段，passthrough 口型）

```bash
python3 -m istream render recipes/demo60/out/timeline.json --cat catalog/standin/plates.json --jobs recipes/demo60/out/lipsync_jobs.json \
        --workdir recipes/demo60/build --out recipes/demo60/out/demo60_preview_169.mp4 --scale 0.6667
```

- **产物：** `recipes/demo60/out/demo60_preview_169.mp4`，1280×720，1682 帧 = 56.07 s，带配音。
- **画面内容：**
  - 推近锚在脸上；
  - 画中画是圆窗加青色描边；
  - B-roll 段是演播室虚化加“待替换”标签；
  - Glass Protocol 卡淡入淡出，都放在主播让出的那一侧；
  - 字幕按宽度断行，不以标点开头，不留孤字。

---

## 7. 同一份脚本，一个参数出竖版

```bash
python3 -m istream plan recipes/demo60/script.md --cat catalog/standin/plates.json --align recipes/demo60/align.json --aspect 9:16 --out recipes/demo60/out/916/timeline.json
```

- **重新取景：** 每个镜头按脸框裁成 9:16，三个机位各自跟脸。
- **复活缺陷镜头：** P02_s4 / P02_s5 在横版里因右半区乱码不可用。竖版裁到人物后乱码被裁掉，规划器自动用上它们（横版 10 个不同镜头，竖版 12 个）。
- **MG：** 动效卡回退为竖版预览卡。
- **放大倍数：** QC 报出 720p 素材裁竖版要放大到 3×。这就是为什么生产底板要按目标画幅生成，或用 4K 横版拍摄。
- **路由：** 竖版的脸大，更多任务进入 hero 档，所以口型成本比横版高（见第 9 步）。

**产物：**
- `recipes/demo60/out/916/demo60_preview_916.mp4`（540×960 预览）
- 联系表 `docs/demo60_916_sheet.jpg`

---

## 8. 像改代码一样改

`recipes/demo60/edit/01_edit.ops`：

```
swap c03 P01_s3
punch c09 1.15
hide c13 card
mg 32.97 34.41 card full 换个平台 = 重写一遍
order c02,c07,c20
mg 26.10 28.70 keyword_pop lower_third 会写代码 ≠ 会用工具
lock c01
```

**QC 立刻拦下 4 个问题（`01_qc.txt`）：**

```
QC: FAIL — 4 FAIL …
  [FAIL] mg_zone: @3.38s MG m02 (an_history) in right_half collides with host in c02 (P01_s6)
  [FAIL] repeat: @23.22s c09 reuses P01_s1 only 3.4s after it was shown
  [FAIL] repeat: @36.45s c15 reuses P01_s1 (same variant) 13.2s after 23.2s
  [FAIL] repeat: @50.89s c20 reuses P01_s3 (same variant) 44.8s after 6.1s
```

**4 行修复（`02_fix.ops`）后：**

```
swap c02 P01_s2 3.05
scale c20 1.1
hide c07 broll:旧流程里塞进AI的办公室
scale c15 1.0
```

```
QC: PASS — 0 FAIL, 3 RISK …
```

**重新渲染：** 只重建改过的片段（首次 41 个片段缓存，改片后新增 11 个）。

**产物：**
- `recipes/demo60/edit/demo60_edited_169.mp4`
- 两次 diff：`01_diff.txt`、`02_diff.txt`
- 联系表 `docs/demo60_edited_sheet.jpg`

**同样的能力，另一种用法：换种子。** `--seed 11` 让 21 个镜头里 5 个不同，`--seed 23` 有 8 个不同，QC 都通过。同一份稿可以出多个版本做 A/B 或多账号分发。

---

## 9. 成本（同一份时间轴，只换路由策略文件）

```bash
python3 -m istream cost recipes/demo60/out/timeline.json --cat catalog/standin/plates.json --jobs recipes/demo60/out/lipsync_jobs.json
```

| 策略 | demo60 横版（56 s） |
|---|---|
| 默认混合（`policies/default_mixed.json`） | $2.02–3.25 |
| 全自部署（`policies/selfhost.json`） | $0.11–0.72 |
| 全 pro（`policies/premium.json`） | $3.61–5.21 |
| 不分段、整片 pro（基线） | $4.11–6.07 |

竖版默认混合是 $3.37–5.06，因为脸变大，更多任务进入 hero 档。价格为 2026-10 公开价，TTS 另计。

---

## 10. 长视频配方：约 4 分钟、9:16、规格目录、占位动态分镜

```bash
python3 -m istream plan recipes/longform/script.md --cat catalog/spec/plates.json --out recipes/longform/out/timeline.json
```

```
planned 50 clips, 25 MG, 140 captions · 231.61s · profile long · 9:16 · VO delayed 1.4s for the opening
  c01   0.00-  4.08  full   O01_s1      2.20-  6.28  cut                        ← 开场专用：从“低头看提纲”中途切入
  c02   4.08-  8.15  full   L01_s4     21.50- 25.57  zoomcut
  c03   8.15- 10.45  punch  K01H_s2     7.50-  9.80  zoomcut    crop9:16@0.315,scale1.12
  c04  10.45- 17.65  pip    K03_s4     21.50- 28.70  zoomcut    pip:bl0.34
  …
  c08  33.05- 35.90  punch  K01_s2      8.00- 10.85  mgwipe     scale1.12     ← 章节“第一步 · 选”：章节卡 + MG 擦除
  …
  c11  46.70- 52.65  hidden —               —        broll_fade hide:broll:报销单据堆成山的桌面
```

- **开场到场：** 目录里有开场专用镜头 → 配音整体延后 1.4 s → 第一镜是 O01_s1。她先抬眼、吸气、笑，再开口。
- **长档节奏：** 平均镜头长 4.28 s，6 张章节卡（开场 / 选 / 拆 / 量 / 三个坑 / 总结），5 处 MG 擦除转场，覆盖率 26%。
- **QC：** PASS，0 FAIL，0 RISK（估算语速 5.0 字/s）。13 个 WARN：12 个远距离变体复用，1 个 K01H 裁竖版放大 1.99×。
- **口型：** 28 个任务，212.4 s 送口型，19.2 s 跳过。
- **成本：**

  | 策略 | 本条 | 每成片分钟 |
  |---|---|---|
  | 默认混合 | $9.27–15.40 | $2.40–3.99 |
  | 全自部署 | $1.32–4.88 | $0.34–1.26 |
  | 全 pro | $15.93–23.65 | — |

- **动态分镜：** 底板还没生成，渲染器用带标签的占位底板（显示底板号、时间码、镜头标签）把整片跑了一遍，可以先看节奏和版式。产物 `recipes/longform/out/longform_animatic_916.mp4`（360×640，无配音），联系表 `docs/longform_animatic_sheet.jpg`。

---

## 11. 复现

```bash
cd /path/to/talking-head-workshop
PY_NUMPY=/path/to/python-with-numpy bash tools/run_demo.sh      # 全部产物 + 22 个测试
python3 -m unittest discover -s tests -v                          # 只跑测试
```

- **依赖：** Python 3.10+、ffmpeg ≥ 7（需要 libass 和 freetype）、Noto Sans CJK 字体；切片需要 numpy（OpenCV 可选）。
- **离线限制：** demo60 依赖项目里的 `source/*.mp4`。只有 zip 包时可以跑规划、QC、口型任务、成本和长视频动态分镜，替身底板的渲染会自动跳过。

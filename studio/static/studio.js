"use strict";
const paths = {
  grid: '<rect x="3" y="3" width="7" height="7" rx="1.3"/><rect x="14" y="3" width="7" height="7" rx="1.3"/><rect x="3" y="14" width="7" height="7" rx="1.3"/><rect x="14" y="14" width="7" height="7" rx="1.3"/>',
  library:
    '<rect x="3" y="7" width="15" height="14" rx="2"/><path d="m6 4 13-1 2 14M6 16l3-4 3 3 2-2 2 3"/>',
  history: '<path d="M3 11a9 9 0 1 1 2 7M3 4v7h7M12 7v5l4 2"/>',
  cpu: '<rect x="6" y="6" width="12" height="12" rx="2"/><rect x="9" y="9" width="6" height="6" rx="1"/><path d="M9 3v3m6-3v3M9 18v3m6-3v3M3 9h3m-3 6h3m12-6h3m-3 6h3"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  clap: '<path d="M3 9h18v11H3zM3 9l-.7-5L20 2l.7 4zM7 4l3 3m3-4 3 3"/>',
  screen:
    '<rect x="2.5" y="4" width="19" height="14" rx="2"/><path d="M8 21h8m-4-3v3"/>',
  tracks:
    '<path d="M3 5h18M3 12h18M3 19h18"/><path d="M7 3v4m8 3v4m-5 3v4" stroke-width="4"/>',
  sliders:
    '<path d="M4 6h7m5 0h4M4 12h2m5 0h9M4 18h12m4 0h1"/><circle cx="13" cy="6" r="2"/><circle cx="8" cy="12" r="2"/><circle cx="18" cy="18" r="2"/>',
  play: '<path fill="currentColor" stroke="none" d="m7 4 13 8-13 8z"/>',
  pause: '<path d="M8 5v14m8-14v14" stroke-width="4"/>',
  focus: '<path d="M3 8V3h5m8 0h5v5m0 8v5h-5m-8 0H3v-5M8 12h8m-4-4v8"/>',
  expand: '<path d="M4 9V4h5m6 0h5v5m0 6v5h-5m-6 0H4v-5"/>',
  voice: '<path d="M3 10v4m4-8v12m5-16v20m5-16v12m4-8v4"/>',
  video:
    '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m10 9 5 3-5 3z"/>',
  captions:
    '<rect x="2" y="5" width="20" height="14" rx="2"/><path d="M5 11h5m2 0h6M5 15h3m3 0h8"/>',
  upload: '<path d="M12 16V3m-5 5 5-5 5 5M3 16v4h18v-4"/>',
  folder: '<path d="M3 6h6l2 2h10v12H3z"/>',
  arrow: '<path d="M4 12h15m-6-6 6 6-6 6"/>',
  landscape: '<rect x="2" y="5" width="20" height="14" rx="2"/>',
  portrait: '<rect x="6" y="2" width="12" height="20" rx="2"/>',
  music:
    '<path d="M9 18V6l11-3v12M9 9l11-3"/><ellipse cx="6" cy="18" rx="3" ry="2"/><ellipse cx="17" cy="15" rx="3" ry="2"/>',
  check: '<path d="m3 12 6 6L21 6"/>',
  download: '<path d="M12 3v12m-5-5 5 5 5-5M3 17v4h18v-4"/>',
};
const icon = (k) =>
  '<svg viewBox="0 0 24 24" aria-hidden="true">' + (paths[k] || "") + "</svg>";
const $ = (q) => document.querySelector(q);
const esc = (v) =>
  String(v ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const opt = (value, label, selected) =>
  '<option value="' +
  esc(value) +
  '" ' +
  (value === selected ? "selected" : "") +
  ">" +
  esc(label) +
  "</option>";
const steps = [
  "准备母片",
  "切片打标",
  "文案配音",
  "选镜与口型",
  "多风格剪辑",
  "检查导出",
];
const layouts = {
  auto: "跟随风格",
  full: "全屏人物",
  split: "分屏讲解",
  pip: "圆形小窗",
  card: "动态图文",
  insert: "补充画面",
};
const styles = {
  studio: "人物主讲",
  editorial: "编辑混剪",
  lecture: "课程讲解",
};
const views = {
  work: ["grid", "制作工作台"],
  library: ["library", "素材库"],
  history: ["history", "导出记录"],
};
const fmt = (t) => {
  t = Math.max(0, Math.floor(Number(t) || 0));
  return (
    String(Math.floor(t / 60)).padStart(2, "0") +
    ":" +
    String(t % 60).padStart(2, "0")
  );
};
const sec = (t) => Number(t || 0).toFixed(2) + " s";
let session,
  draft,
  view = "work",
  step = 2,
  mode = "source",
  activeAsset,
  busy = false,
  pollTimer,
  toastTimer,
  playingJob,
  stillClock = 0,
  stillTimer,
  progressJob;
let shotMap = {},
  resultTimeline = null,
  resultVoice = null;
const mediaURL = (id, type) =>
  "/api/assets/" + encodeURIComponent(id) + "/" + type;
const findAsset = (id) => session.assets.find((a) => a.id === id);
const getJob = (id) => session.jobs.find((j) => j.id === id);
const current = () => getJob(playingJob || draft.job);
function message(s) {
  const n = $("#toast");
  n.textContent = s;
  n.style.display = "block";
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (n.style.display = "none"), 4200);
}
async function api(url, body, form = false) {
  const o =
    body === undefined
      ? {}
      : {
          method: "POST",
          headers: {
            "X-Studio-Request": "1",
            ...(form ? {} : { "Content-Type": "application/json" }),
          },
          body: form ? body : JSON.stringify(body),
        };
  const r = await fetch(url, o);
  const data = await r.json();
  if (!r.ok) throw Error(data.error || "请求失败");
  return data;
}
function defaultVoice(text) {
  if (text === session.demoText && findAsset("demo-audio")) return "demo-audio";
  return session.engine.tts ? "reed" : "";
}
function fresh(title) {
  const host =
    findAsset("demo-plate") || session.assets.find((a) => a.role === "host");
  return {
    id: crypto.randomUUID(),
    title: title || "三步制作数字人口播",
    hosts: host ? [host.id] : [],
    text: session.demoText,
    voice: defaultVoice(session.demoText),
    aspect: "16:9",
    style: "editorial",
    subtitles: true,
    shift: 0,
    insert: "",
    voiceData: null,
    lines: [],
    job: null,
  };
}
function scriptSamples() {
  return {
    三步制作数字人口播: session.demoText,
    自我介绍: "大家好，我是 Gerry。\n我平时写程序，也喜欢拍照。\n今天用一张海边的照片，跟你打个招呼。",
    产品演示: "今天试试帧间的口播工作台。\n选一张照片，写下你想说的话，再点一下试听。\n听到哪里不顺，就改那一句。",
    口型与停顿: "爸爸把白色的杯子摆在旁边。\n慢一点，抿抿嘴。\n好，我们再说一遍。",
    英文短句: "Hi, I'm Gerry.\nI took this photo by the sea.\nCan you hear the waves?",
  };
}
function savedProjects() {
  try {
    return JSON.parse(localStorage.getItem("frame-studio-projects") || "{}");
  } catch {
    return {};
  }
}
function save() {
  try {
    draft.id ||= crypto.randomUUID();
    const projects = savedProjects();
    projects[draft.id] = draft;
    localStorage.setItem("frame-studio-projects", JSON.stringify(projects));
    localStorage.setItem("frame-studio-draft-v1", JSON.stringify(draft));
  } catch (e) {
    message("浏览器未能保存草稿");
  }
}
function discardVoice() {
  draft.voiceData = null;
  draft.lines = [];
  if (mode === "result") {
    mode = "source";
    prepMonitor();
  }
  save();
  drawTracks();
  updateClock();
}
function task(fn) {
  return async (...args) => {
    try {
      await fn(...args);
    } catch (e) {
      message(e.message);
    }
  };
}
function updateJob(j) {
  session.jobs = [j, ...session.jobs.filter((a) => a.id !== j.id)];
}
function nav() {
  $("#views").innerHTML = Object.entries(views)
    .map(
      ([k, [g, n]]) =>
        '<button class="navbtn ' +
        (view === k ? "on" : "") +
        '" data-view="' +
        k +
        '">' +
        icon(g) +
        n +
        "</button>",
    )
    .join("");
  $("#steps").innerHTML = steps
    .map(
      (n, i) =>
        '<button class="navbtn stage ' +
        (view === "work" && step === i ? "on" : "") +
        '" data-step="' +
        i +
        '"><span class="order">0' +
        (i + 1) +
        "</span>" +
        n +
        "</button>",
    )
    .join("");
  $("#crumb").textContent = views[view][1];
  $("#title").textContent = view === "work" ? "口播工作台" : views[view][1];
  $("#subheading").innerHTML =
    icon("folder") +
    esc(
      view === "work"
        ? draft.title
        : view === "library"
          ? "本机人物、声音与补充画面"
          : "本机渲染任务与素材使用记录",
    );
  $("#work").hidden = view !== "work";
  $("#other").hidden = view === "work";
}
function prepMonitor() {
  const v = $("#video"),
    im = $("#still"),
    empty = $("#empty"),
    screen = $("#screen");
  v.pause();
  stopStill();
  stillClock = 0;
  const a = findAsset(activeAsset) || findAsset(draft.hosts[0]),
    j = current(),
    ready = j?.status === "done";
  if (mode === "result" && !ready) mode = "source";
  const result = mode === "result";
  const videoSrc = result
    ? "/api/jobs/" + j.id + "/film"
    : a?.kind === "video"
      ? mediaURL(a.id, "source")
      : "";
  const imgSrc = !result && a ? mediaURL(a.id, "poster") : "";
  v.hidden = !videoSrc;
  im.hidden = Boolean(videoSrc) || !imgSrc;
  empty.hidden = Boolean(videoSrc || imgSrc);
  empty.textContent = "先导入一张人物照片或一段母片";
  if (videoSrc) {
    if (v.getAttribute("src") !== videoSrc) {
      v.src = videoSrc;
      v.load();
    }
    if (imgSrc) v.poster = imgSrc;
    else v.removeAttribute("poster");
  } else {
    v.removeAttribute("src");
    v.load();
    if (imgSrc) im.src = imgSrc;
  }
  $("#screenTag").textContent = result ? "PROGRAM  /  成片" : "SOURCE  /  母片";
  screen.classList.toggle(
    "vertical",
    result ? j.aspect === "9:16" : draft.aspect === "9:16",
  );
  for (const b of document.querySelectorAll("[data-mode]")) {
    b.classList.toggle("chosen", b.dataset.mode === mode);
    if (b.dataset.mode === "result") b.disabled = !ready;
  }
  updateClock();
}
function duration() {
  const v = $("#video");
  if (!v.hidden && Number.isFinite(v.duration)) return v.duration;
  return draft?.voiceData?.duration || findAsset(activeAsset)?.duration || 0;
}
function updateClock() {
  const v = $("#video"),
    t = v.hidden ? stillClock : v.currentTime;
  $("#at").textContent = fmt(t);
  $("#length").textContent = fmt(duration());
  $("#seek").value = duration() ? (t / duration()) * 1000 : 0;
  $("#play").innerHTML = icon(
    (!v.hidden && !v.paused) || stillTimer ? "pause" : "play",
  );
}
function stopStill() {
  if (stillTimer) clearInterval(stillTimer);
  stillTimer = null;
}
function seek(t) {
  const v = $("#video");
  if (v.hidden) stillClock = t;
  else if (Number.isFinite(v.duration)) v.currentTime = Math.min(t, v.duration);
  updateClock();
}
function setStep(i) {
  step = i;
  view = "work";
  nav();
  inspector();
  drawTracks();
}
function showView(k) {
  view = k;
  nav();
  if (k === "work") {
    inspector();
    prepMonitor();
    drawTracks();
  } else {
    $("#video").pause();
    stopStill();
    alternative();
  }
}
function drawTracks() {
  const actual = mode === "result" && resultTimeline;
  const vv = actual ? resultVoice : draft.voiceData,
    lines = actual ? resultTimeline.rows : draft.lines || [],
    time = vv?.duration || 0,
    root = $("#tracks");
  $("#timelineInfo").textContent = "25 FPS" + (time ? "  ·  " + sec(time) : "");
  if (!time) {
    root.innerHTML =
      '<p class="timelineNote">准备配音后，这里会显示按声音对齐的镜头和字幕。</p>';
    return;
  }
  const p = findAsset(activeAsset) || findAsset(draft.hosts[0]);
  const pic = p ? mediaURL(p.id, "poster") : "";
  const lane = (kind) => {
    let result = "",
      cursor = 0;
    for (const [i, l] of lines.entries()) {
      const s = Number(l.start) || 0,
        e = Number(l.end) || 0;
      const space = (Math.max(0, s - cursor) / time) * 100;
      if (space) result += '<i style="width:' + space + '%"></i>';
      const pattern = {
        studio: ["full"],
        editorial: ["full", "split", "card"],
        lecture: ["full", "pip", "split"],
      }[draft.style];
      const layout =
        l.layout && l.layout !== "auto"
          ? l.layout
          : pattern[i % pattern.length];
      const thumb = actual && l.shot ? mediaURL(l.shot.asset, "poster") : pic;
      const bg =
        thumb && kind === "video" && !["card", "insert"].includes(layout)
          ? "background-image:linear-gradient(#15201075,#15201089),url(" +
            thumb +
            ");"
          : "";
      result +=
        '<button title="' +
        esc(l.text) +
        '" data-jump="' +
        s +
        '" class="' +
        (kind === "video" ? "videoClip" : "subClip") +
        '" style="' +
        bg +
        "width:" +
        Math.max(0, ((e - s) / time) * 100) +
        '%">' +
        esc(kind === "video" ? layouts[layout] : l.text) +
        "</button>";
      cursor = e;
    }
    return result;
  };
  const tr = (k, label, draw) =>
    '<div class="tr"><label>' + icon(k) + label + "</label>" + draw + "</div>";
  root.innerHTML =
    '<div class="trackgrid">' +
    tr(
      "",
      "",
      '<div class="ruler">' +
        [0, 0.25, 0.5, 0.75, 1]
          .map((t) => "<span>" + fmt(t * time) + "</span>")
          .join("") +
        "</div>",
    ) +
    tr("video", "镜头", '<div class="lane">' + lane("video") + "</div>") +
    tr(
      "voice",
      "配音",
      '<div class="lane wave">' +
        vv.waveform
          .map((v) => '<i style="height:' + Math.max(2, v * 18) + 'px"></i>')
          .join("") +
        "</div>",
    ) +
    tr("captions", "字幕", '<div class="lane">' + lane("subs") + "</div>") +
    "</div>";
}
const upload = (role, label) =>
  '<label class="uploadBtn">' +
  icon("upload") +
  label +
  '<input type="file" hidden data-upload="' +
  role +
  '" accept="' +
  (role === "audio"
    ? ".wav,.mp3,.m4a,.aiff,.aac"
    : ".png,.jpg,.jpeg,.webp,.mp4,.mov,.m4v") +
  '"></label>';
function aspectButtons() {
  return (
    '<div class="field"><span>导出画幅</span><div class="formatrow">' +
    ["16:9", "9:16"]
      .map(
        (a, i) =>
          '<button class="outline ' +
          (draft.aspect === a ? "selected" : "") +
          '" data-aspect="' +
          a +
          '">' +
          icon(i ? "portrait" : "landscape") +
          (i ? "竖版 " : "横版 ") +
          a +
          "</button>",
      )
      .join("") +
    "</div></div>"
  );
}
async function openFilm(id, playNow = true) {
  const tl = await api("/api/jobs/" + id + "/timeline");
  resultVoice = await api("/api/voice/" + tl.voice + "/info");
  resultTimeline = tl;
  playingJob = id;
  mode = "result";
  setStep(5);
  prepMonitor();
  drawTracks();
  if (playNow)
    $("#video")
      .play()
      .catch(() => {});
}
function jobBox(j) {
  if (!j)
    return '<p class="hint">生成完成后，可在监看区播放整条成片并下载。</p>';
  return (
    '<div class="jobstatus stack"><b>' +
    esc(j.title) +
    '</b><span class="hint">' +
    esc(j.message) +
    "</span>" +
    (j.status === "running" || j.status === "queued"
      ? '<progress max="100" value="' + j.progress + '"></progress>'
      : "") +
    (j.qc
      ? '<p class="hint">' +
        j.qc.size.join(" × ") +
        " · " +
        j.qc.frames +
        " 帧 · " +
        sec(j.qc.duration) +
        "<br>推理 " +
        j.qc.inferred +
        " 帧 · 复用 " +
        j.qc.cached +
        " 帧 · 跳过 " +
        j.qc.skipped +
        " 帧</p><small>素材使用：" +
        esc(
          Object.entries(j.usage || {})
            .map(([id, n]) => id + " × " + n)
            .join("、") || "纯图文",
        ) +
        '</small><div class="btnrow"><button class="minor" data-watch="' +
        j.id +
        '">播放成片</button><a href="/api/jobs/' +
        j.id +
        '/film?download=1">下载 MP4</a><a href="/api/jobs/' +
        j.id +
        '/timeline?download=1">时间轴</a></div>'
      : "") +
    "</div>"
  );
}
function inspector() {
  const descriptions = [
    "选择可复用的人物影像，或导入自己的照片和母片。",
    "核对切点和表演标签，取消有遮挡或异常的镜头。",
    "以最终配音锁定时间轴，字幕和镜头跟随声音。",
    "逐句指定镜头与版式，隐藏人物的句段跳过推理。",
    "为同一套素材选择画幅和镜头组合。",
    "带声复核闭唇、接缝、字幕和遮挡。",
  ];
  const a = findAsset(activeAsset) || findAsset(draft.hosts[0]);
  const shots = shotMap[a?.id] || [];
  let body = "";
  if (step === 0) {
    body =
      '<div class="stack">' +
      session.assets
        .filter((a) => a.role === "host")
        .map(
          (a) =>
            '<label class="assetrow"><input type="checkbox" data-host="' +
            a.id +
            '" ' +
            (draft.hosts.includes(a.id) ? "checked" : "") +
            '><img src="' +
            mediaURL(a.id, "poster") +
            '" alt=""><div><b>' +
            esc(a.name) +
            "</b><small>" +
            (a.kind === "photo" ? "人物照片" : sec(a.duration)) +
            " · " +
            a.width +
            " × " +
            a.height +
            "</small></div></label>",
        )
        .join("") +
      upload("host", "导入人物照片或母片") +
      "</div>";
  }
  if (step === 1) {
    body =
      '<label class="field"><span>复核母片</span><select id="reviewAsset">' +
      session.assets
        .filter((a) => a.role === "host")
        .map((o) => opt(o.id, o.name, a?.id))
        .join("") +
      '</select></label><div class="stack">' +
      shots
        .map(
          (s, i) =>
            '<div class="shot" data-index="' +
            i +
            '"><div class="subline"><label><input type="checkbox" data-shotprop="enabled" ' +
            (s.enabled ? "checked" : "") +
            "> " +
            esc(s.label) +
            '</label><button class="minor" data-jump="' +
            s.start +
            '">定位</button></div>' +
            (a.kind === "video"
              ? '<div class="pair">' +
                ["start", "end"]
                  .map(
                    (k, j) =>
                      "<label>" +
                      (j ? "出点" : "入点") +
                      '（秒）<input data-shotprop="' +
                      k +
                      '" type="number" step=".04" min="0" max="' +
                      a.duration +
                      '" value="' +
                      s[k] +
                      '"></label>',
                  )
                  .join("") +
                "</div>"
              : "") +
            ["emotion", "gaze", "gesture"]
              .map(
                (k, j) =>
                  "<label>" +
                  ["表情", "视线", "手势"][j] +
                  '<input data-shotprop="' +
                  k +
                  '" value="' +
                  esc(s[k]) +
                  '"></label>',
              )
              .join("") +
            (s.warning ? "<small>" + esc(s.warning) + "</small>" : "") +
            "</div>",
        )
        .join("") +
      "</div>" +
      (a
        ? '<div class="btnrow">' +
          (a.kind === "video"
            ? '<button class="minor" id="addshot">增加切片</button>'
            : "") +
          '<button class="outline" id="saveShots">保存切片标签</button></div>'
        : "");
  }
  if (step === 2) {
    body =
      '<label class="field"><span>测试文案</span><select id="scriptSample"><option value="" disabled selected>选择一篇填入口播文案</option>' +
      Object.entries(scriptSamples()).map(([name, text]) => opt(text, name, draft.text)).join("") +
      '</select></label><label class="field"><span>口播文案</span><textarea id="script" maxlength="1500" placeholder="输入文案，按句号或换行分句。">' +
      esc(draft.text) +
      '</textarea><small class="count" id="count">' +
      draft.text.length +
      ' / 1500</small></label><label class="field"><span>配音来源</span><select id="voiceChoice">' +
      (!draft.voice ? '<option value="" selected>请选择或导入配音</option>' : "") +
      (session.engine.tts
        ? opt("reed", "系统声音 · Reed 普通话", draft.voice) +
          opt("tingting", "系统声音 · Tingting 普通话", draft.voice)
        : "") +
      session.assets
        .filter((a) => a.role === "audio")
        .map((a) => opt(a.id, a.name, draft.voice))
        .join("") +
      '</select></label><div class="pair"><button class="outline" id="voiceBtn">' +
      icon("voice") +
      (draft.voiceData ? "试听配音" : "生成并试听") +
      "</button>" +
      upload("audio", "导入配音") +
      '</div><div id="audioPreview" class="stack"></div><hr class="splitline">' +
      aspectButtons();
  }
  if (step === 3) {
    body =
      (draft.lines.length
        ? '<p class="hint">' +
          esc(draft.voiceData.method) +
          ' · 时间单位为秒</p><div class="stack">' +
          draft.lines
            .map(
              (l, i) =>
                '<div class="lineRow" data-line="' +
                i +
                '"><b>' +
                String(i + 1).padStart(2, "0") +
                "　" +
                esc(l.text) +
                '</b><div class="pair">' +
                ["start", "end"]
                  .map(
                    (k, j) =>
                      "<label>" +
                      (j ? "结束" : "开始") +
                      '<input type="number" step=".01" min="0" data-lineprop="' +
                      k +
                      '" value="' +
                      l[k] +
                      '"></label>',
                  )
                  .join("") +
                '</div><select data-lineprop="shot" aria-label="选择镜头">' +
                opt("", "自动轮换切片", l.shot || "") +
                draft.hosts
                  .flatMap((id) =>
                    (shotMap[id] || [])
                      .filter((s) => s.enabled)
                      .map((s) =>
                        opt(s.id, findAsset(id).name + " · " + s.label, l.shot),
                      ),
                  )
                  .join("") +
                '</select><select data-lineprop="layout" aria-label="选择版式">' +
                Object.entries(layouts)
                  .map(([k, n]) => opt(k, n, l.layout || "auto"))
                  .join("") +
                "</select></div>",
            )
            .join("") +
          "</div>"
        : '<button class="outline" id="voiceBtn">准备配音后开始选镜</button>') +
      '<label class="field"><span>嘴型延后帧数（负数为提前）</span><input id="shift" type="number" min="-8" max="8" value="' +
      draft.shift +
      '"></label>';
  }
  if (step === 4) {
    body =
      '<label class="field"><span>剪辑风格</span><select id="styleChoice">' +
      Object.entries(styles)
        .map(([k, n]) => opt(k, n, draft.style))
        .join("") +
      '</select></label><p class="hint">' +
      {
        studio: "每句话均由人物全屏主讲。",
        editorial: "全屏人物、分屏讲解、动态图文按句轮换。",
        lecture: "全屏、圆形小窗、分屏按句轮换。",
      }[draft.style] +
      "</p>" +
      aspectButtons() +
      '<label class="reviewline"><input id="subs" type="checkbox" ' +
      (draft.subtitles ? "checked" : "") +
      '> 在主讲与补充画面下方显示字幕</label><hr class="splitline"><label class="field"><span>补充画面</span><select id="inserts">' +
      opt("", "暂未选用", draft.insert) +
      session.assets
        .filter((a) => a.role === "insert")
        .map((a) => opt(a.id, a.name, draft.insert))
        .join("") +
      "</select></label>" +
      upload("insert", "导入补充画面") +
      '<p class="hint">在「选镜与口型」中将对应句段设为「补充画面」。</p>';
  }
  if (step === 5) {
    body =
      jobBox(current()) +
      '<div class="stack"><span class="fieldLabel">人工复核</span>' +
      ["完整带声播放", "闭唇与句间停顿", "镜头接缝、字幕与遮挡"]
        .map(
          (x, i) =>
            '<label class="reviewline"><input type="checkbox" data-qc="' +
            i +
            '" ' +
            (draft.review?.[current()?.id]?.[i] ? "checked" : "") +
            ">" +
            x +
            "</label>",
        )
        .join("") +
      "</div>";
  }
  $("#stepnum").textContent = "0" + (step + 1) + " / 06";
  $("#inspector").innerHTML =
    '<select class="mobileSteps" id="mobileSteps" aria-label="切换制作阶段">' +
    steps.map((n, i) => opt(String(i), n, String(step))).join("") +
    '</select><div class="sectIntro"><span class="kicker">STEP 0' +
    (step + 1) +
    "</span><h3>" +
    steps[step] +
    '</h3><p class="hint">' +
    descriptions[step] +
    "</p></div>" +
    body +
    (step < 5
      ? '<button class="outline wide accent" id="next">' +
        steps[step + 1] +
        icon("arrow") +
        "</button>"
      : "");
  $("#voiceBtn")?.toggleAttribute("disabled", busy);
  $("#produce").disabled = busy || !!progressJob;
}
function alternative() {
  if (view === "history") {
    $("#other").innerHTML =
      '<div class="subline"><h3>导出记录</h3><span class="mono">' +
      session.jobs.length +
      ' 个任务</span></div><div class="stack topgap">' +
      (session.jobs
        .map(
          (j) =>
            '<div class="historyrow"><div><b>' +
            esc(j.title) +
            "</b><small>" +
            esc(j.created.replace("T", " ").slice(0, 19)) +
            " · " +
            j.aspect +
            " · " +
            esc(j.message) +
            "</small></div>" +
            (j.status === "done"
              ? '<button class="outline" data-watch="' +
                j.id +
                '">查看成片</button>'
              : "") +
            "</div>",
        )
        .join("") || '<p class="hint">导出的成片和检查结果会保存在这里。</p>') +
      "</div>";
    return;
  }
  $("#other").innerHTML =
    '<div class="subline"><h3>素材库</h3>' +
    upload("host", "导入母片") +
    '</div><div class="altgrid">' +
    session.assets
      .map(
        (a) =>
          '<article class="assetcard">' +
          (a.kind === "audio"
            ? '<div class="audioart">' + icon("music") + "</div>"
            : '<img alt="" src="' + mediaURL(a.id, "poster") + '">') +
          "<div><b>" +
          esc(a.name) +
          "</b><small>" +
          { host: "人物素材", audio: "配音", insert: "补充画面" }[a.role] +
          " · " +
          (a.duration ? sec(a.duration) : a.width + " × " + a.height) +
          '</small><button class="minor topgap" data-use="' +
          a.id +
          '">用于当前项目</button></div></article>',
      )
      .join("") +
    "</div>";
}
async function loadShots(id) {
  if (id && !shotMap[id]) shotMap[id] = (await api("/api/shots/" + id)).shots;
}
async function ensureVoice() {
  if (draft.voiceData) return;
  const text = draft.text,
    voice = draft.voice;
  if (!text.trim()) throw Error("请先填写口播文案");
  if (!voice) throw Error("请先选择或导入声音");
  const v = await api("/api/voice", { text, voice });
  if (draft.text !== text || draft.voice !== voice)
    throw Error("文案或声音已更改，请重新准备配音");
  draft.voiceData = v;
  draft.lines = v.lines.map((l) => ({ ...l, layout: "auto", shot: "" }));
  save();
  drawTracks();
  updateClock();
}
async function toggleVoice() {
  busy = true;
  inspector();
  try {
    await ensureVoice();
    inspector();
    if (step === 3) return;
    const el = $("#audioPreview");
    if (el) {
      el.innerHTML =
        '<audio controls style="width:100%" src="/api/voice/' +
        draft.voiceData.id +
        '"></audio><small>' +
        esc(draft.voiceData.method) +
        " · " +
        sec(draft.voiceData.duration) +
        "</small>";
      el.querySelector("audio")
        .play()
        .catch(() => {});
    }
  } finally {
    busy = false;
    $("#produce").disabled = !!progressJob;
    $("#voiceBtn")?.removeAttribute("disabled");
  }
}
async function poll(id) {
  clearTimeout(pollTimer);
  try {
    const j = await api("/api/jobs/" + id);
    updateJob(j);
    if (step === 5 && view === "work") inspector();
    if (view === "history") alternative();
    if (["done", "failed"].includes(j.status)) {
      progressJob = null;
      $("#produce").disabled = false;
      if (j.status === "done") {
        await openFilm(id, false);
        message("成片已生成，可播放并下载");
      } else message(j.message);
      return;
    }
  } catch (e) {
    message(e.message);
  }
  pollTimer = setTimeout(() => poll(id), 1800);
}
async function generate() {
  if (progressJob || busy) return;
  busy = true;
  $("#produce").disabled = true;
  try {
    await ensureVoice();
    const cfg = { ...draft, voiceId: draft.voiceData.id };
    const j = await api("/api/jobs", cfg);
    draft.job = j.id;
    playingJob = j.id;
    save();
    updateJob(j);
    progressJob = j.id;
    setStep(5);
    poll(j.id);
  } finally {
    busy = false;
    $("#produce").disabled = !!progressJob;
  }
}
async function switchStep(n) {
  if (n === 1) await loadShots(activeAsset);
  if (n === 3) {
    await Promise.all(draft.hosts.map(loadShots));
    if (draft.text.trim()) await ensureVoice();
  }
  setStep(n);
}
async function use(a) {
  if (a.role === "host") {
    if (!draft.hosts.includes(a.id)) draft.hosts.push(a.id);
    activeAsset = a.id;
    await loadShots(a.id);
    setStep(0);
  } else if (a.role === "audio") {
    draft.voice = a.id;
    discardVoice();
    setStep(2);
  } else {
    draft.insert = a.id;
    setStep(4);
  }
  save();
  mode = "source";
  prepMonitor();
  drawTracks();
}
async function uploadFile(el) {
  const file = el.files[0];
  if (!file) return;
  message("正在读取本机素材…");
  const f = new FormData();
  f.append("file", file);
  f.append("role", el.dataset.upload);
  const a = await api("/api/assets", f, true);
  session.assets.push(a);
  await use(a);
  message("素材已导入");
}
function play() {
  const v = $("#video");
  if (!v.hidden) {
    if (v.paused) v.play().catch((e) => message(e.message));
    else v.pause();
    return;
  }
  if (stillTimer) {
    stopStill();
    updateClock();
    return;
  }
  if (!duration()) return;
  if (stillClock >= duration()) stillClock = 0;
  stillTimer = setInterval(() => {
    stillClock += 0.1;
    if (stillClock >= duration()) stopStill();
    updateClock();
  }, 100);
  updateClock();
}
document.addEventListener(
  "click",
  task(async (e) => {
    const b = e.target.closest("button,a[data-use]");
    if (!b) return;
    if (b.dataset.view) {
      showView(b.dataset.view);
      return;
    }
    if (b.dataset.step !== undefined) {
      await switchStep(+b.dataset.step);
      return;
    }
    if (b.dataset.mode) {
      if (b.dataset.mode === "result" && current())
        await openFilm(current().id, false);
      else {
        mode = "source";
        prepMonitor();
        drawTracks();
      }
      return;
    }
    if (b.dataset.aspect) {
      draft.aspect = b.dataset.aspect;
      save();
      inspector();
      prepMonitor();
      return;
    }
    if (b.dataset.jump !== undefined) {
      seek(+b.dataset.jump);
      return;
    }
    if (b.dataset.use) {
      await use(findAsset(b.dataset.use));
      return;
    }
    if (b.dataset.watch) {
      await openFilm(b.dataset.watch);
      return;
    }
    if (b.dataset.project) {
      save();
      draft = savedProjects()[b.dataset.project];
      activeAsset = draft.hosts[0];
      mode = "source";
      playingJob = null;
      resultTimeline = null;
      resultVoice = null;
      save();
      $("#dialog").close();
      setStep(2);
      prepMonitor();
      drawTracks();
      return;
    }
    switch (b.id) {
      case "produce":
        await generate();
        break;
      case "voiceBtn":
        await toggleVoice();
        break;
      case "next":
        await switchStep(step + 1);
        break;
      case "play":
        play();
        break;
      case "expand":
        if (document.fullscreenElement) await document.exitFullscreen();
        else await $("#screen").requestFullscreen();
        break;
      case "guideline":
        $("#guides").hidden = !$("#guides").hidden;
        break;
      case "new":
        if (progressJob) {
          message("请待当前任务完成后新建项目");
          break;
        }
        $("#dialogBody").innerHTML =
          '<h3>新建口播项目</h3><label class="field"><span>项目名称</span><input id="newTitle" maxlength="80" placeholder="例如：一分钟产品介绍"></label><button class="primary wide topgap" id="confirmNew">开始制作</button>';
        const others = Object.values(savedProjects()).filter(
          (p) => p.id !== draft.id,
        );
        if (others.length)
          $("#dialogBody").insertAdjacentHTML(
            "beforeend",
            '<div class="field topgap"><span>继续已有项目</span>' +
              others
                .map(
                  (p) =>
                    '<button class="outline" data-project="' +
                    esc(p.id) +
                    '">' +
                    esc(p.title) +
                    "</button>",
                )
                .join("") +
              "</div>",
          );
        $("#dialog").showModal();
        break;
      case "confirmNew": {
        const t = $("#newTitle").value.trim();
        if (!t) throw Error("请输入项目名称");
        save();
        draft = fresh(t);
        activeAsset = draft.hosts[0];
        playingJob = null;
        resultTimeline = null;
        resultVoice = null;
        mode = "source";
        save();
        $("#dialog").close();
        setStep(0);
        prepMonitor();
        drawTracks();
        break;
      }
      case "addshot": {
        const a = findAsset(activeAsset);
        const arr = shotMap[a.id];
        arr.push({
          asset: a.id,
          id: a.id + "-" + (arr.length + 1),
          label: "镜头 " + (arr.length + 1),
          enabled: true,
          start: 0,
          end: a.duration,
          emotion: "待复核",
          gaze: "待复核",
          gesture: "待复核",
        });
        inspector();
        break;
      }
      case "saveShots": {
        const a = findAsset(activeAsset);
        shotMap[a.id] = (
          await api("/api/shots/" + a.id, { shots: shotMap[a.id] })
        ).shots;
        message("切片和标签已保存");
        break;
      }
    }
  }),
);
document.addEventListener("input", (e) => {
  const el = e.target;
  if (el.id === "script") {
    draft.text = el.value;
    const samples = $("#scriptSample");
    samples.value = draft.text;
    if (samples.selectedIndex < 0) samples.selectedIndex = 0;
    if (draft.voice === "demo-audio" && draft.text !== session.demoText) {
      draft.voice = defaultVoice(draft.text);
      const voices = $("#voiceChoice");
      if (!draft.voice) voices.add(new Option("请选择或导入配音", ""), 0);
      voices.value = draft.voice;
      message(draft.voice ? "文案已修改，将用系统普通话重新配音" : "请为新文案选择或导入配音");
    }
    discardVoice();
    $("#count").textContent = el.value.length + " / 1500";
    $("#audioPreview").innerHTML = "";
    if ($("#voiceBtn")) $("#voiceBtn").innerHTML = icon("voice") + "生成并试听";
  }
  if (el.id === "seek") seek((el.value / 1000) * duration());
});
document.addEventListener(
  "change",
  task(async (e) => {
    const el = e.target;
    if (el.dataset.upload) {
      await uploadFile(el);
      return;
    }
    if (el.dataset.host) {
      if (el.checked) {
        if (!draft.hosts.includes(el.dataset.host))
          draft.hosts.push(el.dataset.host);
        activeAsset = el.dataset.host;
        await loadShots(activeAsset);
      } else {
        draft.hosts = draft.hosts.filter((i) => i !== el.dataset.host);
        if (activeAsset === el.dataset.host) activeAsset = draft.hosts[0];
      }
      save();
      prepMonitor();
      drawTracks();
      return;
    }
    if (el.dataset.shotprop) {
      const shot = shotMap[activeAsset][+el.closest(".shot").dataset.index],
        k = el.dataset.shotprop;
      shot[k] =
        k === "enabled"
          ? el.checked
          : ["start", "end"].includes(k)
            ? Number(el.value)
            : el.value;
      return;
    }
    if (el.dataset.lineprop) {
      const k = el.dataset.lineprop;
      draft.lines[+el.closest(".lineRow").dataset.line][k] = [
        "start",
        "end",
      ].includes(k)
        ? Number(el.value)
        : el.value;
      save();
      drawTracks();
      return;
    }
    if (el.dataset.qc !== undefined) {
      const id = current()?.id;
      if (!id) {
        el.checked = false;
        message("请先打开成片");
        return;
      }
      draft.review ??= {};
      draft.review[id] ??= {};
      draft.review[id][el.dataset.qc] = el.checked;
      save();
      return;
    }
    switch (el.id) {
      case "scriptSample":
        if (!el.value || el.value === draft.text) break;
        draft.text = el.value;
        if (!["reed", "tingting"].includes(draft.voice))
          draft.voice = defaultVoice(draft.text);
        discardVoice();
        inspector();
        break;
      case "mobileSteps":
        await switchStep(+el.value);
        break;
      case "reviewAsset":
        activeAsset = el.value;
        await loadShots(activeAsset);
        mode = "source";
        inspector();
        prepMonitor();
        break;
      case "voiceChoice":
        draft.voice = el.value;
        discardVoice();
        inspector();
        break;
      case "styleChoice":
        draft.style = el.value;
        save();
        inspector();
        drawTracks();
        break;
      case "inserts":
        draft.insert = el.value;
        save();
        break;
      case "subs":
        draft.subtitles = el.checked;
        save();
        break;
      case "shift":
        draft.shift = Number(el.value);
        save();
        break;
    }
  }),
);
async function start() {
  document
    .querySelectorAll("[data-icon]")
    .forEach((el) => (el.innerHTML = icon(el.dataset.icon)));
  session = await api("/api/session");
  try {
    draft = JSON.parse(localStorage.getItem("frame-studio-draft-v1"));
  } catch (e) {}
  if (!draft) draft = fresh();
  draft.hosts = draft.hosts.filter((id) => findAsset(id));
  activeAsset =
    draft.hosts[0] || session.assets.find((a) => a.role === "host")?.id;
  $("#engineInfo").textContent = session.engine.ready
    ? session.engine.engine
    : "依赖待安装";
  $("#engineDot").classList.toggle("off", !session.engine.ready);
  $("#engineInfo").title = session.engine.missing.join(", ");
  nav();
  inspector();
  prepMonitor();
  drawTracks();
  const v = $("#video");
  ["timeupdate", "loadedmetadata", "play", "pause", "ended"].forEach((k) =>
    v.addEventListener(k, updateClock),
  );
  if (draft.job && ["queued", "running"].includes(getJob(draft.job)?.status)) {
    progressJob = draft.job;
    setStep(5);
    poll(draft.job);
  }
  if (
    !draft.voiceData &&
    draft.voice === "demo-audio" &&
    draft.text === session.demoText
  ) {
    await ensureVoice();
    if (step === 2) inspector();
    updateClock();
  }
  if (activeAsset) await loadShots(activeAsset);
}
start().catch((e) => message(e.message));

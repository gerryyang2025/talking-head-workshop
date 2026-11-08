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
function lineLayout(line, i) {
  const pattern = {studio: ["full"], editorial: ["full", "split", "card"], lecture: ["full", "pip", "split"]}[draft.style];
  return line.layout && line.layout !== "auto" ? line.layout : pattern[i % pattern.length];
}
const usesHost = (layout) => layout !== "card" && layout !== "insert";
function lineInsert(line) {
  const sole = draft.inserts.length === 1 ? draft.inserts[0].id : "";
  const item = draft.inserts.find(item => item.id === (line.insert ?? sole));
  return {id: item?.id, speaking: Boolean(item && (line.insertSpeaking ?? item.speaking))};
}
function needsInsert(line, layout) {
  if (usesHost(layout) || lineInsert(line).id) return false;
  return layout === "insert" || (line.insert == null && draft.inserts.length > 1);
}
function lineInsertControls(line, layout) {
  const visual = lineInsert(line);
  let options = "";
  if (needsInsert(line, layout)) options += '<option selected disabled>请选择本句素材</option>';
  if (layout === "card") options += opt("", "纯文字卡", visual.id || (needsInsert(line, layout) ? null : ""));
  for (const item of draft.inserts) options += opt(item.id, findAsset(item.id).name, visual.id);
  let html = '<label class="field"><span>本句补充素材</span><select data-lineprop="insert">' + options + '</select></label>';
  if (visual.id) {
    const mode = visual.speaking ? "speaker" : "visual";
    html += '<label class="field"><span>本句素材用途</span><select data-lineprop="insertSpeaking">' +
      opt("visual", "配图", mode) + opt("speaker", "人物口播", mode) + '</select></label>';
  }
  return html;
}
function materialRow(a, removable = false) {
  return '<div class="assetrow"><img loading="lazy" src="' + mediaURL(a.id, "poster") + '" alt=""><div><b>' +
    esc(a.name) + '</b><small>' + (a.kind === "photo" ? "照片" : "视频 · " + sec(a.duration)) + '</small></div>' +
    (removable ? '<button class="minor" data-toggle-insert="' + esc(a.id) + '" aria-label="移出补充素材 ' +
      esc(a.name) + '">移出</button>' : "") + '</div>';
}
function toggleInsert(id) {
  if (draft.inserts.some(item => item.id === id)) {
    for (const cut of draft.cutaways) {
      if (cut.insert === id) cut.insert = "";
    }
    for (const line of draft.lines) {
      if (lineInsert(line).id === id) {
        line.insert = "";
        delete line.insertSpeaking;
      }
    }
    draft.inserts = draft.inserts.filter(item => item.id !== id);
  } else {
    if (draft.inserts.length === 1) {
      draft.lines.forEach((line, index) => {
        if (line.insert == null && !usesHost(lineLayout(line, index))) line.insert = draft.inserts[0].id;
      });
    }
    draft.inserts.push({id, speaking: false});
  }
  save();
  if (view === "library") alternative();
  else inspector();
  drawTracks();
}
const reviewLabels = {
  playback: "完整带声播放",
  mouth: "闭唇与句间停顿",
  edit: "镜头接缝、字幕与遮挡",
};
const savingReviews = new Set();
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
  mode = "framing",
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
let voiceRequest = null, voiceError = "", voiceLookupTimer;
const mediaURL = (id, type) =>
  "/api/assets/" + encodeURIComponent(id) + "/" + type;
const findAsset = (id) => session.assets.find((a) => a.id === id);
const primaryHost = () => findAsset(draft.hosts[0]);
function setPrimaryHost(id) {
  draft.hosts = id ? [id] : [];
  // Shot IDs end in "-<index>"; old multi-host drafts can contain foreign pins.
  for (const line of draft.lines || []) {
    if (line.shot && line.shot.slice(0, line.shot.lastIndexOf("-")) !== id) line.shot = "";
  }
}
async function restoreDraft() {
  clearTimeout(voiceLookupTimer);
  voiceError = "";
  voiceRequest = null;
  draft.cutaways ||= [];
  const referenceVersion = findAsset(draft.voice)?.referenceVersion;
  if (referenceVersion && draft.voiceData && draft.voiceData.referenceVersion !== referenceVersion) {
    Object.assign(draft, {voiceData: null, lines: [], job: null});
    save();
  }
  const first = findAsset(draft.hosts?.[0]);
  if (!Array.isArray(draft.inserts)) {
    const ids = [draft.insert, ...(draft.hosts || []).slice(1)].filter(Boolean);
    draft.inserts = [...new Set(ids)].map(id => ({id, speaking: id === draft.insert && draft.insertSpeaking === true}));
    if (draft.inserts.length) {
      for (const line of draft.lines || []) line.insert = draft.insert || "";
    }
    delete draft.insert;
    delete draft.insertSpeaking;
  }
  draft.inserts = draft.inserts.filter(item => ["photo", "video"].includes(findAsset(item.id)?.kind));
  const available = new Set(draft.inserts.map(item => item.id));
  for (const line of draft.lines || []) {
    if (line.insert && !available.has(line.insert)) {
      line.insert = "";
      delete line.insertSpeaking;
    }
  }
  setPrimaryHost(first && first.kind !== "audio" ? first.id : null);
  const job = getJob(draft.job);
  if (job?.status === "done") {
    // Older exports record the audio ID only in their timeline.
    const project = draft;
    const voiceId = job.voiceId || await api("/api/jobs/" + job.id + "/timeline")
      .then(timeline => timeline.voice).catch(() => null);
    if (project === draft && project.job === job.id &&
        (!project.voiceData || (voiceId && project.voiceData.id !== voiceId))) {
      project.job = null;
      save();
    }
  }
}
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
  const voices = session.systemVoices;
  return (systemVoice("reed") || voices.find(v => v.locale === "zh-CN") || voices[0])?.id || "";
}
function systemVoice(id) {
  return session.systemVoices.find(v => v.id === id);
}
function narrationVoice(id) {
  const profile = findAsset(id);
  return profile?.role === "personal_voice" ? profile : systemVoice(id);
}
function voiceOptions() {
  const choices = session.systemVoices;
  const recordings = session.assets.filter(a => a.role === "audio");
  const profiles = session.assets.filter(a => a.role === "personal_voice");
  const groups = new Map();
  const localeNames = new Intl.DisplayNames(["zh-CN"], {type: "language"});
  const chinese = {"zh-CN": "普通话", "zh-TW": "台湾华语", "zh-HK": "粤语（香港）"};
  for (const voice of choices) {
    if (!groups.has(voice.locale)) groups.set(voice.locale, []);
    groups.get(voice.locale).push(voice);
  }
  const group = (label, options) => '<optgroup label="' + esc(label) + '">' + options + '</optgroup>';
  const locales = Object.keys(chinese).filter(locale => groups.has(locale));
  const others = [...groups.keys()].filter(locale => !locales.includes(locale)).sort();
  let html = "";
  if (!draft.voice) html = '<option value="" selected disabled>请选择或导入配音</option>';
  else if (!narrationVoice(draft.voice) && !recordings.some(a => a.id === draft.voice))
    html = '<option value="' + esc(draft.voice) + '" selected disabled>原配音来源在本机不可用</option>';
  if (profiles.length)
    html += group("个人音色", profiles.map(a => opt(a.id, a.name, draft.voice)).join(""));
  if (recordings.length)
    html += group("素材库录音", recordings.map(a => opt(a.id, a.name, draft.voice)).join(""));
  for (const locale of [...locales, ...others]) {
    const label = chinese[locale] || localeNames.of(locale);
    html += group(label, groups.get(locale).map(v => opt(v.id, v.name + " · " + label, draft.voice)).join(""));
  }
  return html;
}
const longScripts = [
  {
    title: "海边照片里，少了哪十秒",
    text: `先别看镜头里的人，看看他脚边那块石头。上半截是干的，下半截颜色很深，中间留着一道弯弯的水印。
如果请你给这张照片配十秒钟的声音，你会从哪里开始？我会从浪退下去的时候开始录。水从石头缝里抽走，碎石子跟着滚了两下，然后有那么一小会儿，四周安静极了。
这时再切回照片，你可能会注意到，那个人坐得挺靠后，鞋尖离水印还有一段距离。刚才第一眼看过去，你大概只记住了他的脸。
如果手里还有一段海浪的视频，我会等到下一排白沫快碰到鞋尖时，再把视频接进来。让观众看一眼水涨到哪里，然后回到同一张照片。
片尾那两秒，我想只留浪退下去的声音。等碎石子又响起来，就知道下一波浪还在路上。`,
  },
  {
    title: "平均只等四分之一秒，谁等了三秒",
    text: `假设一家小店刚换了点单系统。午休时一共来了一百位客人，店长看了眼报表，说平均不到四分之一秒就能打开菜单。可收银台前偏偏有人说，我刚才等了整整三秒。
我们把一百次点单排开看。九十五次只用十分之一秒，另外五次各用了三秒。把等待时间加起来，再除以一百，店长的数字确实算对了，那五位客人的感受也很准确。
接下来该查哪儿？先把最慢的五次单独挑出来，看它们发生在几点，点开的是哪一页。如果五次都卡在同一张新品大图，就拿一台手机，分别加载原图和缩小后的图，记下两次等待时间。
第二天再去柜台，除了看平均值，我还想问收银员一句：今天午休，还有多少客人点开菜单以后，抬起头来问你，是不是没点上？`,
  },
  {
    title: "用三次试录，找出旁白里的杂音",
    text: `戴上耳机，听一遍你刚录好的旁白。每说完一句，尾音后面都跟着一层沙沙声。先把原录音留着，我们用同一句话做三次试录：把白色的本子放在桌边。
第一次，手机放在平常的位置，念完以后坐着别动，再录三秒。回放时专听这三秒，如果人已经停下，沙沙声还稳稳地响着，就值得先找找房间里有什么一直在转。
第二次，只关掉桌边的小风扇，手机和椅子都留在原处。把两段停顿连起来听，声音在哪一段轻下去了？如果还是分不清，先别急着开降噪。
第三次，把手机往自己这边挪近一掌，朝嘴角稍微偏一点，再念一遍。回放前把三段人声调到差不多响，特别听听“白”和“本”开头有没有扑的一声。
最后选一段你愿意一直听下去的，把手机的位置用一小截胶带标出来。明天接着录下一段时，那截胶带能省下重新试三遍的工夫。`,
  },
  {
    title: "读到一半换手机，书签该落在哪",
    text: `设想你在地铁上读一篇长访谈，读到摄影师讲第一份工作的地方，刚好到站。晚上换一部手机接着看，屏幕上显示阅读进度百分之六十，可眼前这一段，你明明已经看过了。
问题可能出在这个百分数上。两部手机一宽一窄，同样一句话，在一块屏幕上占两行，换一块可能要占四行。访谈前面还有张通栏照片，屏幕一窄，照片反而变矮了。这么一来，直接跳到页面高度的六成，就可能落在另一段。
要是让你设计这个书签，可以试试记住读者停下时，屏幕上方露出的是哪一段，再记下那一段开头的几个字。下次打开时，先找这段文字，再按新屏幕的宽度把它排出来。
现在请朋友做一次小改动，在访谈开头补一张老照片，再把两处回答的第一句都改成“我记得那天”。你手里的书签还能找到原处吗？这时，给每段文字一个固定编号就派上了用场。照片多占了半屏，两句话也长得一模一样，但书签记得读者停在哪一段。
还有个小麻烦：如果编辑恰好删掉了那一段呢？这时可以退回到前一个还在的小标题，让读者从熟悉的地方往下找。
最后，把一部手机的字调到最大，另一部调到最小，在两边各打开一次书签。请两个人分别念出屏幕上的第一句话。听到他们同时念出摄影师的那句回答，这次测试才算过关。`,
  },
];
function fresh(title) {
  const host =
    findAsset("demo-plate") || session.assets.find((a) => a.role === "host");
  const sample = session.engine.tts ? longScripts[0] : {title: "三步制作数字人口播", text: session.demoText};
  return {
    id: crypto.randomUUID(),
    title: title || sample.title,
    hosts: host ? [host.id] : [],
    text: sample.text,
    voice: defaultVoice(sample.text),
    aspect: "16:9",
    style: "editorial",
    subtitles: true,
    shift: 0,
    inserts: [],
    cutaways: [],
    voiceData: null,
    lines: [],
    job: null,
  };
}
function shortScripts() {
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
  clearTimeout(voiceLookupTimer);
  voiceRequest = null;
  voiceError = "";
  delete draft.voicePending;
  draft.voiceData = null;
  draft.lines = [];
  draft.job = null;
  playingJob = null;
  resultTimeline = null;
  resultVoice = null;
  if (mode === "result") {
    mode = "source";
    prepMonitor();
  } else updateMonitorFrame();
  save();
  drawTracks();
  updateClock();
}
function task(fn) {
  return async (...args) => {
    try {
      await fn(...args);
    } catch (e) {
      if (e.name !== "AbortError") message(e.message);
    }
  };
}
function updateJob(j) {
  const index = session.jobs.findIndex((item) => item.id === j.id);
  if (index < 0) session.jobs.unshift(j);
  else session.jobs[index] = j;
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
function updateMonitorFrame() {
  const result = mode === "result";
  const aspect = (result ? current()?.aspect : draft.aspect) || "16:9";
  const screen = $("#screen");
  screen.dataset.aspect = aspect;
  screen.dataset.mode = mode;
  screen.dataset.fit = draft.framing || "cover";
  if (mode === "framing") {
    const height = session.exportSizes[aspect][1];
    const scale = draft.subtitles ? (height - session.captionBand) / height : 1;
    screen.style.setProperty("--picture-scale", scale * 100 + "%");
  }
  $("#screenTag").textContent = mode === "source"
    ? "SOURCE  /  母片原貌"
    : (result ? "PROGRAM  /  成片" : "全屏取景") + " · " + aspect;
  for (const b of document.querySelectorAll("button[data-mode]")) {
    b.classList.toggle("chosen", b.dataset.mode === mode);
    b.setAttribute("aria-pressed", b.dataset.mode === mode);
    if (b.dataset.mode === "result") b.disabled = current()?.status !== "done";
  }
}
function showMaterialMode(next) {
  const wasResult = mode === "result";
  mode = next;
  if (wasResult) {
    prepMonitor();
    drawTracks();
  } else {
    updateMonitorFrame();
  }
  if (step === 5) inspector();
}
function prepMonitor() {
  const v = $("#video"),
    im = $("#still"),
    empty = $("#empty");
  v.pause();
  stopStill();
  stillClock = 0;
  const a = primaryHost(),
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
  updateMonitorFrame();
  updateClock();
}
function duration() {
  const v = $("#video");
  if (!v.hidden && Number.isFinite(v.duration)) return v.duration;
  return draft?.voiceData?.duration || primaryHost()?.duration || 0;
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
  if (i >= 2 && i <= 4) showMaterialMode("framing");
  else if (i < 2) showMaterialMode("source");
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
    $("#cutAudio").pause();
    stopStill();
    alternative();
  }
}
const timelineFPS = 25;
const timelineFrames = () => Math.ceil(draft.voiceData.duration * timelineFPS - 1e-8);
// Match Python's nearest-even rounding of existing voice cue boundaries.
function cueFrame(seconds) {
  const frames = seconds * timelineFPS;
  const lower = Math.floor(frames);
  return frames - lower === 0.5 ? lower + lower % 2 : Math.round(frames);
}
const cutSeconds = frame => (frame / timelineFPS).toFixed(2);
const cutRange = cut => cutSeconds(cut.first) + "–" + cutSeconds(cut.stop) + " 秒";
const cutName = cut => findAsset(cut.insert)?.name || "待选素材";

function baseVisible(index) {
  let cursor = index ? cueFrame(draft.lines[index - 1].end) : 0;
  const stop = index + 1 === draft.lines.length ? timelineFrames() : cueFrame(draft.lines[index].end);
  for (const cut of draft.cutaways) {
    if (cut.first > cursor) break;
    cursor = Math.max(cursor, cut.stop);
    if (cursor >= stop) return false;
  }
  return cursor < stop;
}

function cutEditorList() {
  return '<div class="cut-list"><b>时间线补充镜头</b>' +
    '<small>在剪辑时间线播放或拖动配音，定位后插入。镜头结束时回到原画面。</small>' +
    draft.cutaways.map((cut, i) =>
      '<div class="cut-item"><div><b>' + esc(cutName(cut)) + '</b><small>' + cutRange(cut) +
      ' · ' + (cut.insertSpeaking ? "人物口播" : "配图") + '</small></div>' +
      '<button class="minor" data-edit-cut="' + i + '">编辑</button>' +
      '<button class="minor" data-preview-cut="' + i + '">预览</button></div>').join("") +
    '<button class="outline" data-add-cut>在配音当前位置插入</button></div>';
}
function editCut(index) {
  const audio = $("#cutAudio");
  audio.pause();
  $("#video").pause();
  stopStill();
  updateClock();
  const total = timelineFrames();
  let cut = draft.cutaways[index];
  if (!cut) {
    let first = Math.min(total - 1, Math.round(audio.currentTime * timelineFPS));
    // Repeated insertions at the same playhead append after existing adjacent shots.
    for (const item of draft.cutaways) {
      if (item.first <= first && item.stop > first) first = item.stop;
    }
    const next = draft.cutaways.find(item => item.first > first);
    const stop = Math.min(first + 2 * timelineFPS, next?.first ?? total, total);
    if (first >= stop) throw Error("当前位置之后没有空白，请移动配音播放位置或调整已有镜头");
    cut = {first, stop, insert: "", insertSpeaking: false};
  }
  const options = session.assets.filter(a => a.kind === "photo" || a.kind === "video");
  if (!options.length && index < 0) {
    showView("library");
    message("请先在素材库导入照片或视频");
    return;
  }
  const timing = (name, title, frame) => '<label class="field"><span>' + title +
    '（秒）</span><input required type="number" name="' + name + '" min="0" step="0.01" max="' +
    cutSeconds(total) + '" value="' + cutSeconds(frame) + '"></label>';
  $("#dialogBody").innerHTML = '<h3>' + (index < 0 ? '插入补充画面' : '编辑补充镜头') + '</h3>' +
    '<form id="cutForm" class="stack" data-index="' + index + '">' +
    '<label class="field"><span>素材库</span><select name="asset" required>' +
    opt("", "选择照片或视频", cut.insert || "") +
    options.map(a => opt(a.id, a.name + (a.kind === "video" ? " · 视频" : " · 照片"), cut.insert)).join("") +
    '</select></label><img id="cutPoster" alt="所选素材预览" hidden>' +
    '<div class="pair">' + timing("start", "开始", cut.first) + timing("end", "结束", cut.stop) + '</div><small>时间按 25 FPS 对齐，每帧 0.04 秒。</small>' +
    '<label class="field"><span>镜头用途</span><select name="usage">' +
    opt("visual", "配图 · 沿用原配音", cut.insertSpeaking ? "speaker" : "visual") +
    opt("speaker", "人物口播 · 按原配音做口型", cut.insertSpeaking ? "speaker" : "visual") +
    '</select></label><span role="alert"></span><div class="btnrow">' +
    '<button class="primary" type="submit">保存镜头</button>' +
    (index >= 0 ? '<button class="minor" type="button" id="deleteCut">删除镜头</button>' : '') +
    '</div></form>';
  showCutPoster(cut.insert);
  $("#dialog").showModal();
}
function showCutPoster(id) {
  const img = $("#cutPoster");
  img.hidden = !findAsset(id);
  if (!img.hidden) img.src = mediaURL(id, "poster");
}
function finishCutEdit() {
  draft.cutaways.sort((a, b) => a.first - b.first);
  save();
  $("#dialog").close();
  inspector();
  drawTracks();
}
function saveCut(form) {
  const index = Number(form.dataset.index);
  const cut = {
    first: Math.round(form.elements.start.valueAsNumber * timelineFPS),
    stop: Math.round(form.elements.end.valueAsNumber * timelineFPS),
    insert: form.elements.asset.value,
    insertSpeaking: form.elements.usage.value === "speaker",
  };
  if (!Number.isInteger(cut.first) || !Number.isInteger(cut.stop) ||
      cut.first < 0 || cut.first >= cut.stop || cut.stop > timelineFrames())
    throw Error("结束时间须晚于开始时间，且在配音范围内");
  if (draft.cutaways.some((c, i) => i !== index && c.first < cut.stop && cut.first < c.stop))
    throw Error("与已有补充镜头重叠，请调整开始或结束时间");
  if (!draft.inserts.some(item => item.id === cut.insert)) {
    // Adding a library item on this track must preserve existing automatic cards.
    if (draft.inserts.length <= 1) {
      for (const line of draft.lines) line.insert ??= draft.inserts[0]?.id || "";
    }
    draft.inserts.push({id: cut.insert, speaking: false});
  }
  if (index < 0) draft.cutaways.push(cut);
  else draft.cutaways[index] = cut;
  finishCutEdit();
}
function drawTracks() {
  const actual = mode === "result" && resultTimeline;
  const vv = actual ? resultVoice : draft.voiceData,
    lines = actual ? resultTimeline.rows : draft.lines || [],
    time = vv?.duration || 0,
    root = $("#tracks");
  $("#timelineInfo").textContent = "25 FPS" + (time ? "  ·  " + sec(time) : "");
  const cuts = actual ? resultTimeline.cutaways || [] : draft.cutaways;
  const toolbar = $("#cutTransport"), audio = $("#cutAudio");
  toolbar.hidden = !time || !!actual || step !== 3 || view !== "work";
  if (toolbar.hidden) audio.pause();
  else {
    const src = "/api/voice/" + vv.id;
    if (audio.getAttribute("src") !== src) audio.src = src;
  }
  if (!time) {
    const recorded = findAsset(draft.voice)?.role === "audio";
    let tip, action = "";
    if (!draft.text.trim() || !draft.voice) {
      tip = "填写口播文案并选择配音来源，即可准备时间线。";
      if (step !== 2) action = '<button class="minor" data-step="2">前往文案配音</button>';
    } else if (voiceRequest?.project === draft) {
      tip = voiceRequest.cachedOnly ? "正在查找这篇文案已有的配音…" :
        recorded ? "正在载入录音并排列字幕…" : "正在生成整篇配音，完成后会显示镜头、波形和字幕。";
    } else {
      tip = voiceError || (recorded ? "可以用这份录音为当前文案排列镜头和字幕。" : "当前文案和音色尚未准备好整篇配音。");
      action = '<button class="minor" data-prepare-voice>' +
        (voiceError ? "重试" : recorded ? "载入录音" : "生成整篇配音") + '</button>';
    }
    root.innerHTML = '<div class="timelineNote" role="status">' + esc(tip) + ' ' + action + '</div>';
    return;
  }
  const p = primaryHost();
  const pic = p ? mediaURL(p.id, "poster") : "";
  const lane = (kind) => {
    let result = "",
      cursor = 0;
    for (const [i, l] of lines.entries()) {
      const s = Number(l.start) || 0,
        e = Number(l.end) || 0;
      const space = (Math.max(0, s - cursor) / time) * 100;
      if (space) result += '<i style="width:' + space + '%"></i>';
      const layout = lineLayout(l, i);
      const visual = actual
        ? {id: l.insert || (layout === "insert" && resultTimeline.insert), speaking: l.insertSpeaking}
        : lineInsert(l);
      const insert = visual.id;
      const isGraphic = !usesHost(layout);
      const speaking = isGraphic && insert && visual.speaking;
      const thumb = isGraphic ? (insert && mediaURL(insert, "poster"))
        : actual && l.shot ? mediaURL(l.shot.asset, "poster") : pic;
      const bg =
        thumb && kind === "video"
          ? "background-image:linear-gradient(#15201075,#15201089),url(" +
            thumb +
            ");"
          : "";
      result +=
        '<button ' +
        (!actual && (isGraphic || cuts.length) && kind === "video" ? `data-card-line="${i}" ` : "") +
        'title="' +
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
        esc(kind === "video" ? layouts[layout] +
          (!actual && needsInsert(l, layout) ? " · 待选素材" : speaking ? " · 人物口播" : "") : l.text) +
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
    ((cuts.length || !toolbar.hidden) ? tr("library", "补充", '<div class="lane cut-lane">' + cuts.map((cut, i) => {
      const title = cutName(cut) + " · " + cutRange(cut);
      const action = actual ? 'data-jump="' + cut.first / timelineFPS : 'data-edit-cut="' + i;
      return '<button ' + action + '" title="' + esc(title) + '" aria-label="' + esc(title) +
        '" style="left:' + (100 * cut.first / timelineFPS / time) + '%;width:' +
        (100 * (cut.stop - cut.first) / timelineFPS / time) + '%">' + esc(cutName(cut)) + '</button>';
    }).join("") + (!toolbar.hidden ? '<i id="cutHead" aria-hidden="true"></i>' : "") + '</div>') : "") +
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
  updateCutHead();
}
function updateCutHead() {
  const head = $("#cutHead");
  if (head) head.style.left = Math.min(100, $("#cutAudio").currentTime * 100 / draft.voiceData.duration) + "%";
}
async function previewCard(index) {
  const line = draft.lines[index];
  if (draft.cutaways.length) {
    return previewTimeline(cueFrame(line.start), cueFrame(line.end));
  }
  const layout = lineLayout(line, index);
  const visual = lineInsert(line);
  if (needsInsert(line, layout)) {
    await switchStep(3);
    document.querySelector(`[data-line="${index}"] [data-lineprop="insert"]`)?.focus();
    message("请先为这句选择补充素材");
    return;
  }
  return playPreview("/api/card-preview", layouts[layout] + "预览", {
    voiceId: draft.voiceData.id, aspect: draft.aspect, insert: visual.id,
    layout, insertSpeaking: visual.speaking, shift: draft.shift,
    subtitles: draft.subtitles, framing: draft.framing || "cover",
    line: index, start: line.start, end: line.end,
  });
}
function previewTimeline(first, stop) {
  return playPreview("/api/timeline-preview", "剪辑预览 · " + cutRange({first, stop}), {
    ...draft, voiceId: draft.voiceData.id, previewFirst: first, previewStop: stop,
  });
}
async function playPreview(endpoint, title, config) {
  const dialog = $("#cardPreview");
  const video = dialog.querySelector("video"), status = dialog.querySelector("[role=status]");
  const controller = new AbortController();
  let url;
  $("#cutAudio").pause();
  $("#video").pause();
  stopStill();
  updateClock();
  $("#cardPreviewTitle").textContent = title;
  status.textContent = "正在生成带声预览…";
  video.hidden = true;
  dialog.showModal();
  dialog.addEventListener("close", () => {
    controller.abort();
    video.pause();
    video.removeAttribute("src");
    video.load();
    if (url) URL.revokeObjectURL(url);
  }, {once: true});
  try {
    const response = await fetch(endpoint, {
      method: "POST", signal: controller.signal,
      headers: {"Content-Type": "application/json", "X-Studio-Request": "1"},
      body: JSON.stringify(config),
    });
    if (!response.ok) throw Error((await response.json()).error || "图文预览失败");
    const clip = await response.blob();
    if (controller.signal.aborted) return;
    url = URL.createObjectURL(clip);
    video.src = url;
    video.hidden = false;
    status.textContent = "";
    await video.play().catch(() => {});
  } catch (error) {
    if (!controller.signal.aborted) status.textContent = error.message;
  }
}
const upload = (role, label) =>
  '<label class="uploadBtn">' +
  icon("upload") +
  label +
  '<input type="file" hidden multiple data-upload="' +
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
          '" aria-pressed="' +
          (draft.aspect === a) +
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
  const [job, tl] = await Promise.all([
    api("/api/jobs/" + id), api("/api/jobs/" + id + "/timeline"),
  ]);
  const voice = await api("/api/voice/" + tl.voice + "/info");
  if (!playNow && current()?.id !== id) return;
  updateJob(job);
  resultVoice = voice;
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
function reviewSummary(job) {
  const items = Object.keys(reviewLabels);
  const passed = items.filter((k) => job.review?.[k]?.status === "passed").length;
  const issues = items.filter((k) => job.review?.[k]?.status === "issue").length;
  if (issues) return `待修改 · ${issues} 项有问题 · ${passed}/${items.length} 通过`;
  if (passed === items.length) return `复核通过 · ${passed}/${items.length}`;
  return `${passed ? "复核中" : "待复核"} · ${passed}/${items.length} 通过`;
}
function reviewPanel(job) {
  if (job?.status !== "done") return "";
  const rows = Object.entries(reviewLabels).map(([key, label]) => {
    const entry = job.review?.[key] || {status: "pending"};
    const issue = entry.status === "issue" ? `
      <div class="issue-note">
        <button class="minor" data-review-seek="${entry.time}" aria-label="跳到问题位置 ${sec(entry.time)}">${sec(entry.time)}</button>
        <span>${esc(entry.note)}</span>
        <button class="minor" data-edit-issue="${key}">编辑</button>
      </div>` : "";
    return `<div><label class="review-item"><span>${label}</span>
      <select data-review-item="${key}">
        ${opt("pending", "待检查", entry.status)}${opt("passed", "通过", entry.status)}${opt("issue", "有问题", entry.status)}
      </select></label>${issue}</div>`;
  });
  return `<section class="stack"><div class="review-heading"><b>人工复核</b><small aria-live="polite">${reviewSummary(job)}</small></div>
    ${mode === "result" ? `<fieldset class="review-list" data-review-job="${job.id}" ${savingReviews.has(job.id) ? "disabled" : ""}>${rows.join("")}</fieldset>`
      : '<small>请打开成片后复核。</small>'}</section>`;
}
async function saveReview(id, key, entry) {
  if (savingReviews.has(id)) throw Error("正在保存上一项复核");
  savingReviews.add(id);
  const panel = document.querySelector(`fieldset[data-review-job="${id}"]`);
  if (panel) panel.disabled = true;
  try {
    const job = await api("/api/jobs/" + id + "/review", {items: {[key]: entry}});
    updateJob(job);
  } finally {
    savingReviews.delete(id);
    if (view === "work" && step === 5 && current()?.id === id) inspector();
    if (view === "history") alternative();
  }
}
function editIssue(id, key) {
  const video = $("#video"), job = getJob(id);
  video.pause();
  const entry = job.review?.[key];
  const end = Math.floor(job.qc.duration * 100) / 100;
  const time = Math.min(end, entry?.time ?? video.currentTime).toFixed(2);
  $("#dialogBody").innerHTML = `<h3>${reviewLabels[key]}</h3>
    <form class="stack" id="issueForm" data-job="${id}" data-item="${key}">
      <label class="field"><span>成片位置（秒）</span><input name="time" type="number" min="0" max="${end}" step=".01" value="${time}" required></label>
      <label class="field"><span>问题说明</span><textarea name="note" required maxlength="300" placeholder="例如：这句说完后嘴仍张着">${esc(entry?.note || "")}</textarea></label>
      <small role="alert"></small><button class="primary" type="submit">保存问题</button>
    </form>`;
  $("#dialog").showModal();
  $("#issueForm textarea").focus();
}
async function importDraftReviews() {
  const missing = new Map();
  for (const project of [...Object.values(savedProjects()), draft]) {
    for (const [id, flags] of Object.entries(project.review || {})) {
      const job = getJob(id);
      if (job?.status !== "done") continue;
      Object.keys(reviewLabels).forEach((key, i) => {
        if (flags?.[i] !== true || job.review?.[key]) return;
        if (!missing.has(id)) missing.set(id, {});
        missing.get(id)[key] = {status: "passed"};
      });
    }
  }
  for (const [id, items] of missing) {
    updateJob(await api("/api/jobs/" + id + "/review", {items, onlyMissing: true}));
  }
}
function jobBox(j) {
  if (!j)
    return '<p class="hint">点击「生成口播」，即可用当前文案和配音生成成片。已生成的版本可在「导出记录」查看。</p>';
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
            .map(([id, n]) => (findAsset(id)?.name || id) + " × " + n)
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
    "主讲母片用于人物出镜。把本片需要的配图和其他口播素材一起加入项目。",
    "核对切点和表演标签，取消有遮挡或异常的镜头。",
    "以最终配音锁定时间轴，字幕和镜头跟随声音。",
    "逐句指定镜头与版式，隐藏人物的句段跳过推理。",
    "为同一套素材选择画幅和镜头组合。",
    "带声复核闭唇、接缝、字幕和遮挡。",
  ];
  const a = primaryHost();
  const shots = shotMap[a?.id] || [];
  let body = "";
  if (step === 0) {
    const selected = draft.inserts.map(item => findAsset(item.id)).filter(Boolean);
    body = '<div class="field"><span>主讲母片</span>' +
      (a ? materialRow(a) : '<small>请从素材库选择主讲人物。</small>') +
      '</div><div class="field"><span>补充素材（' + selected.length + '）</span>' +
      (selected.length ? '<div class="stack project-materials">' + selected.map(item => materialRow(item, true)).join("") + '</div>'
        : '<small>可选多张照片或多段视频。</small>') +
      '</div><button class="outline wide" data-view="library">从素材库选取</button>';
  }
  if (step === 1) {
    body =
      '<p class="hint">主讲母片：' + esc(a?.name || "请先在「准备母片」选择") +
      '</p><div class="stack">' +
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
      '<optgroup label="长篇口播">' + longScripts.map(s => opt(s.text, s.title, draft.text)).join("") +
      '</optgroup><optgroup label="快速测试">' + Object.entries(shortScripts()).map(([name, text]) => opt(text, name, draft.text)).join("") +
      '</optgroup></select></label><label class="field"><span>口播文案</span><textarea id="script" maxlength="1500" placeholder="输入文案，按句号或换行分句。">' +
      esc(draft.text) +
      '</textarea><small class="count" id="count">' +
      draft.text.length +
      ' / 1500</small></label><label class="field"><span>配音来源</span><select id="voiceChoice">' +
      voiceOptions() +
      '</select></label><div class="btnrow"><button class="minor" id="toneBtn"' +
      (narrationVoice(draft.voice) ? '' : ' hidden') + '>短句试听音色</button>' +
      '<button class="minor" data-view="library">从素材库选配音</button></div>' +
      (findAsset(draft.voice)?.role === "personal_voice" ? '<p class="hint">' +
        (session.engine.personalVoice ? 'Qwen3-TTS 在本机逐句合成，单条配音最长 120 秒。'
          : '个人音色引擎尚未就绪，请按 README 的个人音色安装步骤配置。') + '</p>' : '') +
      (findAsset(draft.voice)?.role === "personal_voice" ? '<button class="minor" data-edit-reference="' +
        esc(draft.voice) + '">核对参考录音与逐字稿</button>' : '') +
      '<button class="outline wide" id="voiceBtn">' +
      icon("voice") +
      (draft.voiceData ? "试听配音" : "生成并试听") +
      '</button><div id="audioPreview" class="stack"></div><hr class="splitline">' +
      aspectButtons();
  }
  if (step === 3) {
    body =
      (draft.lines.length ? cutEditorList() : "") +
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
                '</div><select data-lineprop="layout" aria-label="选择版式">' +
                Object.entries(layouts)
                  .map(([k, n]) => opt(k, n, l.layout || "auto"))
                  .join("") +
                "</select>" +
                (usesHost(lineLayout(l, i))
                  ? '<select data-lineprop="shot" aria-label="主讲母片切片">' +
                    opt("", (a?.name || "主讲母片") + " · 自动选片", l.shot || "") +
                    shots.filter(s => s.enabled).map(s => opt(s.id, a.name + " · " + s.label, l.shot)).join("") +
                    "</select>"
                  : lineInsertControls(l, lineLayout(l, i))) +
                "</div>",
            )
            .join("") +
          "</div>"
        : '<button class="outline" id="voiceBtn">准备配音后开始选镜</button>') +
      '<button class="outline" data-view="library">从素材库选取补充素材</button>' +
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
      '<label class="field"><span>全屏镜头取景</span><select id="framing">' +
      opt("cover", "铺满画幅（居中裁切）", draft.framing || "cover") +
      opt("contain", "保留全貌（等比留边）", draft.framing || "cover") +
      '</select></label>' +
      '<label class="reviewline"><input id="subs" type="checkbox" ' +
      (draft.subtitles ? "checked" : "") +
      '> 在主讲与补充画面下方显示字幕</label>' +
      '<button class="minor" data-step="3">调整逐句镜头与素材</button>';
  }
  if (step === 5) {
    body = jobBox(current()) + reviewPanel(current());
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
  updateVoiceButton();
  $("#toneBtn")?.toggleAttribute("disabled", busy);
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
            (j.status === "done" ? " · " + reviewSummary(j) : "") +
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
    '<div class="subline library-tools"><span>当前项目 · ' + esc(draft.title) +
    ' · 已选 ' + draft.inserts.length + ' 份补充素材</span><div class="btnrow">' +
    upload("host", "导入照片或视频") + upload("audio", "导入配音") +
    '<button class="outline" id="addVoiceProfile">添加个人音色</button>' +
    '<button class="outline" data-view="work">返回工作台</button></div></div><div class="altgrid">' +
    session.assets.map(a => {
      const audio = a.kind === "audio", primary = draft.hosts[0] === a.id;
      const selected = draft.inserts.some(item => item.id === a.id);
      const personal = a.role === "personal_voice";
      const useLabel = audio ? (draft.voice === a.id ? "当前配音" : personal ? "用此音色配音" : "用作配音") : (primary ? "当前主讲" : "设为主讲");
      return '<article class="assetcard">' +
        (audio ? '<div class="audioart">' + icon("music") + '</div>'
          : '<img loading="lazy" alt="" src="' + mediaURL(a.id, "poster") + '">') +
        '<div><b>' + esc(a.name) + '</b><small>' +
        (personal ? "个人音色 · 参考录音" : {photo: "照片", video: "视频", audio: "配音"}[a.kind]) + ' · ' +
        (a.duration ? sec(a.duration) : a.width + ' × ' + a.height) +
        '</small>' + (personal ? '<details class="voice-reference"><summary>参考录音与逐字稿</summary>' +
          '<audio controls preload="none" aria-label="参考录音" src="' + mediaURL(a.id, "reference") +
          '"></audio><p>' + esc(a.transcript) + '</p><button class="minor" data-edit-reference="' +
          esc(a.id) + '">修改逐字稿</button></details>' : '') +
        '<div class="btnrow topgap"><button class="minor" data-use="' + esc(a.id) + '"' +
        (primary || (audio && draft.voice === a.id) ? ' disabled' : '') + '>' + useLabel + '</button>' +
        (audio ? '' : '<button class="minor" aria-pressed="' + selected + '" data-toggle-insert="' + esc(a.id) + '">' +
          (selected ? '已选为补充' : '选为补充') + '</button>') +
        '</div></div></article>';
    }).join("") + '</div>';
}
async function loadShots(id) {
  if (id && !shotMap[id]) shotMap[id] = (await api("/api/shots/" + id)).shots;
}
function updateVoiceButton() {
  const button = $("#voiceBtn");
  if (!button) return;
  const pending = voiceRequest?.project === draft && !voiceRequest.cachedOnly;
  button.disabled = busy || pending;
  if (step === 2) button.innerHTML = icon("voice") + (draft.voiceData ? "试听配音" :
    pending ? "正在准备配音…" : findAsset(draft.voice)?.role === "audio" ? "载入并试听" : "生成并试听");
}
async function ensureVoice(cachedOnly = false) {
  if (draft.voiceData) return draft.voiceData;
  const {text, voice} = draft;
  if (!text.trim()) throw Error("请先填写口播文案");
  if (!voice) throw Error("请先选择或导入声音");
  if (voiceRequest?.project === draft && (cachedOnly || !voiceRequest.cachedOnly)) return voiceRequest.promise;
  const request = {project: draft, cachedOnly};
  voiceRequest = request;
  voiceError = "";
  if (!cachedOnly) {
    draft.voicePending = true;
    save();
  }
  drawTracks();
  updateVoiceButton();
  const isCurrent = () => voiceRequest === request && request.project === draft;
  request.promise = api("/api/voice" + (cachedOnly ? "?cached=1" : ""), {text, voice}).then(v => {
    if (!isCurrent()) throw new DOMException("配音选择已更改", "AbortError");
    if (v) {
      draft.voiceData = v;
      draft.lines = v.lines.map(l => ({...l, layout: "auto", shot: ""}));
    }
    return v;
  }).catch(error => {
    if (!isCurrent()) throw new DOMException("配音选择已更改", "AbortError");
    voiceError = error.message;
    throw error;
  }).finally(() => {
    if (!isCurrent()) return;
    voiceRequest = null;
    delete draft.voicePending;
    if (draft.voiceData || !cachedOnly) save();
    if (view === "work" && step === 3 && draft.voiceData) inspector();
    updateVoiceButton();
    drawTracks();
    updateClock();
  });
  return request.promise;
}
function restoreTimeline() {
  if (!draft.voiceData && draft.voice && draft.text.trim()) {
    const cachedOnly = !draft.voicePending && findAsset(draft.voice)?.role !== "audio";
    // Background lookup errors are displayed in the timeline alongside a retry action.
    ensureVoice(cachedOnly).catch(() => {});
  }
}
async function selectVoice(id) {
  if (draft.voice !== id) {
    draft.voice = id;
    discardVoice();
  }
  inspector();
  if (id && draft.text.trim()) await ensureVoice();
}
function playVoice(audio, label) {
  const el = $("#audioPreview");
  if (!el) return;
  el.innerHTML = '<audio controls style="width:100%" src="/api/voice/' + esc(audio.id) +
    '"></audio><small>' + esc(label) + " · " + sec(audio.duration) + "</small>";
  el.querySelector("audio").play().catch(() => {});
}
async function previewTone(button) {
  const voice = narrationVoice(draft.voice);
  if (!voice) return;
  const text = voice.role === "personal_voice" || voice.locale.startsWith("zh") ? "你好，欢迎来到帧间。听听这句话的语气和停顿。"
    : voice.sample || "Welcome to Frame Studio.";
  button.disabled = true;
  button.textContent = "正在准备试听…";
  try {
    const sample = await api("/api/voice", {text, voice: voice.id});
    if (button.isConnected && view === "work" && draft.voice === voice.id)
      playVoice(sample, "音色试听 · " + voice.name);
  } finally {
    button.disabled = false;
    button.textContent = "短句试听音色";
  }
}
async function toggleVoice() {
  const audio = await ensureVoice();
  if (step === 2 && view === "work" && audio === draft.voiceData) playVoice(audio, audio.method);
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
      if (draft.job !== id) return;
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
    const invalidCut = draft.cutaways.findIndex(cut =>
      !findAsset(cut.insert) || cut.stop > timelineFrames());
    if (invalidCut !== -1) {
      await switchStep(3);
      editCut(invalidCut);
      const alert = $("#cutForm [role=alert]");
      if (alert) alert.textContent = "请重新选择素材，并确认镜头在当前配音范围内";
      return;
    }
    const missing = draft.lines.findIndex((line, i) =>
      needsInsert(line, lineLayout(line, i)) && baseVisible(i));
    if (missing !== -1) {
      await switchStep(3);
      document.querySelector(`[data-line="${missing}"] [data-lineprop="insert"]`)?.focus();
      throw Error("请为第 " + (missing + 1) + " 句选择补充素材或调整版式");
    }
    const cfg = { ...draft, voiceId: draft.voiceData.id };
    const j = await api("/api/jobs", cfg);
    updateJob(j);
    progressJob = j.id;
    if (draft.id === cfg.id && draft.voiceData?.id === cfg.voiceId) {
      draft.job = j.id;
      playingJob = j.id;
      save();
      setStep(5);
    }
    poll(j.id);
  } finally {
    busy = false;
    $("#produce").disabled = !!progressJob;
  }
}
async function switchStep(n) {
  if (n === 5 && current()?.status === "done" && mode !== "result") {
    await openFilm(current().id, false);
    return;
  }
  if (n === 1) await loadShots(draft.hosts[0]);
  if (n === 3) {
    await loadShots(draft.hosts[0]);
    if (draft.text.trim()) await ensureVoice();
  }
  setStep(n);
}
async function use(a) {
  if (a.kind === "audio") {
    setStep(2);
    await selectVoice(a.id);
    return;
  } else {
    await loadShots(a.id);
    setPrimaryHost(a.id);
    save();
  }
  alternative();
}
async function uploadFile(el) {
  const files = Array.from(el.files);
  if (!files.length) return;
  const errors = [];
  for (const [index, file] of files.entries()) {
    message("正在导入 " + (index + 1) + " / " + files.length + " · " + file.name);
    const form = new FormData();
    form.append("file", file);
    form.append("role", el.dataset.upload);
    try {
      session.assets.push(await api("/api/assets", form, true));
    } catch (err) {
      errors.push(file.name + "：" + err.message);
    }
  }
  if (view === "library") alternative();
  message("已导入 " + (files.length - errors.length) + " / " + files.length + " 份素材" +
    (errors.length ? "。" + errors.join("；") : ""));
}
function play() {
  $("#cutAudio").pause();
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
    if (!b) {
      const lane = e.target.closest("#tracks .wave, #tracks .cut-lane, #tracks .ruler");
      if (lane && !$("#cutTransport").hidden) {
        const bounds = lane.getBoundingClientRect();
        $("#cutAudio").currentTime = draft.voiceData.duration *
          Math.max(0, Math.min(1, (e.clientX - bounds.left) / bounds.width));
        updateCutHead();
      }
      return;
    }
    if (b.hasAttribute("data-engines")) {
      const list = items => '<ul class="model-list">' + items.map(item => {
        const ok = !item.missing.length;
        return '<li><div><b>' + esc(item.name) + '</b><small class="status ' + (ok ? '' : 'missing') +
          '">' + (ok ? '已就绪' : '缺依赖') + '</small></div><small>' + esc(item.purpose) + '</small>' +
          (ok ? '' : '<small class="missing">缺少 ' + esc(item.missing.join('、')) + '</small>') + '</li>';
      }).join('') + '</ul>';
      $("#dialogBody").innerHTML = '<h3>本地模型与引擎</h3><p class="hint">按本机安装的模型文件和运行依赖检查。</p>' +
        list(session.engine.models) + '<h4>系统语音与媒体工具</h4>' + list(session.engine.tools);
      $("#dialog").showModal();
      return;
    }
    if (b.hasAttribute("data-prepare-voice")) {
      await ensureVoice();
      return;
    }
    if (b.dataset.editReference) {
      const a = findAsset(b.dataset.editReference);
      $("#dialogBody").innerHTML = '<h3>核对参考录音与逐字稿</h3><form id="editTranscript" class="stack" data-profile="' + esc(a.id) + '">' +
        '<b>' + esc(a.name) + ' · ' + sec(a.duration) + '</b><audio controls aria-label="参考录音" src="' + mediaURL(a.id, 'reference') + '"></audio>' +
        '<label class="field"><span>录音中实际说出的内容</span><textarea name="transcript" maxlength="1500" required>' + esc(a.transcript) +
        '</textarea></label><small role="alert"></small><button class="primary" type="submit">保存逐字稿</button></form>';
      $("#dialog").showModal();
      return;
    }
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
      else showMaterialMode(b.dataset.mode);
      return;
    }
    if (b.dataset.aspect) {
      draft.aspect = b.dataset.aspect;
      save();
      showMaterialMode("framing");
      for (const button of document.querySelectorAll("button[data-aspect]")) {
        const selected = button.dataset.aspect === draft.aspect;
        button.classList.toggle("selected", selected);
        button.setAttribute("aria-pressed", selected);
      }
      return;
    }
    if (b.hasAttribute("data-add-cut") || b.dataset.editCut !== undefined) {
      editCut(b.hasAttribute("data-add-cut") ? -1 : Number(b.dataset.editCut));
      return;
    }
    if (b.id === "deleteCut") {
      draft.cutaways.splice(Number($("#cutForm").dataset.index), 1);
      finishCutEdit();
      return;
    }
    if (b.dataset.previewCut !== undefined || b.id === "previewEdit") {
      const cut = draft.cutaways[Number(b.dataset.previewCut)];
      const first = cut ? Math.max(0, cut.first - timelineFPS) : 0;
      const stop = cut ? Math.min(timelineFrames(), cut.stop + timelineFPS) : timelineFrames();
      await previewTimeline(first, stop);
      return;
    }
    if (b.dataset.cardLine !== undefined) {
      await previewCard(Number(b.dataset.cardLine));
      return;
    }
    if (b.dataset.jump !== undefined) {
      seek(+b.dataset.jump);
      if (!$("#cutTransport").hidden) $("#cutAudio").currentTime = Number(b.dataset.jump);
      return;
    }
    if (b.dataset.reviewSeek !== undefined) {
      $("#video").pause();
      $("#video").currentTime = Number(b.dataset.reviewSeek);
      updateClock();
      return;
    }
    if (b.dataset.editIssue) {
      editIssue(b.closest("fieldset").dataset.reviewJob, b.dataset.editIssue);
      return;
    }
    if (b.dataset.toggleInsert) {
      toggleInsert(b.dataset.toggleInsert);
      if (view === "library") document.querySelector('[data-toggle-insert="' + CSS.escape(b.dataset.toggleInsert) + '"]')?.focus();
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
      mode = "source";
      playingJob = null;
      resultTimeline = null;
      resultVoice = null;
      await restoreDraft();
      save();
      $("#dialog").close();
      setStep(2);
      prepMonitor();
      drawTracks();
      restoreTimeline();
      return;
    }
    switch (b.id) {
      case "addVoiceProfile":
        $("#dialogBody").innerHTML = `<h3>添加个人音色</h3><form id="voiceProfileForm" class="stack">
          <label class="field"><span>音色名称</span><input name="name" maxlength="60" required placeholder="例如 Gerry"></label>
          <label class="field"><span>参考录音</span><input name="file" type="file" accept=".wav,.mp3,.m4a,.aiff,.aac" required>
          <small>建议使用 10～20 秒清晰的单人讲话，避开背景音乐。</small></label>
          <label class="field"><span>录音逐字稿</span><textarea name="transcript" maxlength="1500" required placeholder="填写参考录音中实际说出的内容。"></textarea></label>
          <label class="field"><span>从文本文件填入逐字稿（可选）</span><input type="file" id="transcriptFile" accept=".txt,text/plain"></label>
          <small role="alert"></small><button class="primary" type="submit">保存音色</button></form>`;
        $("#dialog").showModal();
        break;
      case "produce":
        await generate();
        break;
      case "voiceBtn":
        await toggleVoice();
        break;
      case "toneBtn":
        await previewTone(b);
        break;
      case "next":
        await switchStep(step + 1);
        break;
      case "play":
        play();
        break;
      case "expand":
        if (document.fullscreenElement) await document.exitFullscreen();
        else await $("#monitorStage").requestFullscreen();
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
        clearTimeout(voiceLookupTimer);
        voiceRequest = null;
        voiceError = "";
        playingJob = null;
        resultTimeline = null;
        resultVoice = null;
        mode = "source";
        save();
        $("#dialog").close();
        setStep(0);
        prepMonitor();
        drawTracks();
        restoreTimeline();
        break;
      }
      case "addshot": {
        const a = primaryHost();
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
        const a = primaryHost();
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
  if (el.matches("#voiceProfileForm [name=transcript]")) {
    const file = el.form.querySelector("#transcriptFile");
    file.value = "";
    file.setCustomValidity("");
    el.form.querySelector("[role=alert]").textContent = "";
  }
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
      $("#toneBtn").hidden = !narrationVoice(draft.voice);
      message(draft.voice ? "文案已修改，将用所选系统声音重新配音" : "请为新文案选择或导入配音");
    }
    discardVoice();
    $("#count").textContent = el.value.length + " / 1500";
    $("#audioPreview").innerHTML = "";
    updateVoiceButton();
    voiceLookupTimer = setTimeout(restoreTimeline, 500);
  }
  if (el.id === "seek") seek((el.value / 1000) * duration());
});
document.addEventListener(
  "change",
  task(async (e) => {
    const el = e.target;
    if (el.matches("#cutForm [name=asset]")) {
      showCutPoster(el.value);
      return;
    }
    if (el.dataset.upload) {
      await uploadFile(el);
      return;
    }
    if (el.dataset.shotprop) {
      const shot = shotMap[draft.hosts[0]][+el.closest(".shot").dataset.index],
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
      const line = draft.lines[+el.closest(".lineRow").dataset.line];
      if (k === "insert") {
        line.insert = el.value;
        delete line.insertSpeaking;
      } else if (k === "insertSpeaking") {
        line.insertSpeaking = el.value === "speaker";
      } else {
        line[k] = ["start", "end"].includes(k) ? Number(el.value) : el.value;
      }
      save();
      if (k === "layout" || k === "insert") inspector();
      drawTracks();
      return;
    }
    if (el.dataset.reviewItem) {
      const id = el.closest("fieldset").dataset.reviewJob, key = el.dataset.reviewItem;
      const status = el.value;
      el.value = getJob(id).review?.[key]?.status || "pending";
      if (status === "issue") editIssue(id, key);
      else await saveReview(id, key, {status});
      return;
    }
    switch (el.id) {
      case "scriptSample":
        if (!el.value || el.value === draft.text) break;
        draft.text = el.value;
        if (!draft.voice || draft.voice === "demo-audio")
          draft.voice = defaultVoice(draft.text);
        discardVoice();
        inspector();
        restoreTimeline();
        break;
      case "mobileSteps":
        await switchStep(+el.value);
        break;
      case "voiceChoice":
        await selectVoice(el.value);
        break;
      case "transcriptFile": {
        const file = el.files[0];
        const form = el.form;
        const status = form.querySelector("[role=alert]");
        status.textContent = "";
        el.setCustomValidity("");
        if (!file) break;
        el.setCustomValidity("正在读取逐字稿");
        try {
          if (file.size > 10000) throw Error("逐字稿最多 1500 字");
          const bytes = await file.arrayBuffer();
          if (el.files[0] !== file || !form.isConnected) break;
          const text = new TextDecoder("utf-8", {fatal: true}).decode(bytes).trim();
          if (!text || text.includes("\0")) throw Error("请选择包含逐字稿的 UTF-8 文本文件");
          if (text.length > 1500) throw Error("逐字稿最多 1500 字");
          form.elements.transcript.value = text;
          el.setCustomValidity("");
        } catch (error) {
          if (el.files[0] !== file || !form.isConnected) break;
          const hint = error instanceof TypeError ? "无法按 UTF-8 读取逐字稿" : error.message;
          status.textContent = hint + "，请重新选文件或直接填写。";
          el.setCustomValidity(status.textContent);
        }
        break;
      }
      case "styleChoice":
        draft.style = el.value;
        save();
        inspector();
        drawTracks();
        break;
      case "subs":
        draft.subtitles = el.checked;
        save();
        showMaterialMode("framing");
        break;
      case "framing":
        draft.framing = el.value;
        save();
        showMaterialMode("framing");
        break;
      case "shift":
        draft.shift = Number(el.value);
        save();
        break;
    }
  }),
);
document.addEventListener("submit", async (event) => {
  const form = event.target;
  if (form.id === "editTranscript") {
    event.preventDefault();
    const button = form.querySelector("button");
    if (button.disabled) return;
    button.disabled = true;
    try {
      const a = findAsset(form.dataset.profile);
      const updated = await api("/api/assets/" + a.id + "/transcript", {transcript: form.elements.transcript.value});
      const changed = a.transcript !== updated.transcript;
      Object.assign(a, updated);
      if (changed && draft.voice === a.id) discardVoice();
      if (view === "library") alternative();
      if (view === "work") inspector();
      if (form.isConnected && $("#dialog").open) $("#dialog").close();
      message("参考录音逐字稿已保存");
    } catch (error) {
      form.querySelector("[role=alert]").textContent = error.message;
    } finally {
      button.disabled = false;
    }
    return;
  }
  if (form.id === "voiceProfileForm") {
    event.preventDefault();
    const button = form.querySelector("button");
    if (button.disabled) return;
    button.disabled = true;
    button.textContent = "正在保存…";
    const data = new FormData(form);
    data.set("role", "personal_voice");
    try {
      const profile = await api("/api/assets", data, true);
      session.assets.push(profile);
      if (form.isConnected && $("#dialog").open) $("#dialog").close();
      if (view === "library") alternative();
      message("个人音色已保存，可在「文案配音」中选择 " + profile.name);
    } catch (error) {
      form.querySelector("[role=alert]").textContent = error.message;
    } finally {
      button.textContent = "保存音色";
      button.disabled = false;
    }
    return;
  }
  if (form.id === "cutForm") {
    event.preventDefault();
    try { saveCut(form); }
    catch (error) { form.querySelector("[role=alert]").textContent = error.message; }
    return;
  }
  if (form.id !== "issueForm") return;
  event.preventDefault();
  const button = form.querySelector("button");
  button.disabled = true;
  try {
    await saveReview(form.dataset.job, form.dataset.item, {
      status: "issue", note: form.elements.note.value.trim(), time: Number(form.elements.time.value),
    });
    if (form.isConnected && $("#dialog").open) $("#dialog").close();
  } catch (error) {
    form.querySelector("[role=alert]").textContent = error.message;
  } finally {
    button.disabled = false;
  }
});
async function start() {
  $("#cutAudio").addEventListener("timeupdate", updateCutHead);
  $("#cutAudio").addEventListener("play", () => {
    $("#video").pause();
    stopStill();
    updateClock();
  });
  document
    .querySelectorAll("[data-icon]")
    .forEach((el) => (el.innerHTML = icon(el.dataset.icon)));
  session = await api("/api/session");
  try {
    draft = JSON.parse(localStorage.getItem("frame-studio-draft-v1"));
  } catch (e) {}
  if (!draft) draft = fresh();
  await importDraftReviews().catch(() => message("旧勾选暂未同步，刷新后会重试"));
  await restoreDraft();
  const engines = [...session.engine.models, ...session.engine.tools];
  const ready = engines.filter(item => !item.missing.length).length;
  $("#engineInfo").textContent = ready + " / " + engines.length + " 项就绪 · 查看";
  $("#engineDot").classList.toggle("off", ready !== engines.length);
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
  restoreTimeline();
}
start().catch((e) => message(e.message));

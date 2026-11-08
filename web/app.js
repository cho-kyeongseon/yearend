/* 연말정산 도우미 (정적 웹페이지 버전)
 * 내용 데이터: data/content.json (checklist.py · faq.py 에서 build_web.py 가 생성)
 * 검색 데이터: data/chunks.json (ingest.py 가 만든 자료 조각)
 * Python 버전(rag.py · bot.py · app.py)과 같은 규칙으로 동작한다.
 */
"use strict";

let C = null;          // content.json
let CHUNKS = [];       // chunks.json
let R = null;          // 검색기
let PAGES = new Map(); // "문서명|8쪽" -> 원문

const $ = (s) => document.querySelector(s);
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const nl = (s) => esc(s).replace(/\n/g, "<br>");
const reEsc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
const RESULT_ICON = { ok: "⭕", no: "❌", info: "ℹ️" };

/* ============================================================ 검색 (rag.py 와 동일) */
function tokenize(text) {
  const toks = [];
  // \p{Nd}: Python 정규식의 \d 처럼 유니코드 숫자(전각 숫자 등)도 숫자로 본다
  for (const w of text.toLowerCase().match(/[가-힣]+|[a-z]+|\p{Nd}+/gu) || []) {
    if (w[0] >= "가" && w[0] <= "힣" && w.length > 1) {
      for (let i = 0; i < w.length - 1; i++) toks.push(w.slice(i, i + 2));
    } else toks.push(w);
  }
  return toks;
}

function counter(arr) {
  const m = new Map();
  for (const t of arr) m.set(t, (m.get(t) || 0) + 1);
  return m;
}

class Retriever {
  constructor(chunks, k1 = 1.5, b = 0.75) {
    this.chunks = chunks; this.k1 = k1; this.b = b;
    this.postings = new Map(); this.lengths = [];
    chunks.forEach((c, i) => {
      const tf = counter(tokenize(c.source + " " + c.text));
      let len = 0;
      for (const [t, n] of tf) {
        len += n;
        if (!this.postings.has(t)) this.postings.set(t, []);
        this.postings.get(t).push([i, n]);
      }
      this.lengths.push(len);
    });
    this.avgdl = this.lengths.reduce((a, b) => a + b, 0) / Math.max(this.lengths.length, 1);
    const N = chunks.length;
    this.idf = new Map();
    for (const [t, p] of this.postings) this.idf.set(t, Math.log(1 + (N - p.length + 0.5) / (p.length + 0.5)));
  }
  search(query, k = 8) {
    const scores = new Map();
    for (const [t, qn] of counter(tokenize(query))) {
      const idf = this.idf.get(t);
      if (idf === undefined) continue;
      for (const [doc, tf] of this.postings.get(t)) {
        const norm = tf + this.k1 * (1 - this.b + this.b * this.lengths[doc] / this.avgdl);
        scores.set(doc, (scores.get(doc) || 0) + qn * idf * tf * (this.k1 + 1) / norm);
      }
    }
    return [...scores.entries()].sort((a, b) => b[1] - a[1]).slice(0, k)
      .map(([d, s]) => ({ ...this.chunks[d], score: Math.round(s * 100) / 100 }));
  }
}

/* ============================================================ 핵심 단어·발췌 (bot.py 와 동일) */
const TOP_K = 8, MIN_SCORE = 8.0;
const STOPWORDS = new Set(["뭐야", "뭐예요", "뭔가요", "무엇", "무엇인가요", "알려줘", "알려주세요", "어떻게", "어떤",
  "되나요", "돼", "되는지", "있어", "있나요", "있는지", "해줘", "해주세요", "궁금", "궁금해",
  "하나요", "하는지", "인가요", "건가요", "얼마", "얼마나", "언제", "누가", "요즘", "그럼"]);
const JOSA = /(으로|에서|에게|까지|부터|이랑|하고|이란|이면|려면|으면|은|는|이|가|을|를|에|의|도|로|와|과|만|요)$/;

function keywords(question) {
  const out = [];
  for (const w of question.match(/[가-힣]+|[A-Za-z]+|\p{Nd}+/gu) || []) {
    if (STOPWORDS.has(w)) continue;
    const stem = w.length > 2 ? w.replace(JOSA, "") : w;
    if (stem.length >= 2 && !STOPWORDS.has(stem) && !out.includes(stem)) out.push(stem);
  }
  return out;
}

function bestWindow(text, kws, width = 5) {
  const lines = text.split("\n").map((l) => l.trim()).filter(Boolean);
  if (lines.length <= width) return lines.join("\n");
  const q = new Set(tokenize(kws.join(" ")));
  const score = (ln) => {
    const toks = new Set(tokenize(ln));
    let s = 0;
    for (const t of q) if (toks.has(t)) s++;
    for (const k of kws) if (k) s += ln.split(k).length - 1;
    return s;
  };
  const scores = lines.map(score);
  let start = 0, best = -1;
  for (let i = 0; i <= lines.length - width; i++) {
    let s = 0; for (let j = i; j < i + width; j++) s += scores[j];
    if (s > best) { best = s; start = i; }
  }
  let peak = start;
  for (let i = start; i < start + width; i++) if (scores[i] > scores[peak]) peak = i;
  start = Math.min(Math.max(0, peak - Math.floor(width / 2)), lines.length - width);
  return lines.slice(start, start + width).join("\n");
}

function search(question) {
  const kws = keywords(question);
  const hits = R.search(kws.join(" ") || question, TOP_K * 2);
  const results = [], seen = new Set();
  for (const h of hits) {
    const key = h.source + "|" + h.loc;
    if (seen.has(key)) continue;
    seen.add(key);
    results.push({ ...h, snippet: bestWindow(h.text, kws) });
    if (results.length === TOP_K) break;
  }
  return { keywords: kws, found: results.length > 0 && results[0].score >= MIN_SCORE, results };
}

function highlight(text, kws) {
  const safe = esc(text);
  const words = [...new Set(kws.map(esc))].filter(Boolean).sort((a, b) => b.length - a.length);
  if (!words.length) return safe;
  return safe.replace(new RegExp(words.map(reEsc).join("|"), "g"), (m) => `<mark>${m}</mark>`);
}

/* ============================================================ 항목·FAQ 인식 (checklist.py · faq.py 와 동일) */
function matchItem(text) {
  let best = null, bestScore = 0;
  for (const [k, { words, weight }] of Object.entries(C.KEYWORDS)) {
    const s = words.filter((w) => text.includes(w)).length * weight;
    if (s > bestScore) { best = k; bestScore = s; }
  }
  return best;
}

function itemRefs(key) {
  const refs = [];
  for (const n of Object.values(C.ITEMS[key].nodes)) {
    if (n.result === "ok") for (const r of n.refs) if (!refs.some((x) => x[0] === r[0] && x[1] === r[1])) refs.push(r);
  }
  return refs;
}

function matchFaq(text) {
  const t = text.replace(/ /g, "").toLowerCase();
  let best = null, bg = 0, bl = 0;
  for (const f of C.FAQS) {
    const hits = f.keys.map((group) => Math.max(0, ...group.filter((w) => t.includes(w.replace(/ /g, "").toLowerCase())).map((w) => w.length)));
    if (hits.every((h) => h > 0)) {
      const g = hits.length, l = hits.reduce((a, b) => a + b, 0);
      if (g > bg || (g === bg && l > bl)) { best = f; bg = g; bl = l; }
    }
  }
  return best;
}

const faqByQ = (q) => C.FAQS.find((f) => f.q === q);
const refsText = (refs) => esc(refs.map(([d, p]) => `${C.DOC_TITLES[d]} ${p}쪽`).join(", "));
const pageText = (d, p) => PAGES.get(C.DOCS[d] + "|" + p + "쪽");

/* ============================================================ 탭 */
function showTab(name) {
  document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t.dataset.tab === name));
  document.querySelectorAll(".panel").forEach((p) => { p.hidden = p.id !== "panel-" + name; });
  if (name === "chat") scrollRoom();
  try { localStorage.setItem("tab", name); } catch (e) { /* 저장 안 돼도 무관 */ }
}

/* ============================================================ 체크리스트 */
const CL = { item: null, answers: [] };

function renderGroups() {
  $("#groups").innerHTML = C.GROUPS.map((g) => {
    const keys = Object.keys(C.ITEMS).filter((k) => C.ITEMS[k].group === g);
    return `<div class="grp">${esc(g)}</div><div class="items">` + keys.map((k) =>
      `<button class="item ${C.ITEMS[k].kind === "소득공제" ? "inc" : "tax"}" data-item="${k}">${esc(C.ITEMS[k].label)}</button>`).join("") + "</div>";
  }).join("");
  $("#groups").addEventListener("click", (e) => {
    const b = e.target.closest("[data-item]");
    if (b) pickItem(b.dataset.item);
  });
}

function pickItem(key) {
  CL.item = key; CL.answers = [];
  document.querySelectorAll(".item").forEach((b) => b.classList.toggle("sel", b.dataset.item === key));
  renderFlow();
  $("#flow .cl-head").scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderRefs(refs) {
  return "<p><b>근거 자료</b></p>" + refs.map(([d, p]) =>
    `<details><summary>📄 ${esc(C.DOC_TITLES[d])} ${p}쪽</summary><div class="hit-snip">${esc(pageText(d, p) || "(원문을 찾지 못했습니다)")}</div></details>`).join("");
}

function renderFlow() {
  const item = C.ITEMS[CL.item];
  const color = item.kind === "소득공제" ? "var(--green)" : "var(--blue)";
  let html = `<div class="cl-head" style="color:${color}">✔ ${esc(item.title)}</div>`;
  let nid = item.start, step = 0;
  while (item.nodes[nid].q !== undefined) {
    const n = item.nodes[nid];
    const chosen = CL.answers[step];
    html += `<div class="cl-q cl-mark"><b>Q${step + 1}.</b>${esc(n.q)}${n.hint ? `<div class="cl-hint">※ ${esc(n.hint)}</div>` : ""}</div>
      <div class="yn"><button class="${chosen === "yes" ? "chosen" : ""}" data-step="${step}" data-val="yes">네</button>
      <button class="${chosen === "no" ? "chosen" : ""}" data-step="${step}" data-val="no">아니오</button></div>`;
    if (!chosen) { $("#flow").innerHTML = html; return; }
    nid = n[chosen]; step++;
  }
  const r = item.nodes[nid];
  html += `<div class="cl-res cl-mark ${r.result}"><div class="t">${RESULT_ICON[r.result]} ${esc(r.title)}</div>${esc(r.text)}</div>`
    + renderRefs(r.refs) + `<button class="ghost" data-reset="1">↺ 처음부터 다시</button>`;
  $("#flow").innerHTML = html;
}

function onFlowClick(e) {
  const b = e.target.closest("button");
  if (!b || !CL.item) return;
  if (b.dataset.reset) { pickItem(CL.item); return; }
  if (b.dataset.val) {
    CL.answers = CL.answers.slice(0, +b.dataset.step).concat(b.dataset.val);
    renderFlow();
    const marks = document.querySelectorAll("#flow .cl-mark");
    marks[marks.length - 1].scrollIntoView({ behavior: "smooth", block: "center" });
  }
}

/* ============================================================ 자료 검색 */
const EXAMPLES = ["월세액 세액공제 요건", "중소기업 취업자 소득세 감면 기간", "2026년 개정세법 연말정산", "의료비 실손보험금"];

function renderSearch(q) {
  const box = $("#results");
  if (!q.trim()) { box.innerHTML = ""; return; }
  const r = search(q);
  let html = "";
  if (!r.found) {
    html += `<div class="warn">넣어 둔 자료에서 이 질문과 잘 맞는 내용을 찾지 못했습니다. 단어를 바꿔 다시 찾아보시거나, 국세청 홈택스·국세상담센터(☎126)에서 확인하세요.</div>`;
    if (!r.results.length) { box.innerHTML = html; return; }
    html += `<p class="muted">그나마 가까운 자료:</p>`;
  } else if (r.keywords.length) html += `<p class="muted">찾은 핵심 단어: ${esc(r.keywords.join(", "))}</p>`;
  const card = (h, i) => `<div class="hit-src">${i}. 📄 ${esc(h.source)} · ${esc(h.loc)}</div><div class="hit-snip">${highlight(h.snippet, r.keywords)}</div>`;
  r.results.slice(0, 3).forEach((h, i) => {
    html += card(h, i + 1) + `<details><summary>이 부분 전체 보기</summary><div class="hit-snip">${highlight(h.text, r.keywords)}</div></details>`;
  });
  if (r.results.length > 3) {
    html += `<details><summary>다른 관련 자료 ${r.results.length - 3}건</summary><div>` + r.results.slice(3).map((h, i) => card(h, i + 4)).join("") + "</div></details>";
  }
  box.innerHTML = html;
}

/* ============================================================ 상담하기 (카톡형) */
const BOT_NAME = "연말정산 도우미";
const GREET = /^(안녕|하이|헬로|hello|hi|ㅎㅇ|반가)/i;
const THANKS = /(고마|감사|땡큐|thx|ㄱㅅ)/i;
const GREETING = "안녕하세요! 연말정산 도우미예요 🧾\n궁금한 걸 편하게 물어봐 주세요.\n\n"
  + "예) \"부모님 부양가족 공제 조건이 뭐야?\"\n      \"피부과 비용도 공제돼?\"\n      \"월세도 공제돼?\"";
const DEFAULT_QR = [
  ["부모님 공제 조건", ["ask", "부모님 부양가족 공제 조건이 뭐야?"]],
  ["월세 세액공제", ["ask", "월세 세액공제 받을 수 있어?"]],
  ["의료비 공제", ["ask", "의료비 공제 기준 알려줘"]],
  ["❓ 자주 묻는 질문", ["faqlist"]],
];
const CHAT = { msgs: [], flow: null, qr: DEFAULT_QR };

function nowLabel() {
  const t = new Date(), h = t.getHours();
  return `${h < 12 ? "오전" : "오후"} ${h % 12 || 12}:${String(t.getMinutes()).padStart(2, "0")}`;
}
const say = (role, html) => CHAT.msgs.push({ role, html, time: nowLabel() });

function chatInit() {
  CHAT.msgs = []; CHAT.flow = null; CHAT.qr = DEFAULT_QR;
  say("bot", nl(GREETING));
  renderChat();
}

function saySnippets(result, n) {
  for (const h of result.results.slice(0, n)) {
    say("bot", `<div class="kk-snip-src">📄 ${esc(h.source)} · ${esc(h.loc)}</div>${highlight(h.snippet, result.keywords).replace(/\n/g, "<br>")}`);
  }
}

function saySummary(key) {
  say("bot", `<div class="kk-title">📌 ${esc(C.ITEMS[key].title)}</div>${nl(C.SUMMARY[key])}<div class="kk-src">근거: ${refsText(itemRefs(key))}</div>`);
}

function sayFaq(f) {
  const cases = (f.cases || []).map(([kind, lines]) =>
    `<div class="kk-case ${kind}"><div class="h">${C.CASE_LABELS[kind]}</div><ul>${lines.map((l) => `<li>${esc(l)}</li>`).join("")}</ul></div>`).join("");
  const note = f.note ? `<div class="kk-note">※ ${esc(f.note)}</div>` : "";
  say("bot", `<div class="kk-res ${f.result}"><div class="kk-title">${RESULT_ICON[f.result]} ${esc(f.title)}</div>${nl(f.text)}</div>${cases}${note}<div class="kk-src">근거: ${refsText(f.refs)}</div>`);
  let qr = [["📄 근거 원문", ["page", f.q]]];
  if (f.item) qr = qr.concat([["✅ 내 상황 확인", ["flow", f.item]], ["📌 요건 정리", ["summary", f.item]]]);
  CHAT.qr = qr.concat([["❓ 다른 질문", ["faqlist"]]]);
}

function sayPage(f) {
  const kws = keywords(f.q).concat(keywords(f.title), f.keys.flat());
  for (const [d, p] of f.refs.slice(0, 2)) {
    const body = pageText(d, p);
    if (body) say("bot", `<div class="kk-snip-src">📄 ${esc(C.DOC_TITLES[d])} ${p}쪽</div>${highlight(bestWindow(body, kws, 7), kws).replace(/\n/g, "<br>")}`);
  }
}

function reply(text) {
  const key = matchItem(text);
  if (!key && text.length < 20 && GREET.test(text)) {
    say("bot", nl("안녕하세요! 😊 어떤 공제가 궁금하세요?\n아래 버튼을 누르거나 편하게 물어봐 주세요.")); CHAT.qr = DEFAULT_QR; return;
  }
  if (!key && THANKS.test(text)) {
    say("bot", nl("천만에요! 또 궁금한 게 있으면 언제든 물어봐 주세요 🙌")); CHAT.qr = DEFAULT_QR; return;
  }
  const f = matchFaq(text);
  if (f) { sayFaq(f); return; }

  // 항목을 알아들었으면 항목 이름을 검색어에 보태서 엉뚱한 대목이 걸리지 않게 한다
  const result = search(key ? `${C.ITEMS[key].title} ${text}` : text);
  if (key) {
    saySummary(key);
    if (result.found) { say("bot", "관련된 자료 원문도 함께 보여 드릴게요 👇"); saySnippets(result, 2); }
    say("bot", nl("내 상황에 해당하는지 질문 몇 개로 확인해 볼까요?"));
    CHAT.qr = [["✅ 내 상황 확인", ["flow", key]]].concat(DEFAULT_QR.slice(0, 3));
  } else if (result.found) {
    say("bot", "자료에서 관련 내용을 찾았어요. 원문을 확인해 보세요 👇");
    saySnippets(result, 3);
    say("bot", nl("공제 항목 이름(예: 부모님 공제, 월세, 의료비)을 넣어 물어보시면\n요건을 정리해서 알려 드릴 수 있어요."));
    CHAT.qr = DEFAULT_QR;
  } else {
    say("bot", nl("죄송해요, 넣어 둔 자료에서 맞는 내용을 찾지 못했어요 😥\n다른 말로 바꿔 물어보시거나 국세상담센터(☎126)에 문의해 주세요."));
    CHAT.qr = DEFAULT_QR;
  }
}

function askNode() {
  const fl = CHAT.flow, item = C.ITEMS[fl.item], n = item.nodes[fl.node];
  if (n.q !== undefined) {
    say("bot", `<span class="kk-q">Q${fl.step}.</span> ${nl(n.q)}${n.hint ? `<div class="kk-hint">※ ${esc(n.hint)}</div>` : ""}`);
    CHAT.qr = [["네", ["ans", "yes"]], ["아니오", ["ans", "no"]], ["그만하기", ["stop"]]];
    return;
  }
  say("bot", `<div class="kk-res ${n.result}"><div class="kk-title">${RESULT_ICON[n.result]} ${esc(n.title)}</div>${nl(n.text)}</div><div class="kk-src">근거: ${refsText(n.refs)}</div>`);
  say("bot", nl("다른 것도 궁금하면 편하게 물어봐 주세요!"));
  CHAT.qr = [["🔁 다시 확인하기", ["flow", fl.item]]].concat(DEFAULT_QR.slice(0, 3));
  CHAT.flow = null;
}

function onUserText(text) {
  text = text.trim();
  if (!text) return;
  say("me", nl(text));
  CHAT.flow = null; // 직접 입력하면 진행 중인 확인은 멈춤
  reply(text);
  renderChat();
}

function onQr(label, action) {
  const kind = action[0];
  if (kind === "ask") { onUserText(action[1]); return; }
  say("me", nl(label));
  if (kind === "flow") {
    const key = action[1];
    CHAT.flow = { item: key, node: C.ITEMS[key].start, step: 1 };
    say("bot", nl(`좋아요! '${C.ITEMS[key].title}' 요건을 하나씩 확인해 볼게요.`));
    askNode();
  } else if (kind === "ans" && CHAT.flow) {
    const fl = CHAT.flow;
    fl.node = C.ITEMS[fl.item].nodes[fl.node][action[1]];
    fl.step++;
    askNode();
  } else if (kind === "stop") {
    CHAT.flow = null;
    say("bot", nl("네, 확인을 멈출게요. 궁금한 걸 편하게 물어봐 주세요!"));
    CHAT.qr = DEFAULT_QR;
  } else if (kind === "page") {
    say("bot", "근거가 된 자료 원문이에요 👇");
    sayPage(faqByQ(action[1]));
    const rest = CHAT.qr.filter((b) => b[1][0] !== "page");
    CHAT.qr = rest.length ? rest : DEFAULT_QR;
  } else if (kind === "summary") {
    saySummary(action[1]);
    CHAT.qr = [["✅ 내 상황 확인", ["flow", action[1]]]].concat(DEFAULT_QR.slice(0, 3));
  } else if (kind === "faqlist") {
    say("bot", nl("많이 물어보시는 질문이에요. 궁금한 걸 눌러 보세요 👇\n이 밖에도 미용·성형, 치과, 안경, 한의원, 라식, 건강검진, 산후조리원, 교복, 대학원, 확정일자 등을 물어보실 수 있어요."));
    CHAT.qr = C.POPULAR.map(([lb, q]) => [lb, ["ask", q]]);
  }
  renderChat();
}

function renderChat() {
  const m = CHAT.msgs, t = new Date();
  let html = `<div class="kk-day"><span>${t.getFullYear()}년 ${t.getMonth() + 1}월 ${t.getDate()}일</span></div>`;
  m.forEach((msg, i) => {
    const prev = i ? m[i - 1].role : null, next = i + 1 < m.length ? m[i + 1].role : null;
    const start = prev !== msg.role;
    const time = next !== msg.role ? `<span class="kk-time">${msg.time}</span>` : "";
    const bubble = `<div class="kk-bubble">${msg.html}</div>`;
    if (msg.role === "me") html += `<div class="kk-row me${start ? " start" : ""}"><div class="kk-line">${time}${bubble}</div></div>`;
    else if (start) html += `<div class="kk-row bot start"><div class="kk-ava">🧾</div><div><div class="kk-name">${BOT_NAME}</div><div class="kk-line">${bubble}${time}</div></div></div>`;
    else html += `<div class="kk-row bot cont"><div class="kk-line">${bubble}${time}</div></div>`;
  });
  $("#room").innerHTML = html;
  $("#qr").innerHTML = CHAT.qr.map(([lb], i) => `<button data-qr="${i}">${esc(lb)}</button>`).join("");
  scrollRoom();
}

function scrollRoom() { const r = $("#room"); r.scrollTop = r.scrollHeight; }

/* ============================================================ 시작 */
async function main() {
  const [content, chunks] = await Promise.all([
    fetch("data/content.json").then((r) => r.json()),
    fetch("data/chunks.json").then((r) => r.json()),
  ]);
  C = content; CHUNKS = chunks;
  R = new Retriever(CHUNKS);
  for (const c of CHUNKS) {
    const k = c.source + "|" + c.loc;
    PAGES.set(k, PAGES.has(k) ? PAGES.get(k) + "\n" + c.text : c.text);
  }

  // 탭
  document.querySelectorAll(".tab").forEach((t) => t.addEventListener("click", () => showTab(t.dataset.tab)));
  // 체크리스트
  renderGroups();
  $("#flow").addEventListener("click", onFlowClick);
  // 검색
  $("#examples").innerHTML = EXAMPLES.map((e) => `<button type="button">${esc(e)}</button>`).join("");
  $("#examples").addEventListener("click", (e) => {
    const b = e.target.closest("button"); if (!b) return;
    $("#search-input").value = b.textContent; renderSearch(b.textContent);
  });
  $("#search-form").addEventListener("submit", (e) => { e.preventDefault(); renderSearch($("#search-input").value); });
  // 상담
  $("#chat-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const v = $("#chat-input").value; $("#chat-input").value = ""; onUserText(v);
  });
  $("#qr").addEventListener("click", (e) => {
    const b = e.target.closest("[data-qr]"); if (!b) return;
    const [label, action] = CHAT.qr[+b.dataset.qr]; onQr(label, action);
  });
  $("#chat-reset").addEventListener("click", chatInit);
  chatInit();

  $("#loading").hidden = true;
  let tab = "chat";
  try { tab = localStorage.getItem("tab") || "chat"; } catch (e) { /* 무관 */ }
  showTab(["chat", "check", "search"].includes(tab) ? tab : "chat");
}

main().catch((err) => {
  $("#loading").textContent = "자료를 불러오지 못했어요. 페이지를 새로고침해 주세요. (" + err.message + ")";
});

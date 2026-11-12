"""연말정산 도우미 웹 화면 (외부 AI 호출 없음).

- 체크리스트: 항목을 고르면 네/아니오 질문을 따라가며 공제 가능 여부를 판단 (checklist.py)
- 자료 검색: 넣어 둔 자료에서 관련 대목을 찾아 보여줌 (bot.py)

실행:  .venv\\Scripts\\streamlit.exe run app.py
"""
import html
import json
import re
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components

from bot import INDEX_READY, _best_window, keywords, search
from checklist import DOC_TITLES, DOCS, GROUPS, ITEMS, SUMMARY, item_refs, match_item
from faq import CASE_LABELS, POPULAR, faq_by_question, match_faq
from rag import INDEX_FILE

GREEN, BLUE = "#0b9446", "#2c4fa3"

st.set_page_config(page_title="연말정산 도우미", page_icon="🧾", layout="centered")

# 항목 버튼 색: 소득공제 초록, 세액공제 파랑 (st-key-<key> 클래스로 지정)
item_css = "\n".join(
    f".st-key-item_{k} button {{background:{GREEN if v['kind'] == '소득공제' else BLUE};"
    f"color:#fff;border:none;font-weight:600;min-height:2.8rem}}"
    f".st-key-item_{k} button:hover, .st-key-item_{k} button:focus, .st-key-item_{k} button:active"
    f" {{background:{GREEN if v['kind'] == '소득공제' else BLUE};filter:brightness(1.12);color:#fff}}"
    f".st-key-item_{k} button p {{white-space:normal;line-height:1.3}}"
    for k, v in ITEMS.items()
)
st.markdown(
    f"""<style>
    {item_css}
    .legend span {{display:inline-flex;align-items:center;margin-right:1rem}}
    .legend i {{width:14px;height:14px;border-radius:50%;display:inline-block;margin-right:.35rem}}
    .grp {{font-weight:700;padding-top:.7rem;text-align:center}}
    .cl-head {{font-size:1.25rem;font-weight:700;margin:.3rem 0 .6rem}}
    .cl-q {{background:rgba(128,128,128,.08);border-radius:10px;padding:.7rem .9rem;margin-top:.4rem}}
    .cl-q b {{color:#e07b00;margin-right:.35rem}}
    .cl-hint {{font-size:.85rem;opacity:.75;margin-top:.25rem}}
    .cl-res {{border-radius:10px;padding:.9rem 1rem;margin-top:.6rem;border:2px solid}}
    .cl-res.ok {{border-color:{GREEN};background:rgba(11,148,70,.07)}}
    .cl-res.no {{border-color:#c62828;background:rgba(198,40,40,.06)}}
    .cl-res.info {{border-color:{BLUE};background:rgba(44,79,163,.07)}}
    .cl-res .t {{font-size:1.1rem;font-weight:700;margin-bottom:.35rem}}
    .hit-src {{font-weight:600;margin-bottom:.25rem}}
    .hit-snip {{white-space:pre-wrap;line-height:1.6;padding:.6rem .8rem;
               border-left:3px solid #f0a020;background:rgba(240,160,32,.08);border-radius:4px}}
    .hit-snip mark {{background:#ffe08a;color:inherit;padding:0 2px;border-radius:2px}}

    /* ---- 상담하기 (카카오톡 스타일) ---- */
    .kk-room {{background:#b2c7da;border-radius:14px;padding:14px 12px 18px;height:540px;overflow-y:auto}}
    .kk-day {{text-align:center;margin:2px 0 10px}}
    .kk-day span {{background:rgba(0,0,0,.18);color:#fff;font-size:.74rem;padding:3px 12px;border-radius:12px}}
    .kk-row {{display:flex;align-items:flex-start;margin:3px 0}}
    .kk-row.start {{margin-top:12px}}
    .kk-row.bot {{gap:8px}}
    .kk-row.bot.cont {{padding-left:48px}}
    .kk-row.me {{justify-content:flex-end}}
    .kk-ava {{width:40px;height:40px;border-radius:15px;background:#fff;display:flex;align-items:center;
              justify-content:center;font-size:21px;flex:none}}
    .kk-name {{font-size:.78rem;color:#2b2b2b;margin:0 0 4px 2px}}
    .kk-line {{display:flex;align-items:flex-end;gap:5px}}
    .kk-bubble {{max-width:min(480px,74vw);padding:8px 12px;border-radius:15px;font-size:.92rem;line-height:1.55;
                 color:#111;word-break:keep-all;overflow-wrap:anywhere}}
    .bot .kk-bubble {{background:#fff;border-top-left-radius:4px}}
    .me .kk-bubble {{background:#fee500;border-top-right-radius:4px}}
    .kk-time {{font-size:.68rem;color:#4a5560;white-space:nowrap}}
    .kk-title {{font-weight:700;margin-bottom:4px}}
    .kk-src {{margin-top:7px;font-size:.74rem;color:#777}}
    .kk-snip-src {{font-size:.75rem;color:#555;font-weight:600;margin-bottom:3px}}
    .kk-bubble mark {{background:#ffe08a;color:inherit;padding:0 2px;border-radius:2px}}
    .kk-q {{color:#e07b00;font-weight:700}}
    .kk-hint {{font-size:.8rem;color:#777;margin-top:4px}}
    .kk-res {{border-left:4px solid;padding-left:8px}}
    .kk-res.ok {{border-color:{GREEN}}} .kk-res.no {{border-color:#c62828}} .kk-res.info {{border-color:{BLUE}}}
    .kk-case {{margin-top:8px;padding:7px 10px;border-radius:9px}}
    .kk-case .h {{font-weight:700;font-size:.86rem;margin-bottom:2px}}
    .kk-case ul {{margin:0;padding-left:1.1em}} .kk-case li {{margin:2px 0}}
    .kk-case.ok {{background:#e8f5ec}} .kk-case.ok .h {{color:{GREEN}}}
    .kk-case.no {{background:#fdecec}} .kk-case.no .h {{color:#c62828}}
    .kk-case.check {{background:#fff6dd}} .kk-case.check .h {{color:#a86a00}}
    .kk-case.tip {{background:#eaf0fb}} .kk-case.tip .h {{color:{BLUE}}}
    .kk-note {{margin-top:7px;font-size:.76rem;color:#8a6d00}}
    .st-key-qr_box button {{border-radius:18px;background:#fff;border:1px solid #c9d3dc;color:#222;font-size:.85rem}}
    .st-key-qr_box button:hover {{border-color:#e0b800;color:#222}}
    .st-key-chat_send button {{background:#fee500;color:#111;border:none;font-weight:700}}
    .st-key-chat_send button:hover {{background:#f5d800;color:#111}}
    </style>""",
    unsafe_allow_html=True,
)

st.title("🧾 연말정산 도우미")
st.caption("국세청 2025년 귀속 연말정산 안내 자료를 근거로 합니다. 일반적인 안내이며 세무 자문이 아닙니다. "
           "최종 판단은 회사 담당자나 국세상담센터(☎126)에 확인하세요.")

if not INDEX_READY:
    st.error("검색 인덱스가 없습니다. 먼저 `.venv\\Scripts\\python.exe ingest.py`를 실행하세요.")
    st.stop()


@st.cache_data
def page_texts() -> dict:
    """(문서명, '8쪽') -> 그 쪽의 원문."""
    pages: dict = {}
    for c in json.loads(INDEX_FILE.read_text(encoding="utf-8")):
        pages.setdefault((c["source"], c["loc"]), []).append(c["text"])
    return {k: "\n".join(v) for k, v in pages.items()}


def run_js(body: str) -> None:
    """화면(부모 문서)에서 자바스크립트를 실행한다. 매번 다시 실행되도록 번호를 붙인다."""
    st.session_state.js_n = st.session_state.get("js_n", 0) + 1
    components.html(
        f"<script>/* {st.session_state.js_n} */ const doc = window.parent.document;"
        f"setTimeout(() => {{ {body} }}, 250);</script>",
        height=0,
    )


def scroll_to(selector: str, block: str = "start") -> None:
    run_js(f"const els = doc.querySelectorAll('{selector}');"
           f"if (els.length) els[els.length - 1].scrollIntoView({{behavior: 'smooth', block: '{block}'}});")


# ======================================================================== 체크리스트
def pick_item(key: str) -> None:
    st.session_state.cl_item = key
    st.session_state.cl_answers = []
    st.session_state.cl_scroll = "head"


def answer(i: int, val: str) -> None:
    st.session_state.cl_answers = st.session_state.cl_answers[:i] + [val]
    st.session_state.cl_scroll = "last"


def render_refs(refs) -> None:
    texts = page_texts()
    st.markdown("**근거 자료**")
    for doc, page in refs:
        with st.expander(f"📄 {DOC_TITLES[doc]} {page}쪽"):
            body = texts.get((DOCS[doc], f"{page}쪽"), "(원문을 찾지 못했습니다)")
            st.markdown(f'<div class="hit-snip">{html.escape(body)}</div>', unsafe_allow_html=True)


def render_flow(key: str) -> None:
    flag = st.session_state.pop("cl_scroll", None)
    if flag == "head":
        scroll_to(".cl-head")
    elif flag == "last":
        scroll_to(".cl-mark", "center")
    _render_flow(key)


def _render_flow(key: str) -> None:
    item = ITEMS[key]
    nodes, answers = item["nodes"], st.session_state.cl_answers
    color = GREEN if item["kind"] == "소득공제" else BLUE
    st.markdown(f'<div class="cl-head" style="color:{color}">✔ {item["title"]}</div>', unsafe_allow_html=True)

    nid, step = item["start"], 0
    while "q" in nodes[nid]:
        node = nodes[nid]
        hint = f'<div class="cl-hint">※ {html.escape(node["hint"])}</div>' if node["hint"] else ""
        st.markdown(f'<div class="cl-q cl-mark"><b>Q{step + 1}.</b>{html.escape(node["q"])}{hint}</div>',
                    unsafe_allow_html=True)
        chosen = answers[step] if step < len(answers) else None
        c1, c2, _ = st.columns([1, 1, 3])
        c1.button("네", key=f"{key}_{step}_y", use_container_width=True,
                  type="primary" if chosen == "yes" else "secondary", on_click=answer, args=(step, "yes"))
        c2.button("아니오", key=f"{key}_{step}_n", use_container_width=True,
                  type="primary" if chosen == "no" else "secondary", on_click=answer, args=(step, "no"))
        if chosen is None:
            return  # 아직 답하지 않은 질문에서 멈춤
        nid, step = node[chosen], step + 1

    res = nodes[nid]
    icon = {"ok": "⭕", "no": "❌", "info": "ℹ️"}[res["result"]]
    st.markdown(f'<div class="cl-res cl-mark {res["result"]}"><div class="t">{icon} {html.escape(res["title"])}</div>'
                f'{html.escape(res["text"])}</div>', unsafe_allow_html=True)
    render_refs(res["refs"])
    st.button("↺ 처음부터 다시", key=f"{key}_reset", on_click=pick_item, args=(key,))


def checklist_tab() -> None:
    st.markdown(f'<div class="legend">범례 : <span><i style="background:{GREEN}"></i>소득공제항목</span>'
                f'<span><i style="background:{BLUE}"></i>세액공제항목</span></div>', unsafe_allow_html=True)
    st.write("")
    for group in GROUPS:
        keys = [k for k, v in ITEMS.items() if v["group"] == group]
        g, body = st.columns([1, 5])
        g.markdown(f'<div class="grp">{group}</div>', unsafe_allow_html=True)
        for row in range(0, len(keys), 3):
            cols = body.columns(3)
            for col, k in zip(cols, keys[row : row + 3]):
                col.button(ITEMS[k]["label"], key=f"item_{k}", use_container_width=True,
                           on_click=pick_item, args=(k,))
    st.caption("질문이 많은 항목 위주로 만들었으며, 모든 공제 항목을 다루지는 않습니다.")
    st.divider()

    key = st.session_state.get("cl_item")
    if key:
        render_flow(key)
    else:
        st.info("위에서 확인하고 싶은 항목을 눌러 보세요. 질문에 '네/아니오'로 답하면 공제 가능 여부를 알려 드립니다.")


# ======================================================================== 자료 검색
EXAMPLES = ["월세액 세액공제 요건", "중소기업 취업자 소득세 감면 기간", "2026년 개정세법 연말정산", "의료비 실손보험금"]


def highlight(text: str, kws: list[str]) -> str:
    safe = html.escape(text)
    words = sorted({html.escape(k) for k in kws}, key=len, reverse=True)
    if not words:
        return safe
    return re.sub("|".join(map(re.escape, words)), lambda m: f"<mark>{m.group(0)}</mark>", safe)


def render_search(result: dict) -> None:
    kws, items = result["keywords"], result["results"]
    if not result["found"]:
        st.warning("넣어 둔 자료에서 이 질문과 잘 맞는 내용을 찾지 못했습니다. "
                   "단어를 바꿔 다시 찾아보시거나, 국세청 홈택스·국세상담센터(☎126)에서 확인하세요.")
        if not items:
            return
        st.caption("그나마 가까운 자료:")
    elif kws:
        st.caption("찾은 핵심 단어: " + ", ".join(kws))
    for i, h in enumerate(items, 1):
        if i == 4:
            more = st.expander(f"다른 관련 자료 {len(items) - 3}건")
        box = more if i >= 4 else st.container()
        box.markdown(f'<div class="hit-src">{i}. 📄 {html.escape(h["source"])} · {h["loc"]}</div>'
                     f'<div class="hit-snip">{highlight(h["snippet"], kws)}</div>', unsafe_allow_html=True)
        if i < 4:
            with st.expander("이 부분 전체 보기"):
                st.markdown(f'<div class="hit-snip">{highlight(h["text"], kws)}</div>', unsafe_allow_html=True)


def set_query(q: str) -> None:
    st.session_state.search_q = q


def search_tab() -> None:
    st.caption("체크리스트에 없는 내용은 여기서 자료 원문을 찾아보세요. 짧은 핵심 단어로 찾을수록 정확합니다.")
    cols = st.columns(len(EXAMPLES))
    for col, ex in zip(cols, EXAMPLES):
        col.button(ex, key=f"ex_{ex}", use_container_width=True, on_click=set_query, args=(ex,))
    q = st.text_input("검색어", key="search_q", placeholder="예) 교육비 대학원, 부양가족 중복공제")
    if q.strip():
        render_search(search(q))


# ======================================================================== 상담하기 (카톡형 채팅)
BOT_NAME = "연말정산 도우미"
GREET = re.compile(r"^(안녕|하이|헬로|hello|hi|ㅎㅇ|반가)", re.I)
THANKS = re.compile(r"(고마|감사|땡큐|thx|ㄱㅅ)", re.I)
GREETING = ("안녕하세요! 연말정산 도우미예요 🧾\n궁금한 걸 편하게 물어봐 주세요.\n\n"
            "예) \"부모님 부양가족 공제 조건이 뭐야?\"\n      \"미용 목적 시술도 공제돼?\"\n      \"월세도 공제돼?\"")
DEFAULT_QR = [
    ("부모님 공제 조건", ("ask", "부모님 부양가족 공제 조건이 뭐야?")),
    ("월세 세액공제", ("ask", "월세 세액공제 받을 수 있어?")),
    ("의료비 공제", ("ask", "의료비 공제 기준 알려줘")),
    ("❓ 자주 묻는 질문", ("faqlist",)),
]
RESULT_ICON = {"ok": "⭕", "no": "❌", "info": "ℹ️"}


def now_label() -> str:
    t = datetime.now()
    return f"{'오전' if t.hour < 12 else '오후'} {t.hour % 12 or 12}:{t.minute:02d}"


def nl(text: str) -> str:
    return html.escape(text).replace("\n", "<br>")


def say(role: str, body: str) -> None:
    st.session_state.chat.append({"role": role, "html": body, "time": now_label()})


def chat_init(force: bool = False) -> None:
    if force or "chat" not in st.session_state:
        st.session_state.chat = []
        st.session_state.chat_flow = None
        st.session_state.chat_qr = DEFAULT_QR
        say("bot", nl(GREETING))


def say_snippets(result: dict, n: int) -> None:
    for h in result["results"][:n]:
        say("bot", f'<div class="kk-snip-src">📄 {html.escape(h["source"])} · {h["loc"]}</div>'
                   f'{highlight(h["snippet"], result["keywords"]).replace(chr(10), "<br>")}')


def refs_text(refs) -> str:
    return html.escape(", ".join(f"{DOC_TITLES[d]} {p}쪽" for d, p in refs))


def say_summary(key: str) -> None:
    say("bot", f'<div class="kk-title">📌 {html.escape(ITEMS[key]["title"])}</div>{nl(SUMMARY[key])}'
               f'<div class="kk-src">근거: {refs_text(item_refs(key))}</div>')


def say_faq(f: dict) -> None:
    cases = "".join(
        f'<div class="kk-case {kind}"><div class="h">{CASE_LABELS[kind]}</div><ul>'
        + "".join(f"<li>{html.escape(line)}</li>" for line in lines) + "</ul></div>"
        for kind, lines in f.get("cases", [])
    )
    note = f'<div class="kk-note">※ {html.escape(f["note"])}</div>' if f.get("note") else ""
    say("bot", f'<div class="kk-res {f["result"]}"><div class="kk-title">{RESULT_ICON[f["result"]]} '
               f'{html.escape(f["title"])}</div>{nl(f["text"])}</div>{cases}{note}'
               f'<div class="kk-src">근거: {refs_text(f["refs"])}</div>')
    qr = [("📄 근거 원문", ("page", f["q"]))]
    if f["item"]:
        qr += [("✅ 내 상황 확인", ("flow", f["item"])), ("📌 요건 정리", ("summary", f["item"]))]
    st.session_state.chat_qr = qr + [("❓ 다른 질문", ("faqlist",))]


def say_page(f: dict) -> None:
    """FAQ 근거 쪽의 원문에서 질문과 가장 관련 있는 부분을 보여준다."""
    texts = page_texts()
    kws = keywords(f["q"]) + keywords(f["title"]) + [w for group in f["keys"] for w in group]
    for d, p in f["refs"][:2]:
        body = texts.get((DOCS[d], f"{p}쪽"))
        if body:
            say("bot", f'<div class="kk-snip-src">📄 {DOC_TITLES[d]} {p}쪽</div>'
                       f'{highlight(_best_window(body, kws, width=7), kws).replace(chr(10), "<br>")}')


def reply(text: str) -> None:
    key = match_item(text)
    if key is None and len(text) < 20 and GREET.search(text):
        say("bot", nl("안녕하세요! 😊 어떤 공제가 궁금하세요?\n아래 버튼을 누르거나 편하게 물어봐 주세요."))
        st.session_state.chat_qr = DEFAULT_QR
        return
    if key is None and THANKS.search(text):
        say("bot", nl("천만에요! 또 궁금한 게 있으면 언제든 물어봐 주세요 🙌"))
        st.session_state.chat_qr = DEFAULT_QR
        return

    faq = match_faq(text)
    if faq:
        say_faq(faq)
        return

    # 항목을 알아들었으면 항목 이름을 검색어에 보태서 엉뚱한 대목이 걸리지 않게 한다
    result = search(f"{ITEMS[key]['title']} {text}" if key else text)
    if key:
        say_summary(key)
        if result["found"]:
            say("bot", "관련된 자료 원문도 함께 보여 드릴게요 👇")
            say_snippets(result, 2)
        say("bot", nl("내 상황에 해당하는지 질문 몇 개로 확인해 볼까요?"))
        st.session_state.chat_qr = [("✅ 내 상황 확인", ("flow", key))] + DEFAULT_QR[:3]
    elif result["found"]:
        say("bot", "자료에서 관련 내용을 찾았어요. 원문을 확인해 보세요 👇")
        say_snippets(result, 3)
        say("bot", nl("공제 항목 이름(예: 부모님 공제, 월세, 의료비)을 넣어 물어보시면\n요건을 정리해서 알려 드릴 수 있어요."))
        st.session_state.chat_qr = DEFAULT_QR
    else:
        say("bot", nl("죄송해요, 넣어 둔 자료에서 맞는 내용을 찾지 못했어요 😥\n"
                      "다른 말로 바꿔 물어보시거나 국세상담센터(☎126)에 문의해 주세요."))
        st.session_state.chat_qr = DEFAULT_QR


def ask_node() -> None:
    """진행 중인 확인 흐름의 현재 노드(질문 또는 결과)를 말풍선으로 보낸다."""
    flow = st.session_state.chat_flow
    item = ITEMS[flow["item"]]
    node = item["nodes"][flow["node"]]
    if "q" in node:
        hint = f'<div class="kk-hint">※ {html.escape(node["hint"])}</div>' if node["hint"] else ""
        say("bot", f'<span class="kk-q">Q{flow["step"]}.</span> {nl(node["q"])}{hint}')
        st.session_state.chat_qr = [("네", ("ans", "yes")), ("아니오", ("ans", "no")), ("그만하기", ("stop",))]
        return
    icon = {"ok": "⭕", "no": "❌", "info": "ℹ️"}[node["result"]]
    refs = ", ".join(f"{DOC_TITLES[d]} {p}쪽" for d, p in node["refs"])
    say("bot", f'<div class="kk-res {node["result"]}"><div class="kk-title">{icon} {html.escape(node["title"])}</div>'
               f'{nl(node["text"])}</div><div class="kk-src">근거: {html.escape(refs)}</div>')
    say("bot", nl("다른 것도 궁금하면 편하게 물어봐 주세요!"))
    st.session_state.chat_flow = None
    st.session_state.chat_qr = [("🔁 다시 확인하기", ("flow", flow["item"]))] + DEFAULT_QR[:3]


def on_qr(label: str, action: tuple) -> None:
    kind = action[0]
    if kind == "ask":
        on_user_text(action[1])
        return
    say("me", nl(label))
    if kind == "flow":
        key = action[1]
        st.session_state.chat_flow = {"item": key, "node": ITEMS[key]["start"], "step": 1}
        say("bot", nl(f"좋아요! '{ITEMS[key]['title']}' 요건을 하나씩 확인해 볼게요."))
        ask_node()
    elif kind == "ans" and st.session_state.chat_flow:
        flow = st.session_state.chat_flow
        flow["node"] = ITEMS[flow["item"]]["nodes"][flow["node"]][action[1]]
        flow["step"] += 1
        ask_node()
    elif kind == "stop":
        st.session_state.chat_flow = None
        say("bot", nl("네, 확인을 멈출게요. 궁금한 걸 편하게 물어봐 주세요!"))
        st.session_state.chat_qr = DEFAULT_QR
    elif kind == "page":
        f = faq_by_question(action[1])
        say("bot", "근거가 된 자료 원문이에요 👇")
        say_page(f)
        rest = [b for b in st.session_state.chat_qr if b[1][0] != "page"]
        st.session_state.chat_qr = rest or DEFAULT_QR
    elif kind == "summary":
        say_summary(action[1])
        st.session_state.chat_qr = [("✅ 내 상황 확인", ("flow", action[1]))] + DEFAULT_QR[:3]
    elif kind == "faqlist":
        say("bot", nl("많이 물어보시는 질문이에요. 궁금한 걸 눌러 보세요 👇\n"
                      "이 밖에도 미용·성형, 치과, 안경, 한의원, 라식, 건강검진, 산후조리원, 교복, 대학원, "
                      "확정일자 등을 물어보실 수 있어요."))
        st.session_state.chat_qr = [(label, ("ask", q)) for label, q in POPULAR]


def on_user_text(text: str) -> None:
    text = text.strip()
    if not text:
        return
    say("me", nl(text))
    st.session_state.chat_flow = None  # 직접 입력하면 진행 중인 확인은 멈춤
    reply(text)


def on_send() -> None:
    on_user_text(st.session_state.get("chat_text", ""))
    st.session_state.chat_text = ""


def render_room() -> None:
    msgs = st.session_state.chat
    t = datetime.now()
    rows = [f'<div class="kk-day"><span>{t.year}년 {t.month}월 {t.day}일</span></div>']
    for i, m in enumerate(msgs):
        prev = msgs[i - 1]["role"] if i else None
        nxt = msgs[i + 1]["role"] if i + 1 < len(msgs) else None
        start = prev != m["role"]
        time = f'<span class="kk-time">{m["time"]}</span>' if nxt != m["role"] else ""
        bubble = f'<div class="kk-bubble">{m["html"]}</div>'
        if m["role"] == "me":
            rows.append(f'<div class="kk-row me{" start" if start else ""}"><div class="kk-line">{time}{bubble}</div></div>')
        elif start:
            rows.append(f'<div class="kk-row bot start"><div class="kk-ava">🧾</div><div>'
                        f'<div class="kk-name">{BOT_NAME}</div><div class="kk-line">{bubble}{time}</div></div></div>')
        else:
            rows.append(f'<div class="kk-row bot cont"><div class="kk-line">{bubble}{time}</div></div>')
    st.markdown(f'<div class="kk-room">{"".join(rows)}</div>', unsafe_allow_html=True)
    run_js("doc.querySelectorAll('.kk-room').forEach(r => r.scrollTop = r.scrollHeight);")


def chat_tab() -> None:
    chat_init()
    render_room()
    with st.container(key="qr_box"):
        qr = st.session_state.chat_qr
        for col, (label, action) in zip(st.columns(len(qr)), qr):
            col.button(label, key=f"qr_{len(st.session_state.chat)}_{label}", use_container_width=True,
                       on_click=on_qr, args=(label, action))
    c1, c2 = st.columns([5, 1])
    c1.text_input("메시지", key="chat_text", placeholder="메시지를 입력하고 Enter 또는 전송을 누르세요",
                  label_visibility="collapsed", on_change=on_send)
    c2.button("전송", key="chat_send", use_container_width=True, on_click=on_send)
    st.button("🗑 대화 새로 시작", key="chat_reset", on_click=chat_init, args=(True,))


tab0, tab1, tab2 = st.tabs(["💬 상담하기", "✅ 공제 체크리스트", "🔎 자료 검색"])
with tab0:
    chat_tab()
with tab1:
    checklist_tab()
with tab2:
    search_tab()

"""ScholarShield AI - Streamlit app. Run: streamlit run app.py"""
import os
import pandas as pd
import streamlit as st
from datetime import date
try:
    from dotenv import load_dotenv; load_dotenv()
except ImportError:
    pass
import db, engine
from i18n import tr, RESP_LANGS
from demo_data import DEMO_OPPS, DEMO_PROFILE

st.set_page_config(page_title="ScholarShield AI", page_icon="🛡️", layout="wide")
db.init_db()
PAGES = ["Dashboard", "Analyze Opportunity", "Guided Demo", "My Profile", "Saved Opportunities",
         "Deadline Tracker", "Why ScholarShield?", "About ScholarShield"]
STATUSES = ["Saved", "Preparing", "Applied", "Deadline Passed"]
RISK_COLOR = {"LOW": "#15803d", "MEDIUM": "#b45309", "HIGH": "#b91c1c"}
DEMO_STEPS = ["Analyze an Opportunity", "Load a fictional scholarship", "AI extraction", "Eligibility match",
              "Risk indicators", "Application checklist", "Save the opportunity", "Deadline tracker"]
DEMO_KEY = list(DEMO_OPPS)[0]
st.session_state.setdefault("page", PAGES[0])
go = lambda p: st.session_state.update(page=p)
def start_demo():
    st.session_state.update(page="Guided Demo", demo_step=1, demo_res=None, demo_saved=False)

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif}
.hero{background:linear-gradient(135deg,#0b1220,#1e3a8a 70%,#0e7490);color:#fff;padding:2.4rem;border-radius:18px;margin-bottom:1rem}
.hero h1{margin:0;font-size:2.6rem;font-weight:800;color:#fff}.hero h3{font-weight:600;line-height:1.35;color:#e0f2fe}.hero p{color:#cbd5e1;font-size:1.05rem}
.card{border:1px solid #e2e8f0;border-radius:14px;padding:1.1rem;background:#fff;color:#0f172a;height:100%;box-shadow:0 1px 3px rgba(15,23,42,.06)}
.card h4{margin:.1rem 0 .4rem 0;color:#0f172a}.card p{margin:0;color:#475569}
.badge{color:#fff;padding:.25rem .8rem;border-radius:999px;font-weight:700;font-size:.85rem;display:inline-block}
.demo{background:#fef3c7;color:#92400e;padding:.1rem .5rem;border-radius:6px;font-size:.72rem;font-weight:700}
.mode{padding:.5rem .8rem;border-radius:8px;font-weight:600;font-size:.85rem;margin-bottom:.6rem}
.final{background:#eff6ff;border-left:4px solid #1d4ed8;padding:.6rem .9rem;border-radius:6px;color:#1e3a8a;font-size:.92rem}
.closing{background:#ecfdf5;border:1px solid #6ee7b7;color:#065f46;padding:1rem;border-radius:12px;font-weight:600;font-size:1.1rem}
</style>""", unsafe_allow_html=True)

def badge(level): return f"<span class='badge' style='background:{RISK_COLOR[level]}'>{tr("Risk level")}: {level}</span>"
def days_left(dl): return (pd.to_datetime(dl).date() - date.today()).days if dl else None
def eff_status(o): return "Deadline Passed" if (days_left(o.get("deadline")) or 0) < 0 and o.get("deadline") and o["status"] != "Applied" else o["status"]
def alert(d): return "⛔ " + tr("Passed") if d < 0 else "⚠️ " + tr("Soon") if d <= 14 else "🟢 OK"
def mode_banner():
    llm = bool(os.getenv("LLM_API_KEY"))
    bg, fg = ("#dcfce7", "#166534") if llm else ("#fef3c7", "#92400e")
    st.markdown(f"<div class='mode' style='background:{bg};color:{fg}'>{tr(engine.MODE_LLM if llm else engine.MODE_DEMO)}</div>", unsafe_allow_html=True)
def card(col, title, body): col.markdown(f"<div class='card'><h4>{tr(title)}</h4><p>{tr(body)}</p></div>", unsafe_allow_html=True)

def render_extraction(ext):
    c = st.columns(4)
    for col, (k, v) in zip(c, [("Type", ext["type"]), ("Organization", ext["organization"]), ("Country/region", ext["country"]), ("Deadline", ext["deadline"] or "Not found")]):
        col.metric(tr(k), v)
    with st.expander(tr("📌 Eligibility requirements"), expanded=True):
        age = f"{ext['min_age']}-{ext['max_age']} years" if ext["min_age"] else "Not stated"
        st.table(pd.DataFrame([("Study level", ext["level"]), ("Eligible countries", ext["eligible_countries"]), ("Age", age),
            ("Academic", ext["academic_requirements"]), ("Field", ext.get("field_requirements", "Not stated")),
            ("English/language", ext["language_requirements"])], columns=["Requirement", "Detail"]).set_index("Requirement"))
    with st.expander(tr("💰 Funding & benefits"), expanded=True): st.write(ext["funding"])
    with st.expander(tr("📎 Documents & link")):
        st.write("**Documents:** " + (", ".join(ext["required_documents"]) or "Not listed")); st.write("**Application link:** " + ext["link"])

def render_match(m):
    a, b = st.columns([1, 3]); a.metric(tr("Compatibility"), f"{m['pct']}%"); b.progress(m["pct"] / 100)
    c1, c2, c3 = st.columns(3)
    c1.markdown(tr("**✓ Requirements matched**")); _ = [c1.write("✓ " + x) for x in m["ok"] or ["None yet"]]
    c2.markdown(tr("**⚠ Need verification**")); _ = [c2.write("⚠ " + x) for x in m["unknown"] or ["None"]]
    c3.markdown(tr("**✗ Missing / not satisfied**")); _ = [c3.write("✗ " + x) for x in m["missing"] or ["None detected"]]
    with st.expander(tr("Why this percentage?")): st.write(m["explanation"]); _ = [st.write("• " + s) for s in m["steps"]]
    st.markdown(f"<div class='final'>{tr(engine.FINAL)}</div>", unsafe_allow_html=True)

def render_risk(risk):
    st.markdown(badge(risk["level"]), unsafe_allow_html=True)
    tiers = risk.get("tiers") or {risk["level"]: risk["signals"]}
    if not any(tiers.values()): st.success(tr("No common warning indicators detected in the text provided."))
    for t in ("HIGH", "MEDIUM", "LOW"):
        if tiers.get(t):
            with st.expander(f"{tr(t + ' RISK INDICATORS')} ({len(tiers[t])})", expanded=t == "HIGH"): _ = [st.write("• " + x) for x in tiers[t]]
    if risk["level"] != "LOW": st.warning(tr("These indicators require verification."))
    st.caption(tr("Risk indicators are not proof of fraud. Always verify with the official organization."))

def render_checklist(items, prefix):
    done = [st.checkbox(tr(i), key=f"{prefix}{n}") for n, i in enumerate(items)]
    missing = [i for i, d in zip(items, done) if not d]
    st.info(f"☐ {len(missing)} {tr('of')} {len(items)} {tr('items still missing. Tick what you already have.')}")

def render_tracker():
    rows = [{"Opportunity": o["title"], "Deadline": o["deadline"], "Days remaining": days_left(o["deadline"]), "Status": tr(eff_status(o))}
            for o in db.list_saved() if o["deadline"]]
    if not rows: st.info(tr("No saved opportunities with deadlines yet.")); return
    df = pd.DataFrame(rows); df["Alert"] = df["Days remaining"].map(alert)
    asc = st.radio("Sort by deadline", ["Soonest first", "Latest first"], horizontal=True, format_func=tr, key="sort_" + st.session_state.page) == "Soonest first"
    st.dataframe(df.sort_values("Deadline", ascending=asc).rename(columns=tr), hide_index=True, use_container_width=True)
    soon = df[(df["Days remaining"] >= 0) & (df["Days remaining"] <= 14)]
    if not soon.empty: st.warning(f"⚠️ {len(soon)} " + tr("deadline(s) within 14 days") + ": " + ", ".join(soon["Opportunity"]))

def save_result(res):
    ext, r, m = res["r"]["ext"], res["r"], res["m"]
    db.save_opportunity(ext, res["text"], res["demo"], m["pct"], r["risk"]["level"], r["checklist"], r["mode"], r)

def run(text, prof, demo): 
    r = engine.analyze(text, prof, st.session_state.get("resp_lang", "English")); return {"r": r, "m": engine.match(prof, r["ext"]), "text": text, "demo": demo}

profile = {**DEMO_PROFILE, **db.get_profile(DEMO_PROFILE)}
has_prof = db.has_profile(); demo_prof = profile if has_prof else DEMO_PROFILE
st.sidebar.title("🛡️ ScholarShield AI")
st.sidebar.radio("Language / Langue", ["English", "Français"], key="ui_lang", horizontal=True)
st.sidebar.selectbox(tr("AI response language"), RESP_LANGS, key="resp_lang")
st.sidebar.caption(tr("AI-generated translations: please verify important details."))
st.sidebar.radio(tr("Navigate"), PAGES, key="page", format_func=tr)
st.sidebar.button(tr("🚀 Start Demo"), on_click=start_demo, use_container_width=True)
page = st.session_state.page

if page == "Dashboard":
    st.markdown(f"""<div class='hero'><h1>ScholarShield AI</h1><h3>{tr("Find opportunities.")}<br>{tr("Understand your chances.")}<br>{tr("Apply with confidence.")}</h3>
    <p>{tr("ScholarShield AI helps students discover, understand and evaluate opportunities using AI-powered analysis.")}</p></div>""", unsafe_allow_html=True)
    mode_banner()
    c = st.columns(3)
    card(c[0], "🔎 Discover", "Find and understand opportunities."); card(c[1], "🎯 Match", "See how an opportunity fits your profile."); card(c[2], "🛡️ Verify", "Identify risk indicators before applying.")
    st.write("")
    b = st.columns(3)
    b[0].button(tr("🚀 Start Demo"), type="primary", on_click=start_demo, use_container_width=True, key="b1")
    b[1].button(tr("Analyze an Opportunity"), on_click=go, args=("Analyze Opportunity",), use_container_width=True)
    b[2].button(tr("Explore Dashboard"), on_click=go, args=("Saved Opportunities",), use_container_width=True)
    st.subheader(tr("Why ScholarShield?"))
    w = st.columns(4)
    for col, t in zip(w, ["⏱️ Less time searching", "📋 Clearer eligibility", "📅 Fewer missed deadlines", "🛡️ Safer opportunity discovery"]): card(col, t, "")
    saved = db.list_saved(); st.subheader(tr("Your dashboard"))
    upcoming = [o for o in saved if o["deadline"] and 0 <= days_left(o["deadline"]) <= 30]
    m = st.columns(4)
    m[0].metric(tr("Opportunities analyzed"), db.count_history()); m[1].metric(tr("Saved opportunities"), len(saved))
    m[2].metric(tr("Upcoming deadlines (30d)"), len(upcoming)); m[3].metric(tr("Applications in progress"), sum(eff_status(o) == "Preparing" for o in saved))
    l, r = st.columns(2)
    with l:
        st.markdown(tr("**Recent analyses**"))
        for h in db.recent_history(5): st.markdown(f"• {h['title'][:55]} {badge(h['risk'])}", unsafe_allow_html=True)
        if not saved: st.caption("Nothing yet. Start the demo or load DEMO DATA below.")
    with r:
        st.markdown(tr("**Upcoming deadlines**"))
        for o in sorted(upcoming, key=lambda o: o["deadline"])[:5]: st.write(f"{alert(days_left(o['deadline']))} {o['title'][:45]} — {o['deadline']} ({days_left(o['deadline'])} days)")
        if not upcoming: st.caption("No deadlines in the next 30 days.")
    if not saved and st.button(tr("Load DEMO DATA into my dashboard")):
        for text in DEMO_OPPS.values(): save_result(run(text, profile, True))
        st.rerun()

elif page == "Analyze Opportunity":
    st.title(tr("Analyze Opportunity")); mode_banner()
    choice = st.selectbox(tr("Load a sample (DEMO DATA — Fictional example) or paste your own"), ["— paste my own —"] + list(DEMO_OPPS))
    text = st.text_area(tr("Opportunity text"), value=DEMO_OPPS.get(choice, ""), height=220, key=f"txt_{choice}")
    if st.button(tr("Analyze"), type="primary"):
        if len(text.strip()) < 30: st.warning(tr("Please paste more text (at least a few sentences)."))
        else:
            with st.spinner(tr("Analyzing...")): st.session_state.result = run(text, profile, choice in DEMO_OPPS)
    res = st.session_state.get("result")
    if res:
        if res["r"]["note"]: st.warning(res["r"]["note"])
        if st.session_state.get("resp_lang", "English") != "English" and res["r"]["mode"] == engine.MODE_DEMO: st.info(tr("Response language applies in AI MODE only."))
        st.caption(res["r"]["mode"] + ("  ·  DEMO DATA — Fictional example" if res["demo"] else ""))
        if res["r"]["summary"]: st.info(res["r"]["summary"])
        t1, t2, t3, t4 = st.tabs([tr(x) for x in ["📄 Extracted info", "🎯 Eligibility", "⚠️ Risk analysis", "✅ Checklist"]])
        with t1: render_extraction(res["r"]["ext"])
        with t2: render_match(res["m"])
        with t3: render_risk(res["r"]["risk"])
        with t4: render_checklist(res["r"]["checklist"], "ck")
        if st.button(tr("💾 Save to dashboard"), type="primary"):
            save_result(res); st.success(f"Saved! Deadline: {res['r']['ext']['deadline'] or 'not found'}")
            st.button(tr("Go to Saved Opportunities"), on_click=go, args=("Saved Opportunities",))

elif page == "Guided Demo":
    st.session_state.setdefault("demo_step", 1); step = st.session_state.demo_step
    st.title(tr("🚀 Guided Demo")); mode_banner(); st.progress(step / 8, text=f"{tr('Step')} {step} {tr('of')} 8: {tr(DEMO_STEPS[step-1])}")
    st.caption(tr("Uses fictional DEMO DATA with your saved profile.") if has_prof else tr("Uses DEMO DATA — Fictional example and the demo profile."))
    if step >= 2 and not st.session_state.get("demo_res"): st.session_state.demo_res = run(DEMO_OPPS[DEMO_KEY], demo_prof, True)
    res = st.session_state.get("demo_res")
    if step == 1:
        st.markdown("### " + tr("A confusing opportunity, turned into an action plan") + "\n" + tr("A student finds a long scholarship announcement. Is she eligible? Is it safe? What must she prepare, and by when?"))
    elif step == 2: st.markdown(tr("**DEMO DATA — Fictional example**")); st.text_area(tr("Opportunity text"), DEMO_OPPS[DEMO_KEY], height=260, disabled=True)
    elif step == 3: render_extraction(res["r"]["ext"])
    elif step == 4: st.caption(tr("Profile") + ": " + ", ".join(f"{k}: {v}" for k, v in demo_prof.items() if k in ("age", "country", "education", "field", "english"))); render_match(res["m"])
    elif step == 5: render_risk(res["r"]["risk"])
    elif step == 6: render_checklist(res["r"]["checklist"], "dk")
    elif step == 7:
        st.write(f"Deadline: **{res['r']['ext']['deadline']}** · Compatibility: **{res['m']['pct']}%** · Risk: **{res['r']['risk']['level']}**")
        if st.session_state.get("demo_saved"): st.success(tr("Saved to your dashboard."))
        elif st.button(tr("💾 Save this opportunity"), type="primary"): save_result(res); st.session_state.demo_saved = True; st.rerun()
    else:
        render_tracker()
        st.markdown(f"<div class='closing'>{tr('ScholarShield turns a confusing opportunity into an actionable application plan.')}</div>", unsafe_allow_html=True)
    n = st.columns([1, 1, 1, 3])
    if step > 1 and n[0].button(tr("← Back")): st.session_state.demo_step -= 1; st.rerun()
    if step < 8 and n[1].button(tr("Next →"), type="primary", disabled=(step == 7 and not st.session_state.get("demo_saved"))): st.session_state.demo_step += 1; st.rerun()
    if step == 8: n[1].button(tr("Dashboard"), on_click=go, args=("Saved Opportunities",))
    n[2].button(tr("Restart"), on_click=start_demo)

elif page == "My Profile":
    st.title(tr("My Profile")); st.caption(tr("Used for eligibility matching."))
    st.button(tr("Load Demo Profile"), on_click=lambda: db.save_profile(DEMO_PROFILE))
    with st.form("profile"):
        c1, c2 = st.columns(2)
        p = {"name": c1.text_input(tr("Name"), profile["name"]), "age": c2.number_input(tr("Age"), 14, 60, int(profile["age"])),
             "country": c1.text_input(tr("Country"), profile["country"]),
             "education": c2.selectbox(tr("Education level"), engine.LEVELS, engine.LEVELS.index(profile["education"])),
             "field": c1.text_input(tr("Field of study"), profile["field"]), "languages": c2.text_input(tr("Languages"), profile["languages"]),
             "english": c1.selectbox(tr("English level"), engine.ENGLISH, engine.ENGLISH.index(profile["english"])),
             "academic": c2.text_input(tr("Academic information"), profile["academic"]),
             "interests": c1.text_input(tr("Interests"), profile["interests"]), "skills": c2.text_input(tr("Skills"), profile["skills"])}
        if st.form_submit_button(tr("Save profile"), type="primary"): db.save_profile(p); st.success(tr("Profile saved."))

elif page == "Saved Opportunities":
    st.title(tr("Saved Opportunities"))
    saved = db.list_saved()
    if not saved: st.info(tr("Nothing saved yet. Use Start Demo or Analyze Opportunity."))
    for o in saved:
        with st.container(border=True):
            demo = " <span class='demo'>DEMO DATA — Fictional example</span>" if o["is_demo"] else ""
            st.markdown(f"**{o['title']}**{demo}  {badge(o['risk'])}", unsafe_allow_html=True)
            c = st.columns(5); dl = days_left(o["deadline"])
            c[0].write(f"🌍 {o['country']}"); c[1].write(f"📅 {o['deadline'] or 'n/a'}" + (f" ({alert(dl)}, {dl}d)" if dl is not None else ""))
            c[2].write(f"💰 {str(o['funding'])[:40]}"); c[3].progress(o["compatibility"] / 100, text=f"{o['compatibility']}% match")
            cur = eff_status(o)
            new = c[4].selectbox("Status", STATUSES, STATUSES.index(cur), key=f"st{o['sid']}", label_visibility="collapsed", format_func=tr)
            if new != o["status"] and new != cur: db.set_status(o["sid"], new); st.rerun()
            with st.expander(tr("Checklist")): _ = [st.write("☐ " + tr(i)) for i in o["checklist"]]
            if st.button(tr("Remove"), key=f"rm{o['sid']}"): db.delete_saved(o["sid"]); st.rerun()

elif page == "Deadline Tracker":
    st.title(tr("Deadline Tracker")); render_tracker()

elif page == "Why ScholarShield?":
    st.title(tr("Why ScholarShield?"))
    a, b, c = st.columns(3)
    card(a, "VALUE", "• Solves a real problem for students<br>• Reduces wasted application effort<br>• Helps students understand opportunities")
    card(b, "AI & TECHNOLOGY", "• AI extracts requirements<br>• AI analyzes eligibility<br>• AI identifies risk indicators<br>• AI generates application checklists<br><i>(LLM mode with API key; rule-based otherwise)</i>")
    card(c, "FEASIBILITY", "• Working Streamlit prototype<br>• SQLite database<br>• Modular architecture<br>• Fallback mode without API key<br>• Could later integrate official opportunity sources (not implemented)")

else:
    st.title(tr("About ScholarShield"))
    for h, t in [("Problem", "African students face scattered information, hard-to-read eligibility rules, missed deadlines and offers that may request money or sensitive data."),
                 ("Solution", "Paste an opportunity and get extracted requirements, an eligibility assessment, risk indicators, a checklist and deadline tracking."),
                 ("How AI is used", "With an API key, an LLM extracts requirements, flags risk indicators and adds checklist items. Without one, deterministic rules do the same in a simpler way. The compatibility score is always rule-based and explained."),
                 ("Social impact", "Reduces information barriers so students can make better-informed decisions about international opportunities."),
                 ("Technology", "Python, Streamlit, SQLite, Pandas; optional LLM through the LLM_API_KEY environment variable."),
                 ("Limitations", "Rule-based extraction can miss details; AI can make mistakes; organizations are not verified automatically; no live opportunity feeds yet.")]:
        st.subheader(h); st.write(t)
    st.markdown("<div class='final'>ScholarShield AI is an AI-assisted decision-support tool. It does not replace official eligibility decisions or verify organizations automatically.</div>", unsafe_allow_html=True)

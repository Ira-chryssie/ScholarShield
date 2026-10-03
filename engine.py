"""Analysis engine: LLM (if LLM_API_KEY set) with deterministic fallback for every step."""
import os, re, json, requests
import pandas as pd
from datetime import date

LEVELS = ["High School", "Bachelor", "Master", "PhD"]
ENGLISH = ["Basic", "Intermediate", "Advanced", "Fluent"]
DOCS = {"passport": "Passport", "transcript": "Transcript", "cv": "CV / Resume", "motivation": "Motivation letter",
        "recommendation": "Recommendation letter", "ielts": "English proof (IELTS/TOEFL)", "toefl": "English proof (IELTS/TOEFL)",
        "certificate": "Academic certificate", "diploma": "Academic certificate", "portfolio": "Portfolio", "proposal": "Project proposal"}
FINAL = "Final eligibility must be confirmed by the opportunity provider."
FIELDS = ["computer science","data science","artificial intelligence","engineering","medicine","health","business","economics","education","law","agriculture","environment","design","journalism"]
MODE_DEMO = "DEMO MODE — Rule-based AI analysis"
MODE_LLM = "AI MODE — LLM-assisted analysis"
DISCLAIMER = ("This is an AI-assisted assessment, not an official decision. Only the opportunity provider "
              "can confirm eligibility, and no tool can detect scams with certainty.")

def _field(text, name):
    m = re.search(rf"(?im)^\s*{name}\s*:\s*(.+)$", text)
    return m.group(1).strip() if m else None

def heuristic_extract(text):
    low = text.lower(); lines = [l.strip() for l in text.splitlines() if l.strip()]
    ages = re.search(r"(\d{2})\s*(?:-|–|to)\s*(\d{2})\s*years", low)
    dl = None
    m = re.search(r"deadline[^\n]*?(\d{1,2}\s+[A-Za-z]+\s+\d{4}|\d{4}-\d{2}-\d{2})", text, re.I)
    if m:
        d = pd.to_datetime(m.group(1), errors="coerce"); dl = None if pd.isna(d) else d.date().isoformat()
    pick = lambda pairs, default: next((n for k, n in pairs if k in low), default)
    docs = sorted({v for k, v in DOCS.items() if re.search(rf"\b{k}", low)})
    link = re.search(r"https?://[^\s,]+", text)
    fund = _field(text, "funding") or next((l for l in lines if re.search(r"funded|stipend|tuition|\$\d", l, re.I)), "Not stated")
    fields = [f.title() for f in FIELDS if f in low]
    return {"title": lines[0] if lines else "Untitled", "organization": _field(text, "organi[sz]ation") or "Not stated",
            "country": _field(text, "country") or "Not stated",
            "type": pick([("internship", "Internship"), ("fellowship", "Fellowship"), ("competition", "Competition"),
                          ("scholarship", "Scholarship"), ("admission", "University opportunity")], "Other"),
            "level": pick([("phd", "PhD"), ("master", "Master"), ("bachelor", "Bachelor"), ("undergraduate", "Bachelor")], "Any"),
            "eligible_countries": _field(text, "eligible countries") or "Not specified",
            "min_age": int(ages.group(1)) if ages else None, "max_age": int(ages.group(2)) if ages else None,
            "field_requirements": ", ".join(fields) or "Not stated", "academic_requirements": "Degree/grades mentioned" if re.search(r"degree|grades|gpa|diploma", low) else "Not stated",
            "english_required": bool(re.search(r"ielts|toefl|english", low)),
            "language_requirements": "English proof required" if re.search(r"ielts|toefl|english", low) else "Not stated",
            "funding": fund, "deadline": dl, "required_documents": docs, "link": link.group(0) if link else "Not provided"}

def heuristic_risk(text, ext):
    """Rule-based risk indicators grouped by tier. Indicators need verification; they are not proof of fraud."""
    low = text.lower(); tiers = {"HIGH": [], "MEDIUM": [], "LOW": []}
    free = re.search(r"free of charge|no (application )?fee", low)
    checks = [("HIGH", r"(processing|application|registration|admin)\w* fee|pay\b.*\$|western union|mobile money|bitcoin|wire transfer", "Requests a payment or fee to secure a place", not free),
        ("HIGH", r"bank account|card pin|\bpin\b|password|card number|ssn", "Asks for sensitive financial/security information", True),
        ("HIGH", r"(pay|fee|send).{0,90}(within \d+ hours|immediately|today)", "Pressure to pay or send information immediately", not free),
        ("MEDIUM", r"@(gmail|yahoo|hotmail|outlook)\.", "Contact uses a free public email domain, not an official organization domain", True),
        ("MEDIUM", r"guaranteed|100%|no requirements|no experience needed|you have been selected", "Unrealistic promises or guaranteed outcomes", True),
        ("MEDIUM", r"extended to", "Inconsistent or shifting deadlines", True),
        ("LOW", r"within (24|48) hours|last chance|act now|urgent", "Artificial urgency", True)]
    for tier, pat, msg, cond in checks:
        if cond and re.search(pat, low): tiers[tier].append(msg)
    if ext["organization"] == "Not stated": tiers["MEDIUM"].append("Organization identity is unclear or missing")
    if ext["link"] == "Not provided": tiers["MEDIUM"].append("No official website or application link provided")
    if ext["funding"] == "Not stated": tiers["LOW"].append("Funding information is unclear")
    score = 3 * len(tiers["HIGH"]) + 2 * len(tiers["MEDIUM"]) + len(tiers["LOW"])
    level = "HIGH" if score >= 4 else "MEDIUM" if score >= 2 else "LOW"
    flat = [m for t in ("HIGH", "MEDIUM", "LOW") for m in tiers[t]]
    return {"level": level, "signals": flat or ["No common warning indicators detected in the text provided."], "tiers": tiers}

def build_checklist(ext, profile, risk, extra=()):
    items = list(ext["required_documents"]) or ["Passport", "CV / Resume", "Transcript", "Motivation letter"]
    if ext["english_required"] and ENGLISH.index(profile["english"]) < 2 and "English proof (IELTS/TOEFL)" not in items:
        items.append("English proof (IELTS/TOEFL)")
    items += list(extra)
    if risk["level"] != "LOW": items.append("Verify the organization via its official website (not links in the message)")
    items.append("Confirm eligibility directly with the official provider")
    return list(dict.fromkeys(items))

def match(profile, ext):
    ok, missing, unknown = [], [], []
    if ext["level"] != "Any":
        need = LEVELS[max(LEVELS.index(ext["level"]) - 1, 0)]
        (ok if LEVELS.index(profile["education"]) >= LEVELS.index(need) else missing).append(f"Education: {ext['level']} programme needs {need} or higher (you: {profile['education']})")
    if ext["min_age"] is not None or ext["max_age"] is not None:
        lo, hi = ext["min_age"] or 0, ext["max_age"] or 120
        label = f"{lo}-{hi}" if ext["min_age"] is not None and ext["max_age"] is not None else (f"{lo}+" if ext["min_age"] is not None else f"up to {hi}")
        (ok if lo <= profile["age"] <= hi else missing).append(f"Age {label} (you: {profile['age']})")
    else: unknown.append("Age requirement not stated")
    fr = ext.get("field_requirements", "Not stated")
    if fr != "Not stated":
        words = set(re.findall(r"[a-z]+", " ".join(str(profile.get(k, "")) for k in ("field", "interests", "skills")).lower()))
        hit = any(f.split()[0].lower() in words for f in fr.split(", "))
        (ok if hit else unknown).append(f"Field: {fr}" + (" matches your profile" if hit else " - verify it fits your field of study"))
    ec = ext["eligible_countries"].lower()
    if ec == "not specified": unknown.append("Eligible countries not specified")
    elif profile["country"].lower() in ec or "all african" in ec or "africa" in ec or "all countries" in ec:
        ok.append(f"Country: open to your region ({profile['country']})")
    else: missing.append(f"Country: {profile['country']} not listed as eligible")
    if ext["english_required"]:
        need = 2 if re.search("ielts|toefl", " ".join(ext["required_documents"]).lower()) else 1
        (ok if ENGLISH.index(profile["english"]) >= need else missing).append(f"English level (you: {profile['english']})")
    if ext["deadline"]:
        (missing if ext["deadline"] < date.today().isoformat() else ok).append(
            "Deadline has passed" if ext["deadline"] < date.today().isoformat() else f"Deadline still open ({ext['deadline']})")
    else: unknown.append("Deadline not found")
    total = len(ok) + len(missing) + len(unknown)
    pct = round(100 * (len(ok) + 0.5 * len(unknown)) / total) if total else 0
    steps = ([f"Close the gap: {m}" for m in missing[:3]] or ["You appear to meet the stated requirements."]) + ["Read the official call carefully and prepare documents early."]
    expl = (f"{len(ok)} matched, {len(missing)} missing, {len(unknown)} need verification, out of {total} criteria found in the text. "
            f"Score = (matched + 0.5 x needs-verification) / total = {pct}%. " + FINAL + " " + DISCLAIMER)
    return {"pct": pct, "ok": ok, "missing": missing, "unknown": unknown, "steps": steps, "explanation": expl}

PROMPT = """You analyze scholarship/opportunity text. Return ONLY JSON: {"extraction": {title, organization, country, type, level (High School|Bachelor|Master|PhD|Any),
eligible_countries, min_age (int|null), max_age (int|null), academic_requirements, english_required (bool), language_requirements, funding,
deadline (YYYY-MM-DD|null), required_documents [strings], link}, "risk": {"level": "LOW|MEDIUM|HIGH", "signals": [strings], "tiers": {"HIGH": [strings], "MEDIUM": [strings], "LOW": [strings]}},
"checklist_extra": [strings], "summary": "2 sentences"}. Never say something is definitely a scam. Use only info in the text.\n\nTEXT:\n"""

def _provider():
    """Auto-detect: Google keys start with 'AIza' -> Gemini; otherwise Anthropic. Override with LLM_PROVIDER."""
    p = os.getenv("LLM_PROVIDER", "").lower()
    return p if p in ("gemini", "anthropic") else ("gemini" if os.getenv("LLM_API_KEY", "").startswith("AIza") else "anthropic")

def _prompt(text, lang):
    note = f"Write summary, risk signals/tiers and checklist_extra in {lang}. Keep JSON keys and extraction values faithful to the text.\n\nTEXT:\n"
    return PROMPT.replace("TEXT:\n", note) + text[:6000]

def _call_llm(text, lang="English"):
    key, model = os.environ["LLM_API_KEY"], os.getenv("LLM_MODEL", "")
    if _provider() == "gemini":
        first = "" if (not model or model.startswith("claude")) else model
        last = None
        for mdl in dict.fromkeys(m for m in (first, "gemini-flash-lite-latest", "gemini-flash-latest") if m):
            try:  # if a model is overloaded (503) or unknown (404), try the next one
                r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{mdl}:generateContent", timeout=25,
                    headers={"x-goog-api-key": key, "content-type": "application/json"},
                    json={"contents": [{"parts": [{"text": _prompt(text, lang)}]}], "generationConfig": {"responseMimeType": "application/json"}})
                r.raise_for_status()
                raw = "".join(p.get("text", "") for p in r.json()["candidates"][0]["content"]["parts"])
                return json.loads(re.search(r"\{.*\}", raw, re.S).group(0))
            except Exception as e:
                last = e
        raise last
    else:
        r = requests.post("https://api.anthropic.com/v1/messages", timeout=60,
            headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": model or "claude-sonnet-4-6", "max_tokens": 1500, "messages": [{"role": "user", "content": _prompt(text, lang)}]})
        r.raise_for_status()
        raw = "".join(b.get("text", "") for b in r.json()["content"])
    return json.loads(re.search(r"\{.*\}", raw, re.S).group(0))

def _clean(ext, base):
    """Normalize LLM output types; fall back to the rule-based value when a field is unusable."""
    out = dict(base)
    for k in ("title", "organization", "country", "type", "eligible_countries", "academic_requirements",
              "field_requirements", "language_requirements", "funding", "link"):
        v = ext.get(k)
        if isinstance(v, list): v = ", ".join(str(x) for x in v)
        if isinstance(v, (str, int, float)) and str(v).strip(): out[k] = str(v).strip()
    if str(ext.get("level", "")) in LEVELS + ["Any"]: out["level"] = ext["level"]
    for k in ("min_age", "max_age"):
        try: out[k] = int(ext[k]) if ext.get(k) is not None else base[k]
        except (ValueError, TypeError): out[k] = base[k]
    if isinstance(ext.get("english_required"), bool): out["english_required"] = ext["english_required"]
    docs = ext.get("required_documents")
    if isinstance(docs, str): docs = [docs]
    if isinstance(docs, list) and docs: out["required_documents"] = [str(d) for d in docs]
    dl = pd.to_datetime(ext.get("deadline"), errors="coerce") if ext.get("deadline") else None
    if dl is not None and not pd.isna(dl): out["deadline"] = dl.date().isoformat()
    return out

def analyze(text, profile, lang="English"):
    """Returns dict(mode, ext, risk, checklist, summary). Falls back to heuristics on any LLM failure."""
    ext, risk, extra, summary, mode, note = heuristic_extract(text), None, [], "", MODE_DEMO, ""
    if os.getenv("LLM_API_KEY"):
        try:
            out = _call_llm(text, lang)
            ext = _clean(out["extraction"], ext)
            if out["risk"]["level"].upper() in ("LOW", "MEDIUM", "HIGH"):
                risk = {"level": out["risk"]["level"].upper(), "signals": out["risk"]["signals"]}
                t = out["risk"].get("tiers")
                if lang != "English" and isinstance(t, dict) and all(isinstance(t.get(k), list) for k in ("HIGH", "MEDIUM", "LOW")):
                    risk["tiers"] = {k: [str(x) for x in t[k]] for k in ("HIGH", "MEDIUM", "LOW")}
            extra, summary, mode = out.get("checklist_extra", []), out.get("summary", ""), MODE_LLM
        except Exception as e:
            resp = getattr(e, "response", None); detail = ""
            if resp is not None:
                try: detail = f" {resp.status_code}: {resp.json()['error']['message'][:200]}"
                except Exception: detail = f" {resp.status_code}"
            note = f"LLM unavailable ({type(e).__name__}{detail}); using fallback mode."
    htr = heuristic_risk(text, ext)
    if risk is None: risk = htr
    elif "tiers" not in risk:
        risk["tiers"] = {k: list(v) for k, v in htr["tiers"].items()}
        risk["tiers"][risk["level"]] += [x for x in risk["signals"] if x not in htr["signals"]]
    return {"mode": mode, "note": note, "ext": ext, "risk": risk, "summary": summary,
            "checklist": build_checklist(ext, profile, risk, extra)}

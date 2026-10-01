# ScholarShield AI — Submission (Ignite Your Future 2026 / AI Innovation Challenge)

## 1. Project name
ScholarShield AI

## 2. One-line description
An AI-assisted tool that turns a confusing opportunity announcement into an actionable application plan for African students.

## 3. Problem
Opportunities are scattered across websites and social media, eligibility rules are hard to read, deadlines are missed, students apply where they are not eligible, and some offers ask for money or sensitive data.

## 4. Target users
African students and young people seeking scholarships, university places, internships, fellowships and competitions.

## 5. Solution
Paste an opportunity; ScholarShield extracts its requirements, compares them with the student's profile, shows risk indicators, builds a checklist, and tracks the deadline.

## 6. Key features (all implemented)
Opportunity Analyzer · Eligibility Match with explained percentage · Risk indicators (HIGH/MEDIUM/LOW tiers) · Application checklist · Saved opportunities with status · Deadline tracker with days remaining and warnings · Profile with demo profile · Guided 8-step demo · Fictional DEMO DATA.

## 7. How AI is used
- **AI mode (LLM_API_KEY set):** an LLM extracts requirements, flags risk indicators, writes a summary and adds checklist items.
- **Demo mode (no key, or if the API fails):** deterministic rules do extraction, matching and risk analysis.
- The compatibility percentage is always rule-based and explained on screen.

## 8. Technology stack
Python, Streamlit, SQLite, Pandas; optional LLM via HTTP API. Modules: app.py (UI), engine.py (analysis), db.py (storage), demo_data.py.

## 9. Social impact
Reduces information barriers so students spend effort on suitable, safer opportunities and miss fewer deadlines. We make no claim of guaranteed outcomes.

## 10. Feasibility
Working local prototype, no paid services required, modular code, automatic fallback. Official opportunity sources could be integrated later (not implemented).

## 11. Future improvements
Multilingual support (French, Swahili, Kirundi) · verified-source and official-domain checks · deadline reminders by email/SMS · PDF/URL import · motivation-letter feedback.

## 12. Known limitations
Rule-based extraction can miss details; LLM output can be wrong; organizations are not verified automatically; no live opportunity feeds; risk indicators are not proof of fraud; final eligibility must be confirmed by the provider.

## 13. Demo walkthrough
Click **🚀 Start Demo** → 8 steps: intro → load fictional scholarship → extraction → eligibility → risk indicators → checklist → save → deadline tracker. Ends with: "ScholarShield turns a confusing opportunity into an actionable application plan."

## 14. 180-second pitch structure
0–20s Problem · 20–45s Who is affected · 45–80s Introduce ScholarShield AI · 80–125s Live demo · 125–155s AI + impact + feasibility · 155–180s Closing: "ScholarShield AI helps young people move from opportunity overload to informed action."

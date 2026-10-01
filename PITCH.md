# Pitch material

## 30s - Problem
Every year, talented African students miss international opportunities, not for lack of talent, but for lack of clear information. Details are scattered, eligibility rules are confusing, deadlines slip by, and fake offers ask for fees and personal data. Students lose time, money and trust.

## 30s - Solution
ScholarShield AI lets a student paste any opportunity. In seconds it extracts the key facts, compares them with the student's profile, shows LOW/MEDIUM/HIGH risk signals, builds a personalized document checklist, and tracks deadlines, always saying the provider has the final word.

## 180s script
**0:00-0:20 Problem** Finding a scholarship should be exciting. Instead, students face dozens of scattered posts, confusing rules, missed deadlines, and offers that may ask for money.
**0:20-0:45 Who is affected** African students and young people, often without mentors or reliable guidance, lose time and sometimes money on opportunities they can't win or can't trust.
**0:45-1:20 Introduce ScholarShield AI** Paste any opportunity and ScholarShield AI extracts requirements, compares them with your profile, shows risk indicators, builds a checklist and tracks the deadline.
**1:20-2:05 Live demo** Click Start Demo. Fictional scholarship loads; AI extraction; compatibility with matched, to-verify and missing items; risk level with indicators; checklist; save; deadline tracker with days remaining.
**2:05-2:35 AI + impact + feasibility** An LLM does the extraction and risk analysis when a key is present; rule-based fallback keeps it working without one. Python, Streamlit, SQLite: runs locally today. It supports decisions; it doesn't replace official eligibility decisions.
**2:35-3:00 Closing** "ScholarShield AI helps young people move from opportunity overload to informed action."

## Judge Q&A
1. **Is it accurate?** It is an assessment aid. Percentages come from transparent rules on stated criteria; we show unclear items and always require official confirmation.
2. **Can it detect scams?** No tool can with certainty. It flags warning signals (fees, free email domains, sensitive data requests, unrealistic promises) as LOW/MEDIUM/HIGH indicators.
3. **What if there's no internet or API key?** Fallback mode uses rule-based extraction and scoring, so it still works.
4. **How is the LLM used?** Extraction, risk-signal analysis, summaries and extra checklist items; output is validated and merged with rule-based results.
5. **Privacy?** Profile and history stay in a local SQLite file; no keys in code; users should avoid pasting passwords or ID numbers.
6. **Why Africa?** Students often lack mentors and reliable guidance, and are targeted by opportunity fraud; the tool lowers that information gap.
7. **Is the demo data real?** No, it is fictional and labelled DEMO DATA.
8. **How would you sustain it?** Free for students; partnerships with universities and youth organizations.

## 5 future improvements
1. Multilingual support (French, Kirundi, Swahili, Arabic).
2. Verified-source database and official-domain checks.
3. Email/WhatsApp/SMS deadline reminders.
4. PDF/URL upload and OCR for scanned calls.
5. Application-writing feedback (motivation letters) and community reviews.

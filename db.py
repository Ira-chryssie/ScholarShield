"""SQLite persistence: profile, opportunities, saved, analysis history."""
import sqlite3, json, os
DB = os.getenv("DB_PATH", "scholarshield.db")

def conn():
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row; return c

def init_db():
    with conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS profile(id INTEGER PRIMARY KEY CHECK(id=1), data TEXT);
        CREATE TABLE IF NOT EXISTS opportunities(id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, data TEXT,
            source_text TEXT, is_demo INTEGER, created TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS saved(id INTEGER PRIMARY KEY AUTOINCREMENT, opp_id INTEGER, compatibility INTEGER,
            risk TEXT, status TEXT DEFAULT 'Saved', checklist TEXT, created TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS history(id INTEGER PRIMARY KEY AUTOINCREMENT, opp_id INTEGER, mode TEXT,
            result TEXT, created TEXT DEFAULT CURRENT_TIMESTAMP);""")

def get_profile(default):
    with conn() as c:
        r = c.execute("SELECT data FROM profile WHERE id=1").fetchone()
    return json.loads(r["data"]) if r else dict(default)

def save_profile(p):
    with conn() as c:
        c.execute("INSERT INTO profile(id,data) VALUES(1,?) ON CONFLICT(id) DO UPDATE SET data=excluded.data", (json.dumps(p),))

def save_opportunity(ext, source, is_demo, compat, risk, checklist, mode, result):
    with conn() as c:
        oid = c.execute("INSERT INTO opportunities(title,data,source_text,is_demo) VALUES(?,?,?,?)",
                        (ext["title"], json.dumps(ext), source, int(is_demo))).lastrowid
        c.execute("INSERT INTO saved(opp_id,compatibility,risk,checklist) VALUES(?,?,?,?)",
                  (oid, compat, risk, json.dumps(checklist)))
        c.execute("INSERT INTO history(opp_id,mode,result) VALUES(?,?,?)", (oid, mode, json.dumps(result)))

def list_saved():
    with conn() as c:
        rows = c.execute("""SELECT s.id sid, s.compatibility, s.risk, s.status, s.checklist, o.data, o.is_demo
                            FROM saved s JOIN opportunities o ON o.id=s.opp_id ORDER BY s.id DESC""").fetchall()
    out = []
    for r in rows:
        d = json.loads(r["data"]); d.update(sid=r["sid"], compatibility=r["compatibility"], risk=r["risk"],
            status=r["status"], checklist=json.loads(r["checklist"]), is_demo=bool(r["is_demo"])); out.append(d)
    return out

def set_status(sid, status):
    with conn() as c: c.execute("UPDATE saved SET status=? WHERE id=?", (status, sid))

def delete_saved(sid):
    with conn() as c: c.execute("DELETE FROM saved WHERE id=?", (sid,))

def count_history():
    with conn() as c: return c.execute("SELECT COUNT(*) FROM history").fetchone()[0]

def recent_history(n=5):
    """Most recent analyses: title, mode, created, risk level."""
    with conn() as c:
        rows = c.execute("SELECT o.title, h.mode, h.created, h.result FROM history h JOIN opportunities o ON o.id=h.opp_id ORDER BY h.id DESC LIMIT ?", (n,)).fetchall()
    out = []
    for r in rows:
        try: risk = json.loads(r["result"])["risk"]["level"]
        except Exception: risk = "LOW"
        out.append({"title": r["title"], "mode": r["mode"], "created": r["created"], "risk": risk})
    return out

def has_profile():
    with conn() as c: return c.execute("SELECT 1 FROM profile WHERE id=1").fetchone() is not None

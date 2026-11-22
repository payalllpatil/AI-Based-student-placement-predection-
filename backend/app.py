"""College ERP - Flask REST API. Run: python app.py  ->  http://127.0.0.1:5000"""
import os, sqlite3
from functools import wraps
from flask import Flask, g, jsonify, request, session, send_from_directory
from werkzeug.security import check_password_hash, generate_password_hash

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "erp.db")
FRONT = os.path.join(BASE, "..", "frontend")
app = Flask(__name__, static_folder=None)
app.secret_key = "change-this-secret-for-production"

# ---- Table registry: columns that may be written, who may write, which student-scoped joins apply ----
SOFT = ["verbal", "written", "english", "presentation", "group_discussion", "teamwork", "leadership",
        "problem_solving", "time_management", "confidence", "adaptability"]
TABLES = {
    "students": dict(cols=["student_code", "name", "email", "mobile", "dob", "gender", "city", "state", "course", "department_id",
                           "specialization", "semester", "academic_year", "admission_year", "roll_no", "faculty_id"],
                     write={"admin"}, search=["name", "student_code", "email", "roll_no", "city"]),
    "faculty": dict(cols=["name", "email", "designation", "department_id"], write={"admin"}, search=["name", "email"]),
    "departments": dict(cols=["name", "hod", "building"], write={"admin"}, search=["name", "hod"]),
    "academics": dict(cols=["student_id", "ssc", "hsc", "graduation", "sgpa1", "sgpa2", "sgpa3", "sgpa4", "sgpa5", "sgpa6", "cgpa",
                            "current_backlogs", "previous_backlogs", "attendance", "performance"], write={"admin", "faculty"}),
    "tech_skills": dict(cols=["student_id", "skill", "level", "score"], write={"admin", "faculty"}, search=["skill"]),
    "soft_skills": dict(cols=["student_id"] + SOFT, write={"admin", "faculty"}),
    "assessments": dict(cols=["student_id", "quant", "logical", "verbal_ability", "coding", "tech_mcq", "programming", "mock_interview"],
                        write={"admin", "faculty"}),
    "projects": dict(cols=["student_id", "title", "description", "technologies", "domain", "project_type"], write={"admin", "faculty"},
                     search=["title", "technologies", "domain"]),
    "internships": dict(cols=["student_id", "company", "role", "duration_months", "performance"], write={"admin", "faculty"},
                        search=["company", "role"]),
    "certifications": dict(cols=["student_id", "kind", "name", "organization", "cert_date"], write={"admin", "faculty"},
                           search=["name", "organization", "kind"]),
    "placements": dict(cols=["student_id", "eligible", "preferred_role", "preferred_industry", "interview_history", "company",
                             "status", "package_lpa", "placement_date"], write={"admin", "placement"}, search=["company", "preferred_role"]),
}
NUMERIC = {"semester", "admission_year", "department_id", "faculty_id", "student_id", "score", "ssc", "hsc", "graduation", "cgpa",
           "current_backlogs", "previous_backlogs", "attendance", "duration_months", "package_lpa"} | set(SOFT) | \
          {"sgpa%d" % i for i in range(1, 7)} | {"quant", "logical", "verbal_ability", "coding", "tech_mcq", "programming", "mock_interview"}
STUDENT_SCOPED = set(TABLES) - {"faculty", "departments"}


def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_):
    d = g.pop("db", None)
    if d:
        d.close()


def login_required(fn):
    @wraps(fn)
    def w(*a, **k):
        if "uid" not in session:
            return jsonify(error="Please sign in."), 401
        return fn(*a, **k)
    return w


def rows(sql, args=()):
    return [dict(r) for r in db().execute(sql, args).fetchall()]


def scope_sql():
    """Faculty only see their assigned students (and records linked to them)."""
    if session.get("role") == "faculty":
        return " AND s.faculty_id = ?", [session.get("faculty_id")]
    return "", []


def select_for(t):
    if t == "students":
        return ("SELECT s.*, d.name AS department, f.name AS faculty_name FROM students s "
                "LEFT JOIN departments d ON d.id=s.department_id LEFT JOIN faculty f ON f.id=s.faculty_id", "s")
    if t == "faculty":
        return "SELECT f.*, d.name AS department FROM faculty f LEFT JOIN departments d ON d.id=f.department_id", "f"
    if t == "departments":
        return ("SELECT d.*, (SELECT COUNT(*) FROM students x WHERE x.department_id=d.id) AS student_count, "
                "(SELECT COUNT(*) FROM faculty x WHERE x.department_id=d.id) AS faculty_count FROM departments d"), "d"
    return (f"SELECT t.*, s.name AS student_name, s.student_code, s.course FROM {t} t JOIN students s ON s.id=t.student_id", "t")


# ---------------- Auth ----------------
@app.post("/api/login")
def login():
    b = request.get_json(silent=True) or {}
    u = db().execute("SELECT * FROM users WHERE username=?", (b.get("username", "").strip(),)).fetchone()
    if not u or not check_password_hash(u["password_hash"], b.get("password", "")):
        return jsonify(error="Invalid username or password."), 401
    session.update(uid=u["id"], role=u["role"], faculty_id=u["faculty_id"], student_id=u["student_id"], name=u["full_name"])
    return jsonify(me())


def me():
    return dict(role=session["role"], name=session["name"], faculty_id=session.get("faculty_id"), student_id=session.get("student_id"))


@app.before_request
def student_guard():
    """Student accounts may only use the AI portal and read their own ERP profile."""
    p = request.path
    if session.get("role") != "student" or not p.startswith("/api/"):
        return None
    own = f"/api/students/{session.get('student_id')}/profile"
    if p in ("/api/login", "/api/logout", "/api/me", own) or p.startswith("/api/ai/"):
        return None
    return jsonify(error="Student accounts can only access their own portal."), 403


@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify(ok=True)


@app.get("/api/me")
@login_required
def whoami():
    return jsonify(me())


# ---------------- Meta lookups for dropdowns ----------------
@app.get("/api/lookups")
@login_required
def lookups():
    return jsonify(departments=rows("SELECT id, name FROM departments ORDER BY name"),
                   faculty=rows("SELECT id, name FROM faculty ORDER BY name"),
                   students=rows("SELECT id, name, student_code FROM students ORDER BY name"
                                 if session["role"] != "faculty" else
                                 "SELECT id, name, student_code FROM students WHERE faculty_id=%d ORDER BY name" % (session.get("faculty_id") or 0)),
                   courses=[r["course"] for r in rows("SELECT DISTINCT course FROM students ORDER BY course")])


# ---------------- Generic CRUD ----------------
@app.get("/api/<t>")
@login_required
def list_rows(t):
    if t not in TABLES:
        return jsonify(error="Unknown module"), 404
    cfg = TABLES[t]
    base, alias = select_for(t)
    where, args = ["1=1"], []
    if t in STUDENT_SCOPED:
        sc, a = scope_sql()
        if sc:
            where.append("s.faculty_id = ?" if t == "students" else "t.student_id IN (SELECT id FROM students WHERE faculty_id = ?)")
            args += a
    q = request.args.get("q", "").strip()
    sc_cols = cfg.get("search", [])
    if q and sc_cols:
        parts = [f"{alias}.{c} LIKE ?" for c in sc_cols]
        if t not in ("students", "faculty", "departments"):
            parts += ["s.name LIKE ?", "s.student_code LIKE ?"]
            args += [f"%{q}%"] * (len(sc_cols) + 2)
        else:
            args += [f"%{q}%"] * len(sc_cols)
        where.append("(" + " OR ".join(parts) + ")")
    for k, v in request.args.items():  # exact-match filters: ?course=MCA&status=Placed
        if k == "course" and t in STUDENT_SCOPED and t != "students" and v != "":
            where.append("s.course = ?")
            args.append(v)
        elif k in cfg["cols"] + ["id"] and v != "":
            where.append(f"{alias}.{k} = ?")
            args.append(v)
    sort = request.args.get("sort", "id")
    extra = {"student_name": "s.name", "course": "s.course", "department": "department", "faculty_name": "faculty_name",
             "student_count": "student_count", "faculty_count": "faculty_count"}
    sort = f"{alias}.{sort}" if sort in cfg["cols"] + ["id"] else extra.get(sort, f"{alias}.id")
    order = "DESC" if request.args.get("order") == "desc" else "ASC"
    page, per = max(1, int(request.args.get("page", 1))), min(100, int(request.args.get("per_page", 15)))
    wsql = " WHERE " + " AND ".join(where)
    inner = base + wsql
    total = db().execute(f"SELECT COUNT(*) FROM ({inner})", args).fetchone()[0]
    data = rows(f"{inner} ORDER BY {sort} {order} LIMIT ? OFFSET ?", args + [per, (page - 1) * per])
    return jsonify(data=data, total=total, page=page, per_page=per, pages=max(1, -(-total // per)),
                   can_write=session["role"] in cfg["write"])


def clean(t, body):
    out = {}
    for c in TABLES[t]["cols"]:
        if c in body:
            v = body[c]
            if v == "" or v is None:
                v = None
            elif c in NUMERIC:
                try:
                    v = float(v)
                    v = int(v) if v == int(v) and c not in {"cgpa", "ssc", "hsc", "graduation", "attendance", "package_lpa"} and not c.startswith("sgpa") else v
                except ValueError:
                    raise ValueError(f"{c.replace('_', ' ').title()} must be a number.")
            out[c] = v
    return out


def can_write(t):
    return session["role"] in TABLES[t]["write"]


def student_allowed(t, data, row_id=None):
    """Faculty may only change records belonging to their assigned students."""
    if session["role"] != "faculty":
        return True
    sid = data.get("student_id")
    if sid is None and row_id:
        r = db().execute(f"SELECT student_id FROM {t} WHERE id=?", (row_id,)).fetchone()
        sid = r["student_id"] if r else None
    r = db().execute("SELECT 1 FROM students WHERE id=? AND faculty_id=?", (sid, session.get("faculty_id"))).fetchone()
    return bool(r)


def db_error(e):
    msg = str(e)
    if "UNIQUE" in msg:
        return jsonify(error="A record with this value already exists (duplicate)."), 409
    if "FOREIGN KEY" in msg:
        return jsonify(error="Linked record not found or record is still in use."), 409
    if "NOT NULL" in msg:
        return jsonify(error="A required field is missing."), 400
    if "CHECK" in msg:
        return jsonify(error="A value is out of its allowed range."), 400
    return jsonify(error=msg), 400


@app.post("/api/<t>")
@login_required
def create(t):
    if t not in TABLES:
        return jsonify(error="Unknown module"), 404
    if not can_write(t):
        return jsonify(error="Your role cannot add records here."), 403
    try:
        d = clean(t, request.get_json(silent=True) or {})
        if t in STUDENT_SCOPED and t != "students" and not student_allowed(t, d):
            return jsonify(error="You can only edit your assigned students."), 403
        cur = db().execute(f"INSERT INTO {t}({','.join(d)}) VALUES({','.join('?' * len(d))})", list(d.values()))
        if t == "students":   # every new student automatically gets a portal login (username = student code)
            from init_db import STUDENT_PASSWORD
            db().execute("INSERT INTO users(username,password_hash,role,full_name,student_id) VALUES(?,?,?,?,?)",
                         (str(d.get("student_code", f"stu{cur.lastrowid}")).lower(), generate_password_hash(STUDENT_PASSWORD), "student", d.get("name"), cur.lastrowid))
        db().commit()
        return jsonify(id=cur.lastrowid), 201
    except (sqlite3.Error, ValueError) as e:
        return db_error(e)


@app.put("/api/<t>/<int:rid>")
@login_required
def update(t, rid):
    if t not in TABLES:
        return jsonify(error="Unknown module"), 404
    if not can_write(t):
        return jsonify(error="Your role cannot edit records here."), 403
    try:
        d = clean(t, request.get_json(silent=True) or {})
        if t in STUDENT_SCOPED and t != "students" and not student_allowed(t, d, rid):
            return jsonify(error="You can only edit your assigned students."), 403
        if not d:
            return jsonify(error="Nothing to update."), 400
        cur = db().execute(f"UPDATE {t} SET {','.join(k + '=?' for k in d)} WHERE id=?", list(d.values()) + [rid])
        db().commit()
        return jsonify(updated=cur.rowcount) if cur.rowcount else (jsonify(error="Record not found."), 404)
    except (sqlite3.Error, ValueError) as e:
        return db_error(e)


@app.delete("/api/<t>/<int:rid>")
@login_required
def delete(t, rid):
    if t not in TABLES:
        return jsonify(error="Unknown module"), 404
    if not can_write(t):
        return jsonify(error="Your role cannot delete records here."), 403
    if t in STUDENT_SCOPED and t != "students" and not student_allowed(t, {}, rid):
        return jsonify(error="You can only edit your assigned students."), 403
    cur = db().execute(f"DELETE FROM {t} WHERE id=?", (rid,))
    db().commit()
    return jsonify(deleted=cur.rowcount) if cur.rowcount else (jsonify(error="Record not found."), 404)


# ---------------- Student profile & dashboard ----------------
@app.get("/api/students/<int:sid>/profile")
@login_required
def profile(sid):
    base, _ = select_for("students")
    sc, a = scope_sql()
    s = db().execute(base + " WHERE s.id=?" + sc, [sid] + a).fetchone()
    if not s:
        return jsonify(error="Student not found or not assigned to you."), 404
    one = lambda t: (rows(f"SELECT * FROM {t} WHERE student_id=?", (sid,)) or [None])[0]
    many = lambda t: rows(f"SELECT * FROM {t} WHERE student_id=?", (sid,))
    return jsonify(student=dict(s), academics=one("academics"), soft_skills=one("soft_skills"), assessments=one("assessments"),
                   placement=one("placements"), tech_skills=many("tech_skills"), projects=many("projects"),
                   internships=many("internships"), certifications=many("certifications"))


@app.get("/api/dashboard")
@login_required
def dashboard():
    if session["role"] == "faculty":
        sc, a = " WHERE s.faculty_id=?", [session.get("faculty_id")]
    else:
        sc, a = "", []
    q = lambda sql: rows(sql + "", a)
    one = lambda sql: db().execute(sql, a).fetchone()[0]
    J = "FROM students s JOIN academics ac ON ac.student_id=s.id JOIN placements p ON p.student_id=s.id" + sc
    total = one("SELECT COUNT(*) FROM students s" + sc)
    placed = one("SELECT COUNT(*) " + J + (" AND" if sc else " WHERE") + " p.status='Placed'")
    eligible = one("SELECT COUNT(*) " + J + (" AND" if sc else " WHERE") + " p.eligible='Eligible'")
    avg = lambda col: round(one(f"SELECT COALESCE(AVG({col}),0) " + J), 2)
    cg = [r["cgpa"] for r in q("SELECT ac.cgpa " + J)]
    buckets = [("< 6", 0, 6), ("6 - 7", 6, 7), ("7 - 8", 7, 8), ("8 - 9", 8, 9), ("9+", 9, 11)]
    skill_sql = ("SELECT ts.skill, ROUND(AVG(ts.score),1) avg_score, COUNT(*) students FROM tech_skills ts JOIN students s ON s.id=ts.student_id"
                 + sc + " GROUP BY ts.skill ORDER BY avg_score DESC")
    return jsonify(
        totals=dict(students=total, faculty=db().execute("SELECT COUNT(*) FROM faculty").fetchone()[0],
                    departments=db().execute("SELECT COUNT(*) FROM departments").fetchone()[0], placed=placed,
                    unplaced=total - placed, eligible=eligible, placement_pct=round(placed * 100 / eligible, 1) if eligible else 0,
                    placed_of_total_pct=round(placed * 100 / total, 1) if total else 0,
                    avg_cgpa=avg("ac.cgpa"), avg_attendance=avg("ac.attendance")),
        cgpa_distribution=[dict(label=l, count=sum(lo <= c < hi for c in cg)) for l, lo, hi in buckets],
        by_course=q("SELECT s.course label, COUNT(*) count " + "FROM students s" + sc + " GROUP BY s.course ORDER BY count DESC"),
        by_gender=q("SELECT s.gender label, COUNT(*) count FROM students s" + sc + " GROUP BY s.gender"),
        by_department=q("SELECT d.name label, COUNT(*) count FROM students s JOIN departments d ON d.id=s.department_id" + sc + " GROUP BY d.name"),
        performance=q("SELECT ac.performance label, COUNT(*) count " + J + " GROUP BY ac.performance"),
        avg_cgpa_by_course=q("SELECT s.course label, ROUND(AVG(ac.cgpa),2) value " + J + " GROUP BY s.course"),
        skills=q(skill_sql),
        placement_by_course=q("SELECT s.course label, SUM(p.status='Placed') placed, SUM(p.eligible='Eligible' AND p.status!='Placed') unplaced_eligible " + J + " GROUP BY s.course"),
        top_companies=q("SELECT p.company label, COUNT(*) count " + J + (" AND" if sc else " WHERE") + " p.status='Placed' GROUP BY p.company ORDER BY count DESC LIMIT 8"),
        salary_bands=q("SELECT CASE WHEN p.package_lpa<4 THEN '< 4 LPA' WHEN p.package_lpa<6 THEN '4 - 6 LPA' WHEN p.package_lpa<10 THEN '6 - 10 LPA' ELSE '10+ LPA' END label, COUNT(*) count "
                       + J + (" AND" if sc else " WHERE") + " p.status='Placed' GROUP BY label"),
    )


# ---------------- AI module (prediction, skill test, skill-gap analysis) ----------------
import ai_routes
ai_routes.init(app, db, DB)


# ---------------- Frontend ----------------
@app.get("/")
def index():
    return send_from_directory(FRONT, "index.html")


@app.get("/<path:path>")
def static_files(path):
    if path.startswith("api/"):
        return jsonify(error="Not found"), 404
    return send_from_directory(FRONT, path)


if __name__ == "__main__":
    if not os.path.exists(DB):
        import init_db
        init_db.build()
    try:
        import ml
        st = ml.get_state(DB)   # train the placement model once at start-up
        print(f"AI model ready: {st['name']} (AUC {st['metrics']['auc']:.2f}, trained on {st['n_train']} historical records)")
    except Exception as e:   # the ERP still works if ML libraries are missing
        print("WARNING: AI model could not be trained:", e)
    app.run(debug=False, port=5000)

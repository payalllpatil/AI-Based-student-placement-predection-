"""AI endpoints: adaptive skill test, placement prediction and skill-gap report. Reads live data from the ERP tables."""
import datetime, json, random
from flask import Blueprint, jsonify, request, session
import ml, roles, question_bank as qb

bp = Blueprint("ai", __name__, url_prefix="/api/ai")
db = None          # set by init(): returns the request-scoped sqlite connection
DB_PATH = None
TEST_MINUTES = 30
COURSE_SEMS = {"MCA": 4, "BCA": 6, "BSc Computer Science": 6, "BE Computer Engineering": 8}
now = lambda: datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def init(app, get_db, path):
    global db, DB_PATH
    db, DB_PATH = get_db, path
    app.register_blueprint(bp)


def state():
    return ml.get_state(DB_PATH)


@bp.before_request
def guard():
    if "uid" not in session:
        return jsonify(error="Please sign in."), 401


def rows(sql, args=()):
    return [dict(r) for r in db().execute(sql, args).fetchall()]


def resolve_student():
    """Students may only access themselves; faculty only their assigned students."""
    if session["role"] == "student":
        return session["student_id"], None
    sid = request.args.get("student_id", type=int) or (request.get_json(silent=True) or {}).get("student_id")
    if not sid:
        return None, (jsonify(error="student_id is required."), 400)
    if session["role"] == "faculty" and not db().execute("SELECT 1 FROM students WHERE id=? AND faculty_id=?", (sid, session.get("faculty_id"))).fetchone():
        return None, (jsonify(error="Student not found or not assigned to you."), 404)
    return sid, None


def staff_only():
    if session["role"] == "student":
        return jsonify(error="Not available for student accounts."), 403


# ---------- test results -> effective profile ----------
def latest_results(sid):
    sk, apt = {}, {}
    for r in rows("""SELECT r.kind, r.name, r.score FROM test_results r JOIN tests t ON t.id=r.test_id
                     WHERE r.student_id=? AND t.status='submitted' ORDER BY t.submitted_at, t.id""", (sid,)):
        (sk if r["kind"] == "skill" else apt)[r["name"]] = r["score"]
    return sk, apt


def student_row(sid):
    r = db().execute("""SELECT s.id, s.name, s.student_code, s.course, s.semester, d.name department, p.preferred_role, p.status, p.company,
                        p.package_lpa, p.eligible, a.cgpa, a.current_backlogs FROM students s LEFT JOIN departments d ON d.id=s.department_id
                        LEFT JOIN placements p ON p.student_id=s.id LEFT JOIN academics a ON a.student_id=s.id WHERE s.id=?""", (sid,)).fetchone()
    return dict(r) if r else None


def role_for(stu, requested=None):
    for r in (requested, stu.get("preferred_role")):
        if r in roles.ROLES:
            return r
    return roles.DEFAULT_ROLE


# ---------- report ----------
def build_report(sid, requested_role=None):
    stu = student_row(sid)
    if not stu:
        return None
    b = ml.load_bundles(db(), sid)[sid]
    sk, apt = latest_results(sid)
    tested = bool(sk or apt)
    eb = ml.apply_test(b, sk, apt) if tested else b
    st = state()
    pred = ml.predict(eb, st, None if tested else sid)
    role = role_for(stu, requested_role)
    gaps, readiness = roles.analyse(eb, role, verified=set(sk))
    ranking = sorted([dict(role=r, readiness=roles.analyse(eb, r, set(sk))[1]) for r in roles.ROLES], key=lambda x: -x["readiness"])
    # what-if: close the three biggest technical/assessment gaps and re-predict
    b2 = {**eb, "skills": dict(eb["skills"]), "assess": dict(eb["assess"])}
    key_of = {v: k for k, v in roles.APT_LABELS.items()}
    top = [g for g in gaps if g["gap"] and g["category"] in ("Technical", "Assessment")][:3]
    for g in top:
        if g["category"] == "Technical":
            b2["skills"][g["name"]] = g["target"]
        else:
            b2["assess"][key_of[g["name"]]] = g["target"]
    after = ml.predict(b2, st)["probability"] if top else pred["probability"]
    f_now, f_pl, f_un = ml.features(eb), None, None
    bench = [dict(label=ml.FEATURE_LABELS[f], student=round(f_now[ml.FEATURES.index(f)], 1), placed=round(st["bench"][f][0], 1), unplaced=round(st["bench"][f][1], 1)) for f in ml.BENCH]
    todo = [g for g in gaps if g["gap"]][:5]
    roadmap = [dict(step=i + 1, title=f"Raise {g['name']} from {g['current']} to {g['target']}", priority=g["priority"], weeks=max(1, -(-g["gap"] // 6)), detail=g["action"]) for i, g in enumerate(todo)]
    tests = rows("SELECT id, submitted_at, overall_score FROM tests WHERE student_id=? AND status='submitted' ORDER BY submitted_at DESC", (sid,))
    sections = rows("""SELECT kind, name, score, correct, total FROM test_results WHERE test_id=? ORDER BY kind DESC, name""", (tests[0]["id"],)) if tests else []
    eligible, why = stu["eligible"] == "Eligible", []
    if not eligible:
        if stu["semester"] < COURSE_SEMS.get(stu["course"], 6) - 1:
            why.append("Not yet in the final year (placement drives start in the last two semesters)")
        if (stu["cgpa"] or 0) < 6:
            why.append("CGPA is below the usual 6.0 cut-off")
        if (stu["current_backlogs"] or 0) > 1:
            why.append("More than one active backlog")
    return dict(
        student=stu, role=role, roles=ranking, readiness=readiness, eligibility=dict(eligible=eligible, reasons=why),
        data_source=dict(fetched_at=now(), tables=["students", "academics", "tech_skills", "soft_skills", "assessments", "projects", "internships", "certifications", "placements"],
                         tested=tested, tests_taken=len(tests), basis="ERP records + skill test results" if tested else "ERP records only (take the skill test to verify)"),
        prediction=dict(**pred, after_gaps=after, closed=[g["name"] for g in top], model=st["name"], auc=round(st["metrics"]["auc"], 3), basis=("ERP + test" if tested else "ERP only")),
        gaps=gaps, strengths=[g for g in gaps if not g["gap"]], benchmark=bench, roadmap=roadmap, test_sections=sections,
        history=rows("SELECT created_at date, probability, basis FROM predictions WHERE student_id=? ORDER BY id", (sid,)), tests=tests)


@bp.get("/report")
def report():
    sid, err = resolve_student()
    if err:
        return err
    r = build_report(sid, request.args.get("role"))
    return jsonify(r) if r else (jsonify(error="Student not found."), 404)


# ---------- adaptive test ----------
def public_questions(test_id):
    return [dict(id=q["id"], section=q["section"], skill=q["skill"], difficulty=q["difficulty"], text=q["text"], options=json.loads(q["options_json"]))
            for q in rows("SELECT * FROM test_questions WHERE test_id=? ORDER BY id", (test_id,))]


@bp.get("/tests")
def tests_list():
    sid, err = resolve_student()
    if err:
        return err
    open_t = rows("SELECT id, started_at FROM tests WHERE student_id=? AND status='started' ORDER BY id DESC LIMIT 1", (sid,))
    return jsonify(attempts=rows("SELECT id, role_name, submitted_at, overall_score FROM tests WHERE student_id=? AND status='submitted' ORDER BY id DESC", (sid,)),
                   in_progress=open_t[0] if open_t else None, minutes=TEST_MINUTES)


@bp.post("/test/start")
def test_start():
    if session["role"] != "student":
        return jsonify(error="Only students can take the skill test."), 403
    sid = session["student_id"]
    cur = rows("SELECT * FROM tests WHERE student_id=? AND status='started' ORDER BY id DESC LIMIT 1", (sid,))
    if cur:   # resume the unfinished attempt instead of generating a new one
        t = cur[0]
        left = max(0, TEST_MINUTES * 60 - int((datetime.datetime.now() - datetime.datetime.strptime(t["started_at"], "%Y-%m-%d %H:%M:%S")).total_seconds()))
        return jsonify(test_id=t["id"], seconds_left=left, plan=json.loads(t["plan_json"]), questions=public_questions(t["id"]), role=t["role_name"], resumed=True)
    stu = student_row(sid)
    role = role_for(stu)
    b = ml.load_bundles(db(), sid)[sid]
    plan, qs = qb.build_test(b, roles.ROLES[role], role, random.Random())
    c = db().execute("INSERT INTO tests(student_id, role_name, status, started_at, duration_min, plan_json) VALUES(?,?,?,?,?,?)",
                     (sid, role, "started", now(), TEST_MINUTES, json.dumps(plan)))
    tid = c.lastrowid
    for q in qs:
        db().execute("INSERT INTO test_questions(test_id, section, skill, difficulty, text, options_json, correct_idx) VALUES(?,?,?,?,?,?,?)",
                     (tid, q["section"], q["skill"], q["difficulty"], q["text"], json.dumps(q["options"]), q["correct"]))
    db().commit()
    return jsonify(test_id=tid, seconds_left=TEST_MINUTES * 60, plan=plan, questions=public_questions(tid), role=role, resumed=False), 201


@bp.post("/test/<int:tid>/submit")
def test_submit(tid):
    if session["role"] != "student":
        return jsonify(error="Only students can submit tests."), 403
    sid = session["student_id"]
    t = db().execute("SELECT * FROM tests WHERE id=? AND student_id=?", (tid, sid)).fetchone()
    if not t:
        return jsonify(error="Test not found."), 404
    if t["status"] == "submitted":
        return jsonify(error="This test was already submitted."), 409
    answers = (request.get_json(silent=True) or {}).get("answers", {})
    had_history = db().execute("SELECT 1 FROM predictions WHERE student_id=?", (sid,)).fetchone()
    if not had_history:   # store the ERP-only baseline so progress can be shown later
        base = ml.predict(ml.load_bundles(db(), sid)[sid], state(), sid)
        db().execute("INSERT INTO predictions(student_id, test_id, probability, label, est_package, basis, created_at) VALUES(?,?,?,?,?,?,?)",
                     (sid, None, base["probability"], base["label"], base["package"]["value"], "ERP only", t["started_at"]))
    agg = {}
    for q in rows("SELECT * FROM test_questions WHERE test_id=?", (tid,)):
        ch = answers.get(str(q["id"]))
        ch = int(ch) if ch is not None and str(ch).lstrip("-").isdigit() else None
        ok = 1 if ch == q["correct_idx"] else 0
        db().execute("UPDATE test_questions SET chosen_idx=?, is_correct=? WHERE id=?", (ch, ok, q["id"]))
        kind, name = ("skill", q["skill"]) if q["section"] == "Technical" else ("aptitude", q["section"])
        a = agg.setdefault((kind, name), dict(w=0.0, got=0.0, c=0, n=0))
        w = qb.WEIGHT[q["difficulty"]]
        a["w"] += w; a["got"] += w * ok; a["c"] += ok; a["n"] += 1
    scores = []
    for (kind, name), a in agg.items():
        sc = round(100 * a["got"] / a["w"], 1)
        scores.append(sc)
        db().execute("INSERT INTO test_results(test_id, student_id, kind, name, score, correct, total) VALUES(?,?,?,?,?,?,?)", (tid, sid, kind, name, sc, a["c"], a["n"]))
    overall = round(sum(scores) / len(scores), 1) if scores else 0
    db().execute("UPDATE tests SET status='submitted', submitted_at=?, overall_score=? WHERE id=?", (now(), overall, tid))
    db().commit()
    rep = build_report(sid)
    pr = rep["prediction"]
    db().execute("INSERT INTO predictions(student_id, test_id, probability, label, est_package, basis, created_at) VALUES(?,?,?,?,?,?,?)",
                 (sid, tid, pr["probability"], pr["label"], pr["package"]["value"], "ERP + test", now()))
    db().commit()
    return jsonify(test_id=tid, overall=overall, probability=pr["probability"], label=pr["label"])


@bp.get("/test/<int:tid>/result")
def test_result(tid):
    sid, err = resolve_student()
    if err:
        return err
    t = db().execute("SELECT * FROM tests WHERE id=? AND student_id=? AND status='submitted'", (tid, sid)).fetchone()
    if not t:
        return jsonify(error="Result not found."), 404
    qs = [dict(section=q["section"], skill=q["skill"], difficulty=q["difficulty"], text=q["text"], options=json.loads(q["options_json"]), correct=q["correct_idx"], chosen=q["chosen_idx"], ok=bool(q["is_correct"]))
          for q in rows("SELECT * FROM test_questions WHERE test_id=? ORDER BY id", (tid,))]
    return jsonify(test=dict(t), results=rows("SELECT kind, name, score, correct, total FROM test_results WHERE test_id=? ORDER BY kind DESC, name", (tid,)), questions=qs, plan=json.loads(t["plan_json"]))


# ---------- staff: model + cohort ----------
@bp.get("/model")
def model_info():
    e = staff_only()
    if e:
        return e
    st = state()
    ps = list(st["full"].values())
    dist = [sum(lo <= p * 100 < hi for p in ps) for lo, hi in [(0, 20), (20, 40), (40, 60), (60, 80), (80, 101)]]
    return jsonify(name=st["name"], metrics=st["metrics"], importances=st["importances"], candidates=st["candidates"], n_train=st["n_train"], n_placed=st["n_placed"],
                   trained_at=st["trained_at"], mae=round(st["mae"], 2), distribution=dist, avg_package=round(st["placed_package_mean"], 1))


@bp.post("/model/retrain")
def retrain():
    if session["role"] != "admin":
        return jsonify(error="Only admin can retrain the model."), 403
    ml.get_state(DB_PATH, retrain=True)
    return model_info()


@bp.get("/cohort")
def cohort():
    e = staff_only()
    if e:
        return e
    st, role = state(), request.args.get("role", roles.DEFAULT_ROLE)
    if role not in roles.ROLES:
        role = roles.DEFAULT_ROLE
    scope, args = ("WHERE s.faculty_id=?", [session.get("faculty_id")]) if session["role"] == "faculty" else ("", [])
    meta = rows(f"""SELECT s.id, s.name, s.student_code, s.course, p.preferred_role, p.status, p.eligible FROM students s
                    JOIN placements p ON p.student_id=s.id {scope}""", args)
    bundles = ml.load_bundles(db())
    at_risk, gap_sum, gap_n = [], {}, {}
    for m in meta:
        if m["eligible"] != "Eligible":
            continue
        prob = st["oof"].get(m["id"], st["full"].get(m["id"], 0))
        items, ready = roles.analyse(bundles[m["id"]], role_for(m))
        if m["status"] != "Placed":
            at_risk.append(dict(id=m["id"], name=m["name"], code=m["student_code"], course=m["course"], role=role_for(m), probability=round(100 * prob, 1),
                                readiness=ready, top_gap=next((f"{g['name']} (-{g['gap']})" for g in items if g["gap"]), "None")))
    for m in meta:   # cohort-wide skill gaps for the selected role (all students in scope)
        for g in roles.analyse(bundles[m["id"]], role)[0]:
            gap_sum[g["name"]] = gap_sum.get(g["name"], 0) + g["gap"]
            gap_n[g["name"]] = gap_n.get(g["name"], 0) + 1
    gaps = sorted([dict(name=k, avg_gap=round(v / gap_n[k], 1)) for k, v in gap_sum.items()], key=lambda x: -x["avg_gap"])
    at_risk.sort(key=lambda x: x["probability"])
    return jsonify(role=role, roles=list(roles.ROLES), at_risk=at_risk[:25], at_risk_total=len(at_risk), cohort_gaps=gaps)

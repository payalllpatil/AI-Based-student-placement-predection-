"""Placement prediction model trained on the ERP's historical placed/unplaced records."""
import datetime, sqlite3, threading
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score, mean_absolute_error, precision_score,
                             recall_score, roc_auc_score)
from sklearn.model_selection import KFold, StratifiedKFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

SOFT = ["verbal", "written", "english", "presentation", "group_discussion", "teamwork", "leadership", "problem_solving",
        "time_management", "confidence", "adaptability"]
ASSESS = ["quant", "logical", "verbal_ability", "coding", "tech_mcq", "programming", "mock_interview"]
FEATURES = ["cgpa", "ssc", "hsc", "attendance", "backlogs", "tech_avg", "tech_top3", "n_skills", "soft_avg"] + ASSESS + \
           ["n_projects", "n_internships", "n_certs", "n_events"]
FEATURE_LABELS = {"cgpa": "CGPA", "ssc": "SSC %", "hsc": "HSC %", "attendance": "Attendance", "backlogs": "Backlogs", "tech_avg": "Avg technical skill",
                  "tech_top3": "Top-3 technical skills", "n_skills": "Number of skills", "soft_avg": "Soft skills average", "quant": "Quantitative aptitude",
                  "logical": "Logical reasoning", "verbal_ability": "Verbal ability", "coding": "Coding test", "tech_mcq": "Technical MCQ",
                  "programming": "Programming test", "mock_interview": "Mock interview", "n_projects": "Projects", "n_internships": "Internships",
                  "n_certs": "Certifications", "n_events": "Hackathons / achievements"}
GROUPS = {"Academics": ["cgpa", "ssc", "hsc", "attendance", "backlogs"],
          "Technical skills": ["tech_avg", "tech_top3", "n_skills"],
          "Soft skills": ["soft_avg"],
          "Aptitude and tests": ASSESS,
          "Projects, internships, certificates": ["n_projects", "n_internships", "n_certs", "n_events"]}
BENCH = ["cgpa", "attendance", "tech_avg", "soft_avg", "quant", "logical", "verbal_ability", "coding", "mock_interview"]


def connect(path):
    c = sqlite3.connect(path)
    c.row_factory = sqlite3.Row
    return c


def load_bundles(db, sid=None):
    """Fetch everything the AI module needs about students straight from the ERP tables."""
    w, a = (" WHERE student_id=?", (sid,)) if sid else ("", ())
    out = {}
    for r in db.execute("SELECT id FROM students" + (" WHERE id=?" if sid else ""), a):
        out[r["id"]] = dict(id=r["id"], acad={}, skills={}, levels={}, soft={}, assess={}, n_projects=0, n_internships=0, intern_months=0, n_certs=0, n_events=0)
    for r in db.execute("SELECT * FROM academics" + w, a):
        out[r["student_id"]]["acad"] = dict(r)
    for r in db.execute("SELECT student_id, skill, level, score FROM tech_skills" + w, a):
        out[r["student_id"]]["skills"][r["skill"]] = r["score"] or 0
        out[r["student_id"]]["levels"][r["skill"]] = r["level"]
    for r in db.execute("SELECT * FROM soft_skills" + w, a):
        out[r["student_id"]]["soft"] = {k: r[k] for k in SOFT}
    for r in db.execute("SELECT * FROM assessments" + w, a):
        out[r["student_id"]]["assess"] = {k: r[k] for k in ASSESS}
    for t, key in (("projects", "n_projects"), ("internships", "n_internships")):
        for r in db.execute(f"SELECT student_id, COUNT(*) n FROM {t}{w} GROUP BY student_id", a):
            out[r["student_id"]][key] = r["n"]
    for r in db.execute("SELECT student_id, SUM(duration_months) m FROM internships" + w + " GROUP BY student_id", a):
        out[r["student_id"]]["intern_months"] = r["m"] or 0
    for r in db.execute("SELECT student_id, kind, COUNT(*) n FROM certifications" + w + " GROUP BY student_id, kind", a):
        out[r["student_id"]]["n_certs" if r["kind"] == "Certification" else "n_events"] += r["n"]
    return out


def features(b):
    g = lambda v: float(v) if v is not None else 0.0
    ac, sk = b["acad"], sorted(b["skills"].values(), reverse=True)
    soft = [v for v in b["soft"].values() if v is not None]
    f = dict(cgpa=g(ac.get("cgpa")) * 10, ssc=g(ac.get("ssc")), hsc=g(ac.get("hsc")), attendance=g(ac.get("attendance")),
             backlogs=g(ac.get("current_backlogs")) + g(ac.get("previous_backlogs")),
             tech_avg=float(np.mean(sk)) if sk else 0.0, tech_top3=float(np.mean(sk[:3])) if sk else 0.0, n_skills=float(len(sk)),
             soft_avg=float(np.mean(soft)) if soft else 0.0, n_projects=g(b["n_projects"]), n_internships=g(b["n_internships"]),
             n_certs=g(b["n_certs"]), n_events=g(b["n_events"]))
    for k in ASSESS:
        f[k] = g(b["assess"].get(k))
    return [f[k] for k in FEATURES]


def apply_test(b, skill_scores, apt_scores):
    """Blend ERP self-reported values with measured test scores (tests carry more weight than self-reports)."""
    nb = {**b, "skills": dict(b["skills"]), "assess": dict(b["assess"])}
    for sk, s in skill_scores.items():
        nb["skills"][sk] = round(0.7 * s + 0.3 * b["skills"][sk]) if sk in b["skills"] else round(s)
    for key, name in (("quant", "Quantitative Aptitude"), ("logical", "Logical Reasoning"), ("verbal_ability", "Verbal Ability")):
        if name in apt_scores:
            nb["assess"][key] = round(0.5 * (b["assess"].get(key) or 0) + 0.5 * apt_scores[name])
    if skill_scores:
        nb["assess"]["tech_mcq"] = round(0.5 * (b["assess"].get("tech_mcq") or 0) + 0.5 * float(np.mean(list(skill_scores.values()))))
    return nb


_LOCK, STATE = threading.Lock(), {}


def train(db_path):
    db = connect(db_path)
    bundles = load_bundles(db)
    ids = sorted(bundles)
    X = np.array([features(bundles[i]) for i in ids])
    pl = {r["student_id"]: r for r in db.execute("SELECT student_id, eligible, status, package_lpa FROM placements")}
    db.close()
    tr = [k for k, i in enumerate(ids) if pl[i]["eligible"] == "Eligible"]
    y = np.array([1 if pl[ids[k]]["status"] == "Placed" else 0 for k in tr])
    Xt = X[tr]
    cv = StratifiedKFold(5, shuffle=True, random_state=7)
    cands = {"Logistic Regression": make_pipeline(StandardScaler(), LogisticRegression(C=0.5, max_iter=2000)),
             "Random Forest": RandomForestClassifier(300, max_depth=5, min_samples_leaf=4, random_state=7)}
    scored = {}
    for name, m in cands.items():
        oof = cross_val_predict(m, Xt, y, cv=cv, method="predict_proba")[:, 1]
        scored[name] = (roc_auc_score(y, oof), oof)
    best = max(scored, key=lambda n: scored[n][0])
    clf, oof = cands[best], scored[best][1]
    clf.fit(Xt, y)
    pred = (oof >= 0.5).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred).ravel()
    if best == "Random Forest":
        imp = clf.feature_importances_
    else:
        imp = np.abs(clf[-1].coef_[0])
        imp = imp / imp.sum()
    placed_k = [k for k in range(len(tr)) if y[k] == 1 and pl[ids[tr[k]]]["package_lpa"]]
    reg = RandomForestRegressor(300, min_samples_leaf=3, random_state=7)
    Xp, yp = Xt[placed_k], np.array([pl[ids[tr[k]]]["package_lpa"] for k in placed_k])
    mae = mean_absolute_error(yp, cross_val_predict(reg, Xp, yp, cv=KFold(5, shuffle=True, random_state=7)))
    reg.fit(Xp, yp)
    allp = clf.predict_proba(X)[:, 1]
    full = {ids[k]: float(allp[k]) for k in range(len(ids))}
    oof_map = {ids[tr[k]]: float(oof[k]) for k in range(len(tr))}  # out-of-fold: no leakage for known students
    bench = {f: (float(Xt[y == 1][:, FEATURES.index(f)].mean()), float(Xt[y == 0][:, FEATURES.index(f)].mean())) for f in BENCH}
    return dict(clf=clf, reg=reg, name=best, mae=float(mae), means=Xt.mean(0), bench=bench, full=full, oof=oof_map,
                importances=sorted([(FEATURE_LABELS[f], float(v)) for f, v in zip(FEATURES, imp)], key=lambda t: -t[1]),
                metrics=dict(accuracy=accuracy_score(y, pred), precision=precision_score(y, pred), recall=recall_score(y, pred),
                             f1=f1_score(y, pred), auc=scored[best][0], confusion=[[int(tn), int(fp)], [int(fn), int(tp)]]),
                candidates=[dict(name=n, auc=round(v[0], 3)) for n, v in scored.items()], n_train=len(tr), n_placed=int(y.sum()),
                trained_at=datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), placed_package_mean=float(yp.mean()))


def get_state(db_path, retrain=False):
    with _LOCK:
        if retrain or not STATE:
            STATE.clear()
            STATE.update(train(db_path))
        return STATE


def label(p):
    return "High" if p >= 0.65 else "Medium" if p >= 0.40 else "Low"


def predict(b, st, known_sid=None):
    """Probability of placement + package estimate + per-group impact. known_sid -> use out-of-fold probability."""
    x = np.array([features(b)])
    p = float(st["oof"][known_sid]) if known_sid in st["oof"] else float(st["clf"].predict_proba(x)[0, 1])
    drivers = []
    for gname, feats in GROUPS.items():
        x2 = x.copy()
        for f in feats:
            x2[0, FEATURES.index(f)] = st["means"][FEATURES.index(f)]
        drivers.append(dict(group=gname, impact=round(100 * (float(st["clf"].predict_proba(x)[0, 1]) - float(st["clf"].predict_proba(x2)[0, 1])), 1)))
    pk = float(st["reg"].predict(x)[0])
    return dict(probability=round(100 * p, 1), label=label(p), drivers=drivers,
                package=dict(value=round(pk, 1), low=round(max(3.0, pk - st["mae"]), 1), high=round(pk + st["mae"], 1)))

# AI-Based Student Placement Prediction and Skill Gap Analysis (integrated with College ERP)

An MCA final-year project. The college ERP (students, academics, skills, assessments, projects, certifications, placements) is the
data source. On top of it, an AI layer gives every student:
1. a **personalised skill test** generated from their ERP skills,
2. a **placement prediction** (probability, expected package band, what drives it),
3. a **skill gap analysis** against a target job role, with a roadmap and a "what if I close my gaps" projection.

Stack: React (CDN) + Chart.js, Flask REST API, SQLite, scikit-learn.

## Logins
| Role | Username | Password | What they see |
|---|---|---|---|
| Student | `stu2002` (any `stu2001` to `stu2520`) | `student123` | Own placement report, skill test, own ERP profile only |
| Admin | `admin` | `admin123` | Full ERP + AI insights + retrain model |
| Faculty | `faculty1` | `faculty123` | Assigned students + AI insights/reports for them |
| Placement Officer | `placement` | `placement123` | All students' data, AI insights and reports |

## Run (VS Code terminal, from the project root folder that contains requirements.txt)
```
python -m venv venv
venv\Scripts\activate            (macOS/Linux: source venv/bin/activate)
pip install -r requirements.txt
cd backend
python app.py
```
Open http://127.0.0.1:5000. On start-up the terminal prints `AI model ready: ...` (training takes a few seconds).
Internet is needed for the React/Chart.js CDN scripts. To rebuild the sample data: `python init_db.py` (deletes erp.db, so test attempts are lost).

## How the student flow works
1. Student signs in and sees the **Placement report** built from ERP data only (marked "ERP records only").
2. **Skill test**: the server reads the student's ERP skills and builds a ~33-question, 30-minute test:
   - the student's 4 strongest recorded skills are *verified*;
   - up to 2 skills the target role needs but the ERP lacks or rates low are *probed*;
   - difficulty follows the ERP score (low: easy/medium, mid: easy to hard mix, high: medium/hard);
   - plus 9 generated aptitude questions (quantitative, logical, verbal). Correct answers never reach the browser.
3. On submit, scores are weighted by difficulty (Easy 1, Medium 1.5, Hard 2) and stored per skill and aptitude area.
4. The report is recomputed from **ERP + test**: measured skill = 70% test + 30% ERP; aptitude and technical-MCQ values blend 50/50.
5. The report shows prediction, drivers, peer benchmark, role readiness ranking, gap table, roadmap, what-if and probability history.

## The AI
- **Training data**: historical placed/unplaced outcomes of eligible students in the ERP (231 records), 20 features
  (CGPA, SSC/HSC, attendance, backlogs, skill averages, soft skills, 7 assessment scores, projects, internships, certificates, hackathons).
- **Models compared by 5-fold cross-validated ROC-AUC**: Logistic Regression vs Random Forest; the best is used (currently Random Forest, AUC about 0.89).
  A Random Forest regressor estimates the package for placed students. Metrics, feature importance and confusion matrix are on the **AI insights** page.
- **No leakage**: for students already in the training set the report uses the out-of-fold probability.
- **Explanations**: each feature group is replaced by the cohort average and the change in probability is reported as its impact.
- **Skill gap**: `backend/roles.py` holds target scores for 9 job roles (technical, soft, assessment). Gap = target - current;
  priority Critical (30+), Moderate (15+), Minor, Met. Readiness = weighted % of targets met. Learning resources per skill are included.
- **What-if**: raises the 3 biggest technical/assessment gaps to target and re-runs the model.

## Files
```
backend/app.py            ERP API (login, CRUD, dashboard) + registers AI blueprint + student access guard
backend/ai_routes.py      /api/ai/*: report, test start/submit/result, model, cohort
backend/ml.py             ERP feature extraction, model training and comparison, prediction, explanations
backend/question_bank.py  102 technical MCQs (17 skills) + generated aptitude + adaptive test builder
backend/roles.py          Job-role profiles, learning resources, gap engine
backend/init_db.py        Schema (ERP + test/prediction tables), 520 dummy students, 520 student logins
frontend/ai.jsx           Skill test, report, review, AI insights screens
frontend/app.jsx          App shell, login, ERP modules, dashboard, profile
```

## Honest notes for your viva
- All data is synthetic. Placement outcomes were generated from rules (ability, CGPA, assessments plus noise), so the model learns those patterns.
  With real college data, retrain from the AI insights page (admin) and expect lower accuracy.
- 231 training records is small, so cross-validation is used for honest metrics.
- Role target scores are expert-set assumptions, not learned values; edit them in `roles.py`.
- Change `app.secret_key` and the default passwords before any real deployment.

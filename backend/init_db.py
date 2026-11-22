"""Creates the SQLite schema and seeds 520 fictional students. Run: python init_db.py"""
import os, random, sqlite3
from datetime import date, timedelta
from werkzeug.security import generate_password_hash

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "erp.db")

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE departments(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, hod TEXT, building TEXT);
CREATE TABLE faculty(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT, designation TEXT,
  department_id INTEGER REFERENCES departments(id) ON DELETE SET NULL);
CREATE TABLE users(id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
  role TEXT NOT NULL CHECK(role IN('admin','faculty','placement','student')), full_name TEXT,
  faculty_id INTEGER REFERENCES faculty(id) ON DELETE SET NULL,
  student_id INTEGER UNIQUE REFERENCES students(id) ON DELETE CASCADE);
CREATE TABLE students(id INTEGER PRIMARY KEY AUTOINCREMENT, student_code TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
  email TEXT, mobile TEXT, dob TEXT, gender TEXT, city TEXT, state TEXT, course TEXT,
  department_id INTEGER REFERENCES departments(id) ON DELETE SET NULL, specialization TEXT, semester INTEGER,
  academic_year TEXT, admission_year INTEGER, roll_no TEXT,
  faculty_id INTEGER REFERENCES faculty(id) ON DELETE SET NULL);
CREATE TABLE academics(id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER UNIQUE NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  ssc REAL, hsc REAL, graduation REAL, sgpa1 REAL, sgpa2 REAL, sgpa3 REAL, sgpa4 REAL, sgpa5 REAL, sgpa6 REAL,
  cgpa REAL, current_backlogs INTEGER DEFAULT 0, previous_backlogs INTEGER DEFAULT 0, attendance REAL, performance TEXT);
CREATE TABLE tech_skills(id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  skill TEXT NOT NULL, level TEXT, score INTEGER CHECK(score BETWEEN 0 AND 100), UNIQUE(student_id, skill));
CREATE TABLE soft_skills(id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER UNIQUE NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  verbal INTEGER, written INTEGER, english INTEGER, presentation INTEGER, group_discussion INTEGER, teamwork INTEGER,
  leadership INTEGER, problem_solving INTEGER, time_management INTEGER, confidence INTEGER, adaptability INTEGER);
CREATE TABLE assessments(id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER UNIQUE NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  quant INTEGER, logical INTEGER, verbal_ability INTEGER, coding INTEGER, tech_mcq INTEGER, programming INTEGER, mock_interview INTEGER);
CREATE TABLE projects(id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  title TEXT NOT NULL, description TEXT, technologies TEXT, domain TEXT, project_type TEXT);
CREATE TABLE internships(id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  company TEXT NOT NULL, role TEXT, duration_months INTEGER, performance TEXT);
CREATE TABLE certifications(id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  kind TEXT NOT NULL, name TEXT NOT NULL, organization TEXT, cert_date TEXT);
CREATE TABLE placements(id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER UNIQUE NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  eligible TEXT, preferred_role TEXT, preferred_industry TEXT, interview_history TEXT, company TEXT,
  status TEXT DEFAULT 'Unplaced', package_lpa REAL, placement_date TEXT);
CREATE TABLE tests(id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  role_name TEXT, status TEXT DEFAULT 'started', started_at TEXT, submitted_at TEXT, duration_min INTEGER, plan_json TEXT, overall_score REAL);
CREATE TABLE test_questions(id INTEGER PRIMARY KEY AUTOINCREMENT, test_id INTEGER NOT NULL REFERENCES tests(id) ON DELETE CASCADE,
  section TEXT, skill TEXT, difficulty TEXT, text TEXT, options_json TEXT, correct_idx INTEGER, chosen_idx INTEGER, is_correct INTEGER);
CREATE TABLE test_results(id INTEGER PRIMARY KEY AUTOINCREMENT, test_id INTEGER NOT NULL REFERENCES tests(id) ON DELETE CASCADE,
  student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE, kind TEXT, name TEXT, score REAL, correct INTEGER, total INTEGER);
CREATE TABLE predictions(id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  test_id INTEGER, probability REAL, label TEXT, est_package REAL, basis TEXT, created_at TEXT);
CREATE INDEX idx_tests_student ON tests(student_id);
CREATE INDEX idx_students_course ON students(course);
CREATE INDEX idx_tech_student ON tech_skills(student_id);
CREATE INDEX idx_cert_student ON certifications(student_id);
"""

STUDENT_PASSWORD = "student123"
R = random.Random(2026)
MALE = "Aarav Rohan Vihaan Arjun Karan Rahul Amit Sahil Nikhil Omkar Pranav Yash Siddharth Tushar Aditya Harsh Ketan Mayur Rushikesh Sumit Varun Kunal Abhishek Gaurav".split()
FEMALE = "Ananya Priya Sneha Pooja Neha Riya Kavya Isha Shruti Aditi Tanvi Divya Meera Sakshi Rutuja Komal Nidhi Payal Swati Anjali Vaishnavi Pallavi Mitali Trupti Simran".split()
LAST = "Patil Sharma Deshmukh Kulkarni Joshi Jadhav Gupta Verma Iyer Reddy Nair Singh Khan Shaikh More Pawar Shinde Gaikwad Mehta Shah Desai Chavan Bhosale Kale Thakur Yadav Mishra".split()
CITIES = [("Pune","Maharashtra"),("Mumbai","Maharashtra"),("Nagpur","Maharashtra"),("Nashik","Maharashtra"),("Aurangabad","Maharashtra"),
 ("Kolhapur","Maharashtra"),("Ahmedabad","Gujarat"),("Surat","Gujarat"),("Indore","Madhya Pradesh"),("Bhopal","Madhya Pradesh"),
 ("Bengaluru","Karnataka"),("Hyderabad","Telangana"),("Chennai","Tamil Nadu"),("Jaipur","Rajasthan"),("Lucknow","Uttar Pradesh"),("Panaji","Goa")]
DEPTS = [("Computer Applications","Dr. R. Menon","Block A"),("Computer Science","Dr. S. Kapoor","Block B"),
         ("Computer Engineering","Dr. A. Bhatt","Block C"),("Information Technology","Dr. P. Rao","Block D"),("Data Science & AI","Dr. M. Fernandes","Block E")]
# course: (dept index, max semester, years, specializations, weight)
COURSES = {
 "MCA": (0, 4, 2, ["Software Development","Data Science","Cloud Computing","AI & ML"], 35),
 "BCA": (0, 6, 3, ["Web Development","Software Development","Cloud Computing"], 22),
 "BSc Computer Science": (1, 6, 3, ["Data Science","Programming","Networking"], 23),
 "BE Computer Engineering": (2, 8, 4, ["AI & ML","Cyber Security","Software Engineering","Cloud Computing"], 20)}
SKILLS = ["Python","Java","C","C++","HTML","CSS","JavaScript","SQL","MySQL","React","Flask","Django",
          "Machine Learning","Artificial Intelligence","Data Science","AWS","Cloud Computing"]
SOFT = ["verbal","written","english","presentation","group_discussion","teamwork","leadership","problem_solving","time_management","confidence","adaptability"]
COMPANIES = [("TCS",3.6,7),("Infosys",3.6,6.5),("Wipro",3.5,6),("Capgemini",3.8,7.5),("Cognizant",4.0,7),("Accenture",4.5,8),
 ("Persistent Systems",5,9),("Zensar",4,6.5),("Tech Mahindra",3.5,6),("LTIMindtree",4,7),("Amazon",14,32),("Deloitte",7,12),("Mphasis",4,7),("Barclays",8,14),("Thoughtworks",9,16)]
ROLES = ["Software Developer","Data Analyst","Web Developer","QA Engineer","Cloud Engineer","ML Engineer","Backend Developer","Business Analyst","DevOps Engineer"]
INDUSTRIES = ["IT Services","Product Company","FinTech","Healthcare IT","E-commerce","Consulting","EdTech","Telecom"]
DOMAINS = ["Web Development","Machine Learning","Mobile App","Data Analytics","Cloud","IoT","Cyber Security","E-commerce","Healthcare"]
PROJ = ["Student Attendance Tracker","Online Exam Portal","Sales Forecasting Model","Library Management System","Chat Application","Movie Recommender",
 "Fake News Detector","Expense Manager","Hospital Appointment System","Resume Screening Tool","Weather Dashboard","Face Recognition Attendance",
 "Smart Parking System","Crop Disease Detector","Food Delivery App","Job Portal","Stock Price Predictor","Inventory Control System"]
INTERN = ["Software Intern","Web Development Intern","Data Analyst Intern","ML Intern","Support Engineer Intern","Cloud Intern"]
CERTS = [("Python for Everybody","Coursera"),("AWS Cloud Practitioner","Amazon Web Services"),("Java Programming","Oracle"),("SQL Bootcamp","Udemy"),
 ("Machine Learning Specialization","Stanford Online"),("React Developer","Meta"),("Azure Fundamentals","Microsoft"),("Data Science with Python","IBM"),
 ("Flask & REST APIs","Udemy"),("Web Design","freeCodeCamp"),("NPTEL Data Structures","NPTEL"),("Google IT Automation","Google")]
EVENTS = {"Workshop":["Full Stack Workshop","Cloud Computing Workshop","AI Bootcamp","Cyber Security Workshop"],
 "Hackathon":["Smart India Hackathon","HackWithInfy","College Hackathon","Devfolio Hack"],
 "Coding Competition":["CodeChef Contest","LeetCode Weekly","HackerRank Challenge","Codeforces Round"],
 "Technical Achievement":["Open-source contribution","Published research paper","Best Project Award","Technical paper presentation"]}


def clamp(v, lo=0, hi=100):
    return int(max(lo, min(hi, round(v))))


def level(s):
    return "Beginner" if s < 40 else "Intermediate" if s < 65 else "Advanced" if s < 85 else "Expert"


def rdate(y1, y2):
    d0 = date(y1, 1, 1)
    return (d0 + timedelta(days=R.randint(0, (date(y2, 12, 28) - d0).days))).isoformat()


def build(path=DB):
    if os.path.exists(path):
        os.remove(path)
    db = sqlite3.connect(path)
    db.executescript(SCHEMA)
    for d in DEPTS:
        db.execute("INSERT INTO departments(name,hod,building) VALUES(?,?,?)", d)
    desig = ["Professor", "Associate Professor", "Assistant Professor"]
    for i in range(20):
        n = f"{R.choice(['Dr.', 'Prof.'])} {R.choice(MALE + FEMALE)} {R.choice(LAST)}"
        db.execute("INSERT INTO faculty(name,email,designation,department_id) VALUES(?,?,?,?)",
                   (n, f"faculty{i+1}@dummycollege.edu", R.choice(desig), i % len(DEPTS) + 1))
    users = [("admin", "admin123", "admin", "System Administrator", None),
             ("faculty1", "faculty123", "faculty", "Faculty Member 1", 1),
             ("faculty2", "faculty123", "faculty", "Faculty Member 2", 2),
             ("placement", "placement123", "placement", "Placement Officer", None)]
    for u, p, r, n, f in users:
        db.execute("INSERT INTO users(username,password_hash,role,full_name,faculty_id) VALUES(?,?,?,?,?)",
                   (u, generate_password_hash(p), r, n, f))
    names, weights = list(COURSES), [COURSES[c][4] for c in COURSES]
    fac_by_dept = {}
    for fid, did in db.execute("SELECT id, department_id FROM faculty").fetchall():
        fac_by_dept.setdefault(did, []).append(fid)
    for i in range(1, 521):
        course = R.choices(names, weights)[0]
        di, maxsem, yrs, specs, _ = COURSES[course]
        if course == "MCA" and R.random() < .3:
            di = 4
        gender = R.choice(["Male", "Female"])
        first = R.choice(MALE if gender == "Male" else FEMALE)
        last = R.choice(LAST)
        city, state = R.choice(CITIES)
        adm = R.randint(2021, 2025) if course != "MCA" else R.randint(2023, 2025)
        year_idx = max(1, min(yrs, 2026 - adm))
        sem = max(1, min(maxsem, year_idx * 2 - R.randint(0, 1)))
        ab = max(15, min(97, R.gauss(62, 17)))  # "ability" drives correlated, realistic records
        age = 17 + yrs + 1 + R.randint(0, 3)
        db.execute("""INSERT INTO students(student_code,name,email,mobile,dob,gender,city,state,course,department_id,
            specialization,semester,academic_year,admission_year,roll_no,faculty_id) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                   (f"STU{2000+i}", f"{first} {last}", f"{first.lower()}.{last.lower()}{i}@student.dummycollege.edu",
                    f"{R.choice('6789')}{R.randint(100000000, 999999999)}", rdate(2026 - age, 2026 - age), gender, city, state,
                    course, di + 1, R.choice(specs), sem, "2025-2026", adm,
                    f"{course.split()[0][:3].upper()}{adm % 100}{i:04d}", R.choice(fac_by_dept[di + 1])))
        sid = i
        ssc = clamp(ab + R.gauss(8, 7), 45, 98)
        hsc = clamp(ab + R.gauss(4, 8), 40, 97)
        grad = clamp(ab + R.gauss(0, 7), 40, 95)
        sg = [round(max(4.0, min(9.9, 5.0 + ab * .046 + R.gauss(0, .45))), 2) if k < sem else None for k in range(6)]
        done = [x for x in sg if x]
        cgpa = round(sum(done) / len(done), 2)
        back = 0 if R.random() < max(.15, ab / 100) else R.randint(1, 4)
        att = round(max(45, min(99, 60 + ab * .35 + R.gauss(0, 6))), 1)
        perf = "Excellent" if cgpa >= 8.5 else "Good" if cgpa >= 7.5 else "Average" if cgpa >= 6.0 else "Needs Improvement"
        db.execute("""INSERT INTO academics(student_id,ssc,hsc,graduation,sgpa1,sgpa2,sgpa3,sgpa4,sgpa5,sgpa6,cgpa,
            current_backlogs,previous_backlogs,attendance,performance) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                   (sid, ssc, hsc, grad, *sg, cgpa, back, back + (R.randint(0, 2) if R.random() < .3 else 0), att, perf))
        pool = SKILLS[:] + (["C++", "C", "Python"] if course == "BE Computer Engineering" else [])
        for sk in R.sample(list(dict.fromkeys(pool)), R.randint(5, 9)):
            sc = clamp(ab + R.gauss(-5, 15))
            db.execute("INSERT INTO tech_skills(student_id,skill,level,score) VALUES(?,?,?,?)", (sid, sk, level(sc), sc))
        sv = [clamp(ab * .6 + 25 + R.gauss(0, 12)) for _ in SOFT]
        db.execute(f"INSERT INTO soft_skills(student_id,{','.join(SOFT)}) VALUES({','.join('?' * 12)})", (sid, *sv))
        a = [clamp(ab + R.gauss(0, 12)) for _ in range(7)]
        db.execute("INSERT INTO assessments(student_id,quant,logical,verbal_ability,coding,tech_mcq,programming,mock_interview) VALUES(?,?,?,?,?,?,?,?)", (sid, *a))
        for _ in range(R.randint(1, 3)):
            t, dom = R.choice(PROJ), R.choice(DOMAINS)
            db.execute("INSERT INTO projects(student_id,title,description,technologies,domain,project_type) VALUES(?,?,?,?,?,?)",
                       (sid, t, f"{t} built as part of the {course} curriculum with a focus on {dom.lower()}.",
                        ", ".join(R.sample(SKILLS[:13], 3)), dom, R.choice(["Individual", "Team"])))
        if R.random() < (.25 + ab / 200):
            db.execute("INSERT INTO internships(student_id,company,role,duration_months,performance) VALUES(?,?,?,?,?)",
                       (sid, R.choice(COMPANIES)[0], R.choice(INTERN), R.choice([1, 2, 3, 6]),
                        R.choices(["Excellent", "Good", "Satisfactory"], [ab, 60, 30])[0]))
        for _ in range(R.choices([0, 1, 2, 3, 4], [10, 30, 30, 20, 10])[0]):
            n, o = R.choice(CERTS)
            db.execute("INSERT INTO certifications(student_id,kind,name,organization,cert_date) VALUES(?,?,?,?,?)", (sid, "Certification", n, o, rdate(2023, 2026)))
        for kind, opts in EVENTS.items():
            if R.random() < (.12 + ab / 400):
                db.execute("INSERT INTO certifications(student_id,kind,name,organization,cert_date) VALUES(?,?,?,?,?)", (sid, kind, R.choice(opts), "Various", rdate(2023, 2026)))
        # Placement: only final-year students without backlogs are eligible; outcome depends on overall strength
        eligible = sem >= maxsem - 1 and cgpa >= 6.0 and back <= 1
        score = ab * .5 + cgpa * 4 + sum(a) / 7 * .2 + R.gauss(0, 8)
        status, comp, pkg, pdate, hist = "Unplaced", None, None, None, "No interviews yet"
        if eligible:
            rounds = R.randint(1, 5)
            hist = f"{rounds} interview(s) attended"
            if score > 82 or (score > 72 and R.random() < .5):
                cap = max(8, (score - 40) * .6)
                c, lo, hi = R.choice([x for x in COMPANIES if x[2] <= cap] or COMPANIES[:5])
                status, comp, pdate = "Placed", c, rdate(2025, 2026)
                pkg = round(min(hi, R.uniform(lo, lo + max(.5, (score - 55) * .3))), 1)
                hist = f"{rounds} interview(s), selected by {c}"
        db.execute("""INSERT INTO placements(student_id,eligible,preferred_role,preferred_industry,interview_history,company,
            status,package_lpa,placement_date) VALUES(?,?,?,?,?,?,?,?,?)""",
                   (sid, "Eligible" if eligible else "Not Eligible", R.choice(ROLES), R.choice(INDUSTRIES), hist, comp, status, pkg, pdate))
    stu_hash = generate_password_hash(STUDENT_PASSWORD)  # one shared demo password for all student accounts
    for sid, code, name in db.execute("SELECT id, student_code, name FROM students").fetchall():
        db.execute("INSERT INTO users(username,password_hash,role,full_name,student_id) VALUES(?,?,?,?,?)", (code.lower(), stu_hash, "student", name, sid))
    db.commit()
    db.close()


if __name__ == "__main__":
    build()
    c = sqlite3.connect(DB)
    print("Database created:", DB)
    for t in ["students", "faculty", "departments", "tech_skills", "projects", "internships", "certifications", "placements"]:
        print(f"  {t}: {c.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]}")
    print("  placed:", c.execute("SELECT COUNT(*) FROM placements WHERE status='Placed'").fetchone()[0],
          "| eligible:", c.execute("SELECT COUNT(*) FROM placements WHERE eligible='Eligible'").fetchone()[0])

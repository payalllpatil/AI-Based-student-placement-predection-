"""Job-role requirement profiles and the skill-gap engine."""

SOFT_LABELS = {"verbal": "Verbal Communication", "written": "Written Communication", "english": "English Proficiency",
               "presentation": "Presentation Skills", "group_discussion": "Group Discussion", "teamwork": "Teamwork",
               "leadership": "Leadership", "problem_solving": "Problem Solving", "time_management": "Time Management",
               "confidence": "Confidence", "adaptability": "Adaptability"}
APT_LABELS = {"quant": "Quantitative Aptitude", "logical": "Logical Reasoning", "verbal_ability": "Verbal Ability",
              "coding": "Coding Test", "tech_mcq": "Technical MCQ", "programming": "Programming Test", "mock_interview": "Mock Interview"}

# target score (0-100) a student should reach to be competitive for the role
ROLES = {
    "Software Developer": dict(tech={"Java": 70, "Python": 65, "SQL": 65, "JavaScript": 55, "C++": 50},
                               soft={"problem_solving": 70, "teamwork": 65, "verbal": 60}, apt={"logical": 65, "coding": 70, "programming": 65}),
    "Backend Developer": dict(tech={"Python": 70, "Flask": 65, "SQL": 70, "MySQL": 60, "Django": 55},
                              soft={"problem_solving": 70, "teamwork": 60, "time_management": 60}, apt={"logical": 65, "coding": 70, "programming": 65}),
    "Web Developer": dict(tech={"HTML": 75, "CSS": 70, "JavaScript": 75, "React": 65, "SQL": 50},
                          soft={"problem_solving": 60, "teamwork": 60, "adaptability": 60}, apt={"logical": 60, "coding": 60}),
    "Data Analyst": dict(tech={"SQL": 75, "Python": 70, "Data Science": 65, "MySQL": 55, "Machine Learning": 45},
                         soft={"problem_solving": 70, "written": 65, "presentation": 60}, apt={"quant": 70, "logical": 65}),
    "ML Engineer": dict(tech={"Python": 75, "Machine Learning": 75, "Artificial Intelligence": 65, "Data Science": 65, "SQL": 50},
                        soft={"problem_solving": 75, "written": 60}, apt={"quant": 70, "logical": 70, "coding": 65}),
    "Cloud Engineer": dict(tech={"AWS": 70, "Cloud Computing": 75, "Python": 55, "SQL": 50},
                           soft={"problem_solving": 65, "adaptability": 65, "teamwork": 60}, apt={"logical": 65, "tech_mcq": 65}),
    "DevOps Engineer": dict(tech={"Cloud Computing": 70, "AWS": 65, "Python": 60, "C": 40},
                            soft={"problem_solving": 70, "teamwork": 65, "time_management": 65}, apt={"logical": 65, "tech_mcq": 65, "programming": 60}),
    "QA Engineer": dict(tech={"Python": 55, "SQL": 60, "JavaScript": 50, "Java": 55},
                        soft={"written": 65, "problem_solving": 65, "time_management": 60}, apt={"logical": 65, "tech_mcq": 60}),
    "Business Analyst": dict(tech={"SQL": 65, "Data Science": 50, "Python": 40},
                             soft={"written": 75, "verbal": 75, "presentation": 70, "english": 75}, apt={"quant": 70, "logical": 65, "verbal_ability": 70}),
}
DEFAULT_ROLE = "Software Developer"

RESOURCES = {
    "Python": "Solve 3 problems a day on HackerRank/LeetCode (Python track) and build one small CLI or Flask project.",
    "Java": "Revise OOP, collections and exceptions with Oracle's Java tutorials; practise 20 collections questions on GeeksforGeeks.",
    "C": "Practise pointers, arrays and memory management; complete the C track on HackerRank.",
    "C++": "Study STL and OOP; solve 25 STL-based problems on CodeChef or GeeksforGeeks.",
    "HTML": "Rebuild two real pages using semantic HTML (MDN Web Docs) and validate them.",
    "CSS": "Practise Flexbox and Grid with Flexbox Froggy and Grid Garden, then clone a landing page.",
    "JavaScript": "Work through javascript.info (closures, async, DOM) and build a small to-do app without a framework.",
    "SQL": "Practise joins, GROUP BY/HAVING and subqueries on SQLZoo and LeetCode Database problems.",
    "MySQL": "Install MySQL locally; practise indexes, transactions and stored procedures on a sample database.",
    "React": "Follow the official react.dev tutorial, then build a CRUD app using hooks and a REST API.",
    "Flask": "Build a REST API with Flask + SQLite (auth, CRUD, validation) and deploy it.",
    "Django": "Complete the official Django polls tutorial, then add authentication and REST endpoints.",
    "Machine Learning": "Take Andrew Ng's ML Specialization and finish 2 Kaggle starter competitions.",
    "Artificial Intelligence": "Study search, knowledge representation and neural-network basics (CS50 AI), then implement A* and a small classifier.",
    "Data Science": "Learn pandas/matplotlib and complete one end-to-end EDA project on a Kaggle dataset.",
    "AWS": "Prepare for AWS Cloud Practitioner; practise S3, EC2, IAM and Lambda in the free tier.",
    "Cloud Computing": "Learn IaaS/PaaS/SaaS, scaling and containers; complete a cloud fundamentals certification.",
    "Quantitative Aptitude": "Practise percentages, ratios, time-work and interest sets (IndiaBix / PrepInsta) for 30 minutes daily.",
    "Logical Reasoning": "Do number series, coding-decoding and seating arrangements daily; take a timed mock each week.",
    "Verbal Ability": "Read an editorial daily, learn 10 new words a day and practise reading comprehension.",
    "Coding Test": "Take timed coding contests (HackerRank/CodeChef) twice a week; focus on arrays, strings and hashing.",
    "Technical MCQ": "Revise OS, DBMS, networks and OOP core concepts; attempt company-specific MCQ sets.",
    "Programming Test": "Practise data structures (arrays, linked lists, trees) with 2 problems every day.",
    "Mock Interview": "Schedule weekly mock interviews with faculty or peers and record yourself for feedback.",
    "Verbal Communication": "Join a speaking club, practise 2-minute self-introductions and explain concepts aloud.",
    "Written Communication": "Write short technical summaries and emails weekly; get them reviewed by faculty.",
    "English Proficiency": "Practise spoken English with apps or peers; watch and summarise English tech talks.",
    "Presentation Skills": "Present a project demo to your class and ask for structured feedback.",
    "Group Discussion": "Join weekly GD practice sessions; learn to open, structure and close points.",
    "Teamwork": "Take a team role in a group project or hackathon and use Git for collaboration.",
    "Leadership": "Lead a project module or student club activity and document the outcome.",
    "Problem Solving": "Solve one structured puzzle or algorithm problem daily and explain your approach.",
    "Time Management": "Plan weekly goals with a calendar and track deadlines for assignments and prep.",
    "Confidence": "Do mock interviews and present in front of small groups to build comfort.",
    "Adaptability": "Learn one new tool or framework each month and reflect on what changed.",
}


def priority(gap):
    return "Met" if gap <= 0 else "Critical" if gap >= 30 else "Moderate" if gap >= 15 else "Minor"


def analyse(b, role, verified=()):
    """Compare the student's (effective) profile with the target profile of a role."""
    prof = ROLES[role]
    items = []
    for sk, t in prof["tech"].items():
        cur = b["skills"].get(sk)
        items.append(dict(category="Technical", name=sk, current=cur if cur is not None else 0, target=t, w=2,
                          source="verified by test" if sk in verified else ("ERP record" if cur is not None else "not recorded in ERP")))
    for k, t in prof["soft"].items():
        items.append(dict(category="Soft skill", name=SOFT_LABELS[k], current=b["soft"].get(k) or 0, target=t, w=1, source="ERP record"))
    for k, t in prof["apt"].items():
        items.append(dict(category="Assessment", name=APT_LABELS[k], current=b["assess"].get(k) or 0, target=t, w=1, source="ERP / test"))
    num = den = 0
    for it in items:
        it["current"] = round(it["current"])
        it["gap"] = max(0, it["target"] - it["current"])
        it["priority"] = priority(it["target"] - it["current"])
        it["action"] = RESOURCES.get(it["name"], "") if it["gap"] else ""
        num += it["w"] * min(1, it["current"] / it["target"])
        den += it["w"]
    items.sort(key=lambda x: -(x["gap"] * x["w"]))
    return items, round(100 * num / den, 1)

"""Question bank + adaptive test builder.
Technical questions are hand-written (6 per skill: 2 Easy, 2 Medium, 2 Hard). The FIRST option listed is the
correct answer; options are shuffled when a test is generated. Aptitude questions are generated with random numbers."""
import random

E, M, H = "Easy", "Medium", "Hard"
WEIGHT = {E: 1.0, M: 1.5, H: 2.0}


def Q(level, text, correct, *wrong):
    return (level, text, correct, list(wrong))


BANK = {
 "Python": [
  Q(E, "Which keyword defines a function in Python?", "def", "func", "function", "define"),
  Q(E, "What does len([1, 2, 3]) return?", "3", "2", "4", "An error"),
  Q(M, "What does [x * 2 for x in range(3)] produce?", "[0, 2, 4]", "[2, 4, 6]", "[0, 1, 2]", "[1, 2, 3]"),
  Q(M, "Which of these data types is immutable?", "tuple", "list", "dict", "set"),
  Q(H, "After a = [1, 2]; b = a; b.append(3), what is a?", "[1, 2, 3]", "[1, 2]", "[3]", "An error"),
  Q(H, "Which statement about the CPython GIL is correct?", "Only one thread executes Python bytecode at a time", "It enables true parallel CPU threads", "It only affects multiprocessing", "It was removed in all versions")],
 "Java": [
  Q(E, "Which keyword is used to inherit a class in Java?", "extends", "implements", "inherits", "super"),
  Q(E, "Which is the correct entry-point signature?", "public static void main(String[] args)", "static main()", "public void run()", "void main(String)"),
  Q(M, "Which collection does not allow duplicate elements?", "HashSet", "ArrayList", "LinkedList", "Vector"),
  Q(M, "A method declared final cannot be:", "Overridden", "Called", "Inherited", "Overloaded"),
  Q(H, "Which statement about equals() and hashCode() is correct?", "Equal objects must have equal hash codes", "Equal objects must have different hash codes", "hashCode must always return 0", "They are unrelated"),
  Q(H, "Which kind of exception must be caught or declared?", "Checked exceptions", "RuntimeException", "Error", "NullPointerException")],
 "C": [
  Q(E, "Which operator gives the address of a variable in C?", "&", "*", "#", "@"),
  Q(E, "Which header declares printf?", "stdio.h", "stdlib.h", "string.h", "math.h"),
  Q(M, "What is sizeof(char) in C?", "1", "2", "4", "8"),
  Q(M, "What is 5 / 2 with integer operands in C?", "2", "2.5", "3", "2.0"),
  Q(H, "What does writing through a pointer after free() cause?", "Undefined behavior", "A compile error", "A guaranteed crash only", "Nothing at all"),
  Q(H, "Which declares p as a pointer to an array of 3 ints?", "int (*p)[3]", "int *p[3]", "int p[3]*", "int *(p)[]")],
 "C++": [
  Q(E, "Which operator is used with cout to print?", "<<", ">>", "::", "->"),
  Q(E, "Which keyword allocates dynamic memory in C++?", "new", "alloc", "create", "make"),
  Q(M, "What is a virtual function mainly used for?", "Runtime polymorphism", "Faster loops", "Compile-time constants", "Freeing memory"),
  Q(M, "Which STL container stores key-value pairs sorted by key?", "map", "vector", "stack", "queue"),
  Q(H, "The Rule of Three involves which members?", "Destructor, copy constructor, copy assignment", "Three constructors", "Three template parameters", "Three base classes"),
  Q(H, "Which smart pointer provides shared ownership?", "shared_ptr", "unique_ptr", "raw pointer", "scoped array")],
 "HTML": [
  Q(E, "Which tag creates a hyperlink?", "<a>", "<link>", "<href>", "<url>"),
  Q(E, "Which tag defines the largest heading?", "<h1>", "<h6>", "<head>", "<title>"),
  Q(M, "Which attribute supplies alternative text for an image?", "alt", "title", "src", "caption"),
  Q(M, "Which of these is a semantic element?", "<article>", "<div>", "<span>", "<b>"),
  Q(H, "Which script attribute downloads in parallel and runs after parsing, in order?", "defer", "async", "lazy", "sync"),
  Q(H, "What is the viewport meta tag mainly for?", "Responsive layout on mobile", "SEO ranking", "Caching", "Security")],
 "CSS": [
  Q(E, "Which property changes text colour?", "color", "font-color", "text-color", "fgcolor"),
  Q(E, "Which unit is relative to the root font size?", "rem", "px", "pt", "cm"),
  Q(M, "Which display value enables flexbox?", "flex", "block", "inline", "table-flex"),
  Q(M, "position: absolute is placed relative to:", "The nearest positioned ancestor", "The previous sibling", "Always the viewport", "The body only"),
  Q(H, "Which selector has the highest specificity?", "ID selector", "Class selector", "Element selector", "Universal selector"),
  Q(H, "In CSS Grid, what does 1fr mean?", "A fraction of the free space", "One pixel", "One frame", "The first row")],
 "JavaScript": [
  Q(E, "Which keyword declares a block-scoped variable?", "let", "var", "dim", "int"),
  Q(E, "Which array method adds an item to the end?", "push", "pop", "shift", "unshift"),
  Q(M, "What does typeof null return?", "\"object\"", "\"null\"", "\"undefined\"", "\"number\""),
  Q(M, "What does === compare?", "Value and type", "Value only", "Reference only", "Nothing; it assigns"),
  Q(H, "What does console.log(0.1 + 0.2 === 0.3) print?", "false", "true", "undefined", "An error"),
  Q(H, "What does a closure capture?", "Variables from its enclosing scope", "Only global variables", "Only its parameters", "The DOM tree")],
 "SQL": [
  Q(E, "Which clause filters rows?", "WHERE", "ORDER BY", "GROUP BY", "LIMIT"),
  Q(E, "Which statement retrieves data?", "SELECT", "GET", "FETCH", "OPEN"),
  Q(M, "Which join keeps all rows from the left table?", "LEFT JOIN", "INNER JOIN", "CROSS JOIN", "SELF JOIN"),
  Q(M, "Which function counts rows?", "COUNT()", "SUM()", "TOTAL()", "NUM()"),
  Q(H, "Which clause filters groups after aggregation?", "HAVING", "WHERE", "FILTER", "ON"),
  Q(H, "What does SELECT DISTINCT do?", "Removes duplicate rows", "Sorts rows", "Limits rows", "Deletes rows")],
 "MySQL": [
  Q(E, "Which command lists the databases on a MySQL server?", "SHOW DATABASES", "LIST DB", "SELECT DATABASES", "DISPLAY DB"),
  Q(E, "Which attribute auto-generates numeric ids?", "AUTO_INCREMENT", "AUTONUM", "SERIAL_ID", "IDENTITY_AUTO"),
  Q(M, "Which MySQL storage engine supports transactions?", "InnoDB", "MyISAM", "MEMORY", "CSV"),
  Q(M, "Which statement empties a table and resets AUTO_INCREMENT?", "TRUNCATE", "DELETE", "DROP ROWS", "REMOVE"),
  Q(H, "What does an index mainly improve?", "Lookup speed on reads", "Insert speed", "Disk usage", "Column count"),
  Q(H, "Which anomaly does REPEATABLE READ (InnoDB default) prevent?", "Non-repeatable reads", "Syntax errors", "All deadlocks", "Table locks")],
 "React": [
  Q(E, "What is JSX?", "A syntax extension that looks like HTML inside JavaScript", "A database", "A CSS preprocessor", "A server"),
  Q(E, "Which hook manages local component state?", "useState", "useRef", "useMemo", "useId"),
  Q(M, "What is the key prop used for in lists?", "Helping React identify items between renders", "Encrypting data", "Styling items", "Fetching data"),
  Q(M, "When does useEffect(fn, []) run?", "After the first render only", "After every render", "Never", "Before rendering"),
  Q(H, "Why should state not be mutated directly?", "React may not detect the change and re-render", "JavaScript forbids it", "It deletes the state", "It is slower in every case"),
  Q(H, "What does React.memo do?", "Skips re-rendering when props are unchanged", "Stores data permanently", "Caches API calls", "Creates a context")],
 "Flask": [
  Q(E, "Which decorator registers a route in Flask?", "@app.route", "@route.app", "@flask.url", "@app.path"),
  Q(E, "Which command starts the development server?", "flask run", "flask start", "python -m serve", "flask open"),
  Q(M, "How do you read a JSON request body?", "request.get_json()", "request.args", "request.url", "request.path"),
  Q(M, "What does jsonify return?", "A Response with a JSON mimetype", "A plain dict", "A string", "A file"),
  Q(H, "What is the application context used for?", "Exposing app-level data such as current_app", "Storing cookies", "Routing URLs", "Rendering templates only"),
  Q(H, "How does Flask store sessions by default?", "In signed client-side cookies", "In a server database", "In Redis", "In local files")],
 "Django": [
  Q(E, "Which file normally holds URL patterns?", "urls.py", "views.py", "models.py", "admin.py"),
  Q(E, "Which command creates a new Django project?", "django-admin startproject", "django new", "python create", "manage.py init"),
  Q(M, "What does makemigrations do?", "Creates migration files from model changes", "Applies migrations", "Starts the server", "Creates a superuser"),
  Q(M, "Which ORM call fetches all rows?", "Model.objects.all()", "Model.all()", "Model.get_all", "Model.select()"),
  Q(H, "What does select_related optimize?", "Foreign-key joins in one query", "Template caching", "Static files", "Sessions"),
  Q(H, "What is middleware for in Django?", "Processing requests and responses globally", "Defining models", "Rendering the admin", "Compiling templates")],
 "Machine Learning": [
  Q(E, "Which type of learning uses labelled data?", "Supervised learning", "Unsupervised learning", "Only reinforcement learning", "None of these"),
  Q(E, "Which of these is a classification algorithm?", "Logistic regression", "Linear regression", "K-means", "PCA"),
  Q(M, "What is overfitting?", "Memorising training data and generalising poorly", "A model that is too simple", "Training too quickly", "Having too many labels"),
  Q(M, "Which metric is better than accuracy for imbalanced classes?", "F1-score", "Row count", "Mean", "Variance"),
  Q(H, "What does L2 regularisation do?", "Penalises large weights to reduce overfitting", "Adds more features", "Removes labels", "Shuffles the data"),
  Q(H, "Why use cross-validation?", "To estimate generalisation more reliably", "To speed up training", "To add data", "To remove features")],
 "Artificial Intelligence": [
  Q(E, "What does the Turing Test evaluate?", "Whether a machine can show human-like conversation", "CPU speed", "Memory size", "Network latency"),
  Q(E, "Which of these is an everyday AI application?", "Voice assistants", "Printer drivers", "File compression", "Screen savers"),
  Q(M, "Why does BFS find shortest paths in unweighted graphs?", "It explores level by level", "It goes deepest first", "It picks random nodes", "It uses heuristics"),
  Q(M, "Why do neural networks use activation functions?", "To introduce non-linearity", "To store data", "To load data", "To normalise labels"),
  Q(H, "In A* search, f(n) equals:", "g(n) + h(n)", "g(n) - h(n)", "h(n) only", "g(n) * h(n)"),
  Q(H, "What does backpropagation compute?", "Gradients used to update weights", "Dataset splits", "Deployment configs", "Tokens")],
 "Data Science": [
  Q(E, "Which Python library is widely used for dataframes?", "pandas", "flask", "requests", "pygame"),
  Q(E, "What does a histogram show?", "The distribution of a numeric variable", "Network paths", "Time zones", "Text meaning"),
  Q(M, "Which measure is robust to outliers?", "Median", "Mean", "Range", "Sum"),
  Q(M, "How should missing values be handled?", "Impute or drop depending on context", "Always ignore them", "Always set to zero", "Duplicate the rows"),
  Q(H, "What does a p-value represent?", "Probability of results at least this extreme if the null is true", "Probability the null is true", "The effect size", "The sample size"),
  Q(H, "What does one-hot encoding do?", "Represents categories numerically without implying order", "Scales numbers", "Removes outliers", "Fills missing values")],
 "AWS": [
  Q(E, "Which AWS service provides object storage?", "S3", "EC2", "RDS", "Lambda"),
  Q(E, "Which AWS service provides virtual servers?", "EC2", "S3", "IAM", "SNS"),
  Q(M, "Which service runs code without managing servers?", "Lambda", "EC2", "EBS", "VPC"),
  Q(M, "What does IAM manage?", "Users, roles and permissions", "Databases", "DNS records", "Backups"),
  Q(H, "What is a VPC?", "An isolated virtual network in AWS", "A content delivery network", "A billing report", "An email service"),
  Q(H, "Which service spreads traffic across instances?", "Elastic Load Balancing", "S3", "CloudTrail", "Glacier")],
 "Cloud Computing": [
  Q(E, "Which of these is a cloud service model?", "IaaS", "HTTP", "SQL", "FTP"),
  Q(E, "Pay-as-you-go pricing is characteristic of:", "Cloud computing", "On-premise only", "Mainframes", "Printers"),
  Q(M, "Which model gives you a runtime platform without managing infrastructure?", "PaaS", "IaaS", "On-premise", "Colocation"),
  Q(M, "What is auto-scaling?", "Adjusting resources automatically with demand", "Manual restarts", "Data backup", "Encryption"),
  Q(H, "What does high availability aim for?", "Minimal downtime through redundancy", "Lower cost only", "Faster CPUs", "Smaller storage"),
  Q(H, "A key difference between containers and VMs is:", "Containers share the host OS kernel", "Containers bundle a full guest OS", "VMs are lighter", "There is no difference")],
}

# ---------------- Procedural aptitude questions ----------------
def _num_opts(rng, ans, step=1):
    pool = [d for d in (-3, -2, -1, 1, 2, 3, 4, 5) if ans + d * step > 0]
    rng.shuffle(pool)
    return [str(ans)] + [str(ans + d * step) for d in pool[:3]]


def q_percent(rng):
    p, n = rng.choice([10, 15, 20, 25, 30, 40, 60, 75]), rng.choice([40, 80, 120, 160, 200, 240, 400])
    a = p * n // 100
    return dict(difficulty=E, text=f"What is {p}% of {n}?", opts=_num_opts(rng, a, 2))


def q_average(rng):
    a, b, c, x = rng.randint(10, 30), rng.randint(10, 30), rng.randint(10, 30), rng.randint(10, 40)
    avg = (a + b + c + x) / 4
    if avg != int(avg):
        return q_average(rng)
    return dict(difficulty=M, text=f"The average of {a}, {b}, {c} and x is {int(avg)}. What is x?", opts=_num_opts(rng, x, 1))


def q_work(rng):
    a, b, t = rng.choice([(12, 6, 4), (15, 10, 6), (20, 5, 4), (30, 20, 12), (24, 8, 6), (18, 9, 6)])
    return dict(difficulty=M, text=f"A can finish a job in {a} days and B in {b} days. Working together, in how many days will they finish it?", opts=_num_opts(rng, t, 1))


def q_interest(rng):
    p, r, t = rng.choice([1000, 2000, 5000, 8000]), rng.choice([5, 8, 10, 12]), rng.choice([2, 3, 4])
    return dict(difficulty=M, text=f"What is the simple interest on Rs {p} at {r}% per annum for {t} years?", opts=_num_opts(rng, p * r * t // 100, 20))


def q_profit(rng):
    cp, pr = rng.choice([200, 400, 500, 800, 1000]), rng.choice([10, 20, 25, 30])
    return dict(difficulty=E, text=f"An item bought for Rs {cp} is sold for Rs {cp + cp * pr // 100}. What is the profit percentage?", opts=_num_opts(rng, pr, 5))


def q_arith(rng):
    s, d = rng.randint(2, 20), rng.randint(2, 9)
    return dict(difficulty=E, text=f"Find the next number: {s}, {s+d}, {s+2*d}, {s+3*d}, ?", opts=_num_opts(rng, s + 4 * d, d))


def q_geo(rng):
    s, r = rng.randint(2, 5), rng.choice([2, 3])
    return dict(difficulty=M, text=f"Find the next number: {s}, {s*r}, {s*r**2}, {s*r**3}, ?", opts=_num_opts(rng, s * r ** 4, s))


def q_squares(rng):
    m = rng.randint(2, 8)
    return dict(difficulty=M, text=f"Find the next number: {m**2}, {(m+1)**2}, {(m+2)**2}, {(m+3)**2}, ?", opts=_num_opts(rng, (m + 4) ** 2, 2))


def q_pronic(rng):
    k = rng.randint(1, 3)
    seq = [(k + i) * (k + i + 1) for i in range(4)]
    return dict(difficulty=H, text=f"Find the next number: {', '.join(map(str, seq))}, ?", opts=_num_opts(rng, (k + 4) * (k + 5), 2))


def q_code(rng):
    w = rng.choice(["CAT", "DOG", "SUN", "MAP", "PEN", "BAG", "CUP"])
    enc = lambda s: "".join(chr((ord(c) - 65 + 1) % 26 + 65) for c in s)
    w2 = rng.choice([x for x in ["DOG", "SUN", "MAP", "PEN", "BAG", "CUP", "FAN"] if x != w])
    wrong = {"".join(chr((ord(c) - 65 + 2) % 26 + 65) for c in w2), "".join(chr((ord(c) - 65 - 1) % 26 + 65) for c in w2), w2[::-1]}
    return dict(difficulty=M, text=f"If {w} is coded as {enc(w)}, how is {w2} coded in the same way?", opts=[enc(w2)] + list(wrong - {enc(w2)})[:3])


def q_order(rng):
    n = rng.sample(["Asha", "Ravi", "Meena", "Kabir", "Tina", "Omar"], 3)
    return dict(difficulty=E, text=f"{n[0]} is taller than {n[1]}. {n[1]} is taller than {n[2]}. Who is the shortest?", opts=[n[2], n[0], n[1], "Cannot be determined"])


SYN = [("happy", "joyful", "sad", "angry", "tired"), ("big", "large", "tiny", "thin", "weak"), ("rapid", "fast", "slow", "calm", "dull"),
       ("begin", "start", "end", "stop", "pause"), ("smart", "clever", "foolish", "lazy", "rude"), ("brave", "courageous", "timid", "weak", "shy"),
       ("assist", "help", "hinder", "ignore", "block"), ("accurate", "precise", "vague", "wrong", "loose"), ("diligent", "hardworking", "careless", "idle", "lazy"),
       ("scarce", "rare", "plentiful", "common", "cheap"), ("ancient", "old", "modern", "new", "fresh"), ("silent", "quiet", "noisy", "loud", "busy")]
ANT = [("expand", "contract", "grow", "stretch", "widen"), ("victory", "defeat", "triumph", "success", "win"), ("generous", "stingy", "kind", "giving", "noble"),
       ("difficult", "easy", "hard", "tough", "complex"), ("early", "late", "soon", "prompt", "quick"), ("visible", "hidden", "clear", "seen", "obvious")]


def _verbal(rng):
    out = []
    for w, c, *wr in rng.sample(SYN, 2):
        out.append(dict(difficulty=E, text=f"Choose the word closest in meaning to '{w}'.", opts=[c] + wr))
    w, c, *wr = rng.choice(ANT)
    out.append(dict(difficulty=M, text=f"Choose the word opposite in meaning to '{w}'.", opts=[c] + wr))
    return out


def make_aptitude(rng):
    qs = []
    quant = rng.sample([q_percent, q_average, q_work, q_interest, q_profit], 3)
    logic = rng.sample([q_arith, q_geo, q_squares, q_pronic, q_code, q_order], 3)
    for sec, gens in (("Quantitative Aptitude", quant), ("Logical Reasoning", logic)):
        for g in gens:
            qs.append(dict(section=sec, skill=None, **g(rng)))
    for v in _verbal(rng):
        qs.append(dict(section="Verbal Ability", skill=None, **v))
    return qs


# ---------------- Adaptive test builder ----------------
LEVEL_PLAN = [(40, [E, E, M, M]), (70, [E, M, M, H]), (101, [M, M, H, H])]


def plan_levels(score):
    for lim, plan in LEVEL_PLAN:
        if score < lim:
            return plan


def build_test(bundle, role_profile, role_name, rng=None):
    """Pick skills to test from the student's ERP record, plus role-critical skills they appear to lack."""
    rng = rng or random.Random()
    erp = sorted(bundle["skills"].items(), key=lambda kv: -kv[1])
    plan, chosen = [], set()
    for sk, sc in erp:
        if sk in BANK and len(plan) < 4:
            lvl = bundle["levels"].get(sk, "")
            plan.append(dict(skill=sk, erp_score=sc, reason=f"Listed in your ERP profile ({lvl or 'level not set'}, score {sc}); checking it is accurate"))
            chosen.add(sk)
    req = sorted(role_profile["tech"].items(), key=lambda kv: -kv[1])
    for sk, tgt in req:
        if len(plan) >= 6:
            break
        cur = bundle["skills"].get(sk)
        if sk in BANK and sk not in chosen and (cur is None or cur < 45):
            why = "not found in your ERP profile" if cur is None else f"scored only {cur} in your ERP profile"
            plan.append(dict(skill=sk, erp_score=cur or 0, reason=f"Required for {role_name} but {why}"))
            chosen.add(sk)
    questions = []
    for p in plan:
        pool = BANK[p["skill"]]
        for lvl in plan_levels(p["erp_score"]):
            cand = [q for q in pool if q[0] == lvl and q[1] not in [x["text"] for x in questions]]
            lv, text, ok, wrong = rng.choice(cand)
            opts = [ok] + wrong
            rng.shuffle(opts)
            questions.append(dict(section="Technical", skill=p["skill"], difficulty=lv, text=text, options=opts, correct=opts.index(ok)))
    for q in make_aptitude(rng):
        opts = list(q["opts"])
        ok = opts[0]
        rng.shuffle(opts)
        questions.append(dict(section=q["section"], skill=None, difficulty=q["difficulty"], text=q["text"], options=opts, correct=opts.index(ok)))
    return plan, questions

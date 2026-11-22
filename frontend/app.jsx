const { useState, useEffect, useRef, useCallback } = React;

/* ---------- API helper ---------- */
async function api(path, opts = {}) {
  const res = await fetch("/api" + path, {
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    ...opts,
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) { const e = new Error(data.error || "Something went wrong."); e.status = res.status; throw e; }
  return data;
}

/* ---------- Module definitions (drive tables, filters and forms) ---------- */
const GENDERS = ["Male", "Female", "Other"];
const LEVELS = ["Beginner", "Intermediate", "Advanced", "Expert"];
const SKILLS = ["Python", "Java", "C", "C++", "HTML", "CSS", "JavaScript", "SQL", "MySQL", "React", "Flask", "Django",
  "Machine Learning", "Artificial Intelligence", "Data Science", "AWS", "Cloud Computing"];
const SOFT = [["verbal", "Verbal Communication"], ["written", "Written Communication"], ["english", "English Proficiency"],
  ["presentation", "Presentation Skills"], ["group_discussion", "Group Discussion"], ["teamwork", "Teamwork"],
  ["leadership", "Leadership"], ["problem_solving", "Problem Solving"], ["time_management", "Time Management"],
  ["confidence", "Confidence"], ["adaptability", "Adaptability"]];
const num = (k, label, extra = {}) => ({ k, label, type: "number", ...extra });
const stu = { k: "student_id", label: "Student", type: "select", lookup: "students", wide: true };
const stuCols = [{ k: "student_code", label: "ID" }, { k: "student_name", label: "Student" }];
const score = (r, k) => r[k] == null ? "-" : r[k];

const MODULES = {
  students: {
    title: "Students", add: "Add student", filters: [{ k: "course", label: "Course", lookup: "courses" }, { k: "gender", label: "Gender", options: GENDERS },
      { k: "department_id", label: "Department", lookup: "departments" }, { k: "semester", label: "Semester", options: [1, 2, 3, 4, 5, 6, 7, 8] }],
    cols: [{ k: "student_code", label: "ID" }, { k: "name", label: "Name", link: true }, { k: "course", label: "Course" }, { k: "department", label: "Department", sort: "department" },
      { k: "semester", label: "Sem" }, { k: "email", label: "Email" }, { k: "mobile", label: "Mobile" }, { k: "city", label: "City" }, { k: "faculty_name", label: "Mentor", sort: "faculty_name" }],
    fields: [{ k: "student_code", label: "Student ID", req: 1 }, { k: "name", label: "Full name", req: 1 }, { k: "email", label: "Email", type: "email" }, { k: "mobile", label: "Mobile" },
      { k: "dob", label: "Date of birth", type: "date" }, { k: "gender", label: "Gender", type: "select", options: GENDERS }, { k: "city", label: "City" }, { k: "state", label: "State" },
      { k: "course", label: "Course", type: "select", lookup: "courses_all" }, { k: "department_id", label: "Department", type: "select", lookup: "departments" },
      { k: "specialization", label: "Specialization" }, num("semester", "Semester"), { k: "academic_year", label: "Academic year", ph: "2025-2026" },
      num("admission_year", "Admission year"), { k: "roll_no", label: "Roll number" }, { k: "faculty_id", label: "Assigned faculty", type: "select", lookup: "faculty" }],
  },
  faculty: {
    title: "Faculty", add: "Add faculty", cols: [{ k: "name", label: "Name" }, { k: "email", label: "Email" }, { k: "designation", label: "Designation" }, { k: "department", label: "Department", sort: "department" }],
    filters: [{ k: "department_id", label: "Department", lookup: "departments" }],
    fields: [{ k: "name", label: "Name", req: 1 }, { k: "email", label: "Email", type: "email" }, { k: "designation", label: "Designation", type: "select", options: ["Professor", "Associate Professor", "Assistant Professor"] },
      { k: "department_id", label: "Department", type: "select", lookup: "departments" }],
  },
  departments: {
    title: "Departments", add: "Add department", cols: [{ k: "name", label: "Department" }, { k: "hod", label: "Head of department" }, { k: "building", label: "Building" },
      { k: "student_count", label: "Students", sort: "student_count" }, { k: "faculty_count", label: "Faculty", sort: "faculty_count" }],
    fields: [{ k: "name", label: "Department name", req: 1 }, { k: "hod", label: "Head of department" }, { k: "building", label: "Building" }],
  },
  academics: {
    title: "Academic records", add: "Add academic record", filters: [{ k: "course", label: "Course", lookup: "courses" }, { k: "performance", label: "Performance", options: ["Excellent", "Good", "Average", "Needs Improvement"] }],
    cols: [...stuCols, { k: "ssc", label: "SSC %" }, { k: "hsc", label: "HSC %" }, { k: "graduation", label: "Grad %" }, { k: "cgpa", label: "CGPA" },
      ...[1, 2, 3, 4, 5, 6].map(i => ({ k: "sgpa" + i, label: "SGPA" + i, render: r => score(r, "sgpa" + i) })), { k: "current_backlogs", label: "Backlogs" },
      { k: "previous_backlogs", label: "Prev. backlogs" }, { k: "attendance", label: "Attend. %" }, { k: "performance", label: "Performance", tag: 1 }],
    fields: [stu, num("ssc", "SSC %", { step: .1, max: 100 }), num("hsc", "HSC %", { step: .1, max: 100 }), num("graduation", "Graduation % / CGPA", { step: .1 }),
      ...[1, 2, 3, 4, 5, 6].map(i => num("sgpa" + i, "SGPA sem " + i, { step: .01, max: 10 })), num("cgpa", "Overall CGPA", { step: .01, max: 10 }),
      num("current_backlogs", "Current backlogs"), num("previous_backlogs", "Previous backlogs"), num("attendance", "Attendance %", { step: .1, max: 100 }),
      { k: "performance", label: "Performance", type: "select", options: ["Excellent", "Good", "Average", "Needs Improvement"] }],
  },
  tech_skills: {
    title: "Technical skills", add: "Add skill", filters: [{ k: "skill", label: "Skill", options: SKILLS }, { k: "level", label: "Level", options: LEVELS }, { k: "course", label: "Course", lookup: "courses" }],
    cols: [...stuCols, { k: "skill", label: "Skill" }, { k: "level", label: "Level", tag: 1 }, { k: "score", label: "Score", bar: 1 }],
    fields: [stu, { k: "skill", label: "Skill", type: "select", options: SKILLS, req: 1 }, { k: "level", label: "Proficiency", type: "select", options: LEVELS }, num("score", "Score (0-100)", { max: 100 })],
  },
  soft_skills: {
    title: "Soft skills", add: "Add soft-skill record", filters: [{ k: "course", label: "Course", lookup: "courses" }],
    cols: [...stuCols, ...SOFT.map(([k, l]) => ({ k, label: l.split(" ")[0] === "Verbal" ? "Verbal" : l.replace(" Communication", "").replace(" Proficiency", "").replace(" Skills", "") }))],
    fields: [stu, ...SOFT.map(([k, l]) => num(k, l, { max: 100 }))],
  },
  assessments: {
    title: "Assessment records", add: "Add assessment", filters: [{ k: "course", label: "Course", lookup: "courses" }],
    cols: [...stuCols, { k: "quant", label: "Quant" }, { k: "logical", label: "Logical" }, { k: "verbal_ability", label: "Verbal" }, { k: "coding", label: "Coding" },
      { k: "tech_mcq", label: "Tech MCQ" }, { k: "programming", label: "Programming" }, { k: "mock_interview", label: "Mock interview" }],
    fields: [stu, num("quant", "Quantitative aptitude", { max: 100 }), num("logical", "Logical reasoning", { max: 100 }), num("verbal_ability", "Verbal ability", { max: 100 }),
      num("coding", "Coding test", { max: 100 }), num("tech_mcq", "Technical MCQ", { max: 100 }), num("programming", "Programming test", { max: 100 }), num("mock_interview", "Mock interview", { max: 100 })],
  },
  projects: {
    title: "Projects", add: "Add project", filters: [{ k: "project_type", label: "Type", options: ["Individual", "Team"] }, { k: "course", label: "Course", lookup: "courses" }],
    cols: [...stuCols, { k: "title", label: "Project title" }, { k: "domain", label: "Domain" }, { k: "technologies", label: "Technologies" }, { k: "project_type", label: "Type", tag: 1 }],
    fields: [stu, { k: "title", label: "Project title", req: 1 }, { k: "domain", label: "Domain" }, { k: "technologies", label: "Technologies used" },
      { k: "project_type", label: "Type", type: "select", options: ["Individual", "Team"] }, { k: "description", label: "Description", type: "textarea", wide: true }],
  },
  internships: {
    title: "Internships", add: "Add internship", filters: [{ k: "performance", label: "Performance", options: ["Excellent", "Good", "Satisfactory"] }, { k: "course", label: "Course", lookup: "courses" }],
    cols: [...stuCols, { k: "company", label: "Company" }, { k: "role", label: "Role" }, { k: "duration_months", label: "Months" }, { k: "performance", label: "Performance", tag: 1 }],
    fields: [stu, { k: "company", label: "Company", req: 1 }, { k: "role", label: "Role" }, num("duration_months", "Duration (months)"),
      { k: "performance", label: "Performance", type: "select", options: ["Excellent", "Good", "Satisfactory"] }],
  },
  certifications: {
    title: "Certifications and achievements", add: "Add entry", filters: [{ k: "kind", label: "Type", options: ["Certification", "Workshop", "Hackathon", "Coding Competition", "Technical Achievement"] }, { k: "course", label: "Course", lookup: "courses" }],
    cols: [...stuCols, { k: "kind", label: "Type", tag: 1 }, { k: "name", label: "Name" }, { k: "organization", label: "Organization" }, { k: "cert_date", label: "Date" }],
    fields: [stu, { k: "kind", label: "Type", type: "select", options: ["Certification", "Workshop", "Hackathon", "Coding Competition", "Technical Achievement"], req: 1 },
      { k: "name", label: "Name", req: 1 }, { k: "organization", label: "Issuing organization" }, { k: "cert_date", label: "Date", type: "date" }],
  },
  placements: {
    title: "Placement management", add: "Add placement record", filters: [{ k: "status", label: "Status", options: ["Placed", "Unplaced"] }, { k: "eligible", label: "Eligibility", options: ["Eligible", "Not Eligible"] }, { k: "course", label: "Course", lookup: "courses" }],
    cols: [...stuCols, { k: "course", label: "Course" }, { k: "eligible", label: "Eligibility", tag: 1 }, { k: "preferred_role", label: "Preferred role" }, { k: "preferred_industry", label: "Industry" },
      { k: "company", label: "Company" }, { k: "status", label: "Status", tag: 1 }, { k: "package_lpa", label: "Package (LPA)" }, { k: "placement_date", label: "Date" }, { k: "interview_history", label: "Interview history" }],
    fields: [stu, { k: "eligible", label: "Eligibility", type: "select", options: ["Eligible", "Not Eligible"] }, { k: "preferred_role", label: "Preferred job role" },
      { k: "preferred_industry", label: "Preferred industry" }, { k: "company", label: "Company" }, { k: "status", label: "Status", type: "select", options: ["Placed", "Unplaced"] },
      num("package_lpa", "Package (LPA)", { step: .1 }), { k: "placement_date", label: "Placement date", type: "date" }, { k: "interview_history", label: "Interview history", type: "textarea", wide: true }],
  },
};

const NAV = [["dashboard", "Dashboard"], ["students", "Students"], ["faculty", "Faculty"], ["departments", "Departments"], ["academics", "Academic records"],
  ["tech_skills", "Technical skills"], ["soft_skills", "Soft skills"], ["assessments", "Assessments"], ["projects", "Projects"], ["internships", "Internships"],
  ["certifications", "Certifications"], ["placements", "Placements"], ["insights", "AI insights"]];
const STUDENT_NAV = [["report", "Placement report"], ["test", "Skill test"], ["me", "My ERP profile"]];
const ROLE_LABEL = { admin: "Admin", faculty: "Faculty", placement: "Placement Officer", student: "Student" };

/* ---------- Small helpers ---------- */
const tagClass = v => ({ Placed: "g", Eligible: "g", Excellent: "g", Expert: "g", Good: "b", Advanced: "b", Team: "b", "Not Eligible": "r", Unplaced: "r", "Needs Improvement": "r", Beginner: "r",
  Average: "y", Intermediate: "y", Satisfactory: "y" }[v] || "");
const Tag = ({ v }) => v ? <span className={"tag " + tagClass(v)}>{v}</span> : "-";
const useToast = () => { const [t, set] = useState(""); const show = m => { set(m); setTimeout(() => set(""), 2500); }; return [t, show]; };

function ChartBox({ type, data, options, height }) {
  const ref = useRef(), inst = useRef();
  useEffect(() => {
    inst.current = new window.Chart(ref.current, { type, data, options: { responsive: true, maintainAspectRatio: false, ...options } });
    return () => inst.current.destroy();
  }, [JSON.stringify(data), type]);
  return <div className="chart" style={height ? { height } : null}><canvas ref={ref}></canvas></div>;
}
const PAL = ["#0d7a78", "#e0a030", "#2f5d8a", "#b8392b", "#7a9e3b", "#8e5aa8", "#c9702f", "#4a8f9e"];

/* ---------- Login ---------- */
function Login({ onLogin }) {
  const [u, setU] = useState(""), [p, setP] = useState(""), [err, setErr] = useState(""), [busy, setBusy] = useState(false);
  const submit = async e => {
    e.preventDefault(); setBusy(true); setErr("");
    try { onLogin(await api("/login", { method: "POST", body: { username: u, password: p } })); }
    catch (x) { setErr(x.message); } setBusy(false);
  };
  const demo = [["stu2002", "student123", "Student"], ["admin", "admin123", "Admin"], ["faculty1", "faculty123", "Faculty"], ["placement", "placement123", "Placement Officer"]];
  return (
    <div className="login">
      <div className="hero"><h1>Know your placement chances, and exactly which skills to build next.</h1>
        <p>An AI layer on top of the college ERP: a personalised skill test, placement prediction and skill gap analysis for every student.</p></div>
      <div className="box"><form onSubmit={submit}>
        <h2>Sign in</h2>
        {err && <div className="err" role="alert">{err}</div>}
        <div className="field"><label htmlFor="u">Username</label><input id="u" value={u} onChange={e => setU(e.target.value)} autoFocus required /></div>
        <div className="field"><label htmlFor="p">Password</label><input id="p" type="password" value={p} onChange={e => setP(e.target.value)} required /></div>
        <button className="btn pri" style={{ width: "100%" }} disabled={busy}>{busy ? "Signing in..." : "Sign in"}</button>
        <div className="demo">Demo accounts (click to fill):<br />{demo.map(([a, b, l]) => <span key={a}><button type="button" onClick={() => { setU(a); setP(b); }}>{l}</button>{" "}</span>)}</div>
      </form></div>
    </div>);
}

/* ---------- Dashboard ---------- */
function Dashboard() {
  const [d, setD] = useState(null), [err, setErr] = useState("");
  useEffect(() => { api("/dashboard").then(setD).catch(e => setErr(e.message)); }, []);
  if (err) return <div className="err">{err}</div>;
  if (!d) return <div className="empty">Loading dashboard...</div>;
  const t = d.totals, lbl = a => a.map(x => x.label), cnt = a => a.map(x => x.count);
  const pie = (a, type = "doughnut") => <ChartBox type={type} data={{ labels: lbl(a), datasets: [{ data: cnt(a), backgroundColor: PAL }] }} options={{ plugins: { legend: { position: "right" } } }} />;
  const bar = (a, key = "count", color = PAL[0], extra = {}) => <ChartBox type="bar" data={{ labels: lbl(a), datasets: [{ data: a.map(x => x[key]), backgroundColor: color }] }} options={{ plugins: { legend: { display: false } }, ...extra }} />;
  return (
    <div className="stack">
      <div className="cards">
        <div className="stat"><b>{t.students}</b><span>Total students</span></div>
        <div className="stat"><b>{t.faculty}</b><span>Total faculty</span></div>
        <div className="stat"><b>{t.departments}</b><span>Departments</span></div>
        <div className="stat green"><b>{t.placed}</b><span>Placed students</span></div>
        <div className="stat red"><b>{t.unplaced}</b><span>Unplaced students</span></div>
        <div className="stat gold"><b>{t.placement_pct}%</b><span>Placement rate ({t.eligible} eligible)</span></div>
        <div className="stat"><b>{t.avg_cgpa}</b><span>Average CGPA</span></div>
        <div className="stat"><b>{t.avg_attendance}%</b><span>Average attendance</span></div>
      </div>
      <div className="grid2">
        <div className="panel"><h3>CGPA distribution</h3>{bar(d.cgpa_distribution)}</div>
        <div className="panel"><h3>Academic performance</h3>{pie(d.performance)}</div>
        <div className="panel"><h3>Students by course</h3>{pie(d.by_course)}</div>
        <div className="panel"><h3>Students by department</h3>{bar(d.by_department, "count", PAL[2], { indexAxis: "y" })}</div>
        <div className="panel"><h3>Average CGPA by course</h3>{bar(d.avg_cgpa_by_course, "value", PAL[1], { scales: { y: { min: 0, max: 10 } } })}</div>
        <div className="panel"><h3>Gender distribution</h3>{pie(d.by_gender)}</div>
        <div className="panel"><h3>Average score by technical skill</h3>{bar(d.skills, "avg_score", PAL[0], { scales: { y: { min: 0, max: 100 } } })}</div>
        <div className="panel"><h3>Placement status by course</h3>
          <ChartBox type="bar" data={{ labels: lbl(d.placement_by_course), datasets: [{ label: "Placed", data: d.placement_by_course.map(x => x.placed), backgroundColor: "#2b8a4e" },
            { label: "Eligible, not yet placed", data: d.placement_by_course.map(x => x.unplaced_eligible), backgroundColor: "#b8392b" }] }}
            options={{ scales: { x: { stacked: true }, y: { stacked: true } } }} /></div>
        <div className="panel"><h3>Top recruiters</h3>{bar(d.top_companies, "count", PAL[3], { indexAxis: "y" })}</div>
        <div className="panel"><h3>Salary bands (placed)</h3>{pie(d.salary_bands)}</div>
      </div>
    </div>);
}

/* ---------- Form modal ---------- */
function FormModal({ mod, row, lookups, onClose, onSaved, fixedStudent }) {
  const [v, setV] = useState(row ? { ...row } : fixedStudent ? { student_id: fixedStudent } : {});
  const [err, setErr] = useState(""), [busy, setBusy] = useState(false);
  const opts = f => {
    if (f.options) return f.options.map(o => [o, o]);
    const L = lookups || {};
    if (f.lookup === "courses_all") return ["MCA", "BCA", "BSc Computer Science", "BE Computer Engineering"].map(o => [o, o]);
    if (f.lookup === "students") return (L.students || []).map(s => [s.id, `${s.student_code} - ${s.name}`]);
    if (f.lookup === "courses") return (L.courses || []).map(o => [o, o]);
    return (L[f.lookup] || []).map(o => [o.id, o.name]);
  };
  const save = async e => {
    e.preventDefault(); setBusy(true); setErr("");
    try {
      const body = {}; mod.fields.forEach(f => { if (v[f.k] !== undefined) body[f.k] = v[f.k]; });
      row ? await api(`/${mod.key}/${row.id}`, { method: "PUT", body }) : await api(`/${mod.key}`, { method: "POST", body });
      onSaved(row ? "Changes saved." : "Record added.");
    } catch (x) { setErr(x.message); setBusy(false); }
  };
  return (
    <div className="modal-bg" onMouseDown={e => e.target === e.currentTarget && onClose()}>
      <form className="modal" onSubmit={save}>
        <h2>{row ? "Edit record" : mod.add}</h2>
        {err && <div className="err" role="alert">{err}</div>}
        <div className="form">
          {mod.fields.map(f => (
            <div key={f.k} className={"field" + (f.wide ? " wide" : "")}>
              <label htmlFor={"f_" + f.k}>{f.label}{f.req ? " *" : ""}</label>
              {f.type === "select" ? (
                <select id={"f_" + f.k} value={v[f.k] ?? ""} required={!!f.req || f.k === "student_id"} disabled={f.k === "student_id" && !!row}
                  onChange={e => setV({ ...v, [f.k]: e.target.value })}><option value="">Select...</option>{opts(f).map(([a, b]) => <option key={a} value={a}>{b}</option>)}</select>
              ) : f.type === "textarea" ? (
                <textarea id={"f_" + f.k} rows="3" value={v[f.k] ?? ""} onChange={e => setV({ ...v, [f.k]: e.target.value })} />
              ) : (
                <input id={"f_" + f.k} type={f.type || "text"} step={f.step} min={f.type === "number" ? 0 : undefined} max={f.max} placeholder={f.ph} required={!!f.req}
                  value={v[f.k] ?? ""} onChange={e => setV({ ...v, [f.k]: e.target.value })} />)}
            </div>))}
        </div>
        <div style={{ display: "flex", gap: 8, justifyContent: "flex-end", marginTop: 18 }}>
          <button type="button" className="btn" onClick={onClose}>Cancel</button><button className="btn pri" disabled={busy}>{busy ? "Saving..." : "Save"}</button>
        </div>
      </form>
    </div>);
}

/* ---------- Generic data module: search, filters, sort, pagination, CRUD ---------- */
function DataModule({ name, lookups, go }) {
  const mod = { ...MODULES[name], key: name };
  const [res, setRes] = useState(null), [err, setErr] = useState(""), [q, setQ] = useState(""), [qs, setQs] = useState("");
  const [page, setPage] = useState(1), [per, setPer] = useState(15), [sort, setSort] = useState("id"), [order, setOrder] = useState("asc"), [flt, setFlt] = useState({});
  const [modal, setModal] = useState(null), [toast, show] = useToast();
  const load = useCallback(() => {
    const p = new URLSearchParams({ q: qs, page, per_page: per, sort, order, ...Object.fromEntries(Object.entries(flt).filter(([, v]) => v !== "")) });
    api(`/${name}?${p}`).then(r => { setRes(r); setErr(""); }).catch(e => setErr(e.message));
  }, [name, qs, page, per, sort, order, JSON.stringify(flt)]);
  useEffect(() => { load(); }, [load]);
  useEffect(() => { const t = setTimeout(() => { setQs(q); setPage(1); }, 300); return () => clearTimeout(t); }, [q]);
  const toggle = c => { const k = c.sort || c.k; if (sort === k) setOrder(order === "asc" ? "desc" : "asc"); else { setSort(k); setOrder("asc"); } setPage(1); };
  const del = async r => {
    if (!confirm("Delete this record? This cannot be undone.")) return;
    try { await api(`/${name}/${r.id}`, { method: "DELETE" }); show("Record deleted."); load(); } catch (x) { show(x.message); }
  };
  const fopts = f => f.options ? f.options.map(o => [o, o]) : f.lookup === "courses" ? (lookups.courses || []).map(o => [o, o]) : (lookups[f.lookup] || []).map(o => [o.id, o.name]);
  const cell = (r, c) => {
    if (c.render) return c.render(r);
    const v = r[c.k];
    if (c.link) return <a href={"#/student/" + r.id} style={{ color: "var(--teal-d)", fontWeight: 600 }}>{v}</a>;
    if (c.tag) return <Tag v={v} />;
    if (c.bar) return <div style={{ minWidth: 90 }}>{v}<div className="meter"><i style={{ width: v + "%" }} /></div></div>;
    return v ?? "-";
  };
  return (
    <div>
      <div className="bar">
        <input className="grow" placeholder={"Search " + mod.title.toLowerCase() + "..."} value={q} onChange={e => setQ(e.target.value)} aria-label="Search" />
        {(mod.filters || []).map(f => (
          <select key={f.k} value={flt[f.k] ?? ""} aria-label={f.label} onChange={e => { setFlt({ ...flt, [f.k]: e.target.value }); setPage(1); }}>
            <option value="">{f.label}: all</option>{fopts(f).map(([a, b]) => <option key={a} value={a}>{b}</option>)}</select>))}
        {Object.values(flt).some(Boolean) && <button className="btn" onClick={() => setFlt({})}>Clear filters</button>}
        {res?.can_write && <button className="btn pri" onClick={() => setModal({})}>{mod.add}</button>}
      </div>
      {err && <div className="err">{err}</div>}
      <div className="tw"><table>
        <thead><tr>{mod.cols.map(c => <th key={c.k} onClick={() => toggle(c)} aria-sort={sort === (c.sort || c.k) ? (order === "asc" ? "ascending" : "descending") : "none"}>
          {c.label}{sort === (c.sort || c.k) ? (order === "asc" ? " ▲" : " ▼") : ""}</th>)}<th>Actions</th></tr></thead>
        <tbody>{res && res.data.map(r => <tr key={r.id}>
          {mod.cols.map(c => <td key={c.k}>{cell(r, c)}</td>)}
          <td className="act">{name === "students" && <button className="btn sm" onClick={() => go("student/" + r.id)}>Profile</button>}
            {res.can_write && <><button className="btn sm" onClick={() => setModal(r)}>Edit</button><button className="btn sm dan" onClick={() => del(r)}>Delete</button></>}</td></tr>)}
        </tbody></table>
        {res && !res.data.length && <div className="empty">No records match. Try clearing the search or filters.</div>}
        {!res && !err && <div className="empty">Loading...</div>}
      </div>
      {res && <div className="pager">
        <span>{res.total} records · page {res.page} of {res.pages}</span>
        <span style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <select value={per} onChange={e => { setPer(+e.target.value); setPage(1); }} aria-label="Rows per page">{[10, 15, 25, 50, 100].map(n => <option key={n} value={n}>{n} / page</option>)}</select>
          <button className="btn" disabled={page <= 1} onClick={() => setPage(1)}>First</button>
          <button className="btn" disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</button>
          <button className="btn" disabled={page >= res.pages} onClick={() => setPage(page + 1)}>Next</button>
          <button className="btn" disabled={page >= res.pages} onClick={() => setPage(res.pages)}>Last</button></span></div>}
      {modal && <FormModal mod={mod} row={modal.id ? modal : null} lookups={lookups} onClose={() => setModal(null)} onSaved={m => { setModal(null); show(m); load(); }} />}
      {toast && <div className="ok" role="status">{toast}</div>}
    </div>);
}

/* ---------- Student profile ---------- */
function Profile({ id, go, role }) {
  const [p, setP] = useState(null), [err, setErr] = useState("");
  useEffect(() => { setP(null); api(`/students/${id}/profile`).then(setP).catch(e => setErr(e.message)); }, [id]);
  if (err) return <div><div className="err">{err}</div><button className="btn" onClick={() => go("students")}>Back to students</button></div>;
  if (!p) return <div className="empty">Loading profile...</div>;
  const s = p.student, a = p.academics, pl = p.placement;
  const KV = ({ items }) => <div className="kv">{items.map(([l, v]) => <div key={l}><small>{l}</small>{v ?? "-"}</div>)}</div>;
  const sg = a ? [1, 2, 3, 4, 5, 6].map(i => a["sgpa" + i]) : [];
  const sk = [...p.tech_skills].sort((x, y) => y.score - x.score);
  return (
    <div className="stack">
      <div style={{ display: "flex", gap: 8 }}>{role !== "student" && <button className="btn" onClick={() => go("students")}>← Back to students</button>}
        {role !== "student" && <button className="btn pri" onClick={() => go("report/" + s.id)}>AI placement report</button>}</div>
      <div className="panel phead">
        <div className="avatar">{s.name.split(" ").map(x => x[0]).join("").slice(0, 2)}</div>
        <div style={{ flex: 1 }}><h2 style={{ margin: 0 }}>{s.name}</h2>
          <div style={{ color: "var(--muted)" }}>{s.student_code} · {s.course} · {s.department} · Semester {s.semester}</div></div>
        {pl && <div style={{ textAlign: "right" }}><Tag v={pl.status} /><div style={{ marginTop: 4 }}>{pl.status === "Placed" ? `${pl.company} · ${pl.package_lpa} LPA` : pl.eligible}</div></div>}
      </div>
      <div className="panel"><h3>Personal and admission details</h3>
        <KV items={[["Email", s.email], ["Mobile", s.mobile], ["Date of birth", s.dob], ["Gender", s.gender], ["City", s.city], ["State", s.state], ["Specialization", s.specialization],
          ["Academic year", s.academic_year], ["Admission year", s.admission_year], ["Roll number", s.roll_no], ["Mentor", s.faculty_name]]} /></div>
      {a && <div className="grid2">
        <div className="panel"><h3>Academic record</h3><KV items={[["SSC %", a.ssc], ["HSC %", a.hsc], ["Graduation %", a.graduation], ["Overall CGPA", a.cgpa], ["Attendance %", a.attendance],
          ["Current backlogs", a.current_backlogs], ["Previous backlogs", a.previous_backlogs], ["Performance", <Tag v={a.performance} />]]} /></div>
        <div className="panel"><h3>Semester-wise SGPA</h3>
          <ChartBox type="line" data={{ labels: ["Sem 1", "Sem 2", "Sem 3", "Sem 4", "Sem 5", "Sem 6"], datasets: [{ data: sg, borderColor: "#0d7a78", backgroundColor: "#0d7a78", tension: .25, spanGaps: false }] }}
            options={{ plugins: { legend: { display: false } }, scales: { y: { min: 0, max: 10 } } }} /></div></div>}
      <div className="grid2">
        <div className="panel"><h3>Technical skills ({sk.length})</h3>
          {sk.length ? <ChartBox type="bar" height={Math.max(160, sk.length * 30)} data={{ labels: sk.map(x => `${x.skill} (${x.level})`), datasets: [{ data: sk.map(x => x.score), backgroundColor: "#0d7a78" }] }}
            options={{ indexAxis: "y", plugins: { legend: { display: false } }, scales: { x: { min: 0, max: 100 } } }} /> : <div className="empty">No skills recorded.</div>}</div>
        {p.soft_skills && <div className="panel"><h3>Communication and soft skills</h3>
          <ChartBox type="radar" data={{ labels: SOFT.map(x => x[1]), datasets: [{ data: SOFT.map(([k]) => p.soft_skills[k]), backgroundColor: "rgba(13,122,120,.25)", borderColor: "#0d7a78" }] }}
            options={{ plugins: { legend: { display: false } }, scales: { r: { min: 0, max: 100 } } }} /></div>}
      </div>
      {p.assessments && <div className="panel"><h3>Assessments</h3><KV items={[["Quantitative aptitude", p.assessments.quant], ["Logical reasoning", p.assessments.logical], ["Verbal ability", p.assessments.verbal_ability],
        ["Coding test", p.assessments.coding], ["Technical MCQ", p.assessments.tech_mcq], ["Programming test", p.assessments.programming], ["Mock interview", p.assessments.mock_interview]]} /></div>}
      <div className="grid2">
        <div className="panel"><h3>Projects ({p.projects.length})</h3>{p.projects.length ? p.projects.map(x => <p key={x.id}><b>{x.title}</b> <Tag v={x.project_type} /><br />
          <small style={{ color: "var(--muted)" }}>{x.domain} · {x.technologies}</small><br />{x.description}</p>) : <div className="empty">No projects recorded.</div>}</div>
        <div className="panel"><h3>Internships ({p.internships.length})</h3>{p.internships.length ? p.internships.map(x => <p key={x.id}><b>{x.company}</b> · {x.role}<br />
          <small style={{ color: "var(--muted)" }}>{x.duration_months} month(s)</small> <Tag v={x.performance} /></p>) : <div className="empty">No internships recorded.</div>}</div>
      </div>
      <div className="panel"><h3>Certifications and achievements ({p.certifications.length})</h3>{p.certifications.length ?
        <table><tbody>{p.certifications.map(x => <tr key={x.id}><td><Tag v={x.kind} /></td><td>{x.name}</td><td>{x.organization}</td><td>{x.cert_date}</td></tr>)}</tbody></table> : <div className="empty">None recorded.</div>}</div>
      {pl && <div className="panel"><h3>Placement</h3><KV items={[["Eligibility", <Tag v={pl.eligible} />], ["Status", <Tag v={pl.status} />], ["Preferred role", pl.preferred_role], ["Preferred industry", pl.preferred_industry],
        ["Company", pl.company], ["Package (LPA)", pl.package_lpa], ["Placement date", pl.placement_date], ["Interview history", pl.interview_history]]} /></div>}
    </div>);
}

/* ---------- Shell ---------- */
function App() {
  const [me, setMe] = useState(undefined), [lookups, setLookups] = useState({}), [open, setOpen] = useState(false);
  const [route, setRoute] = useState(location.hash.slice(2) || "");
  useEffect(() => { api("/me").then(setMe).catch(() => setMe(null)); }, []);
  useEffect(() => { const h = () => { setRoute(location.hash.slice(2) || ""); setOpen(false); }; addEventListener("hashchange", h); return () => removeEventListener("hashchange", h); }, []);
  useEffect(() => { if (me) api("/lookups").then(setLookups).catch(() => {}); }, [me]);
  const go = r => { location.hash = "/" + r; };
  if (me === undefined) return <div className="empty">Loading...</div>;
  if (!me) return <Login onLogin={m => { setMe(m); go(m.role === "student" ? "report" : "dashboard"); }} />;
  const logout = async () => { await api("/logout", { method: "POST" }); setMe(null); };
  const isStu = me.role === "student", home = isStu ? "report" : "dashboard";
  const [page, arg] = (route || home).split("/");
  const NAVS = isStu ? STUDENT_NAV : NAV;
  const titles = { student: "Student profile", dashboard: "Dashboard", report: isStu ? "My placement report" : "AI placement report", test: "Skill assessment", result: "Test review", me: "My ERP profile", insights: "AI insights" };
  const title = titles[page] || MODULES[page]?.title || "Not found";
  return (
    <div className="app">
      <aside className={"side" + (open ? " open" : "")}><div className="brand"><i>AI</i>Placement AI</div>
        {NAVS.map(([k, l]) => <a key={k} className={page === k || (page === "student" && k === "students") || (page === "result" && k === "test") ? "on" : ""} href={"#/" + k}>{l}</a>)}</aside>
      <div className="main">
        <header className="top"><div style={{ display: "flex", gap: 12, alignItems: "center" }}>
          <button className="btn menu-btn" onClick={() => setOpen(!open)} aria-label="Toggle menu">☰</button><h1>{title}</h1></div>
          <div className="who"><span>{me.name}</span><span className="role">{ROLE_LABEL[me.role]}</span><button className="btn" onClick={logout}>Sign out</button></div></header>
        <div className="content">
          {isStu ? (page === "report" ? <Report key="r" go={go} /> : page === "test" ? <SkillTest go={go} /> : page === "result" ? <TestResult id={arg} go={go} />
              : page === "me" ? <Profile id={me.student_id} go={go} role={me.role} /> : <div className="empty">That page does not exist.</div>)
            : page === "dashboard" ? <Dashboard key={me.role} /> : page === "student" ? <Profile id={arg} go={go} role={me.role} />
            : page === "report" ? <Report key={arg} studentId={arg} staff go={go} /> : page === "insights" ? <Insights me={me} go={go} />
            : MODULES[page] ? <DataModule key={page} name={page} lookups={lookups} go={go} /> : <div className="empty">That page does not exist.</div>}
        </div>
      </div>
    </div>);
}
ReactDOM.createRoot(document.getElementById("root")).render(<App />);

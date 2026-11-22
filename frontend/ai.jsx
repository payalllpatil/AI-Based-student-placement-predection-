/* AI module screens. Loaded BEFORE app.jsx; uses helpers (api, ChartBox, Tag, PAL) defined there at render time. */

const PRIO = { Critical: "r", Moderate: "y", Minor: "b", Met: "g" };
const fmtTime = s => `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;

/* ---------- Skill test ---------- */
function SkillTest({ go }) {
  const [info, setInfo] = useState(null), [test, setTest] = useState(null), [err, setErr] = useState(""), [busy, setBusy] = useState(false);
  const [ans, setAns] = useState({}), [cur, setCur] = useState(0), [left, setLeft] = useState(0), [done, setDone] = useState(null);
  const submitted = useRef(false);
  useEffect(() => { api("/ai/tests").then(setInfo).catch(e => setErr(e.message)); }, [done]);
  const start = async () => {
    setBusy(true); setErr("");
    try { const t = await api("/ai/test/start", { method: "POST" }); setTest(t); setLeft(t.seconds_left); setAns({}); setCur(0); submitted.current = false; }
    catch (e) { setErr(e.message); } setBusy(false);
  };
  const submit = useCallback(async (auto) => {
    if (submitted.current || !test) return;
    const unanswered = test.questions.length - Object.keys(ans).length;
    if (!auto && unanswered && !confirm(`${unanswered} question(s) are unanswered. Submit anyway?`)) return;
    submitted.current = true; setBusy(true);
    try { setDone(await api(`/ai/test/${test.test_id}/submit`, { method: "POST", body: { answers: ans } })); setTest(null); }
    catch (e) { setErr(e.message); submitted.current = false; } setBusy(false);
  }, [test, ans]);
  useEffect(() => {
    if (!test) return;
    const t = setInterval(() => setLeft(l => l - 1), 1000);
    return () => clearInterval(t);
  }, [test]);
  useEffect(() => { if (test && left <= 0) submit(true); }, [left, test]);

  if (done) return (
    <div className="panel" style={{ maxWidth: 640 }}>
      <h2 style={{ marginTop: 0 }}>Test submitted</h2>
      <div className="cards"><div className="stat"><b>{done.overall}%</b><span>Overall test score</span></div>
        <div className="stat gold"><b>{done.probability}%</b><span>Updated placement probability ({done.label})</span></div></div>
      <p>Your measured skills now feed the prediction and the skill gap analysis.</p>
      <div style={{ display: "flex", gap: 8 }}><button className="btn pri" onClick={() => go("report")}>View my placement report</button>
        <button className="btn" onClick={() => go("result/" + done.test_id)}>Review my answers</button></div>
    </div>);

  if (test) {
    const q = test.questions[cur], n = test.questions.length;
    return (
      <div className="stack">
        <div className="panel" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
          <div><b>Question {cur + 1} of {n}</b> · {Object.keys(ans).length} answered
            <div style={{ color: "var(--muted)", fontSize: 13 }}>{q.section}{q.skill ? " · " + q.skill : ""} · {q.difficulty}</div></div>
          <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
            <span className="tag" style={{ fontSize: 15, background: left < 120 ? "#f9e3e0" : "#e6f2f1" }} aria-live="off">⏱ {fmtTime(Math.max(0, left))}</span>
            <button className="btn pri" disabled={busy} onClick={() => submit(false)}>Submit test</button></div>
        </div>
        {err && <div className="err">{err}</div>}
        <div className="panel">
          <h3 style={{ fontSize: 17, marginBottom: 16 }}>{q.text}</h3>
          <div style={{ display: "grid", gap: 10 }}>
            {q.options.map((o, i) => (
              <label key={i} style={{ display: "flex", gap: 10, padding: "10px 14px", border: "1px solid " + (ans[q.id] === i ? "var(--teal)" : "var(--line)"), borderRadius: 8, cursor: "pointer", background: ans[q.id] === i ? "#e6f2f1" : "#fff" }}>
                <input type="radio" name={"q" + q.id} checked={ans[q.id] === i} onChange={() => setAns({ ...ans, [q.id]: i })} /> {o}
              </label>))}
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", marginTop: 18 }}>
            <button className="btn" disabled={cur === 0} onClick={() => setCur(cur - 1)}>← Previous</button>
            <button className="btn" disabled={cur === n - 1} onClick={() => setCur(cur + 1)}>Next →</button></div>
        </div>
        <div className="panel"><div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
          {test.questions.map((x, i) => <button key={x.id} className="btn sm" aria-label={"Go to question " + (i + 1)} onClick={() => setCur(i)}
            style={{ width: 34, background: i === cur ? "var(--ink)" : ans[x.id] !== undefined ? "#d6ecea" : "#fff", color: i === cur ? "#fff" : "inherit" }}>{i + 1}</button>)}</div></div>
      </div>);
  }

  if (!info) return err ? <div className="err">{err}</div> : <div className="empty">Loading...</div>;
  return (
    <div className="stack">
      <div className="panel" style={{ maxWidth: 760 }}>
        <h2 style={{ marginTop: 0 }}>Personalised skill assessment</h2>
        <p>Your ERP record is used to build this test just for you. We verify the technical skills your college recorded, probe skills your target role needs but your record is missing,
          and add a short aptitude round (quantitative, logical, verbal). Question difficulty follows your recorded skill level.</p>
        <ul style={{ color: "var(--muted)" }}><li>About 33 multiple-choice questions, {info.minutes} minutes</li><li>One attempt at a time; you can leave and resume while time remains</li>
          <li>Harder questions carry more weight in your score</li></ul>
        {err && <div className="err">{err}</div>}
        <button className="btn pri" disabled={busy} onClick={start}>{info.in_progress ? "Resume test in progress" : info.attempts.length ? "Take the test again" : "Start test"}</button>
      </div>
      {info.attempts.length > 0 && <div className="panel"><h3>Previous attempts</h3>
        <div className="tw"><table><thead><tr><th>Submitted</th><th>Target role</th><th>Score</th><th>Actions</th></tr></thead><tbody>
          {info.attempts.map(a => <tr key={a.id}><td>{a.submitted_at}</td><td>{a.role_name}</td><td>{a.overall_score}%</td>
            <td><button className="btn sm" onClick={() => go("result/" + a.id)}>Review</button></td></tr>)}</tbody></table></div></div>}
    </div>);
}

/* ---------- Test result review ---------- */
function TestResult({ id, go }) {
  const [d, setD] = useState(null), [err, setErr] = useState("");
  useEffect(() => { api(`/ai/test/${id}/result`).then(setD).catch(e => setErr(e.message)); }, [id]);
  if (err) return <div className="err">{err}</div>;
  if (!d) return <div className="empty">Loading...</div>;
  return (
    <div className="stack">
      <div><button className="btn" onClick={() => go("test")}>← Back</button></div>
      <div className="panel"><h3>Score by area (overall {d.test.overall_score}%)</h3>
        <ChartBox type="bar" height={Math.max(180, d.results.length * 32)} data={{ labels: d.results.map(r => r.name), datasets: [{ data: d.results.map(r => r.score), backgroundColor: d.results.map(r => r.kind === "skill" ? "#0d7a78" : "#e0a030") }] }}
          options={{ indexAxis: "y", plugins: { legend: { display: false } }, scales: { x: { min: 0, max: 100 } } }} /></div>
      <div className="panel"><h3>Question review</h3>
        {d.questions.map((q, i) => (
          <div key={i} style={{ padding: "10px 0", borderBottom: "1px solid var(--line)" }}>
            <b>{i + 1}. {q.text}</b> <span className={"tag " + (q.ok ? "g" : "r")}>{q.ok ? "Correct" : q.chosen == null ? "Skipped" : "Wrong"}</span>
            <div style={{ color: "var(--muted)", fontSize: 13 }}>{q.section}{q.skill ? " · " + q.skill : ""} · {q.difficulty}</div>
            <div>Correct answer: <b>{q.options[q.correct]}</b>{!q.ok && q.chosen != null ? <> · Your answer: {q.options[q.chosen]}</> : null}</div>
          </div>))}</div>
    </div>);
}

/* ---------- Placement report (student view and staff view) ---------- */
function Gauge({ value, label }) {
  const col = value >= 65 ? "#2b8a4e" : value >= 40 ? "#e0a030" : "#b8392b";
  return (
    <div style={{ position: "relative", height: 150 }}>
      <ChartBox type="doughnut" height={170} data={{ labels: ["Probability", "Remaining"], datasets: [{ data: [value, 100 - value], backgroundColor: [col, "#e8edf1"], borderWidth: 0 }] }}
        options={{ rotation: -90, circumference: 180, cutout: "74%", plugins: { legend: { display: false }, tooltip: { enabled: false } } }} />
      <div style={{ position: "absolute", left: 0, right: 0, top: 78, textAlign: "center" }}><b style={{ fontSize: 30 }}>{value}%</b><div style={{ color: "var(--muted)" }}>{label} chance</div></div>
    </div>);
}

function Report({ studentId, go, staff }) {
  const [r, setR] = useState(null), [err, setErr] = useState(""), [role, setRole] = useState("");
  useEffect(() => {
    setR(null);
    const q = new URLSearchParams({ ...(studentId ? { student_id: studentId } : {}), ...(role ? { role } : {}) });
    api("/ai/report?" + q).then(x => { setR(x); setErr(""); }).catch(e => setErr(e.message));
  }, [studentId, role]);
  if (err) return <div className="err">{err}</div>;
  if (!r) return <div className="empty">Fetching ERP data and running the prediction model...</div>;
  const p = r.prediction, s = r.student, ds = r.data_source;
  const gapRows = r.gaps.filter(g => g.gap > 0);
  return (
    <div className="stack">
      {staff && <div><button className="btn" onClick={() => history.back()}>← Back</button></div>}
      <div className="panel phead">
        <div className="avatar">{s.name.split(" ").map(x => x[0]).join("").slice(0, 2)}</div>
        <div style={{ flex: 1 }}><h2 style={{ margin: 0 }}>{s.name}</h2>
          <div style={{ color: "var(--muted)" }}>{s.student_code} · {s.course} · Semester {s.semester} · CGPA {s.cgpa}</div>
          <div style={{ marginTop: 4, fontSize: 13 }}>Data fetched from ERP at {ds.fetched_at} · Basis: <b>{ds.basis}</b></div></div>
        <div className="field" style={{ minWidth: 200 }}><label htmlFor="rolesel">Target job role</label>
          <select id="rolesel" value={role || r.role} onChange={e => setRole(e.target.value)}>{r.roles.map(x => <option key={x.role}>{x.role}</option>)}</select></div>
      </div>
      {!ds.tested && !staff && <div className="panel" style={{ borderLeft: "4px solid var(--gold)" }}>This report uses your ERP records only. <a href="#/test" style={{ color: "var(--teal-d)", fontWeight: 600 }}>Take the skill test</a> to verify your skills and sharpen the prediction.</div>}
      {!r.eligibility.eligible && <div className="panel" style={{ borderLeft: "4px solid var(--red)" }}><b>Not placement-eligible yet.</b> {r.eligibility.reasons.join(". ")}. The prediction below shows how your profile would fare if you were eligible today.</div>}
      {s.status === "Placed" && <div className="panel" style={{ borderLeft: "4px solid var(--green)" }}>ERP shows this student as <b>placed at {s.company}</b> ({s.package_lpa} LPA).</div>}

      <div className="grid2">
        <div className="panel"><h3>Placement prediction</h3><Gauge value={p.probability} label={p.label} />
          <div className="kv" style={{ marginTop: 10 }}>
            <div><small>Likely package if placed</small>{p.package.value} LPA <span style={{ color: "var(--muted)" }}>({p.package.low} - {p.package.high})</span></div>
            <div><small>Readiness for {r.role}</small>{r.readiness}%</div>
            <div><small>Model</small>{p.model} (AUC {p.auc})</div>
            <div><small>If top gaps are closed</small><b style={{ color: "var(--green)" }}>{p.after_gaps}%</b></div></div>
          {p.closed.length > 0 && <p style={{ color: "var(--muted)", fontSize: 13 }}>Closing {p.closed.join(", ")} to the target level is projected to move the probability from {p.probability}% to {p.after_gaps}%.</p>}</div>
        <div className="panel"><h3>What is driving your prediction</h3>
          <ChartBox type="bar" data={{ labels: p.drivers.map(d => d.group), datasets: [{ data: p.drivers.map(d => d.impact), backgroundColor: p.drivers.map(d => d.impact >= 0 ? "#2b8a4e" : "#b8392b") }] }}
            options={{ indexAxis: "y", plugins: { legend: { display: false } }, scales: { x: { title: { display: true, text: "Percentage-point effect on placement chance vs. average student" } } } }} />
          <p style={{ color: "var(--muted)", fontSize: 13, margin: "8px 0 0" }}>Green helps you; red holds you back.</p></div>
      </div>

      <div className="grid2">
        <div className="panel"><h3>You vs. placed and unplaced peers (ERP history)</h3>
          <ChartBox type="bar" data={{ labels: r.benchmark.map(b => b.label), datasets: [{ label: "You", data: r.benchmark.map(b => b.student), backgroundColor: "#0d7a78" },
            { label: "Placed peers", data: r.benchmark.map(b => b.placed), backgroundColor: "#2b8a4e" }, { label: "Unplaced peers", data: r.benchmark.map(b => b.unplaced), backgroundColor: "#c9ced4" }] }}
            options={{ scales: { y: { min: 0, max: 100 } } }} /></div>
        <div className="panel"><h3>Readiness by job role</h3>
          <ChartBox type="bar" data={{ labels: r.roles.map(x => x.role), datasets: [{ data: r.roles.map(x => x.readiness), backgroundColor: r.roles.map(x => x.role === r.role ? "#e0a030" : "#2f5d8a") }] }}
            options={{ indexAxis: "y", plugins: { legend: { display: false } }, scales: { x: { min: 0, max: 100 } } }} /></div>
      </div>

      <div className="panel"><h3>Skill gap analysis for {r.role}</h3>
        <div className="tw"><table><thead><tr><th>Area</th><th>Skill</th><th>Current</th><th>Target</th><th>Gap</th><th>Priority</th><th>Source</th></tr></thead><tbody>
          {r.gaps.map(g => <tr key={g.category + g.name}><td>{g.category}</td><td>{g.name}</td>
            <td style={{ minWidth: 110 }}>{g.current}<div className="meter"><i style={{ width: Math.min(100, g.current) + "%", background: g.gap ? "var(--gold)" : "var(--green)" }} /></div></td>
            <td>{g.target}</td><td>{g.gap ? "-" + g.gap : "-"}</td><td><span className={"tag " + PRIO[g.priority]}>{g.priority}</span></td><td style={{ color: "var(--muted)" }}>{g.source}</td></tr>)}
        </tbody></table></div></div>

      <div className="grid2">
        <div className="panel"><h3>Personal improvement roadmap</h3>
          {r.roadmap.length ? r.roadmap.map(x => <div key={x.step} style={{ padding: "8px 0", borderBottom: "1px solid var(--line)" }}>
            <b>{x.step}. {x.title}</b> <span className={"tag " + PRIO[x.priority]}>{x.priority}</span> <span className="tag">~{x.weeks} wk</span><div style={{ color: "var(--muted)" }}>{x.detail}</div></div>)
            : <div className="empty">You meet every target for this role. Keep practising and apply.</div>}</div>
        <div className="panel"><h3>Verified test results</h3>
          {r.test_sections.length ? <ChartBox type="radar" data={{ labels: r.test_sections.map(x => x.name), datasets: [{ data: r.test_sections.map(x => x.score), backgroundColor: "rgba(13,122,120,.25)", borderColor: "#0d7a78" }] }}
            options={{ plugins: { legend: { display: false } }, scales: { r: { min: 0, max: 100 } } }} /> : <div className="empty">No test taken yet.</div>}</div>
      </div>

      {r.history.length > 1 && <div className="panel"><h3>Placement probability over time</h3>
        <ChartBox type="line" data={{ labels: r.history.map(h => h.date.slice(0, 16)), datasets: [{ data: r.history.map(h => h.probability), borderColor: "#0d7a78", backgroundColor: "#0d7a78", tension: .25 }] }}
          options={{ plugins: { legend: { display: false } }, scales: { y: { min: 0, max: 100 } } }} /></div>}
      <div style={{ color: "var(--muted)", fontSize: 12 }}>Predictions are statistical estimates from this college's historical ERP data and are not a guarantee. Data used: {ds.tables.join(", ")}.</div>
    </div>);
}

/* ---------- Staff: AI insights ---------- */
function Insights({ me, go }) {
  const [m, setM] = useState(null), [c, setC] = useState(null), [role, setRole] = useState("Software Developer"), [err, setErr] = useState(""), [busy, setBusy] = useState(false);
  useEffect(() => { api("/ai/model").then(setM).catch(e => setErr(e.message)); }, []);
  useEffect(() => { api("/ai/cohort?role=" + encodeURIComponent(role)).then(setC).catch(e => setErr(e.message)); }, [role]);
  const retrain = async () => { setBusy(true); try { setM(await api("/ai/model/retrain", { method: "POST" })); } catch (e) { setErr(e.message); } setBusy(false); };
  if (err) return <div className="err">{err}</div>;
  if (!m || !c) return <div className="empty">Loading AI insights...</div>;
  const k = m.metrics, pc = x => (x * 100).toFixed(1) + "%";
  return (
    <div className="stack">
      <div className="cards">
        <div className="stat"><b>{m.name}</b><span>Selected model (best CV AUC)</span></div>
        <div className="stat green"><b>{pc(k.accuracy)}</b><span>Accuracy (5-fold CV)</span></div>
        <div className="stat"><b>{pc(k.precision)}</b><span>Precision</span></div>
        <div className="stat"><b>{pc(k.recall)}</b><span>Recall</span></div>
        <div className="stat"><b>{pc(k.f1)}</b><span>F1-score</span></div>
        <div className="stat gold"><b>{k.auc.toFixed(3)}</b><span>ROC-AUC</span></div>
        <div className="stat"><b>{m.n_train}</b><span>Training records ({m.n_placed} placed)</span></div>
        <div className="stat"><b>±{m.mae}</b><span>Package MAE (LPA)</span></div>
      </div>
      <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
        <span style={{ color: "var(--muted)" }}>Trained {m.trained_at} on eligible students' historical outcomes. Compared: {m.candidates.map(x => `${x.name} (AUC ${x.auc})`).join(", ")}.</span>
        {me.role === "admin" && <button className="btn" disabled={busy} onClick={retrain}>{busy ? "Retraining..." : "Retrain model on latest ERP data"}</button>}</div>
      <div className="grid2">
        <div className="panel"><h3>Feature importance</h3>
          <ChartBox type="bar" height={380} data={{ labels: m.importances.slice(0, 12).map(x => x[0]), datasets: [{ data: m.importances.slice(0, 12).map(x => +(x[1] * 100).toFixed(1)), backgroundColor: "#0d7a78" }] }}
            options={{ indexAxis: "y", plugins: { legend: { display: false } } }} /></div>
        <div className="panel"><h3>Predicted placement probability (all students)</h3>
          <ChartBox type="bar" data={{ labels: ["0-20%", "20-40%", "40-60%", "60-80%", "80-100%"], datasets: [{ data: m.distribution, backgroundColor: ["#b8392b", "#c9702f", "#e0a030", "#7a9e3b", "#2b8a4e"] }] }}
            options={{ plugins: { legend: { display: false } } }} />
          <h3 style={{ marginTop: 16 }}>Confusion matrix (cross-validated)</h3>
          <table style={{ maxWidth: 360 }}><thead><tr><th></th><th>Pred. unplaced</th><th>Pred. placed</th></tr></thead><tbody>
            <tr><th>Actual unplaced</th><td>{k.confusion[0][0]}</td><td>{k.confusion[0][1]}</td></tr>
            <tr><th>Actual placed</th><td>{k.confusion[1][0]}</td><td>{k.confusion[1][1]}</td></tr></tbody></table></div>
      </div>
      <div className="panel"><div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 10 }}><h3>Cohort skill gaps for a job role</h3>
        <select value={role} onChange={e => setRole(e.target.value)} aria-label="Job role">{c.roles.map(x => <option key={x}>{x}</option>)}</select></div>
        <ChartBox type="bar" data={{ labels: c.cohort_gaps.map(x => x.name), datasets: [{ data: c.cohort_gaps.map(x => x.avg_gap), backgroundColor: "#e0a030" }] }}
          options={{ plugins: { legend: { display: false } }, scales: { y: { title: { display: true, text: "Average gap to target (points)" } } } }} />
        <p style={{ color: "var(--muted)", fontSize: 13 }}>Use this to decide which training sessions the college should run for students targeting this role.</p></div>
      <div className="panel"><h3>Students needing attention ({c.at_risk_total} eligible and unplaced; lowest probability first)</h3>
        <div className="tw"><table><thead><tr><th>ID</th><th>Name</th><th>Course</th><th>Target role</th><th>Probability</th><th>Readiness</th><th>Biggest gap</th><th></th></tr></thead><tbody>
          {c.at_risk.map(s => <tr key={s.id}><td>{s.code}</td><td>{s.name}</td><td>{s.course}</td><td>{s.role}</td>
            <td><span className={"tag " + (s.probability >= 65 ? "g" : s.probability >= 40 ? "y" : "r")}>{s.probability}%</span></td><td>{s.readiness}%</td><td>{s.top_gap}</td>
            <td><button className="btn sm" onClick={() => go("report/" + s.id)}>AI report</button></td></tr>)}</tbody></table></div></div>
    </div>);
}

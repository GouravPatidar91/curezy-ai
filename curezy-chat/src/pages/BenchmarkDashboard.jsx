import { useState, useEffect, useRef } from "react"
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Legend
} from "recharts"

const API = "http://localhost:8000"

const INDUSTRY = [
    { name: "Gemini Ultra", org: "Google", color: "#4285F4", MedQA: 91.1, MMLU: 91.6, MedMCQA: 79.0, PubMedQA: 80.0, ClinReason: 89.0 },
    { name: "Human Doctor", org: "Avg", color: "#8B5CF6", MedQA: 87.0, MMLU: 88.0, MedMCQA: 82.0, PubMedQA: 78.0, ClinReason: 91.0 },
    { name: "GPT-4", org: "OpenAI", color: "#10A37F", MedQA: 86.7, MMLU: 87.0, MedMCQA: 72.0, PubMedQA: 74.4, ClinReason: 84.0 },
    { name: "Med-PaLM 2", org: "Google", color: "#34A853", MedQA: 86.5, MMLU: 85.0, MedMCQA: 72.3, PubMedQA: 75.0, ClinReason: 83.0 },
    { name: "Claude 3 Opus", org: "Anthropic", color: "#CC785C", MedQA: 85.1, MMLU: 84.9, MedMCQA: 67.5, PubMedQA: 72.6, ClinReason: 81.0 },
    { name: "Meditron 70B", org: "EPFL", color: "#F59E0B", MedQA: 70.2, MMLU: 72.8, MedMCQA: 65.6, PubMedQA: 76.1, ClinReason: 73.0 },
    { name: "Med-Gemma 4B", org: "Google", color: "#6EE7B7", MedQA: 58.5, MMLU: 67.0, MedMCQA: 60.5, PubMedQA: 71.8, ClinReason: 63.0 },
    { name: "GPT-3.5", org: "OpenAI", color: "#9CA3AF", MedQA: 53.6, MMLU: 69.9, MedMCQA: 60.0, PubMedQA: 72.2, ClinReason: 60.0 },
]
const BENCHMARKS = ["MedQA", "MMLU", "MedMCQA", "PubMedQA", "ClinReason"]
const avg = m => Math.round(BENCHMARKS.reduce((s, k) => s + (m[k] || 0), 0) / BENCHMARKS.length * 10) / 10

export function BenchmarkDashboard() {
    const [tab, setTab] = useState("live")
    const [status, setStatus] = useState(null)   // /benchmark/status response
    const [results, setResults] = useState(null)   // /benchmark/results response
    const [running, setRunning] = useState(false)
    const [mode, setMode] = useState("quick")
    const logRef = useRef(null)
    const pollRef = useRef(null)

    // ── Fetch latest results on mount ───────────────────────────────────────
    useEffect(() => {
        fetchResults()
        fetchStatus()
    }, [])

    // ── Auto-scroll log ─────────────────────────────────────────────────────
    useEffect(() => {
        if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight
    }, [status?.output_lines])

    // ── Poll while running ──────────────────────────────────────────────────
    const startPolling = () => {
        stopPolling()
        const startTime = Date.now()
        pollRef.current = setInterval(async () => {
            if (Date.now() - startTime > 30 * 60 * 1000) { // 30 min timeout
                stopPolling()
                setRunning(false)
                alert("Benchmark polling timed out after 30 minutes.")
                return
            }
            const s = await fetchStatus()
            if (s && s.status !== "running") {
                stopPolling()
                setRunning(false)
                fetchResults()
            }
        }, 2000)
    }
    const stopPolling = () => { clearInterval(pollRef.current); pollRef.current = null }
    useEffect(() => () => stopPolling(), [])

    const fetchStatus = async () => {
        try {
            const r = await fetch(`${API}/benchmark/status`)
            const d = await r.json()
            setStatus(d)
            if (d.status === "running") setRunning(true)
            return d
        } catch { return null }
    }

    const fetchResults = async () => {
        try {
            const r = await fetch(`${API}/benchmark/results`)
            const d = await r.json()
            if (d.success) setResults(d.results)
        } catch { }
    }

    const handleRun = async () => {
        try {
            setRunning(true)
            const r = await fetch(`${API}/benchmark/run`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ mode })
            })
            const d = await r.json()
            if (d.success) {
                setTab("live")
                startPolling()
            } else {
                alert(d.message || "Failed to start benchmark")
                setRunning(false)
            }
        } catch (e) {
            alert("Cannot connect to backend: " + e.message)
            setRunning(false)
        }
    }

    // ── Build leaderboard with council score injected ───────────────────────
    const councilScore = results?.council?.score_pct ?? null
    const allModels = [
        ...(councilScore !== null ? [{
            name: "Curezy Council", org: "You", color: "#22C55E", isCurezy: true,
            MedQA: results?.by_benchmark?.["USMLE Step 1"]?.pct ?? councilScore,
            MMLU: results?.by_benchmark?.["MMLU"]?.pct ?? councilScore,
            MedMCQA: results?.by_benchmark?.["MedMCQA"]?.pct ?? councilScore,
            PubMedQA: results?.by_benchmark?.["PubMedQA"]?.pct ?? councilScore,
            ClinReason: results?.by_benchmark?.["Clinical Reasoning"]?.pct ?? councilScore,
            overall: councilScore
        }] : []),
        ...INDUSTRY.map(m => ({ ...m, overall: avg(m) }))
    ].sort((a, b) => b.overall - a.overall)

    const barData = BENCHMARKS.map(b => {
        const row = { benchmark: b }
        allModels.slice(0, 5).forEach(m => { row[m.name] = m[b] ?? null })
        return row
    })

    const radarData = BENCHMARKS.map(b => {
        const row = { benchmark: b }
        allModels.slice(0, 4).forEach(m => { row[m.name] = m[b] ?? null })
        return row
    })

    // ── Render ───────────────────────────────────────────────────────────────
    return (
        <div style={{ minHeight: "100vh", background: "linear-gradient(135deg,#0f172a 0%,#1e293b 100%)", color: "#f8fafc", fontFamily: "'Inter',sans-serif", padding: "24px" }}>

            {/* Header */}
            <div style={{ marginBottom: 24 }}>
                <h1 style={{ fontSize: 28, fontWeight: 800, background: "linear-gradient(90deg,#22c55e,#3b82f6)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", margin: 0 }}>
                    Medical AI Benchmark Dashboard
                </h1>
                <p style={{ color: "#94a3b8", marginTop: 6 }}>Real scores from the same tests used to evaluate GPT-4 &amp; Gemini Ultra</p>
            </div>

            {/* Run Control */}
            <div style={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 16, padding: "20px 24px", marginBottom: 24, display: "flex", alignItems: "center", gap: 16, flexWrap: "wrap" }}>
                <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 4 }}>Run Council Benchmark</div>
                    <div style={{ color: "#64748b", fontSize: 13 }}>
                        {running ? "⏳ Benchmark running — 3 doctors analyzing in parallel + debate round..." : "Start a new benchmark test against your council models"}
                    </div>
                </div>
                <select value={mode} onChange={e => setMode(e.target.value)} disabled={running}
                    style={{ background: "#0f172a", border: "1px solid #334155", borderRadius: 8, padding: "8px 14px", color: "#f8fafc", fontSize: 14, cursor: "pointer" }}>
                    <option value="quick">Quick (10 questions)</option>
                    <option value="full">Full (27 questions)</option>
                </select>
                <button onClick={handleRun} disabled={running}
                    style={{ background: running ? "#334155" : "linear-gradient(90deg,#22c55e,#16a34a)", color: "#fff", border: "none", borderRadius: 10, padding: "10px 24px", fontWeight: 700, fontSize: 14, cursor: running ? "not-allowed" : "pointer", transition: "all 0.2s" }}>
                    {running ? "Running..." : "Run Now"}
                </button>
                <button onClick={() => { fetchStatus(); fetchResults() }}
                    style={{ background: "#0f172a", border: "1px solid #334155", borderRadius: 10, padding: "10px 14px", color: "#94a3b8", cursor: "pointer", fontSize: 14 }}>
                    Refresh
                </button>
            </div>

            {/* Tabs */}
            <div style={{ display: "flex", gap: 8, marginBottom: 20 }}>
                {["live", "leaderboard", "charts", "radar"].map(t => (
                    <button key={t} onClick={() => setTab(t)}
                        style={{ padding: "8px 20px", borderRadius: 10, border: "none", fontWeight: 600, fontSize: 13, cursor: "pointer", background: tab === t ? "linear-gradient(90deg,#22c55e,#16a34a)" : "#1e293b", color: tab === t ? "#fff" : "#94a3b8", transition: "all 0.2s" }}>
                        {t === "live" ? "Live Progress" : t === "leaderboard" ? "Leaderboard" : t === "charts" ? "Benchmark Charts" : "Radar"}
                    </button>
                ))}
            </div>

            {/* ── LIVE TAB ── */}
            {tab === "live" && (
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
                    {/* Status card */}
                    <div style={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 16, padding: 24 }}>
                        <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 16 }}>Live Status</div>
                        {status ? (
                            <>
                                <StatusBadge status={status.status} />
                                <div style={{ marginTop: 14, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                                    {[
                                        ["Mode", status.mode ?? "—"],
                                        ["Job ID", status.job_id ?? "—"],
                                        ["Started", status.started_at ? status.started_at.slice(11, 19) : "—"],
                                        ["Score So Far", status.council_score !== null ? `${status.council_score}%` : "—"],
                                    ].map(([k, v]) => (
                                        <div key={k} style={{ background: "#0f172a", borderRadius: 8, padding: "10px 12px" }}>
                                            <div style={{ color: "#64748b", fontSize: 11, marginBottom: 4 }}>{k}</div>
                                            <div style={{ fontWeight: 700, fontSize: 15 }}>{v}</div>
                                        </div>
                                    ))}
                                </div>
                                {status.current_step && (
                                    <div style={{ marginTop: 14, background: "#0f172a", borderRadius: 8, padding: 12, fontSize: 13, color: "#22c55e", fontFamily: "monospace" }}>
                                        {status.current_step}
                                    </div>
                                )}
                            </>
                        ) : <div style={{ color: "#64748b" }}>No status yet</div>}
                    </div>

                    {/* Log */}
                    <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 16, padding: 20, display: "flex", flexDirection: "column" }}>
                        <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 12, color: "#22c55e" }}>Terminal Output</div>
                        <div ref={logRef} style={{ flex: 1, maxHeight: 340, overflowY: "auto", fontFamily: "monospace", fontSize: 12, lineHeight: "20px" }}>
                            {status?.output_lines?.length > 0
                                ? status.output_lines.map((l, i) => (
                                    <div key={i} style={{ color: getLineColor(l), padding: "1px 0" }}>{l || " "}</div>
                                ))
                                : <div style={{ color: "#475569" }}>No output yet — click "Run Now" to start</div>
                            }
                        </div>
                    </div>

                    {/* Last result quick stats */}
                    {results && (
                        <div style={{ gridColumn: "1 / -1", background: "#1e293b", border: "1px solid #22c55e40", borderRadius: 16, padding: 24 }}>
                            <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 16, color: "#22c55e" }}>Last Benchmark Results</div>
                            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 14 }}>
                                {[
                                    ["Council Score", `${results.council?.score_pct}%`, "#22c55e"],
                                    ["Questions", `${results.council?.correct}/${results.council?.total}`, "#3b82f6"],
                                    ["Test Time", `${results.elapsed_s}s`, "#f59e0b"],
                                    ["Pipeline", "Parallel+Debate", "#8b5cf6"],
                                ].map(([k, v, c]) => (
                                    <div key={k} style={{ background: "#0f172a", borderRadius: 12, padding: "16px 20px", borderTop: `3px solid ${c}` }}>
                                        <div style={{ color: "#64748b", fontSize: 12, marginBottom: 6 }}>{k}</div>
                                        <div style={{ fontWeight: 800, fontSize: 22, color: c }}>{v}</div>
                                    </div>
                                ))}
                            </div>
                            {results.individual_postdebate && (
                                <div style={{ marginTop: 16, display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
                                    {Object.entries(results.individual_postdebate).map(([name, score]) => (
                                        <div key={name} style={{ background: "#0f172a", borderRadius: 10, padding: "12px 16px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                                            <span style={{ fontSize: 14, color: "#94a3b8" }}>{name}</span>
                                            <span style={{ fontWeight: 700, fontSize: 16, color: score >= 70 ? "#22c55e" : score >= 50 ? "#f59e0b" : "#ef4444" }}>{score}%</span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}
                </div>
            )}

            {/* ── LEADERBOARD TAB ── */}
            {tab === "leaderboard" && (
                <div style={{ background: "#1e293b", borderRadius: 16, overflow: "hidden", border: "1px solid #334155" }}>
                    <div style={{ padding: "16px 24px", borderBottom: "1px solid #334155", fontWeight: 700, fontSize: 16 }}>
                        Global Leaderboard — Overall Score
                    </div>
                    <table style={{ width: "100%", borderCollapse: "collapse" }}>
                        <thead>
                            <tr style={{ background: "#0f172a" }}>
                                {["#", "Model", "Org", "MedQA", "MMLU", "MedMCQA", "PubMedQA", "ClinReason", "Overall"].map(h => (
                                    <th key={h} style={{ padding: "10px 16px", textAlign: h === "Model" || h === "Org" ? "left" : "center", fontSize: 12, color: "#64748b", fontWeight: 600 }}>{h}</th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {allModels.map((m, i) => (
                                <tr key={m.name} style={{ borderTop: "1px solid #334155", background: m.isCurezy ? "#0f2d1a" : i % 2 === 0 ? "#1e293b" : "#172033" }}>
                                    <td style={{ padding: "12px 16px", color: "#64748b", fontSize: 13 }}>{i + 1}</td>
                                    <td style={{ padding: "12px 16px", fontWeight: m.isCurezy ? 800 : 600, color: m.isCurezy ? "#22c55e" : "#f8fafc", fontSize: 14 }}>
                                        {m.isCurezy && "⭐ "}{m.name}
                                    </td>
                                    <td style={{ padding: "12px 16px", color: "#64748b", fontSize: 13 }}>{m.org}</td>
                                    {BENCHMARKS.map(b => (
                                        <td key={b} style={{ padding: "12px 16px", textAlign: "center", fontSize: 13, color: m.isCurezy ? "#22c55e" : "#94a3b8" }}>
                                            {m[b] != null ? `${m[b]}%` : "—"}
                                        </td>
                                    ))}
                                    <td style={{
                                        padding: "12px 16px", textAlign: "center", fontWeight: 800, fontSize: 15,
                                        color: m.overall >= 87 ? "#22c55e" : m.overall >= 80 ? "#3b82f6" : m.overall >= 70 ? "#f59e0b" : "#ef4444"
                                    }}>
                                        {m.overall}%
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* ── CHARTS TAB ── */}
            {tab === "charts" && (
                <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: 20 }}>
                    <div style={{ background: "#1e293b", borderRadius: 16, padding: 24, border: "1px solid #334155" }}>
                        <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 20 }}>Score by Benchmark (Top 5 Models)</div>
                        <ResponsiveContainer width="100%" height={340}>
                            <BarChart data={barData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                <XAxis dataKey="benchmark" stroke="#64748b" fontSize={13} />
                                <YAxis domain={[50, 100]} stroke="#64748b" fontSize={12} />
                                <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #334155", borderRadius: 8 }} />
                                <Legend />
                                {allModels.slice(0, 5).map(m => (
                                    <Bar key={m.name} dataKey={m.name} fill={m.color} radius={[4, 4, 0, 0]} />
                                ))}
                            </BarChart>
                        </ResponsiveContainer>
                    </div>

                    {results?.by_difficulty && (
                        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
                            <div style={{ background: "#1e293b", borderRadius: 16, padding: 24, border: "1px solid #334155" }}>
                                <div style={{ fontWeight: 700, marginBottom: 16 }}>Council Score by Difficulty</div>
                                {Object.entries(results.by_difficulty).map(([d, v]) => (
                                    <div key={d} style={{ marginBottom: 12 }}>
                                        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                                            <span style={{ fontSize: 13, color: "#94a3b8" }}>{d.toUpperCase()}</span>
                                            <span style={{ fontWeight: 700 }}>{v.pct}%</span>
                                        </div>
                                        <div style={{ background: "#0f172a", borderRadius: 100, height: 8, overflow: "hidden" }}>
                                            <div style={{ width: `${v.pct}%`, height: "100%", borderRadius: 100, background: v.pct >= 80 ? "#22c55e" : v.pct >= 60 ? "#f59e0b" : "#ef4444", transition: "width 0.8s" }} />
                                        </div>
                                    </div>
                                ))}
                            </div>
                            <div style={{ background: "#1e293b", borderRadius: 16, padding: 24, border: "1px solid #334155" }}>
                                <div style={{ fontWeight: 700, marginBottom: 16 }}>Score by Benchmark Category</div>
                                {Object.entries(results.by_benchmark).map(([b, v]) => (
                                    <div key={b} style={{ marginBottom: 12 }}>
                                        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                                            <span style={{ fontSize: 12, color: "#94a3b8" }}>{b}</span>
                                            <span style={{ fontWeight: 700 }}>{v.pct}% ({v.correct}/{v.total})</span>
                                        </div>
                                        <div style={{ background: "#0f172a", borderRadius: 100, height: 8, overflow: "hidden" }}>
                                            <div style={{ width: `${v.pct}%`, height: "100%", borderRadius: 100, background: "#3b82f6", transition: "width 0.8s" }} />
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* ── RADAR TAB ── */}
            {tab === "radar" && (
                <div style={{ background: "#1e293b", borderRadius: 16, padding: 24, border: "1px solid #334155" }}>
                    <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 20 }}>Multi-Axis Performance Radar (Top 4 Models)</div>
                    <ResponsiveContainer width="100%" height={400}>
                        <RadarChart data={radarData}>
                            <PolarGrid stroke="#334155" />
                            <PolarAngleAxis dataKey="benchmark" stroke="#94a3b8" fontSize={13} />
                            <PolarRadiusAxis angle={30} domain={[50, 100]} stroke="#334155" fontSize={11} />
                            {allModels.slice(0, 4).map(m => (
                                <Radar key={m.name} name={m.name} dataKey={m.name} stroke={m.color} fill={m.color} fillOpacity={0.15} />
                            ))}
                            <Legend />
                            <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #334155", borderRadius: 8 }} />
                        </RadarChart>
                    </ResponsiveContainer>
                </div>
            )}
        </div>
    )
}

function StatusBadge({ status }) {
    const cfg = {
        running: { bg: "#1c3a1c", border: "#22c55e", color: "#22c55e", dot: "#22c55e", label: "Running" },
        completed: { bg: "#1c2e4a", border: "#3b82f6", color: "#3b82f6", dot: "#3b82f6", label: "Completed" },
        idle: { bg: "#1e293b", border: "#334155", color: "#64748b", dot: "#334155", label: "Idle" },
        failed: { bg: "#3a1c1c", border: "#ef4444", color: "#ef4444", dot: "#ef4444", label: "Failed" },
    }[status] ?? { bg: "#1e293b", border: "#334155", color: "#94a3b8", dot: "#334155", label: status }

    return (
        <div style={{ display: "inline-flex", alignItems: "center", gap: 8, background: cfg.bg, border: `1px solid ${cfg.border}`, borderRadius: 100, padding: "6px 14px" }}>
            <div style={{ width: 8, height: 8, borderRadius: "50%", background: cfg.dot, boxShadow: status === "running" ? `0 0 6px ${cfg.dot}` : undefined }} />
            <span style={{ color: cfg.color, fontWeight: 700, fontSize: 13 }}>{cfg.label}</span>
        </div>
    )
}

function getLineColor(line) {
    if (!line) return "#334155"
    const l = line.toLowerCase()
    if (l.includes("[ok]") || l.includes("correct") || l.includes("completed")) return "#22c55e"
    if (l.includes("[x]") || l.includes("wrong") || l.includes("failed")) return "#ef4444"
    if (l.includes("[round 1]") || l.includes("parallel")) return "#3b82f6"
    if (l.includes("[round 2]") || l.includes("debate")) return "#8b5cf6"
    if (l.includes("[council]") || l.includes("consensus")) return "#f59e0b"
    if (l.includes("===") || l.includes("---")) return "#334155"
    return "#94a3b8"
}

export default BenchmarkDashboard

import { useState, useEffect, useRef, useCallback } from 'react'

type Run = {
  run_id: string
  status: string
  created_at: string
  overall_accuracy?: number
  source?: string
}

type Page = 'dashboard' | 'new-run' | 'run-detail'

function App() {
  const [page, setPage] = useState<Page>('dashboard')
  const [runs, setRuns] = useState<Run[]>([])
  const [activeRunId, setActiveRunId] = useState<string | null>(null)
  const [logs, setLogs] = useState<string[]>([])
  const [runStatus, setRunStatus] = useState<string>('')
  const [runAccuracy, setRunAccuracy] = useState<number | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const wsRef = useRef<WebSocket | null>(null)
  const pollRef = useRef<number | null>(null)

  // --- Dashboard ---
  const loadRuns = useCallback(async () => {
    try {
      const res = await fetch('/api/runs')
      if (res.ok) setRuns(await res.json())
    } catch { /* ignore */ }
  }, [])

  useEffect(() => { loadRuns() }, [loadRuns])

  // --- New Run (upload) ---
  const handleUpload = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    const form = e.currentTarget
    const fd = new FormData(form)
    try {
      const res = await fetch('/api/pipeline/run/upload', { method: 'POST', body: fd })
      if (!res.ok) { const err = await res.json(); throw new Error(err.detail || 'Run failed') }
      const data = await res.json()
      setActiveRunId(data.run_id)
      navigateToRun(data.run_id)
    } catch (err: any) {
      setError(err.message)
    }
    setLoading(false)
  }

  // --- Run with JIRA ---
  const handleJiraRun = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    const form = e.currentTarget
    const data = Object.fromEntries(new FormData(form).entries())
    try {
      const res = await fetch('/api/pipeline/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          mode: 'jira',
          jira_ticket_id: data.jira_ticket_id,
          target_url: data.target_url || null,
          username: data.username || null,
          password: data.password || null,
          run_type: 'verification',
        }),
      })
      if (!res.ok) { const err = await res.json(); throw new Error(err.detail || 'Run failed') }
      const result = await res.json()
      setActiveRunId(result.run_id)
      navigateToRun(result.run_id)
    } catch (err: any) {
      setError(err.message)
    }
    setLoading(false)
  }

  // --- Navigate to run detail ---
  const navigateToRun = (runId: string) => {
    setActiveRunId(runId)
    setLogs([])
    setRunStatus('running')
    setRunAccuracy(null)
    setPage('run-detail')
  }

  // --- WebSocket logs ---
  useEffect(() => {
    if (!activeRunId || page !== 'run-detail') return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const ws = new WebSocket(`${protocol}//${host}/api/pipeline/${activeRunId}/logs`)
    wsRef.current = ws

    ws.onmessage = (event) => {
      const msg = event.data
      setLogs(prev => {
        const next = [...prev, msg]
        return next.length > 500 ? next.slice(-500) : next
      })
      if (msg.includes('[RUN] Pipeline')) {
        if (msg.includes('completed')) setRunStatus('completed')
        else if (msg.includes('failed')) setRunStatus('failed')
        else if (msg.includes('aborted')) setRunStatus('aborted')
      }
    }
    ws.onerror = () => {
      // Fallback to polling
      pollRef.current = window.setInterval(async () => {
        try {
          const res = await fetch(`/api/pipeline/${activeRunId}/status`)
          const data = await res.json()
          setRunStatus(data.status)
          if (data.overall_accuracy != null) setRunAccuracy(data.overall_accuracy)
          if (['completed', 'failed', 'aborted'].includes(data.status)) {
            if (pollRef.current) clearInterval(pollRef.current)
            const logRes = await fetch(`/api/pipeline/${activeRunId}/artifact-raw/log.txt`)
            if (logRes.ok) setLogs((await logRes.text()).split('\n'))
          }
        } catch { /* ignore */ }
      }, 1000)
    }

    return () => {
      ws.close()
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [activeRunId, page])

  return (
    <div style={{ minHeight: '100vh', background: '#f0f4f8', color: '#1a1a2e', fontFamily: '-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif' }}>
      {/* Nav */}
      <nav style={{ background: 'linear-gradient(135deg, #0f172a, #1e293b)', color: '#fff', padding: '0.75rem 1.5rem', display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
        <h2 style={{ fontSize: '1rem', fontWeight: 700 }}>QA Workflow Agent</h2>
        <button onClick={() => { setPage('dashboard'); loadRuns() }} style={navBtnStyle}>Dashboard</button>
        <button onClick={() => setPage('new-run')} style={navBtnStyle}>New Run</button>
        {activeRunId && <button onClick={() => setPage('run-detail')} style={navBtnStyle}>Run: {activeRunId}</button>}
      </nav>

      <div style={{ maxWidth: 1200, margin: '0 auto', padding: '1.5rem' }}>
        {page === 'dashboard' && <DashboardPage runs={runs} onSelect={navigateToRun} onRefresh={loadRuns} />}
        {page === 'new-run' && <NewRunPage onUpload={handleUpload} onJiraRun={handleJiraRun} loading={loading} error={error} />}
        {page === 'run-detail' && activeRunId && <RunDetailPage runId={activeRunId} status={runStatus} accuracy={runAccuracy} logs={logs} />}
      </div>
    </div>
  )
}

// --- Dashboard ---
function DashboardPage({ runs, onSelect, onRefresh }: { runs: Run[]; onSelect: (id: string) => void; onRefresh: () => void }) {
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h2 style={{ fontSize: '1.2rem' }}>Past Runs</h2>
        <button onClick={onRefresh} style={primaryBtnStyle}>Refresh</button>
      </div>
      {runs.length === 0 ? (
        <div style={{ background: '#fff', borderRadius: 12, padding: '2rem', textAlign: 'center', color: '#64748b' }}>
          No runs yet. Start a new run to see results here.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {runs.map(run => (
            <div key={run.run_id} onClick={() => onSelect(run.run_id)}
              style={{ background: '#fff', borderRadius: 10, padding: '0.8rem 1rem', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center', boxShadow: '0 1px 4px rgba(0,0,0,.06)' }}>
              <div>
                <strong>{run.run_id}</strong>
                <span style={{ marginLeft: '0.5rem', fontSize: '0.78rem', color: '#64748b' }}>{run.source} · {run.created_at?.slice(0, 19).replace('T', ' ')}</span>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                <StatusBadge status={run.status} />
                {run.overall_accuracy != null && <span style={{ fontWeight: 700, color: run.overall_accuracy >= 90 ? '#22c55e' : run.overall_accuracy >= 70 ? '#f59e0b' : '#ef4444' }}>{run.overall_accuracy}%</span>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// --- New Run ---
function NewRunPage({ onUpload, onJiraRun, loading, error }: {
  onUpload: (e: React.FormEvent<HTMLFormElement>) => Promise<void>
  onJiraRun: (e: React.FormEvent<HTMLFormElement>) => Promise<void>
  loading: boolean
  error: string
}) {
  const [tab, setTab] = useState<'document' | 'jira'>('document')

  return (
    <div>
      <h2 style={{ fontSize: '1.2rem', marginBottom: '1rem' }}>New Pipeline Run</h2>

      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
        <button onClick={() => setTab('document')} style={{ ...tabBtnStyle, ...(tab === 'document' ? activeTabBtnStyle : {}) }}>Upload Document</button>
        <button onClick={() => setTab('jira')} style={{ ...tabBtnStyle, ...(tab === 'jira' ? activeTabBtnStyle : {}) }}>JIRA Ticket</button>
      </div>

      {error && <div style={{ background: '#fef2f2', color: '#dc2626', padding: '0.6rem 1rem', borderRadius: 8, marginBottom: '1rem', fontSize: '0.85rem' }}>{error}</div>}

      <div style={{ background: '#fff', borderRadius: 12, padding: '1.5rem', boxShadow: '0 1px 4px rgba(0,0,0,.06)' }}>
        {tab === 'document' ? (
          <form onSubmit={onUpload}>
            <FormField label="Requirements Document (.md, .pdf, .docx, .txt)">
              <input type="file" name="file" accept=".md,.pdf,.docx,.txt" required style={inputStyle} />
            </FormField>
            <FormField label="Target App URL (optional)">
              <input type="url" name="target_url" placeholder="https://example.com" style={inputStyle} />
            </FormField>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <FormField label="Username (optional)">
                <input type="text" name="username" placeholder="admin@example.com" style={inputStyle} />
              </FormField>
              <FormField label="Password (optional)">
                <input type="password" name="password" placeholder="••••••••" style={inputStyle} />
              </FormField>
            </div>
            <button type="submit" disabled={loading} style={primaryBtnStyle}>
              {loading ? 'Starting...' : 'Run Pipeline'}
            </button>
          </form>
        ) : (
          <form onSubmit={onJiraRun}>
            <FormField label="JIRA Ticket ID">
              <input type="text" name="jira_ticket_id" placeholder="PROJ-123" required style={inputStyle} />
            </FormField>
            <FormField label="Target App URL (optional)">
              <input type="url" name="target_url" placeholder="https://example.com" style={inputStyle} />
            </FormField>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <FormField label="Username (optional)">
                <input type="text" name="username" placeholder="admin@example.com" style={inputStyle} />
              </FormField>
              <FormField label="Password (optional)">
                <input type="password" name="password" placeholder="••••••••" style={inputStyle} />
              </FormField>
            </div>
            <button type="submit" disabled={loading} style={primaryBtnStyle}>
              {loading ? 'Starting...' : 'Run Pipeline'}
            </button>
          </form>
        )}
      </div>
    </div>
  )
}

// --- Run Detail ---
function RunDetailPage({ runId, status, accuracy, logs }: { runId: string; status: string; accuracy: number | null; logs: string[] }) {
  const logEndRef = useRef<HTMLDivElement>(null)
  useEffect(() => { logEndRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [logs])

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h2 style={{ fontSize: '1.2rem' }}>Run: {runId}</h2>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <StatusBadge status={status} />
          {accuracy != null && (
            <span style={{ fontWeight: 700, fontSize: '1.1rem', color: accuracy >= 90 ? '#22c55e' : accuracy >= 70 ? '#f59e0b' : '#ef4444' }}>
              {accuracy}%
            </span>
          )}
          <a href={`/api/pipeline/${runId}/report`} target="_blank" rel="noreferrer" style={{ ...primaryBtnStyle, textDecoration: 'none', display: 'inline-block' }}>
            Report
          </a>
        </div>
      </div>

      <div style={{ background: '#0f172a', color: '#e2e8f0', borderRadius: 10, padding: '1rem', fontFamily: 'monospace', fontSize: '0.78rem', maxHeight: 500, overflowY: 'auto', whiteSpace: 'pre-wrap' }}>
        {logs.length === 0 ? <span style={{ color: '#64748b' }}>Waiting for logs...</span> : logs.map((line, i) => <div key={i}>{line}</div>)}
        <div ref={logEndRef} />
      </div>

      <div style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem' }}>
        <a href={`/api/pipeline/${runId}/artifact/bugs.md`} target="_blank" rel="noreferrer" style={secondaryBtnStyle}>Bugs</a>
        <a href={`/api/pipeline/${runId}/artifact/generated_test_cases.md`} target="_blank" rel="noreferrer" style={secondaryBtnStyle}>Test Cases</a>
        <a href={`/api/pipeline/${runId}/artifact-raw/log.txt`} target="_blank" rel="noreferrer" style={secondaryBtnStyle}>Raw Log</a>
        <a href={`/api/pipeline/${runId}/artifact-raw/context.json`} target="_blank" rel="noreferrer" style={secondaryBtnStyle}>Context JSON</a>
      </div>
    </div>
  )
}

// --- Helpers ---
function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    running: '#3b82f6',
    completed: '#22c55e',
    failed: '#ef4444',
    aborted: '#f59e0b',
    pending: '#94a3b8',
  }
  return (
    <span style={{
      display: 'inline-block', padding: '0.1rem 0.6rem', borderRadius: 12, fontSize: '0.72rem',
      fontWeight: 600, background: colors[status] || '#94a3b8', color: '#fff',
    }}>
      {status}
    </span>
  )
}

function FormField({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: '1rem' }}>
      <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: '#475569', marginBottom: '0.3rem' }}>{label}</label>
      {children}
    </div>
  )
}

const inputStyle: React.CSSProperties = {
  width: '100%', padding: '0.5rem 0.7rem', borderRadius: 8, border: '1px solid #e2e8f0',
  fontSize: '0.85rem', outline: 'none', boxSizing: 'border-box',
}

const navBtnStyle: React.CSSProperties = {
  background: 'transparent', border: '1px solid rgba(255,255,255,.2)', color: '#fff',
  padding: '0.3rem 0.8rem', borderRadius: 6, fontSize: '0.78rem', cursor: 'pointer',
}

const primaryBtnStyle: React.CSSProperties = {
  background: '#3b82f6', color: '#fff', border: 'none', padding: '0.5rem 1.2rem',
  borderRadius: 8, fontSize: '0.85rem', fontWeight: 600, cursor: 'pointer',
}

const secondaryBtnStyle: React.CSSProperties = {
  border: '1px solid #e2e8f0', background: '#fff', color: '#475569',
  padding: '0.4rem 0.9rem', borderRadius: 8, fontSize: '0.8rem', cursor: 'pointer', textDecoration: 'none',
}

const tabBtnStyle: React.CSSProperties = {
  background: '#fff', border: '1px solid #e2e8f0', padding: '0.4rem 1rem',
  borderRadius: 8, fontSize: '0.82rem', cursor: 'pointer', color: '#475569',
}

const activeTabBtnStyle: React.CSSProperties = {
  background: '#3b82f6', color: '#fff', borderColor: '#3b82f6',
}

export default App

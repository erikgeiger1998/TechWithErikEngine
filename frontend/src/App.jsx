import { useState, useEffect } from 'react'
import './index.css'

function App() {
  const [metrics, setMetrics] = useState(null)
  const [recommendation, setRecommendation] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [metricsRes, recRes] = await Promise.all([
          fetch('http://localhost:8000/api/dashboard/metrics'),
          fetch('http://localhost:8000/api/recommendations/today')
        ])
        
        const metricsData = await metricsRes.json()
        const recData = await recRes.json()
        
        setMetrics(metricsData)
        setRecommendation(recData)
      } catch (err) {
        console.error("Failed to fetch data", err)
      } finally {
        setLoading(false)
      }
    }
    
    fetchData()
  }, [])

  if (loading) {
    return <div className="dashboard-layout"><div className="main-content">Loading OS...</div></div>
  }

  return (
    <div className="dashboard-layout">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-dot"></div>
          Editorial OS
        </div>
        <ul className="nav-links">
          <li className="nav-link active">Morning Brief</li>
          <li className="nav-link">Intelligence Hub</li>
          <li className="nav-link">Connectors</li>
          <li className="nav-link">Settings</li>
        </ul>
      </aside>

      <main className="main-content">
        <header className="header">
          <h1 className="title">Morning Brief</h1>
          <p className="subtitle">Deterministic intelligence for today's editorial.</p>
        </header>

        {recommendation && (
          <div className="glass-panel morning-brief">
            <div className="brief-header">
              <div>
                {recommendation.film_decision && <span className="badge">FILM TODAY</span>}
                {!recommendation.film_decision && <span className="badge" style={{color: '#f87171', background: 'rgba(248,113,113,0.1)', borderColor: 'rgba(248,113,113,0.3)'}}>SKIP TODAY</span>}
              </div>
              <div className="roi-circle">
                <span className="roi-val">{recommendation.roi}</span>
                <span className="roi-lbl">ROI</span>
              </div>
            </div>
            <h2 className="brief-topic">{recommendation.topic.replace("Fix: ", "")}</h2>
            <div className="metric-sub" style={{marginBottom: '24px'}}>
              Confidence: <strong>{recommendation.confidence.toFixed(1)}%</strong> &nbsp;&bull;&nbsp; Trust Risk: <strong>{recommendation.trust_risk}</strong>
            </div>
            
            <h3 style={{fontSize: '0.875rem', color: '#8b8b9d', marginBottom: '12px'}}>Primary Evidence</h3>
            <div className="evidence-list">
              {recommendation.evidence.map((ev, i) => (
                <div key={i} className="evidence-tag">
                  <strong>{ev.source}</strong> &middot; {ev.type}
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="metrics-grid">
          <div className="glass-panel metric-card">
            <h3>Raw Signals</h3>
            <div className="metric-value">{metrics?.database.signals.toLocaleString()}</div>
            <div className="metric-sub">Aggregated intelligence points</div>
          </div>
          
          <div className="glass-panel metric-card">
            <h3>Canonical Problems</h3>
            <div className="metric-value">{metrics?.database.problems.toLocaleString()}</div>
            <div className="metric-sub">Clustered narrative entities</div>
          </div>
          
          <div className="glass-panel metric-card">
            <h3>System Health</h3>
            <div className="metric-value" style={{display: 'flex', alignItems: 'center'}}>
              <span className="status-dot healthy"></span> {metrics?.connectors_summary.healthy}
              <span className="status-dot warning" style={{marginLeft: '16px'}}></span> {metrics?.connectors_summary.warnings}
            </div>
            <div className="metric-sub">Last fetch: {metrics?.connectors_summary.last_fetch}</div>
          </div>
        </div>

      </main>
    </div>
  )
}

export default App

import { useState, useEffect } from 'react'
import './index.css'

function App() {
  const [metrics, setMetrics] = useState(null)
  const [recommendation, setRecommendation] = useState(null)
  const [problems, setProblems] = useState([])
  const [activeTab, setActiveTab] = useState('morning-brief')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [metricsRes, recRes, probRes] = await Promise.all([
          fetch('/api/dashboard/metrics'),
          fetch('/api/recommendations/today'),
          fetch('/api/intelligence/problems')
        ])
        
        const metricsData = await metricsRes.json()
        const recData = await recRes.json()
        const probData = await probRes.json()
        
        setMetrics(metricsData)
        setRecommendation(recData)
        setProblems(probData)
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
          <li className={`nav-link ${activeTab === 'morning-brief' ? 'active' : ''}`} onClick={() => setActiveTab('morning-brief')}>Morning Brief</li>
          <li className={`nav-link ${activeTab === 'intelligence-hub' ? 'active' : ''}`} onClick={() => setActiveTab('intelligence-hub')}>Intelligence Hub</li>
          <li className={`nav-link ${activeTab === 'connectors' ? 'active' : ''}`} onClick={() => setActiveTab('connectors')}>Connectors</li>
          <li className={`nav-link ${activeTab === 'settings' ? 'active' : ''}`} onClick={() => setActiveTab('settings')}>Settings</li>
        </ul>
      </aside>

      <main className="main-content">
        <header className="header">
          <h1 className="title">
            {activeTab === 'morning-brief' && "Morning Brief"}
            {activeTab === 'intelligence-hub' && "Intelligence Hub"}
            {activeTab === 'connectors' && "Connectors"}
            {activeTab === 'settings' && "Settings"}
          </h1>
          <p className="subtitle">
            {activeTab === 'morning-brief' && "Deterministic intelligence for today's editorial."}
            {activeTab === 'intelligence-hub' && "Canonical problems & aggregated metrics."}
            {activeTab === 'connectors' && "System health and ingestion status."}
            {activeTab === 'settings' && "Configure OS parameters."}
          </p>
        </header>

        {activeTab === 'morning-brief' && recommendation && (
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
              Confidence: <strong>{(recommendation.confidence || 0).toFixed(1)}%</strong> &nbsp;&bull;&nbsp; Trust Risk: <strong>{recommendation.trust_risk}</strong>
            </div>
            
            <h3 style={{fontSize: '0.875rem', color: '#8b8b9d', marginBottom: '12px'}}>Primary Evidence</h3>
            <div className="evidence-list">
              {recommendation.evidence?.map((ev, i) => (
                <div key={i} className="evidence-tag">
                  <strong>{ev.source}</strong> &middot; {ev.type}
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'morning-brief' && metrics && (
        <div className="metrics-grid">
          <div className="glass-panel metric-card">
            <h3>Raw Signals</h3>
            <div className="metric-value">{metrics.database?.signals?.toLocaleString()}</div>
            <div className="metric-sub">Aggregated intelligence points</div>
          </div>
          
          <div className="glass-panel metric-card">
            <h3>Canonical Problems</h3>
            <div className="metric-value">{metrics.database?.problems?.toLocaleString()}</div>
            <div className="metric-sub">Clustered narrative entities</div>
          </div>
          
          <div className="glass-panel metric-card">
            <h3>System Health</h3>
            <div className="metric-value" style={{display: 'flex', alignItems: 'center'}}>
              <span className="status-dot healthy"></span> {metrics.connectors_summary?.healthy}
              <span className="status-dot warning" style={{marginLeft: '16px'}}></span> {metrics.connectors_summary?.warnings}
            </div>
            <div className="metric-sub">Last fetch: {metrics.connectors_summary?.last_fetch}</div>
          </div>
        </div>
        )}

        {activeTab === 'intelligence-hub' && (
          <div className="glass-panel">
            <h3 style={{marginBottom: '16px'}}>Canonical Entities</h3>
            <table style={{width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem'}}>
              <thead>
                <tr style={{borderBottom: '1px solid #3f3f46', color: '#a1a1aa'}}>
                  <th style={{padding: '12px 8px'}}>Problem Name</th>
                  <th style={{padding: '12px 8px'}}>Aliases</th>
                  <th style={{padding: '12px 8px'}}>Evergreen Score</th>
                  <th style={{padding: '12px 8px'}}>Seasonality Multiplier</th>
                </tr>
              </thead>
              <tbody>
                {(Array.isArray(problems) ? problems : []).map(p => (
                  <tr key={p.id} style={{borderBottom: '1px solid #27272a'}}>
                    <td style={{padding: '12px 8px', fontWeight: 'bold'}}>{p.name}</td>
                    <td style={{padding: '12px 8px', color: '#a1a1aa'}}>{p.aliases?.join(', ')}</td>
                    <td style={{padding: '12px 8px', color: '#10b981'}}>{p.evergreen_score.toFixed(1)}</td>
                    <td style={{padding: '12px 8px'}}>{p.seasonality_multiplier}x</td>
                  </tr>
                ))}
                {(!Array.isArray(problems) || problems.length === 0) && (
                  <tr>
                    <td colSpan="4" style={{padding: '24px', textAlign: 'center', color: '#71717a'}}>No problems found. Run `intel seed`</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {activeTab === 'connectors' && metrics && (
          <div className="metrics-grid">
            {metrics.connectors.map(c => (
              <div key={c.name} className="glass-panel metric-card">
                <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px'}}>
                  <h3 style={{margin: 0}}>{c.name.toUpperCase()}</h3>
                  <span className={`badge`} style={{
                    background: c.status === 'HEALTHY' ? 'rgba(16,185,129,0.1)' : 'rgba(248,113,113,0.1)',
                    color: c.status === 'HEALTHY' ? '#10b981' : '#f87171',
                    border: '1px solid currentColor',
                    padding: '2px 6px', borderRadius: '4px', fontSize: '10px'
                  }}>{c.status}</span>
                </div>
                <div className="metric-sub" style={{marginTop: '12px'}}>
                  Items Processed: <strong style={{color: '#fff'}}>{c.items_processed}</strong><br/>
                  Latency: <strong style={{color: '#fff'}}>{c.latency_ms?.toFixed(0)} ms</strong><br/>
                  Last Success: <strong style={{color: '#fff'}}>{c.last_success}</strong>
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'settings' && (
          <div className="glass-panel">
            <h3 style={{marginBottom: '16px'}}>OS Configuration</h3>
            <p style={{color: '#a1a1aa', fontSize: '14px'}}>Settings are currently configured via .env and CLI for maximum determinism.</p>
          </div>
        )}

      </main>
    </div>
  )
}

export default App

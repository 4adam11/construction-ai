import { useEffect, useState } from 'react'
import { getHealth } from './api'
import Cracks from './features/Cracks'
import DailySite from './features/DailySite'
import Knowledge from './features/Knowledge'
import Planning from './features/Planning'
import Safety from './features/Safety'
import Valuation from './features/Valuation'
import Weather from './features/Weather'

const FEATURES = [
  { id: 'safety', icon: '🦺', name: 'Safety Monitoring', desc: 'PPE compliance and hazard detection from site photos', input: 'Image', Component: Safety },
  { id: 'cracks', icon: '🧱', name: 'Crack Analysis', desc: 'Classify cracks, assess structural risk and plan repairs', input: 'Image', Component: Cracks },
  { id: 'valuation', icon: '🏠', name: 'Property Valuation', desc: 'Market value range, rent and value drivers', input: 'Structured data', Component: Valuation },
  { id: 'planning', icon: '📐', name: 'Project Planning', desc: 'Phased schedule, cost, resources and risks', input: 'Structured data', Component: Planning },
  { id: 'daily', icon: '📋', name: 'Daily Site Assistant', desc: 'Turn rough notes into a structured daily report', input: 'Text + image', Component: DailySite },
  { id: 'weather', icon: '🌦', name: 'Weather Advisory', desc: '7-day work suitability by activity', input: 'Live forecast', Component: Weather },
  { id: 'knowledge', icon: '📘', name: 'Knowledge Assistant', desc: 'Ask about codes, materials and site practice', input: 'Text', Component: Knowledge },
]

const fromHash = () => window.location.hash.slice(1) || 'home'

export default function App() {
  const [page, setPage] = useState(fromHash)
  const [health, setHealth] = useState(null)
  const [navOpen, setNavOpen] = useState(false)

  useEffect(() => {
    const onHash = () => { setPage(fromHash()); setNavOpen(false) }
    window.addEventListener('hashchange', onHash)
    getHealth().then(setHealth).catch(() => setHealth({ status: 'down' }))
    return () => window.removeEventListener('hashchange', onHash)
  }, [])

  const feature = FEATURES.find((f) => f.id === page)

  return (
    <div className="app">
      <aside className={`sidebar ${navOpen ? 'open' : ''}`}>
        <a href="#home" className="brand"><span>🏗️</span> BuildSense <em>AI</em></a>
        <nav>
          <a href="#home" className={page === 'home' ? 'active' : ''}><span>◧</span> Dashboard</a>
          {FEATURES.map((f) => (
            <a key={f.id} href={`#${f.id}`} className={page === f.id ? 'active' : ''}><span>{f.icon}</span> {f.name}</a>
          ))}
        </nav>
        <Status health={health} />
      </aside>

      <main>
        <header className="topbar">
          <button className="menu" onClick={() => setNavOpen(!navOpen)} aria-label="Toggle menu">☰</button>
          <div>
            <h1>{feature ? feature.name : 'Construction Intelligence'}</h1>
            <p className="muted">{feature ? feature.desc : 'Multimodal AI decision support for planning, execution and monitoring.'}</p>
          </div>
        </header>
        <div className="content">
          {feature ? <feature.Component key={feature.id} /> : <Home />}
        </div>
      </main>
    </div>
  )
}

function Status({ health }) {
  if (!health) return <div className="status">Connecting…</div>
  if (health.status !== 'ok') return <div className="status status-down">● Backend offline</div>
  return (
    <div className={`status ${health.mode === 'live' ? 'status-live' : 'status-mock'}`}>
      ● {health.mode === 'live' ? `Live · ${health.model}` : 'Mock mode (no API key)'}
    </div>
  )
}

function Home() {
  return (
    <>
      <div className="feature-grid">
        {FEATURES.map((f) => (
          <a key={f.id} href={`#${f.id}`} className="feature-card">
            <div className="feature-icon">{f.icon}</div>
            <h3>{f.name}</h3>
            <p>{f.desc}</p>
            <span className="badge badge-muted">{f.input}</span>
          </a>
        ))}
      </div>
      <section className="card about">
        <h3 className="card-title">How it works</h3>
        <ol className="flow">
          <li><strong>Input</strong><span>Site photos, notes, or project data</span></li>
          <li><strong>FastAPI</strong><span>Validates input and builds the prompt</span></li>
          <li><strong>Multimodal LLM</strong><span>Analyses text and images together</span></li>
          <li><strong>JSON contract</strong><span>Schema-validated output, every time</span></li>
          <li><strong>Dashboard</strong><span>Actionable, readable insights</span></li>
        </ol>
        <p className="muted small">AI output supports professional judgement and does not replace inspection by a qualified engineer.</p>
      </section>
    </>
  )
}

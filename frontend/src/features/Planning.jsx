import { useState } from 'react'
import { postJSON } from '../api'
import { Badge, Card, Field, List, ResultArea, Stat } from '../components/ui'
import { money, useSubmit } from '../lib'

export default function Planning() {
  const [f, setF] = useState({
    project_name: '', project_type: 'Residential', location: 'Jaipur', plot_area_sqft: 1500, floors: 2,
    budget: 7000000, currency: 'INR', start_date: '', requirements: '',
  })
  const set = (k) => (e) => setF({ ...f, [k]: e.target.type === 'number' ? Number(e.target.value) : e.target.value })
  const [{ loading, error, data, mode }, run] = useSubmit(() =>
    postJSON('/planning/generate', { ...f, start_date: f.start_date || null }))

  return (
    <div className="split">
      <Card title="Project brief">
        <form onSubmit={(e) => { e.preventDefault(); run() }}>
          <Field label="Project name"><input value={f.project_name} onChange={set('project_name')} placeholder="optional" /></Field>
          <div className="grid-2">
            <Field label="Type">
              <select value={f.project_type} onChange={set('project_type')}>
                {['Residential', 'Commercial', 'Industrial', 'Infrastructure'].map((x) => <option key={x}>{x}</option>)}
              </select>
            </Field>
            <Field label="Location"><input value={f.location} onChange={set('location')} required /></Field>
            <Field label="Plot area (sq ft)"><input type="number" min="1" value={f.plot_area_sqft} onChange={set('plot_area_sqft')} required /></Field>
            <Field label="Floors"><input type="number" min="1" value={f.floors} onChange={set('floors')} /></Field>
            <Field label="Budget"><input type="number" min="1" value={f.budget} onChange={set('budget')} required /></Field>
            <Field label="Currency">
              <select value={f.currency} onChange={set('currency')}>{['INR', 'USD', 'EUR', 'GBP', 'AED'].map((x) => <option key={x}>{x}</option>)}</select>
            </Field>
          </div>
          <Field label="Start date"><input type="date" value={f.start_date} onChange={set('start_date')} /></Field>
          <Field label="Requirements"><textarea rows={3} value={f.requirements} onChange={set('requirements')} placeholder="e.g. 3BHK per floor, basement parking, solar roof" /></Field>
          <button className="btn" disabled={loading}>Generate plan</button>
        </form>
      </Card>

      <ResultArea loading={loading} error={error} mode={mode} placeholder="Describe the project to generate a phased schedule, resources and risks.">
        {data && <PlanView plan={data} />}
      </ResultArea>
    </div>
  )
}

function PlanView({ plan }) {
  const total = Math.max(plan.total_duration_weeks, ...plan.phases.map((p) => p.start_week + p.duration_weeks - 1))
  return (
    <>
      <Card><h3 className="plan-title">{plan.project_title}</h3><p>{plan.summary}</p></Card>
      <div className="stats">
        <Stat label="Duration" value={`${plan.total_duration_weeks} weeks`} />
        <Stat label="Estimated cost" value={money(plan.estimated_cost_total, plan.currency)} />
        <Stat label="Budget" value={<Badge value={plan.budget_status} />} />
        <Stat label="Phases" value={plan.phases.length} />
      </div>
      <Card title="Timeline">
        <div className="gantt">
          {plan.phases.map((p, i) => (
            <div className="gantt-row" key={i}>
              <div className="gantt-label">{p.name}</div>
              <div className="gantt-track">
                <div className="gantt-bar" style={{ left: `${((p.start_week - 1) / total) * 100}%`, width: `${(p.duration_weeks / total) * 100}%` }}
                  title={`Week ${p.start_week}–${p.start_week + p.duration_weeks - 1}`}>
                  {p.duration_weeks}w
                </div>
              </div>
            </div>
          ))}
        </div>
      </Card>
      <Card title="Phases">
        {plan.phases.map((p, i) => (
          <details className="row-item" key={i}>
            <summary className="row-head"><strong>{p.name}</strong><span className="muted small">wk {p.start_week} · {p.duration_weeks}w · {money(p.estimated_cost, plan.currency)}</span></summary>
            <List items={p.tasks} />
            <p className="small muted">Milestones: {p.milestones.join('; ')}</p>
          </details>
        ))}
      </Card>
      <div className="grid-2">
        <Card title="Labour">
          <table className="table"><tbody>{plan.labor.map((l, i) => <tr key={i}><td>{l.role}</td><td className="num">{l.count}</td></tr>)}</tbody></table>
        </Card>
        <Card title="Materials">
          <table className="table"><tbody>{plan.materials.map((m, i) => <tr key={i}><td>{m.item}</td><td className="num">{m.quantity.toLocaleString()} {m.unit}</td></tr>)}</tbody></table>
        </Card>
      </div>
      <Card title="Equipment"><List items={plan.equipment} /></Card>
      <Card title="Risks">
        {plan.risks.map((r, i) => (
          <div className="row-item" key={i}>
            <div className="row-head"><strong>{r.risk}</strong><span><Badge value={r.likelihood} /> <Badge value={r.impact} /></span></div>
            <p className="small">→ {r.mitigation}</p>
          </div>
        ))}
      </Card>
    </>
  )
}

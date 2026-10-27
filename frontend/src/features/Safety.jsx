import { useState } from 'react'
import { postForm } from '../api'
import { Badge, Card, Field, ImageDrop, List, ResultArea, Stat, useSubmit } from '../components/ui'

export default function Safety() {
  const [image, setImage] = useState(null)
  const [context, setContext] = useState('')
  const [{ loading, error, data, mode }, run] = useSubmit(() => postForm('/safety/analyze', { image, context }))

  return (
    <div className="split">
      <Card title="Site photo">
        <form onSubmit={(e) => { e.preventDefault(); run() }}>
          <ImageDrop file={image} onChange={setImage} required />
          <Field label="Site context">
            <textarea rows={3} value={context} onChange={(e) => setContext(e.target.value)}
              placeholder="e.g. 3rd floor slab, shuttering in progress" />
          </Field>
          <button className="btn" disabled={!image || loading}>Analyse safety</button>
        </form>
      </Card>

      <ResultArea loading={loading} error={error} mode={mode} placeholder="Upload a site photo to get a PPE and hazard assessment.">
        {data && (
          <>
            <div className="stats">
              <Stat label="Safety score" value={`${data.safety_score}/100`} />
              <Stat label="Overall risk" value={<Badge value={data.overall_risk_level} />} />
              <Stat label="Workers visible" value={data.workers_visible} />
              <Stat label="Hazards" value={data.hazards.length} />
            </div>
            <Card><p>{data.summary}</p></Card>
            <Card title="Immediate actions" className="accent"><List items={data.immediate_actions} /></Card>
            <Card title="Hazards">
              {data.hazards.map((h, i) => (
                <div className="row-item" key={i}>
                  <div className="row-head"><strong>{h.type}</strong><Badge value={h.severity} /></div>
                  <p>{h.description}</p>
                  <p className="muted small">📍 {h.location}</p>
                  <p className="small">→ {h.recommendation}</p>
                </div>
              ))}
            </Card>
            <Card title="PPE compliance">
              <table className="table">
                <tbody>
                  {data.ppe_compliance.map((p, i) => (
                    <tr key={i}><td>{p.item}</td><td><Badge value={p.status} /></td><td className="muted">{p.note}</td></tr>
                  ))}
                </tbody>
              </table>
            </Card>
            <Card title="Violations"><List items={data.violations} /></Card>
          </>
        )}
      </ResultArea>
    </div>
  )
}

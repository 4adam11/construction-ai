import { useState } from 'react'
import { postForm } from '../api'
import { Badge, Card, Field, ImageDrop, List, ResultArea, Stat, label, useSubmit } from '../components/ui'

const ELEMENTS = ['Wall', 'Column', 'Beam', 'Slab', 'Foundation', 'Pavement', 'Bridge deck', 'Other']

export default function Cracks() {
  const [image, setImage] = useState(null)
  const [structure, setStructure] = useState('Wall')
  const [notes, setNotes] = useState('')
  const [{ loading, error, data, mode }, run] = useSubmit(() =>
    postForm('/cracks/analyze', { image, structure_type: structure, notes }))

  return (
    <div className="split">
      <Card title="Crack photo">
        <form onSubmit={(e) => { e.preventDefault(); run() }}>
          <ImageDrop file={image} onChange={setImage} required />
          <Field label="Structural element">
            <select value={structure} onChange={(e) => setStructure(e.target.value)}>
              {ELEMENTS.map((x) => <option key={x}>{x}</option>)}
            </select>
          </Field>
          <Field label="Notes" hint="A coin or tape measure in the photo helps estimate width.">
            <textarea rows={3} value={notes} onChange={(e) => setNotes(e.target.value)}
              placeholder="e.g. appeared after monsoon, building 15 years old" />
          </Field>
          <button className="btn" disabled={!image || loading}>Analyse crack</button>
        </form>
      </Card>

      <ResultArea loading={loading} error={error} mode={mode} placeholder="Upload a close-up of a crack to classify it and get repair guidance.">
        {data && (
          <>
            <div className="stats">
              <Stat label="Crack detected" value={data.crack_detected ? 'Yes' : 'No'} />
              <Stat label="Severity" value={<Badge value={data.severity} />} />
              <Stat label="Width" value={`${data.estimated_width_mm} mm`} sub={`${data.estimated_length_cm} cm long`} />
              <Stat label="Urgency" value={<Badge value={data.urgency} />} />
            </div>
            {data.needs_engineer_inspection && (
              <div className="alert">A structural engineer should inspect this in person.</div>
            )}
            <Card><p>{data.summary}</p></Card>
            <Card title="Classification">
              <table className="table">
                <tbody>
                  <tr><td>Type</td><td>{data.crack_type}</td></tr>
                  <tr><td>Pattern</td><td>{data.pattern}</td></tr>
                  <tr><td>Material</td><td>{data.material}</td></tr>
                  <tr><td>Urgency</td><td>{label(data.urgency)}</td></tr>
                </tbody>
              </table>
            </Card>
            <Card title="Structural risk"><p>{data.structural_risk}</p></Card>
            <div className="grid-2">
              <Card title="Probable causes"><List items={data.probable_causes} /></Card>
              <Card title="Recommended repairs"><List items={data.recommended_repairs} /></Card>
            </div>
          </>
        )}
      </ResultArea>
    </div>
  )
}

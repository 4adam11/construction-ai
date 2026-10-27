import { useState } from 'react'
import { postForm } from '../api'
import { Badge, Card, Field, ImageDrop, List, ResultArea } from '../components/ui'
import { useSubmit } from '../lib'

const SAMPLE = `Columns C4 to C9 cast on 2nd floor. Shuttering for slab ~80% done.
Cement truck didn't come, supplier says tomorrow. Only 30 bags left.
Seepage seen in basement retaining wall near grid B2.
14 labour present, 2 absent. One worker without helmet near the hoist, warned.`

export default function DailySite() {
  const [notes, setNotes] = useState('')
  const [project, setProject] = useState('')
  const [image, setImage] = useState(null)
  const [{ loading, error, data, mode }, run] = useSubmit(() => postForm('/daily/report', { notes, project, image }))

  return (
    <div className="split">
      <Card title="Today's site notes">
        <form onSubmit={(e) => { e.preventDefault(); run() }}>
          <Field label="Project"><input value={project} onChange={(e) => setProject(e.target.value)} placeholder="optional" /></Field>
          <Field label="Raw notes" hint="Write the way you would in a WhatsApp message; the AI will structure it.">
            <textarea rows={8} value={notes} onChange={(e) => setNotes(e.target.value)} placeholder={SAMPLE} required />
          </Field>
          {!notes && <button type="button" className="link" onClick={() => setNotes(SAMPLE)}>Use sample notes</button>}
          <Field label="Site photo"><ImageDrop file={image} onChange={setImage} /></Field>
          <button className="btn" disabled={!notes.trim() || loading}>Create daily report</button>
        </form>
      </Card>

      <ResultArea loading={loading} error={error} mode={mode} placeholder="Paste today's notes to get a structured daily progress report.">
        {data && (
          <>
            <Card>
              <div className="row-head"><strong>Daily report · {data.date}</strong><Badge value={data.progress_status} /></div>
              <p>{data.summary}</p>
            </Card>
            <div className="grid-2">
              <Card title="Work completed"><List items={data.work_completed} /></Card>
              <Card title="Tomorrow's plan"><List items={data.tomorrow_plan} /></Card>
            </div>
            <Card title="Issues">
              {data.issues.length ? data.issues.map((x, i) => (
                <div className="row-item" key={i}>
                  <div className="row-head"><span>{x.issue}</span><Badge value={x.priority} /></div>
                  <p className="muted small">Owner: {x.suggested_owner}</p>
                </div>
              )) : <p className="muted">No issues reported.</p>}
            </Card>
            <div className="grid-2">
              <Card title="Safety reminders" className="accent"><List items={data.safety_reminders} /></Card>
              <Card title="Material requests"><List items={data.material_requests} /></Card>
            </div>
          </>
        )}
      </ResultArea>
    </div>
  )
}

import { useState } from 'react'
import { postJSON } from '../api'
import { Badge, Card, Field, List, ResultArea, useSubmit } from '../components/ui'

const ACTIVITIES = ['Concrete pouring', 'Excavation', 'Roofing', 'Crane lifting', 'Painting (exterior)', 'Brickwork', 'Steel erection']

const icon = (c) => /thunder/i.test(c) ? '⛈' : /snow/i.test(c) ? '❄' : /rain|shower|drizzle/i.test(c) ? '🌧' :
  /fog/i.test(c) ? '🌫' : /overcast|cloud/i.test(c) ? '⛅' : '☀'

export default function Weather() {
  const [location, setLocation] = useState('Mumbai')
  const [activities, setActivities] = useState(['Concrete pouring', 'Roofing'])
  const toggle = (a) => setActivities(activities.includes(a) ? activities.filter((x) => x !== a) : [...activities, a])
  const [{ loading, error, data, mode }, run] = useSubmit(() => postJSON('/weather/advisory', { location, activities }))

  return (
    <div className="split">
      <Card title="Site & activities">
        <form onSubmit={(e) => { e.preventDefault(); run() }}>
          <Field label="Site location" hint="City or town name. Forecast data from Open-Meteo.">
            <input value={location} onChange={(e) => setLocation(e.target.value)} required />
          </Field>
          <Field label="Planned activities">
            <div className="chips">
              {ACTIVITIES.map((a) => (
                <button type="button" key={a} className={`chip ${activities.includes(a) ? 'chip-on' : ''}`} onClick={() => toggle(a)}>{a}</button>
              ))}
            </div>
          </Field>
          <button className="btn" disabled={!activities.length || loading}>Get advisory</button>
        </form>
      </Card>

      <ResultArea loading={loading} error={error} mode={mode} placeholder="Choose a location and activities for a 7-day work advisory.">
        {data && (
          <>
            <Card><strong>{data.location}</strong><p>{data.forecast_summary}</p></Card>
            <div className="days">
              {data.days.map((d) => (
                <div className={`day day-${d.work_suitability}`} key={d.date}>
                  <div className="day-date">{new Date(d.date + 'T00:00').toLocaleDateString(undefined, { weekday: 'short', day: 'numeric' })}</div>
                  <div className="day-icon" title={d.condition}>{icon(d.condition)}</div>
                  <div className="day-temp">{Math.round(d.temp_max_c)}° / {Math.round(d.temp_min_c)}°</div>
                  <div className="small muted">💧 {d.precipitation_mm} mm · 💨 {Math.round(d.wind_kmh)} km/h</div>
                  <Badge value={d.work_suitability} />
                </div>
              ))}
            </div>
            <Card title="Activity advice">
              {data.activity_advice.map((a, i) => (
                <div className="row-item" key={i}>
                  <strong>{a.activity}</strong>
                  <p className="small">{a.recommendation}</p>
                  {a.best_days.length > 0 && <p className="small muted">Best days: {a.best_days.join(', ')}</p>}
                </div>
              ))}
            </Card>
            <Card title="Precautions" className="accent"><List items={data.precautions} /></Card>
          </>
        )}
      </ResultArea>
    </div>
  )
}

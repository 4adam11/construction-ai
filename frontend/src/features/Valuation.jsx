import { useState } from 'react'
import { postJSON } from '../api'
import { Badge, Card, Field, List, ResultArea, Stat } from '../components/ui'
import { money, useSubmit } from '../lib'

const AMENITIES = ['Parking', 'Lift', 'Security', 'Power backup', 'Gym', 'Swimming pool', 'Garden', 'Clubhouse']

export default function Valuation() {
  const [f, setF] = useState({
    location: 'Baner, Pune', property_type: 'Apartment', area_sqft: 1100, bedrooms: 2, bathrooms: 2,
    age_years: 5, condition: 'Good', amenities: ['Parking', 'Lift'], notes: '',
  })
  const set = (k) => (e) => setF({ ...f, [k]: e.target.type === 'number' ? Number(e.target.value) : e.target.value })
  const toggle = (a) => setF({ ...f, amenities: f.amenities.includes(a) ? f.amenities.filter((x) => x !== a) : [...f.amenities, a] })
  const [{ loading, error, data, mode }, run] = useSubmit(() => postJSON('/valuation/estimate', f))

  return (
    <div className="split">
      <Card title="Property details">
        <form onSubmit={(e) => { e.preventDefault(); run() }}>
          <Field label="Location"><input value={f.location} onChange={set('location')} required /></Field>
          <div className="grid-2">
            <Field label="Type">
              <select value={f.property_type} onChange={set('property_type')}>
                {['Apartment', 'Villa', 'Independent house', 'Plot', 'Commercial'].map((x) => <option key={x}>{x}</option>)}
              </select>
            </Field>
            <Field label="Area (sq ft)"><input type="number" min="1" value={f.area_sqft} onChange={set('area_sqft')} required /></Field>
            <Field label="Bedrooms"><input type="number" min="0" value={f.bedrooms} onChange={set('bedrooms')} /></Field>
            <Field label="Bathrooms"><input type="number" min="0" value={f.bathrooms} onChange={set('bathrooms')} /></Field>
            <Field label="Age (years)"><input type="number" min="0" value={f.age_years} onChange={set('age_years')} /></Field>
            <Field label="Condition">
              <select value={f.condition} onChange={set('condition')}>
                {['Excellent', 'Good', 'Fair', 'Poor'].map((x) => <option key={x}>{x}</option>)}
              </select>
            </Field>
          </div>
          <Field label="Amenities">
            <div className="chips">
              {AMENITIES.map((a) => (
                <button type="button" key={a} className={`chip ${f.amenities.includes(a) ? 'chip-on' : ''}`} onClick={() => toggle(a)}>{a}</button>
              ))}
            </div>
          </Field>
          <Field label="Notes"><textarea rows={2} value={f.notes} onChange={set('notes')} placeholder="e.g. corner unit, metro 500 m away" /></Field>
          <button className="btn" disabled={loading}>Estimate value</button>
        </form>
      </Card>

      <ResultArea loading={loading} error={error} mode={mode} placeholder="Fill in the property details to get a market valuation.">
        {data && (
          <>
            <div className="stats">
              <Stat label="Estimated value" value={money(data.estimated_value_mid, data.currency)}
                sub={`${money(data.estimated_value_low, data.currency)} – ${money(data.estimated_value_high, data.currency)}`} />
              <Stat label="Price / sq ft" value={money(data.price_per_sqft, data.currency)} />
              <Stat label="Monthly rent" value={money(data.estimated_monthly_rent, data.currency)} />
              <Stat label="Confidence" value={<Badge value={data.confidence} tone={{ low: 'warn', medium: 'muted', high: 'ok' }[data.confidence]} />} />
            </div>
            <Card title="Value drivers">
              {data.key_value_drivers.map((d, i) => (
                <div className="row-item" key={i}>
                  <div className="row-head"><strong>{d.factor}</strong><Badge value={d.impact} /></div>
                  <p className="small">{d.note}</p>
                </div>
              ))}
            </Card>
            <Card title="Market outlook"><p>{data.market_outlook}</p></Card>
            <div className="grid-2">
              <Card title="Recommendations"><List items={data.recommendations} /></Card>
              <Card title="Assumptions"><List items={data.assumptions} /></Card>
            </div>
          </>
        )}
      </ResultArea>
    </div>
  )
}

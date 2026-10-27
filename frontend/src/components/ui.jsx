import { useEffect, useRef, useState } from 'react'
import { label } from '../lib'

export const Card = ({ title, children, className = '' }) => (
  <section className={`card ${className}`}>
    {title && <h3 className="card-title">{title}</h3>}
    {children}
  </section>
)

const TONES = {
  low: 'ok', good: 'ok', compliant: 'ok', on_track: 'ok', within_budget: 'ok', positive: 'ok', monitor: 'ok', high_conf: 'ok',
  medium: 'warn', caution: 'warn', partial: 'warn', at_risk: 'warn', tight: 'warn', neutral: 'muted',
  repair_within_months: 'warn', repair_within_weeks: 'warn', not_visible: 'muted',
  high: 'bad', critical: 'bad', unsuitable: 'bad', non_compliant: 'bad', delayed: 'bad',
  over_budget: 'bad', negative: 'bad', immediate: 'bad',
}

export const Badge = ({ value, tone }) => (
  <span className={`badge badge-${tone || TONES[value] || 'muted'}`}>{label(value)}</span>
)

export const Field = ({ label: text, children, hint }) => (
  <label className="field">
    <span className="field-label">{text}</span>
    {children}
    {hint && <span className="field-hint">{hint}</span>}
  </label>
)

export const List = ({ items, empty = 'None' }) =>
  items?.length ? (
    <ul className="list">{items.map((x, i) => <li key={i}>{x}</li>)}</ul>
  ) : (
    <p className="muted">{empty}</p>
  )

export const Stat = ({ label: text, value, sub }) => (
  <div className="stat">
    <div className="stat-label">{text}</div>
    <div className="stat-value">{value}</div>
    {sub && <div className="stat-sub">{sub}</div>}
  </div>
)

export function ImageDrop({ file, onChange, required }) {
  const input = useRef(null)
  const [preview, setPreview] = useState(null)
  const [drag, setDrag] = useState(false)

  useEffect(() => {
    if (!file) return setPreview(null)
    const url = URL.createObjectURL(file)
    setPreview(url)
    return () => URL.revokeObjectURL(url)
  }, [file])

  const pick = (f) => f && f.type.startsWith('image/') && onChange(f)

  return (
    <div
      className={`drop ${drag ? 'drop-active' : ''}`}
      onClick={() => input.current.click()}
      onDragOver={(e) => { e.preventDefault(); setDrag(true) }}
      onDragLeave={() => setDrag(false)}
      onDrop={(e) => { e.preventDefault(); setDrag(false); pick(e.dataTransfer.files[0]) }}
    >
      <input ref={input} type="file" accept="image/jpeg,image/png,image/webp,image/gif" hidden
        onChange={(e) => pick(e.target.files[0])} />
      {preview ? (
        <>
          <img src={preview} alt="Selected upload" />
          <button type="button" className="link" onClick={(e) => { e.stopPropagation(); onChange(null) }}>Remove</button>
        </>
      ) : (
        <div className="drop-empty">
          <div className="drop-icon">⬆</div>
          <div>Drop a photo here or <u>browse</u></div>
          <div className="muted small">JPEG, PNG, WebP or GIF · up to 5 MB{required ? '' : ' · optional'}</div>
        </div>
      )}
    </div>
  )
}

export function ResultArea({ loading, error, mode, children, placeholder }) {
  if (loading) return <Card><div className="loading"><span className="spinner" /> Analysing…</div></Card>
  if (error) return <Card><div className="error">⚠ {error}</div></Card>
  if (!children) return <Card><p className="muted placeholder">{placeholder}</p></Card>
  return (
    <div className="results">
      {mode === 'mock' && <div className="mock-banner">Mock mode: sample output. Set ANTHROPIC_API_KEY on the backend for live AI analysis.</div>}
      {children}
    </div>
  )
}

import { useEffect, useRef, useState } from 'react'
import { postJSON } from '../api'
import { Badge, Card } from '../components/ui'

const STARTERS = [
  'What is the minimum curing period for M25 concrete?',
  'How do I check the quality of TMT bars on site?',
  'What cover should I give to a column in a coastal area?',
  'Explain the slump test and acceptable values for RCC work.',
]

export default function Knowledge() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const end = useRef(null)

  useEffect(() => { end.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages, loading])

  const ask = async (q) => {
    const question = q.trim()
    if (!question || loading) return
    const history = messages.map((m) => ({ role: m.role, content: m.role === 'user' ? m.text : m.data?.answer || m.text }))
    setMessages((m) => [...m, { role: 'user', text: question }])
    setInput('')
    setLoading(true)
    try {
      const { data, mode } = await postJSON('/knowledge/ask', { question, history })
      setMessages((m) => [...m, { role: 'assistant', data, mode }])
    } catch (e) {
      setMessages((m) => [...m, { role: 'assistant', text: e.message, error: true }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card className="chat">
      <div className="chat-log">
        {!messages.length && (
          <div className="starters">
            <p className="muted">Ask about codes, materials, methods, quality checks or site practice.</p>
            {STARTERS.map((s) => <button key={s} className="chip" onClick={() => ask(s)}>{s}</button>)}
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`msg msg-${m.role} ${m.error ? 'msg-error' : ''}`}>
            {m.data ? <Answer {...m} onAsk={ask} /> : m.text}
          </div>
        ))}
        {loading && <div className="msg msg-assistant"><span className="spinner" /> Thinking…</div>}
        <div ref={end} />
      </div>
      <form className="chat-input" onSubmit={(e) => { e.preventDefault(); ask(input) }}>
        <input value={input} onChange={(e) => setInput(e.target.value)} placeholder="Ask a construction question…" />
        <button className="btn" disabled={!input.trim() || loading}>Ask</button>
      </form>
    </Card>
  )
}

function Answer({ data, mode, onAsk }) {
  return (
    <>
      {mode === 'mock' && <div className="mock-banner small">Mock mode</div>}
      <p className="pre">{data.answer}</p>
      {data.key_points.length > 0 && (<><h4>Key points</h4><ul className="list">{data.key_points.map((k, i) => <li key={i}>{k}</li>)}</ul></>)}
      {data.related_codes_and_standards.length > 0 && <p className="small muted">📘 {data.related_codes_and_standards.join(' · ')}</p>}
      <div className="row-head small"><span>Confidence</span><Badge value={data.confidence} tone={{ low: 'warn', medium: 'muted', high: 'ok' }[data.confidence]} /></div>
      <div className="chips">{data.follow_up_questions.map((q) => <button key={q} className="chip" onClick={() => onAsk(q)}>{q}</button>)}</div>
    </>
  )
}

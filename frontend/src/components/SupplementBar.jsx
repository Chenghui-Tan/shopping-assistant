import { useState } from 'react'
import { refineRecommendations } from '../api'

function LoadingDots() {
  return <span className="loading-dots"><span /><span /><span /></span>
}

// Render a single preference change in plain English. Skips keys that
// aren't worth showing to the user (e.g. priority, internal flags).
const HUMAN_KEY = {
  use_case:           'Main use',
  use_area:           'Area',
  pain_point:         'Pain point',
  structure_type:     'Organiser type',
  insulated:          'Insulated',
  size_preference:    'Size',
  easy_clean:         'Easy clean',
  easy_install:       'Easy install',
  price_max:          'Max price',
  delivery_days_max:  'Delivery deadline',
  priority:           'Priority',
}

function fmtVal(v) {
  if (v == null || v === '') return '— (not set)'
  if (typeof v === 'boolean') return v ? 'Yes' : 'No'
  if (Array.isArray(v)) return v.length ? v.join(', ') : '— (cleared)'
  if (typeof v === 'number') return v.toString()
  return String(v)
}

function DiffRows({ diff }) {
  const entries = Object.entries(diff || {}).filter(([k]) => HUMAN_KEY[k])
  if (entries.length === 0) return null
  return (
    <div className="diff-card">
      <div className="diff-card-label">What changed</div>
      <ul className="diff-list">
        {entries.map(([key, { from, to }]) => (
          <li key={key}>
            <span className="diff-key">{HUMAN_KEY[key]}</span>
            <span className="diff-from">{fmtVal(from)}</span>
            <span className="diff-arrow">→</span>
            <span className="diff-to">{fmtVal(to)}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}

export default function SupplementBar({ sessionId, supplementLog, onSupplement }) {
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async () => {
    if (!text.trim() || loading) return
    setLoading(true)
    setError(null)
    try {
      const data = await refineRecommendations(sessionId, text.trim())
      onSupplement(data.products, data.ai_response, data.relaxation, data.diff)
      setText('')
      document.getElementById('results-top')?.scrollIntoView({ behavior: 'smooth' })
    } catch (e) {
      setError('Could not refine. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="supplement-bar">
      {supplementLog.length > 0 && (
        <div className="refine-history">
          {supplementLog.slice(0, 3).map((entry, i) => (
            <div
              key={entry.timestamp}
              className="refine-turn"
              style={{
                borderBottom: i < Math.min(supplementLog.length, 3) - 1
                  ? '1px solid var(--border-soft)' : 'none',
              }}
            >
              <div className="refine-ai">
                <span className="refine-ai-label">Assistant: </span>
                {entry.aiResponse}
              </div>
              <DiffRows diff={entry.diff} />
            </div>
          ))}
        </div>
      )}

      <div className="supp-input-row">
        <input
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter') handleSubmit() }}
          placeholder='Refine: "under $20", "faster delivery", "actually for outdoor use"'
          disabled={loading}
          className="text-input"
        />
        <button
          className="btn-primary"
          onClick={handleSubmit}
          disabled={!text.trim() || loading}
          style={{ padding: '11px 18px', whiteSpace: 'nowrap' }}
        >
          {loading ? <LoadingDots /> : 'Update →'}
        </button>
      </div>

      {error && (
        <p className="error-msg" style={{ marginTop: 8 }}>{error}</p>
      )}
    </div>
  )
}

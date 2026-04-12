import { useState } from 'react'
import { refineRecommendations } from '../api'

function LoadingDots() {
  return <span className="loading-dots"><span /><span /><span /></span>
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
      onSupplement(data.products, data.ai_response)
      setText('')
      document.getElementById('results-top')?.scrollIntoView({ behavior: 'smooth' })
    } catch (e) {
      setError('Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="supplement-bar">
      {supplementLog.length > 0 && (
        <div style={{ marginBottom: 10 }}>
          {supplementLog.slice(0, 3).map((entry, i) => (
            <div key={entry.timestamp} style={{
              fontSize: 13, color: 'var(--text-secondary)',
              padding: '6px 0',
              borderBottom: i < Math.min(supplementLog.length, 3) - 1
                ? '1px solid rgba(108,99,255,0.08)' : 'none',
            }}>
              <span style={{ color: 'var(--chip-text)', fontWeight: 600 }}>Assistant: </span>
              {entry.aiResponse}
            </div>
          ))}
        </div>
      )}

      <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
        <input
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter') handleSubmit() }}
          placeholder='Refine: "under $20", "faster delivery", "actually for outdoor use"'
          disabled={loading}
          className="text-input"
          style={{ flex: 1 }}
        />
        <button
          className="btn-primary"
          onClick={handleSubmit}
          disabled={!text.trim() || loading}
          style={{ padding: '10px 20px', whiteSpace: 'nowrap' }}
        >
          {loading ? <LoadingDots /> : 'Update →'}
        </button>
      </div>

      {error && (
        <p style={{ color: '#ef4444', marginTop: 8, fontSize: 13 }}>{error}</p>
      )}
    </div>
  )
}

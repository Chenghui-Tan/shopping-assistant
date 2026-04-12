import { useState } from 'react'
import { startSession } from '../api'

function LoadingDots() {
  return (
    <span className="loading-dots">
      <span /><span /><span />
    </span>
  )
}

export default function Stage1({ onComplete }) {
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async () => {
    if (!text.trim() || loading) return
    setLoading(true)
    setError(null)
    try {
      const data = await startSession(text.trim())
      onComplete(data)
    } catch (e) {
      setError('Something went wrong. Please try again.')
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) handleSubmit()
  }

  return (
    <div style={{ textAlign: 'center', paddingTop: 32 }}>
      <div className="hero-icon">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none"
          stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <path d="M6 2L3 6v14a2 2 0 002 2h14a2 2 0 002-2V6l-3-4z" />
          <line x1="3" y1="6" x2="21" y2="6" />
          <path d="M16 10a4 4 0 01-8 0" />
        </svg>
      </div>

      <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 12 }}>
        AI Shopping Assistant
      </h1>
      <p style={{ color: 'var(--text-secondary)', fontSize: 16, marginBottom: 32, lineHeight: 1.6 }}>
        Tell me what you need, what matters to you,<br />
        or what problem you&apos;re trying to solve
      </p>

      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="I need a water bottle for the gym..."
        rows={4}
        style={{ marginBottom: 16 }}
        autoFocus
      />

      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
        <button
          className="btn-primary"
          onClick={handleSubmit}
          disabled={!text.trim() || loading}
        >
          {loading ? <LoadingDots /> : 'Find my matches →'}
        </button>
        <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
          ⌘ + Enter to submit
        </span>
      </div>

      {error && (
        <p style={{ color: '#ef4444', marginTop: 16, fontSize: 14 }}>{error}</p>
      )}
    </div>
  )
}

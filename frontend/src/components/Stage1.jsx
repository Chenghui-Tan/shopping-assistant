import { useState } from 'react'
import { startSession } from '../api'

// Three sample prompts, one per supported category, framed as the user's
// real situation rather than a category name. The Stage 1 page itself stays
// category-agnostic ('Shopping Assistant', not 'Kitchen Assistant') — these
// samples are the only place a category gets implied, and only when clicked.
const SAMPLE_PROMPTS = [
  "I cook almost every day, but my phone screen is too small to follow recipes while cooking.",
  "I keep losing track of how much water I drink, and my current bottle leaks in my bag.",
  "My kitchen drawers are cluttered, and I can never find the tools I need.",
]
const SAMPLE_LABELS = ['Cooking', 'Hydrating', 'Organizing']

// Frontend fallback only — backend now returns a contextual reply via
// `data.reply` that references the user's inferred use_case. This map is
// the safety net for the rare case where the backend fails to populate it.
const FALLBACK_REPLIES = {
  smart_display: "That sounds frustrating. Would you like a larger screen that can guide you hands-free while cooking and help manage your meals more easily?",
  water_bottle: "I hear you — that's a real pain. Want a lightweight, leak-proof bottle that keeps drinks cold and is easy to track on the go?",
  kitchen_organizer: "Mornings should be calm, not stressful. Let's find organizers that make every utensil and ingredient easy to grab.",
  default: "That sounds frustrating. Let's figure out what would actually make this easier for you — together.",
}

function LoadingDots() {
  return <span className="loading-dots"><span /><span /><span /></span>
}

export default function Stage1({ onComplete }) {
  const [text, setText] = useState('')
  const [submittedText, setSubmittedText] = useState(null)
  const [reply, setReply] = useState(null)
  const [pendingData, setPendingData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (override) => {
    const value = (override ?? text).trim()
    if (!value || loading) return
    setLoading(true)
    setError(null)
    try {
      const data = await startSession(value)
      setSubmittedText(value)
      setPendingData(data)
      // Prefer the backend's contextual reply; fall back per-category only
      // if the backend didn't supply one (older deploys).
      const cat = data.category || 'default'
      setReply(data.reply || FALLBACK_REPLIES[cat] || FALLBACK_REPLIES.default)
    } catch {
      setError('Could not start the conversation. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleContinue = () => {
    if (!pendingData) return
    onComplete(pendingData, { user: submittedText, assistant: reply })
  }

  if (submittedText && reply) {
    return (
      <div className="chat-thread">
        <div className="chat-bubble user-bubble">{submittedText}</div>
        <div className="chat-bubble assistant-bubble">
          <p>{reply}</p>
          <p className="chat-hint">💡 <em>Understanding your context, not just keywords</em></p>
        </div>
        <div className="chat-cta">
          <button className="btn-primary" onClick={handleContinue}>
            Continue conversation →
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="chat-thread">
      <div className="chat-bubble assistant-bubble">
        <p>Tell me what you're trying to solve: a frustration, a goal, or something you're unsure how to shop for.</p>
        <p className="chat-hint">💡 <em>More context helps me recommend better options.</em></p>
      </div>

      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) handleSubmit()
        }}
        placeholder="e.g. I cook almost every day, but my phone screen is too small to follow recipes..."
        rows={3}
        autoFocus
      />

      <div className="chat-cta">
        <button
          className="btn-primary"
          onClick={() => handleSubmit()}
          disabled={!text.trim() || loading}
        >
          {loading ? <LoadingDots /> : 'Start the conversation →'}
        </button>
      </div>

      <div className="sample-row">
        <span className="sample-label">Or try a sample:</span>
        {SAMPLE_PROMPTS.map((prompt, i) => (
          <button
            key={i}
            className="sample-chip"
            onClick={() => { setText(prompt); handleSubmit(prompt) }}
            disabled={loading}
          >
            {SAMPLE_LABELS[i]}
          </button>
        ))}
      </div>

      {error && <p className="error-msg">{error}</p>}
    </div>
  )
}

import { useState, useEffect, useRef } from 'react'
import { answerQuestion, getRecommendations } from '../api'

const CATEGORY_LABELS = [
  { label: 'Smart Display', value: 'smart_display', tag: 'Smart Display', icon: '🖥️' },
  { label: 'Water Bottle',  value: 'water_bottle',  tag: 'Water Bottle',  icon: '🥤' },
  { label: 'Kitchen Organizer', value: 'kitchen_organizer', tag: 'Kitchen Organizer', icon: '🗂️' },
]

// Question metadata used for the multi-question form layout in Scene 2.
// Each question shows its own row of chips; the user picks one before
// submitting all answers at once.
const QUESTION_LAYOUT = {
  smart_display: [
    {
      key: 'use_case',
      icon: '👨‍👩‍👧',
      text: "What's the main thing you'll use it for?",
      chips: ['Cooking', 'Family calendar', 'Entertainment', 'Smart home control'],
    },
    {
      key: 'price_max',
      icon: '💲',
      text: "What's your budget?",
      chips: ['Under $50', 'Under $100', 'Under $150', 'No limit'],
    },
    {
      key: 'delivery_days_max',
      icon: '🚚',
      text: 'How soon do you need it?',
      chips: ['ASAP (1–2 days)', 'This week', 'No rush'],
    },
  ],
  water_bottle: [
    {
      key: 'use_case',
      icon: '🏃',
      text: 'What will you mainly use it for?',
      chips: ['Gym', 'Daily carry', 'Outdoor', 'Kids'],
    },
    {
      key: 'insulated',
      icon: '🧊',
      text: 'Do you need it to keep drinks hot or cold?',
      chips: ['Yes, insulated', "No, doesn't matter"],
    },
    {
      key: 'size_preference',
      icon: '📏',
      text: 'Any size preference?',
      chips: ['Lightweight', 'Large capacity', 'No preference'],
    },
  ],
  kitchen_organizer: [
    {
      key: 'use_area',
      icon: '🏠',
      text: "Where's the main problem area in your kitchen?",
      chips: ['Cabinets', 'Countertop', 'Under the sink'],
    },
    {
      key: 'pain_point',
      icon: '😣',
      text: "What's your biggest frustration?",
      chips: ['Not enough space', 'Hard to find things'],
    },
    {
      key: 'structure_type',
      icon: '🧱',
      text: 'Any preference on the type of organizer?',
      chips: ['Stackable', 'Drawer', 'Bin', 'Expandable', 'Lazy Susan'],
    },
  ],
}

function LoadingDots() {
  return <span className="loading-dots"><span /><span /><span /></span>
}

export default function Stage2({ sessionId, startData, openingTurn, onComplete }) {
  const [category, setCategory] = useState(startData?.category || null)
  const [pickingCategory, setPickingCategory] = useState(!startData?.category)
  const [answers, setAnswers] = useState({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const submitted = useRef(false)

  // If the LLM already pre-filled the category, respect it.
  useEffect(() => {
    if (startData?.category && !category) setCategory(startData.category)
    if (startData?.category) setPickingCategory(false)
  }, [startData])

  const pickCategory = async (cat) => {
    setLoading(true)
    setError(null)
    try {
      const labelMap = { smart_display: 'Smart Display', water_bottle: 'Water Bottle', kitchen_organizer: 'Kitchen Organizer' }
      await answerQuestion(sessionId, 'category', labelMap[cat], true)
      setCategory(cat)
      setPickingCategory(false)
    } catch (e) {
      setError('Could not select category.')
    } finally {
      setLoading(false)
    }
  }

  // Single-select for everything except smart_display 'use_case' (the demo
  // shows that question allowing multiple highlighted chips). For the
  // structured backend, only the first picked chip is sent — the rest are
  // captured as additional preferences for explanation / display only.
  const handleChip = (qKey, chip, allowMulti = false) => {
    if (!allowMulti) {
      setAnswers((prev) => ({ ...prev, [qKey]: chip }))
      return
    }
    setAnswers((prev) => {
      const cur = prev[qKey]
      if (Array.isArray(cur)) {
        return {
          ...prev,
          [qKey]: cur.includes(chip) ? cur.filter((c) => c !== chip) : [...cur, chip],
        }
      }
      return { ...prev, [qKey]: cur === chip ? [] : [chip] }
    })
  }

  const isSelected = (qKey, chip) => {
    const v = answers[qKey]
    return Array.isArray(v) ? v.includes(chip) : v === chip
  }

  const handleSubmitAll = async () => {
    if (submitted.current || loading) return
    const layout = QUESTION_LAYOUT[category] || []
    const missing = layout.filter((q) => !answers[q.key])
    if (missing.length === layout.length) {
      setError('Pick at least one option to continue.')
      return
    }
    submitted.current = true
    setLoading(true)
    setError(null)
    try {
      for (const q of layout) {
        const v = answers[q.key]
        if (!v) continue
        // For multi-select, send the first chip as the structured value;
        // the rest are still visible to the user as their stated preferences.
        const send = Array.isArray(v) ? v[0] : v
        if (send) await answerQuestion(sessionId, q.key, send, true)
      }
      const data = await getRecommendations(sessionId)
      onComplete(data.products)
    } catch (e) {
      submitted.current = false
      setError('Could not load recommendations. Please try again.')
      setLoading(false)
    }
  }

  if (pickingCategory) {
    return (
      <div className="needs-form">
        {openingTurn?.user && (
          <div className="recap-card">
            <div className="recap-label">You said</div>
            <div className="recap-text">"{openingTurn.user}"</div>
          </div>
        )}
        <h3 className="needs-q">First, what category fits best?</h3>
        <div className="cat-grid">
          {CATEGORY_LABELS.map((c) => (
            <button
              key={c.value}
              className="cat-card"
              onClick={() => pickCategory(c.value)}
              disabled={loading}
            >
              <span className="cat-icon">{c.icon}</span>
              <span>{c.tag}</span>
            </button>
          ))}
        </div>
        {loading && <div style={{ marginTop: 16 }}><LoadingDots /></div>}
        {error && <p className="error-msg">{error}</p>}
      </div>
    )
  }

  const layout = QUESTION_LAYOUT[category] || []

  return (
    <div className="needs-form">
      {openingTurn?.user && (
        <div className="recap-card">
          <div className="recap-label">You said</div>
          <div className="recap-text">"{openingTurn.user}"</div>
        </div>
      )}

      {layout.map((q) => {
        // Multi-select for the smart_display use_case question — the demo
        // shows multiple feature chips highlighted at once.
        const multi = category === 'smart_display' && q.key === 'use_case'
        return (
          <div key={q.key} className="needs-question">
            <div className="needs-q-text">
              <span className="needs-q-icon">{q.icon}</span>
              <span>{q.text}{multi && <span className="multi-hint"> · pick one or more</span>}</span>
            </div>
            <div className="needs-chip-row">
              {q.chips.map((chip) => (
                <button
                  key={chip}
                  className={'needs-chip ' + (isSelected(q.key, chip) ? 'needs-chip-selected' : '')}
                  onClick={() => handleChip(q.key, chip, multi)}
                  disabled={loading}
                >
                  {chip}
                </button>
              ))}
            </div>
          </div>
        )
      })}

      <div className="chat-cta">
        <button
          className="btn-primary"
          onClick={handleSubmitAll}
          disabled={loading}
        >
          {loading ? <LoadingDots /> : 'See recommendations →'}
        </button>
      </div>

      {error && <p className="error-msg">{error}</p>}
    </div>
  )
}

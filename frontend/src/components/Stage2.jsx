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
      hint: 'pick one or more',
      chips: ['Cooking', 'Family calendar', 'Entertainment', 'Smart home control'],
    },
    {
      key: 'voice_ecosystem',
      icon: '🎙️',
      text: 'Do you already use a voice ecosystem?',
      chips: ['Alexa', 'Google', 'Apple', "I'm new to this"],
    },
    {
      key: 'placement',
      icon: '🏠',
      text: 'Where will it live?',
      chips: ['Kitchen counter', 'Wall mount', 'Living room', 'Bedroom'],
    },
    {
      key: 'screen_size_priority',
      icon: '📐',
      text: 'How big does the screen need to be?',
      chips: ['Compact (under 8")', 'Mid (8–11")', 'Large (15"+)', "Doesn't matter"],
    },
    {
      key: 'privacy_camera',
      icon: '🛡️',
      text: 'Any privacy preference about the camera?',
      chips: ['Camera is fine', 'Prefer no camera', "Doesn't matter"],
    },
    {
      key: 'price_max',
      icon: '💲',
      text: "What's your budget?",
      chips: ['Under $100', 'Under $150', 'Under $250', 'No limit'],
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

// Reverse the backend's CHIP_TO_VALUE map for the chip groups we know about.
// Used to pre-select chips when the LLM pre-filled preferences from the
// raw text — instead of asking the user to repeat what Claude already heard.
const VALUE_TO_CHIP = {
  use_case: {
    cooking: 'Cooking', family: 'Family calendar',
    entertainment: 'Entertainment', smart_home: 'Smart home control',
    gym: 'Gym', daily: 'Daily carry', outdoor: 'Outdoor', kids: 'Kids',
  },
  use_area:    { cabinet: 'Cabinets', countertop: 'Countertop', under_sink: 'Under the sink' },
  pain_point:  { not_enough_space: 'Not enough space', hard_to_find_things: 'Hard to find things' },
  structure_type: {
    stackable: 'Stackable', drawer: 'Drawer', bin: 'Bin',
    expandable: 'Expandable', lazy_susan: 'Lazy Susan',
  },
  insulated:        { true: 'Yes, insulated', false: "No, doesn't matter" },
  size_preference:  { lightweight: 'Lightweight', large: 'Large capacity', '': 'No preference' },
  price_max:        { 50: 'Under $50', 100: 'Under $100', 150: 'Under $150', 250: 'Under $250', null: 'No limit' },
  delivery_days_max: { 2: 'ASAP (1–2 days)', 7: 'This week', null: 'No rush' },
  voice_ecosystem:  { alexa: 'Alexa', google: 'Google', apple: 'Apple', none: "I'm new to this" },
  placement:        { kitchen: 'Kitchen counter', wall: 'Wall mount', living_room: 'Living room', bedroom: 'Bedroom' },
  screen_size_priority: { compact: 'Compact (under 8")', mid: 'Mid (8–11")', large: 'Large (15"+)', any: "Doesn't matter" },
  privacy_camera:   { ok: 'Camera is fine', no_camera: 'Prefer no camera', any: "Doesn't matter" },
}

function chipFromValue(qKey, v) {
  if (v === undefined || v === null) return undefined
  // Booleans and numbers need string-keyed lookup against VALUE_TO_CHIP.
  const map = VALUE_TO_CHIP[qKey]
  if (!map) return undefined
  if (Array.isArray(v)) return v.map((x) => map[x]).filter(Boolean)
  return map[v]
}

export default function Stage2({ sessionId, startData, openingTurn, onComplete }) {
  const [category, setCategory] = useState(startData?.category || null)
  const [pickingCategory, setPickingCategory] = useState(!startData?.category)

  // Pre-fill chip selections from any preferences the LLM already inferred
  // in /session/start. Matches structured values back to chip labels via
  // VALUE_TO_CHIP. Anything we can't reverse-map is silently dropped — the
  // user just answers that question fresh.
  const initialAnswers = (() => {
    const acc = {}
    const prefs = startData?.preferences || {}
    for (const [k, v] of Object.entries(prefs)) {
      const chip = chipFromValue(k, v)
      if (chip !== undefined && chip !== null && (Array.isArray(chip) ? chip.length > 0 : true)) {
        acc[k] = chip
      }
    }
    return acc
  })()
  const [answers, setAnswers] = useState(initialAnswers)
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
        // Skip when nothing picked, or an empty multi-select array.
        if (v == null || v === '' || (Array.isArray(v) && v.length === 0)) continue
        // Multi-select sends the full array; backend resolves each chip.
        await answerQuestion(sessionId, q.key, v, true)
      }
      const data = await getRecommendations(sessionId)
      onComplete(data.products, data.relaxation, data.picks, data.raw_input)
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
        // Multi-select is opt-in per-question via `hint: 'pick one or more'`.
        const multi = q.hint === 'pick one or more'
        return (
          <div key={q.key} className="needs-question">
            <div className="needs-q-text">
              <span className="needs-q-icon">{q.icon}</span>
              <span>
                {q.text}
                {q.hint && <span className="multi-hint"> · {q.hint}</span>}
              </span>
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

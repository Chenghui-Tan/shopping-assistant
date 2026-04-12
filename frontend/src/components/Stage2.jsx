import { useState, useEffect } from 'react'
import { answerQuestion, getRecommendations } from '../api'

const TOTAL_QUESTIONS = { kitchen_organizer: 3, water_bottle: 3, smart_display: 3 }

function LoadingDots() {
  return <span className="loading-dots"><span /><span /><span /></span>
}

export default function Stage2({ sessionId, startData, onComplete }) {
  const [currentQuestion, setCurrentQuestion] = useState(startData.next_question || null)
  const [showCategoryChips, setShowCategoryChips] = useState(!!startData.chips)
  const [stepIndex, setStepIndex] = useState(0)
  const [totalSteps, setTotalSteps] = useState(
    startData.category ? (TOTAL_QUESTIONS[startData.category] || 3) : 3
  )
  const [freeText, setFreeText] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!showCategoryChips && !currentQuestion) {
      fetchRecommendations()
    }
  }, [])

  const fetchRecommendations = async () => {
    setLoading(true)
    try {
      const data = await getRecommendations(sessionId)
      onComplete(data.products)
    } catch (e) {
      setError('Could not load recommendations. Please try again.')
      setLoading(false)
    }
  }

  const handleChipAnswer = async (questionKey, chipLabel, isCategory = false) => {
    setLoading(true)
    setError(null)
    try {
      const data = await answerQuestion(sessionId, questionKey, chipLabel, true)
      if (isCategory) {
        setShowCategoryChips(false)
        const cat = chipLabel.toLowerCase().replace(/ /g, '_')
        setTotalSteps(TOTAL_QUESTIONS[cat] || 3)
      }
      if (data.next_question) {
        setCurrentQuestion(data.next_question)
        setStepIndex((i) => i + 1)
      } else {
        await fetchRecommendations()
      }
    } catch (e) {
      setError('Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleFreeTextSubmit = async () => {
    if (!freeText.trim() || loading) return
    setLoading(true)
    setError(null)
    try {
      const data = await answerQuestion(sessionId, currentQuestion.key, freeText.trim(), false)
      setFreeText('')
      if (data.next_question) {
        setCurrentQuestion(data.next_question)
        setStepIndex((i) => i + 1)
      } else {
        await fetchRecommendations()
      }
    } catch (e) {
      setError('Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleSkip = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await answerQuestion(sessionId, currentQuestion.key, '', true)
      if (data.next_question) {
        setCurrentQuestion(data.next_question)
        setStepIndex((i) => i + 1)
      } else {
        await fetchRecommendations()
      }
    } catch (e) {
      setError('Something went wrong.')
    } finally {
      setLoading(false)
    }
  }

  const progressPct = totalSteps > 0 ? Math.round((stepIndex / totalSteps) * 100) : 0

  if (loading && !currentQuestion && !showCategoryChips) {
    return (
      <div style={{ textAlign: 'center', paddingTop: 64 }}>
        <p style={{ color: 'var(--text-secondary)', marginBottom: 16 }}>Finding your matches...</p>
        <LoadingDots />
      </div>
    )
  }

  return (
    <div style={{ maxWidth: 480, margin: '0 auto', paddingTop: 16 }}>
      {!showCategoryChips && (
        <div style={{ marginBottom: 32 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
            <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
              Step {stepIndex + 1} of {totalSteps}
            </span>
          </div>
          <div className="progress-bar">
            <div className="progress-bar-fill" style={{ width: `${progressPct}%` }} />
          </div>
        </div>
      )}

      {showCategoryChips && (
        <div style={{ textAlign: 'center' }}>
          <h2 style={{ fontSize: 22, fontWeight: 700, marginBottom: 8 }}>
            What are you shopping for?
          </h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: 28, fontSize: 15 }}>
            Help me point you in the right direction
          </p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, justifyContent: 'center' }}>
            {['Water Bottle', 'Smart Display', 'Kitchen Organizer'].map((label) => (
              <button
                key={label}
                className="chip"
                onClick={() => handleChipAnswer('category', label, true)}
                disabled={loading}
              >
                {label}
              </button>
            ))}
          </div>
          {loading && <div style={{ marginTop: 20 }}><LoadingDots /></div>}
        </div>
      )}

      {!showCategoryChips && currentQuestion && (
        <div>
          <h2 style={{ fontSize: 22, fontWeight: 700, marginBottom: 8 }}>
            {currentQuestion.text}
          </h2>

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10, marginTop: 24, marginBottom: 24 }}>
            {currentQuestion.chips.map((chip) => (
              <button
                key={chip}
                className="chip"
                onClick={() => handleChipAnswer(currentQuestion.key, chip)}
                disabled={loading}
              >
                {chip}
              </button>
            ))}
          </div>

          <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 10 }}>
            Or type your answer:
          </p>
          <div style={{ display: 'flex', gap: 10 }}>
            <textarea
              value={freeText}
              onChange={(e) => setFreeText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleFreeTextSubmit() }
              }}
              placeholder="Type here..."
              rows={2}
              disabled={loading}
              style={{ flex: 1 }}
            />
            <button
              className="btn-primary"
              onClick={handleFreeTextSubmit}
              disabled={!freeText.trim() || loading}
              style={{ alignSelf: 'flex-end', padding: '10px 16px' }}
            >
              {loading ? <LoadingDots /> : '→'}
            </button>
          </div>

          <div style={{ marginTop: 16, textAlign: 'right' }}>
            <button className="btn-ghost" onClick={handleSkip} disabled={loading}>
              Skip →
            </button>
          </div>
        </div>
      )}

      {error && (
        <p style={{ color: '#ef4444', marginTop: 16, fontSize: 14 }}>{error}</p>
      )}
    </div>
  )
}

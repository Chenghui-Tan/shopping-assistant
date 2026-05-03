const BASE = 'http://localhost:8000'

async function post(path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

export const startSession = (text) => post('/session/start', { text })

export const answerQuestion = (sessionId, questionKey, answer, isChip = false) =>
  post('/session/answer', {
    session_id: sessionId,
    question_key: questionKey,
    answer,
    is_chip: isChip,
  })

export const getRecommendations = (sessionId) =>
  post('/session/recommend', { session_id: sessionId })

export const refineRecommendations = (sessionId, text) =>
  post('/session/refine', { session_id: sessionId, text })

export const getLifecycle = async (sessionId) => {
  const res = await fetch(`${BASE}/session/${sessionId}/lifecycle`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export const saveProduct = (sessionId, product) =>
  post('/session/save', { session_id: sessionId, product })

export const getSaved = async (sessionId) => {
  const res = await fetch(`${BASE}/session/${sessionId}/saved`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

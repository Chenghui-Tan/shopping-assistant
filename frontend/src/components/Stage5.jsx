import { useEffect, useState } from 'react'
import { getLifecycle } from '../api'

const FALLBACK = {
  header: 'Kitchen Display',
  schedule: [
    { time: '9:00 AM', label: 'Soccer practice — Emma' },
    { time: '2:00 PM', label: 'Grocery delivery' },
    { time: '6:00 PM', label: 'Family dinner' },
  ],
  menu: [
    { meal: 'Breakfast', label: 'Greek yogurt & granola' },
    { meal: 'Lunch',     label: 'Chicken salad wrap' },
    { meal: 'Dinner',    label: 'Teriyaki salmon bowl' },
  ],
  video: { title: 'Cooking show: Quick weeknight meals', subtitle: 'Watch while preparing dinner' },
  cards: [
    { icon: '🍴', title: 'Meal Planning',
      body: 'Track nutrition, plan meals ahead, and generate shopping lists automatically.' },
    { icon: '👨‍👩‍👧', title: 'Family Hub',
      body: 'Sync schedules, leave messages, and coordinate family activities in one place.' },
    { icon: '🎬', title: 'Entertainment',
      body: 'Watch cooking shows, follow video recipes, or enjoy music during meal prep.' },
  ],
}

export default function Stage5({ sessionId }) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!sessionId) { setData(FALLBACK); return }
    getLifecycle(sessionId)
      .then(setData)
      .catch(() => { setData(FALLBACK); setError('Using sample lifecycle data') })
  }, [sessionId])

  const d = data || FALLBACK

  return (
    <div className="lifecycle-page">
      <div className="lc-mini-card">
        <div className="lc-mini-head">
          <span className="lc-mini-icon">📺</span>
          <span className="lc-mini-title">{d.header}</span>
          <span className="lc-mini-time">{nowLabel()}</span>
        </div>

        <div className="lc-row">
          <div className="lc-pane">
            <div className="lc-pane-title">📅 Today's Schedule</div>
            <ul className="lc-pane-list">
              {d.schedule.map((s, i) => (
                <li key={i}>
                  <span className="lc-pane-key">{s.time}</span>
                  <span className="lc-pane-val">{s.label}</span>
                </li>
              ))}
            </ul>
          </div>
          <div className="lc-pane">
            <div className="lc-pane-title">🍴 Today's Menu</div>
            <ul className="lc-pane-list">
              {d.menu.map((s, i) => (
                <li key={i}>
                  <span className="lc-pane-key">{s.meal}</span>
                  <span className="lc-pane-val">{s.label}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="lc-video">
          <span className="lc-video-icon">▶</span>
          <div>
            <div className="lc-video-title">{d.video.title}</div>
            <div className="lc-video-subtitle">{d.video.subtitle}</div>
          </div>
          <button className="lc-play-btn">Play</button>
        </div>
      </div>

      <div className="lc-cards">
        {d.cards.map((c, i) => (
          <div key={i} className="lc-card">
            <div className="lc-card-icon">{c.icon}</div>
            <div className="lc-card-title">{c.title}</div>
            <div className="lc-card-body">{c.body}</div>
          </div>
        ))}
      </div>

      <div className="lc-banner">
        This assistant continues to support you long after purchase —
        reinforcing long-term value and lifecycle thinking, not just a transaction.
      </div>

      {error && (
        <div className="lc-debug" aria-hidden="true">{error}</div>
      )}
    </div>
  )
}

function nowLabel() {
  const d = new Date()
  let h = d.getHours()
  const m = d.getMinutes().toString().padStart(2, '0')
  const ampm = h >= 12 ? 'PM' : 'AM'
  h = h % 12 || 12
  return `${h}:${m} ${ampm}`
}

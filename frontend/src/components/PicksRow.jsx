/**
 * PicksRow — three differentiated picks with badges (Best Fit / Budget /
 * Stretch). Each card carries a grounded `pick_reason` from the backend.
 * Clicking a card opens its full Stage 4 explanation.
 */
function StarRow({ rating }) {
  if (!rating) return null
  const half = Math.abs(rating - Math.floor(rating) - 0.5) < 0.25
  const filled = half ? Math.floor(rating) : Math.round(rating)
  const stars = '★'.repeat(filled) + (half ? '½' : '') + '☆'.repeat(5 - filled - (half ? 1 : 0))
  return (
    <span className="star-row">
      <span className="stars">{stars}</span>
      <span className="rating-num">{rating.toFixed(1)}</span>
    </span>
  )
}

function PickFacts({ p }) {
  const facts = []
  if (p.screen_inches) facts.push(`${p.screen_inches}" screen`)
  if (p.capacity_oz)   facts.push(`${p.capacity_oz}oz`)
  if (p.ecosystems && p.ecosystems.length)
    facts.push(p.ecosystems.map((e) => e[0].toUpperCase() + e.slice(1)).join(' · '))
  if (p.has_camera === false) facts.push('No camera')
  if (p.has_camera === true)  facts.push('Has camera')
  if (p.arrival_time_days != null)
    facts.push(`Delivery ${p.arrival_time_days}d`)
  return (
    <ul className="pick-facts">
      {facts.slice(0, 4).map((f, i) => <li key={i}>{f}</li>)}
    </ul>
  )
}

const BADGE_CLASS = {
  'Best Fit':              'pick-badge-best',
  'Budget Pick':           'pick-badge-budget',
  'Large Screen Pick':     'pick-badge-stretch',
  'Large Capacity Pick':   'pick-badge-stretch',
  'Best Visibility Pick':  'pick-badge-stretch',
}

export default function PicksRow({ picks, onSelectProduct, isSaved, onToggleSave }) {
  if (!picks || picks.length === 0) return null

  return (
    <div className="picks-row">
      {picks.map((p, i) => (
        <div
          key={p.product_url || i}
          className={'pick-card ' + (i === 0 ? 'pick-card-primary' : '')}
          onClick={() => onSelectProduct(p)}
          role="button"
          tabIndex={0}
        >
          <div className={'pick-badge ' + (BADGE_CLASS[p.pick_label] || 'pick-badge-default')}>
            {p.pick_label}
          </div>

          {onToggleSave && (
            <button
              className={'pick-heart ' + (isSaved?.(p) ? 'pick-heart-on' : '')}
              onClick={(e) => { e.stopPropagation(); onToggleSave(p) }}
              title={isSaved?.(p) ? 'Remove from saved' : 'Save for later'}
              aria-label="save toggle"
            >
              {isSaved?.(p) ? '❤' : '♡'}
            </button>
          )}

          <div className="pick-image">
            {p.image_url ? (
              <img
                src={p.image_url}
                alt={p.title}
                onError={(e) => {
                  const ph = e.target.parentNode.querySelector('.pick-image-fallback')
                  if (ph) ph.style.display = 'flex'
                  e.target.style.display = 'none'
                }}
              />
            ) : null}
            <div
              className="pick-image-fallback"
              style={{ display: p.image_url ? 'none' : 'flex' }}
            >
              {p.category === 'smart_display' ? '🖥️' :
               p.category === 'water_bottle' ? '🥤' : '🗂️'}
            </div>
          </div>

          <div className="pick-title" title={p.title}>{p.title}</div>
          <StarRow rating={p.rating} />

          <div className="pick-reason">
            <span className="pick-reason-icon">→</span>
            <span>{p.pick_reason}</span>
          </div>

          <PickFacts p={p} />

          <div className="pick-footer">
            <span className="pick-price">${p.price?.toFixed(2)}</span>
            <button
              className="see-why-btn"
              onClick={(e) => { e.stopPropagation(); onSelectProduct(p) }}
            >
              See why
            </button>
          </div>
        </div>
      ))}
    </div>
  )
}

function StarRow({ rating }) {
  if (!rating) return null
  // Fractional fill so a 4.6 doesn't look identical to a 5.0.
  // Using a half-star glyph keeps the star count at five.
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

// Tile bullets are now derived from the ranker's signals, not hardcoded.
// Up to two short bullets per tile, category-aware. If we have no
// grounded signals to show we render no bullets — better than fabricating
// "Hands-free voice control" on a $9 plastic bin.
function tileBullets(product) {
  const bullets = []
  const rules = new Set(product.rule_matches || [])
  const features = product.features || {}

  if (rules.has('voice_control') || features.voice_control)
    bullets.push('✓ Hands-free voice control')
  if (rules.has('display_device') && /15|21|wall/.test(product.title || ''))
    bullets.push('✓ Large recipe-friendly screen')
  if (rules.has('family_scheduling'))
    bullets.push('✓ Family calendar / scheduling')
  if (rules.has('insulated_gym') || rules.has('insulated_outdoor') || rules.has('insulated') || features.insulated)
    bullets.push('✓ Insulated double-wall')
  if (rules.has('lightweight_size') || features.lightweight)
    bullets.push('✓ Lightweight build')
  if (rules.has('cabinet_stackable') || rules.has('space_efficient') || features.stackable || features.expandable)
    bullets.push('✓ Stackable / space-saving')
  if (rules.has('visibility_easy_access') || features.drawer_style)
    bullets.push('✓ Clear / compartmented for visibility')

  // Delivery only when we actually have it — no fabrication.
  const days = product.arrival_time_days
  if (days != null) {
    const label = days === 0 ? 'today' : days === 1 ? '1 day' : `${days} days`
    bullets.push(`🚚 Delivery: ${label}`)
  }
  return bullets.slice(0, 2)
}

// Feature tags — same source of truth (rule_matches + features), but
// shown as pill chips at the bottom of the tile.
function featureTags(product) {
  const tags = []
  const rules = new Set(product.rule_matches || [])
  const features = product.features || {}

  if (product.category === 'smart_display' && rules.has('display_device')) tags.push('Recipe Display')
  if (rules.has('voice_control') || features.voice_control) tags.push('Voice control')
  if (rules.has('family_scheduling')) tags.push('Family Hub')
  if (features.insulated) tags.push('Insulated')
  if (features.lightweight) tags.push('Lightweight')
  if (features.stackable) tags.push('Stackable')
  if (features.drawer_style) tags.push('Drawer fit')
  if (/lazy susan|turn table/.test((product.title || '').toLowerCase())) tags.push('Lazy Susan')
  return tags.slice(0, 2)
}

export default function ProductCard({ product, onSelect }) {
  const bullets = tileBullets(product)
  const tags = featureTags(product)

  return (
    <div className="product-tile" onClick={onSelect} role="button" tabIndex={0}>
      <div className="tile-image-wrap">
        {product.image_url ? (
          <img
            src={product.image_url}
            alt={product.title}
            onError={(e) => {
              const ph = e.target.parentNode.querySelector('.image-placeholder')
              if (ph) ph.style.display = 'flex'
              e.target.style.display = 'none'
            }}
          />
        ) : null}
        <div
          className="image-placeholder"
          aria-hidden="true"
          style={{ display: product.image_url ? 'none' : 'flex' }}
        >
          {product.category === 'smart_display' ? '🖥️' :
           product.category === 'water_bottle' ? '🥤' : '🗂️'}
        </div>
      </div>

      <div className="tile-body">
        <div className="tile-title" title={product.title}>{product.title}</div>
        <StarRow rating={product.rating} />
        {bullets.length > 0 && (
          <ul className="tile-meta">
            {bullets.map((b, i) => <li key={i}>{b}</li>)}
          </ul>
        )}
        {tags.length > 0 && (
          <div className="tag-row">
            {tags.map((t) => <span key={t} className="tag-chip">{t}</span>)}
          </div>
        )}
        <div className="tile-footer">
          <span className="tile-price">${product.price?.toFixed(2)}</span>
          <button
            className="see-why-btn"
            onClick={(e) => { e.stopPropagation(); onSelect() }}
          >
            See why
          </button>
        </div>
      </div>
    </div>
  )
}

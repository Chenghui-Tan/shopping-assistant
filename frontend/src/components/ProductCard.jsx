function StarRow({ rating }) {
  if (!rating) return null
  const filled = Math.round(rating)
  return (
    <span className="star-row">
      <span className="stars">
        {'★'.repeat(filled)}{'☆'.repeat(5 - filled)}
      </span>
      <span className="rating-num">{rating.toFixed(1)}</span>
    </span>
  )
}

function FeatureTags({ product }) {
  const tags = []
  const title = (product.title || '').toLowerCase()
  if (product.category === 'smart_display' || /display|hub|touchscreen/.test(title)) tags.push('Recipe Display')
  if (/voice|alexa|echo|google/.test(title)) tags.push('Voice control')
  if (/family|calendar|chore/.test(title)) tags.push('Family Hub')
  if (/insulated|stainless|vacuum/.test(title)) tags.push('Insulated')
  if (/lightweight|tritan|plastic/.test(title)) tags.push('Lightweight')
  if (/stackable/.test(title)) tags.push('Stackable')
  if (/drawer|flatware/.test(title)) tags.push('Drawer fit')
  if (/bin|fridge|pantry/.test(title)) tags.push('Bin')
  if (/lazy susan|turn table/.test(title)) tags.push('Lazy Susan')
  return (
    <div className="tag-row">
      {tags.slice(0, 2).map((t) => (
        <span key={t} className="tag-chip">{t}</span>
      ))}
    </div>
  )
}

export default function ProductCard({ product, onSelect, highlightSale }) {
  const deliveryDays = product.arrival_time_days
  const delivery = deliveryDays != null
    ? `Delivery: ${deliveryDays === 0 ? 'today' : deliveryDays + (deliveryDays === 1 ? ' day' : ' days')}`
    : 'Delivery: 2–3 days'

  return (
    <div className="product-tile" onClick={onSelect} role="button" tabIndex={0}>
      {highlightSale && <span className="sale-badge">SALE</span>}
      <div className="tile-image-wrap">
        {product.image_url ? (
          <img
            src={product.image_url}
            alt={product.title}
            onError={(e) => { e.target.style.display = 'none' }}
          />
        ) : (
          <div className="image-placeholder" aria-hidden="true">🖥️</div>
        )}
      </div>

      <div className="tile-body">
        <div className="tile-title" title={product.title}>{product.title}</div>
        <StarRow rating={product.rating} />
        <ul className="tile-meta">
          <li>✓ Hands-free voice control</li>
          <li>✓ {delivery}</li>
        </ul>
        <FeatureTags product={product} />
        <div className="tile-footer">
          <span className="tile-price">${product.price?.toFixed(2)}</span>
          <button
            className="see-why-btn"
            onClick={(e) => { e.stopPropagation(); onSelect() }}
          >
            See why this fits
          </button>
        </div>
      </div>
    </div>
  )
}

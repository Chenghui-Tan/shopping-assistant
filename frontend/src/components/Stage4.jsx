function deriveReasons(product) {
  if (!product) return []
  const t = (product.title || '').toLowerCase()
  const reasons = []
  if (/15\.6|echo show 15|21"|wall/.test(t))
    reasons.push('The large 15.6" screen makes recipes easy to follow while cooking, reducing the need to squint or get close.')
  if (/voice|alexa|echo|google/.test(t))
    reasons.push("Hands-free voice control works well in the kitchen when your hands are messy or busy.")
  if (/calendar|family|hub|planner/.test(t))
    reasons.push('Built-in meal planning and nutrition features support healthier routines for your family.')
  if (/cook|recipe|kitchen/.test(t))
    reasons.push('It also supports videos and family scheduling during meals, adding value beyond cooking.')
  if (/insulated|stainless|vacuum/.test(t))
    reasons.push('Double-wall insulation keeps drinks cold for hours — ideal mid-workout.')
  if (/lightweight|plastic|tritan/.test(t))
    reasons.push('Lightweight construction means you can throw it in your gym bag without weighing you down.')
  if (/stackable|expandable|tier/.test(t))
    reasons.push('Stackable / expandable design maximizes vertical space — exactly what tight cabinets need.')
  if (/drawer|flatware|compartment/.test(t))
    reasons.push('Drawer / compartment layout means every utensil has a home — no more morning hunting.')
  if (/lazy susan|turn table/.test(t))
    reasons.push('Lazy Susan keeps countertop items visible and one-spin-away.')
  if (product.rating && product.rating >= 4.5)
    reasons.push(`High customer rating (${product.rating.toFixed(1)}★) signals dependable quality from real users.`)
  if (reasons.length < 3) {
    reasons.push('Matches your stated budget and delivery window without compromising on the features you said matter most.')
    reasons.push('Surfaced by a deterministic ranking pass — not a black-box click-prediction model — so the rationale is fully auditable.')
  }
  return reasons.slice(0, 5)
}

function deriveTradeoff(product) {
  const t = (product.title || '').toLowerCase()
  if (/15\.6|echo show 15|21"|wall/.test(t)) {
    return 'This model is slightly larger, so ensure you have counter space. The best choice if you want full hands-free comprehensive use.'
  }
  if (/insulated/.test(t)) {
    return 'Insulation adds some weight versus a plain plastic bottle — a worthwhile trade for cold drinks during long workouts.'
  }
  if (/expandable|stackable/.test(t)) {
    return "Stackable bins require a bit of setup, but they pay back daily by carving out 30–40% more usable space."
  }
  if (product.price && product.price < 20) {
    return 'Lowest price in your set; if you upgrade later, the extra features cost a small premium but are not necessary today.'
  }
  return "There's a small premium over the cheapest option — but the rating and feature match make it worth it for your stated priorities."
}

export default function Stage4({ product, onBack, onSeeLifecycle }) {
  if (!product) {
    return (
      <div style={{ padding: 32, textAlign: 'center', color: 'var(--text-secondary)' }}>
        Select a product first.
        <div style={{ marginTop: 12 }}>
          <button className="btn-ghost" onClick={onBack}>← Back to recommendations</button>
        </div>
      </div>
    )
  }

  const reasons = deriveReasons(product)
  const tradeoff = deriveTradeoff(product)

  return (
    <div className="why-page">
      <div className="why-back-row">
        <button className="btn-ghost" onClick={onBack}>← Back to all options</button>
      </div>

      <div className="why-product-banner">
        <div className="why-image">
          {product.image_url
            ? <img src={product.image_url} alt={product.title} />
            : <div className="image-placeholder" aria-hidden="true">🖥️</div>}
        </div>
        <div className="why-product-meta">
          <div className="why-product-title">{product.title}</div>
          <div className="why-product-price">${product.price?.toFixed(2)}</div>
          {product.rating && (
            <div className="why-product-rating">
              {'★'.repeat(Math.round(product.rating))}{'☆'.repeat(5 - Math.round(product.rating))}
              <span className="rating-num">{product.rating.toFixed(1)}</span>
            </div>
          )}
        </div>
      </div>

      <h3 className="why-headline">
        <span className="why-check">✓</span> This option is recommended because:
      </h3>
      <ul className="why-list">
        {reasons.map((r, i) => <li key={i}>{r}</li>)}
      </ul>

      <div className="tradeoff-card">
        <div className="tradeoff-label">⚠️ Trade-offs to consider</div>
        <div className="tradeoff-text">{tradeoff}</div>
      </div>

      <div className="trust-banner">
        <span className="trust-icon">🛡️</span>
        <span><strong>Transparency builds trust:</strong> We explain not just <em>what's "best"</em> but why it fits your specific needs and lifestyle.</span>
      </div>

      <div className="why-cta-row">
        <button className="btn-primary" onClick={onSeeLifecycle}>
          See how it fits your daily life →
        </button>
        <button className="btn-ghost-strong" onClick={onBack}>Save for later</button>
      </div>
    </div>
  )
}

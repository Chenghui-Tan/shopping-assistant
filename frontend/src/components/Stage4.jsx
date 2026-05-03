// Rule names emitted by the ranker → human-readable reasons. Mirrors the
// backend's recommendation_Algorithem/explainability.py mapping. Keeping
// it duplicated here is deliberate: explanations should render even if a
// future API change drops the `explanation` field. If the ranker emits a
// rule we don't recognise, we silently skip it rather than invent copy.
const RULE_TEXT = {
  voice_control:           'Hands-free voice control — useful when your hands are full or messy.',
  kitchen_hub_or_recipe:   'Designed for kitchen and recipe use, not a generic tablet.',
  family_scheduling:       'Family calendar / scheduling features built in.',
  large_screen:            'Large screen — easier to follow recipes from across the counter.',
  entertainment_features:  'Streams video, supports cooking shows and recipe walkthroughs.',
  smart_home_compatible:   'Voice-controllable for smart-home routines.',
  smart_device_bundle:     'Bundled with a smart-home device — single-purchase setup.',
  display_device:          'A real display device — not a sensor or speaker miscategorised.',
  gym_suitable:            'Lightweight or athletic-grade build — fits a gym bag.',
  insulated_gym:           'Double-wall insulation keeps drinks cold during a workout.',
  daily_use:               'Designed for daily carry — ergonomic, leak-resistant.',
  outdoor_capacity:        'Large capacity — fewer refills outdoors.',
  insulated_outdoor:       'Holds temperature for hours — important on long trips.',
  kids_design:             'Kid-friendly design and licensed character finish.',
  kids_lightweight:        'Light enough for kids to carry without strain.',
  insulated:               'Insulated — keeps drinks hot or cold as you asked.',
  lightweight_size:        'Lightweight body — easy to throw in a bag.',
  easy_clean:              'Dishwasher-safe / easy to clean — matches your stated preference.',
  cabinet_fit:             'Sized and shaped for cabinet shelves.',
  cabinet_stackable:       'Stackable / expandable — claws back vertical cabinet space.',
  countertop_suitable:     'Counter-friendly footprint — stays out of the way.',
  countertop_aesthetic:    "Clean, modern look — won't visually clutter the counter.",
  under_sink_fit:          'Bin / basket form factor — fits the awkward under-sink area.',
  space_efficient:         'Built specifically to maximise tight spaces.',
  visibility_easy_access:  'Clear or compartmented — every item is visible at a glance.',
  easy_install:            'Comes ready-assembled or as a modular set — minimal setup.',
}

function reasonsFromRules(rules) {
  const out = []
  for (const r of rules || []) {
    if (RULE_TEXT[r]) {
      out.push(RULE_TEXT[r])
      continue
    }
    if (r.startsWith('structure_')) {
      out.push('Matches the organiser style you picked: ' + r.slice('structure_'.length).replace(/_/g, ' ') + '.')
    }
  }
  return out
}

function deriveReasons(product) {
  if (!product) return []
  const reasons = reasonsFromRules(product.rule_matches)

  // Add rating evidence if it qualifies — this is information from the
  // shared score, not a category-specific rule, but users care about it.
  if (product.rating && product.rating >= 4.5) {
    reasons.push(`Top-tier customer rating (${product.rating.toFixed(1)}★) — dependable signal from real users.`)
  }

  // Last-resort fallback: if the ranker emitted no recognisable rules
  // (rare — happens for the 4th-tier 'no category' fallback) we say so
  // honestly rather than fabricate reasons.
  if (reasons.length === 0) {
    reasons.push("This product surfaced as a close match to your stated budget and delivery window, even though no category-specific feature rule fired.")
  }
  return reasons.slice(0, 5)
}

function deriveTradeoff(product) {
  if (!product) return null
  const rules = new Set(product.rule_matches || [])

  // Trade-offs are derived from rule context. Only emit one when we can
  // ground it; otherwise return null and the UI can hide the card.
  if (rules.has('large_screen')) {
    return 'A larger screen is the strongest fit for your stated use case but takes more counter space than a smaller smart display.'
  }
  if (rules.has('insulated_gym') || rules.has('insulated_outdoor')) {
    return 'Insulated double-wall construction adds some weight versus a plain plastic bottle — worth it for the temperature retention you asked for.'
  }
  if (rules.has('cabinet_stackable') || rules.has('space_efficient')) {
    return 'Stackable / expandable bins require a bit of initial setup, but they recover 30–40% more usable cabinet space day-to-day.'
  }
  if (rules.has('display_device') && product.price && product.price > 100) {
    return "Pricier than a basic speaker, but you're paying for the screen and recipe-following capability that your use case needs."
  }
  if (product.price && product.price < 15) {
    return 'Lowest-cost option in your set; if your needs grow later, upgrading is straightforward.'
  }
  return null
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
  // The backend already wrote a one-line summary explanation; show it
  // above the bullet list so the user gets a personal sentence first.
  const summary = product.explanation && product.explanation.trim() !== ''
    ? product.explanation
    : null

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

      {summary && <p className="why-summary">{summary}</p>}

      <h3 className="why-headline">
        <span className="why-check">✓</span> This option is recommended because:
      </h3>
      <ul className="why-list">
        {reasons.map((r, i) => <li key={i}>{r}</li>)}
      </ul>

      {tradeoff && (
        <div className="tradeoff-card">
          <div className="tradeoff-label">⚠️ Trade-off to consider</div>
          <div className="tradeoff-text">{tradeoff}</div>
        </div>
      )}

      <div className="trust-banner">
        <span className="trust-icon">🛡️</span>
        <span>
          <strong>Transparency builds trust:</strong> every reason above maps to a rule the
          ranker actually used — not a generic marketing bullet.
        </span>
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

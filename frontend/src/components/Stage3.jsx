import ProductCard from './ProductCard'
import SupplementBar from './SupplementBar'

const RELAXATION_MESSAGES = {
  no_delivery: {
    label: 'Delivery filter dropped',
    body: 'We loosened your delivery deadline to find more matches. Try clicking "No rush" or refining below if you still need fast delivery.',
  },
  no_price: {
    label: 'Price + delivery filters dropped',
    body: "We couldn't find enough matches inside your price and delivery limits, so we relaxed both. The picks below match your category and use case but may exceed your stated budget.",
  },
  no_category: {
    label: 'All filters dropped',
    body: 'We could not find good matches inside your stated category, so we are showing top products across the whole catalog ranked by overall quality.',
  },
}

export default function Stage3({
  sessionId,
  products,
  supplementLog,
  onSupplement,
  onSelectProduct,
  relaxation,
}) {
  if (!products || products.length === 0) {
    return (
      <div style={{ padding: 32, textAlign: 'center', color: 'var(--text-secondary)' }}>
        No matches yet. Try adjusting your preferences.
      </div>
    )
  }

  const note = relaxation && relaxation !== 'strict' ? RELAXATION_MESSAGES[relaxation] : null

  return (
    <div>
      {note && (
        <div className="relax-banner" role="status">
          <div className="relax-banner-head">
            <span className="relax-banner-icon">⚠️</span>
            <strong>{note.label}</strong>
          </div>
          <div className="relax-banner-body">{note.body}</div>
        </div>
      )}

      <p className="grid-summary">
        Showing {products.length} curated options
        {relaxation === 'strict' && ' · all your filters were honoured'}
      </p>

      <div className="product-grid" id="results-top">
        {products.map((product, i) => (
          <ProductCard
            key={product.product_url || i}
            product={product}
            onSelect={() => onSelectProduct(product)}
          />
        ))}
      </div>

      <SupplementBar
        sessionId={sessionId}
        supplementLog={supplementLog}
        onSupplement={onSupplement}
      />
    </div>
  )
}

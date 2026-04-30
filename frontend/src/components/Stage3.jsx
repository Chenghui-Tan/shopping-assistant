import ProductCard from './ProductCard'
import SupplementBar from './SupplementBar'

export default function Stage3({ sessionId, products, supplementLog, onSupplement, onSelectProduct }) {
  if (!products || products.length === 0) {
    return (
      <div style={{ padding: 32, textAlign: 'center', color: 'var(--text-secondary)' }}>
        No matches yet. Try adjusting your preferences.
      </div>
    )
  }

  return (
    <div>
      <p className="grid-summary">
        Showing {products.length} curated options
      </p>

      <div className="product-grid" id="results-top">
        {products.map((product, i) => (
          <ProductCard
            key={product.product_url || i}
            product={product}
            onSelect={() => onSelectProduct(product)}
            highlightSale={i === 0 || i === 4 || i === 7}
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

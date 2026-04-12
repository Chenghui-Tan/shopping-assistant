import ProductCard from './ProductCard'
import SupplementBar from './SupplementBar'

export default function Stage3({ sessionId, products, supplementLog, onSupplement }) {
  return (
    <div>
      <h2 style={{ fontSize: 22, fontWeight: 700, marginBottom: 4 }}>
        Your matches
      </h2>
      <p style={{ color: 'var(--text-secondary)', marginBottom: 28, fontSize: 14 }}>
        {products.length} recommendations, ranked for you
      </p>

      <div id="results-top">
        {products.map((product, i) => (
          <ProductCard key={product.product_url + i} product={product} />
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

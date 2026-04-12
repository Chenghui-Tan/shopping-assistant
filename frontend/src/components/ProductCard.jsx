export default function ProductCard({ product }) {
  return (
    <div className="card" style={{ display: 'flex', gap: 16, padding: 20, marginBottom: 16 }}>
      <a
        href={product.product_url}
        target="_blank"
        rel="noopener noreferrer"
        style={{ flexShrink: 0 }}
      >
        <img
          src={product.image_url}
          alt={product.title}
          style={{
            width: 80, height: 80, objectFit: 'contain',
            borderRadius: 8, background: '#f8f8fc',
          }}
          onError={(e) => { e.target.style.display = 'none' }}
        />
      </a>

      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8 }}>
          <a
            href={product.product_url}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              fontSize: 15, fontWeight: 600, color: 'var(--text-primary)',
              textDecoration: 'none', lineHeight: 1.3,
            }}
          >
            {product.title}
          </a>
          <span style={{
            fontSize: 16, fontWeight: 700,
            background: 'var(--accent-gradient)',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
            backgroundClip: 'text', flexShrink: 0,
          }}>
            ${product.price?.toFixed(2)}
          </span>
        </div>

        {product.rating && (
          <div style={{ fontSize: 13, color: '#f59e0b', marginTop: 4 }}>
            {'★'.repeat(Math.round(product.rating))}
            {'☆'.repeat(5 - Math.round(product.rating))}
            <span style={{ color: 'var(--text-secondary)', marginLeft: 4 }}>
              {product.rating.toFixed(1)}
            </span>
          </div>
        )}

        <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 8, lineHeight: 1.5 }}>
          {product.explanation}
        </p>
      </div>
    </div>
  )
}

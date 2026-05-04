/**
 * ComparisonView — side-by-side table of 2–3 finalists.
 *
 * Driven by category-aware row definitions so each category surfaces
 * the attributes that matter for *that* decision (screen size for
 * displays, capacity for bottles, visibility for organisers).
 *
 * Cells render extracted attributes from the backend (no fabrication).
 * '—' is shown when an attribute is genuinely unknown for a product.
 */

const fmtList = (xs) => Array.isArray(xs) && xs.length ? xs.join(', ') : null

const SD_ROWS = [
  { key: 'price',          label: 'Price',           fmt: (p) => p.price != null ? `$${p.price.toFixed(2)}` : null },
  { key: 'screen_inches',  label: 'Screen size',     fmt: (p) => p.screen_inches ? `${p.screen_inches}"` : null },
  { key: 'ecosystems',     label: 'Voice ecosystem', fmt: (p) => fmtList((p.ecosystems || []).map((e) => e[0].toUpperCase() + e.slice(1))) },
  { key: 'has_camera',     label: 'Camera',          fmt: (p) => p.has_camera === true ? 'Yes' : p.has_camera === false ? 'No' : null },
  { key: 'mounting',       label: 'Mounting',        fmt: (p) => fmtList(p.mounting) },
  { key: 'arrival',        label: 'Delivery',        fmt: (p) => p.arrival_time_days != null
                                                                  ? (p.arrival_time_days === 0 ? 'today' : `${p.arrival_time_days} days`)
                                                                  : null },
  { key: 'rating',         label: 'Rating',          fmt: (p) => p.rating ? `${p.rating.toFixed(1)}★` : null },
  { key: 'rule_count',     label: 'Rules matched',   fmt: (p) => p.rule_matches ? `${p.rule_matches.length}` : null },
]

const WB_ROWS = [
  { key: 'price',          label: 'Price',          fmt: (p) => p.price != null ? `$${p.price.toFixed(2)}` : null },
  { key: 'capacity_oz',    label: 'Capacity',       fmt: (p) => p.capacity_oz ? `${p.capacity_oz} oz` : null },
  { key: 'bottle_material',label: 'Material',       fmt: (p) => p.bottle_material ? p.bottle_material[0].toUpperCase() + p.bottle_material.slice(1) : null },
  { key: 'drinking_style', label: 'Drinking style', fmt: (p) => p.drinking_style ? p.drinking_style[0].toUpperCase() + p.drinking_style.slice(1) : null },
  { key: 'insulated',      label: 'Insulated',      fmt: (p) => p.features?.insulated ? 'Yes' : (p.features ? 'No' : null) },
  { key: 'lightweight',    label: 'Lightweight',    fmt: (p) => p.features?.lightweight ? 'Yes' : null },
  { key: 'arrival',        label: 'Delivery',       fmt: (p) => p.arrival_time_days != null
                                                                  ? `${p.arrival_time_days} days` : null },
  { key: 'rating',         label: 'Rating',         fmt: (p) => p.rating ? `${p.rating.toFixed(1)}★` : null },
]

const KO_ROWS = [
  { key: 'price',                 label: 'Price',         fmt: (p) => p.price != null ? `$${p.price.toFixed(2)}` : null },
  { key: 'organizer_material',    label: 'Material',      fmt: (p) => p.organizer_material ? p.organizer_material[0].toUpperCase() + p.organizer_material.slice(1) : null },
  { key: 'organizer_visibility',  label: 'Visibility',    fmt: (p) => p.organizer_visibility ? p.organizer_visibility[0].toUpperCase() + p.organizer_visibility.slice(1) : null },
  { key: 'structure',             label: 'Structure',     fmt: (p) => {
      const t = (p.title || '').toLowerCase()
      if (/stackable|tier/.test(t)) return 'Stackable'
      if (/expandable/.test(t))    return 'Expandable'
      if (/lazy susan|turn table/.test(t)) return 'Lazy Susan'
      if (/drawer|flatware/.test(t)) return 'Drawer'
      if (/bin|basket/.test(t)) return 'Bin'
      return null
    } },
  { key: 'arrival',               label: 'Delivery',      fmt: (p) => p.arrival_time_days != null
                                                                          ? `${p.arrival_time_days} days` : null },
  { key: 'rating',                label: 'Rating',        fmt: (p) => p.rating ? `${p.rating.toFixed(1)}★` : null },
]

const ROWS_BY_CATEGORY = {
  smart_display:     SD_ROWS,
  water_bottle:      WB_ROWS,
  kitchen_organizer: KO_ROWS,
}

/** Highlight the row's "winner" with a subtle bg. Defines what 'best' means
 * for each row — lowest price, largest capacity, fastest delivery, etc.
 * Returns the index of the winning column or -1.
 */
function winningColumn(rowKey, products) {
  const vals = products.map((p) => {
    if (rowKey === 'price')         return p.price ?? Infinity
    if (rowKey === 'screen_inches') return p.screen_inches ?? -Infinity
    if (rowKey === 'capacity_oz')   return p.capacity_oz ?? -Infinity
    if (rowKey === 'arrival')       return p.arrival_time_days ?? Infinity
    if (rowKey === 'rating')        return p.rating ?? -Infinity
    if (rowKey === 'rule_count')    return p.rule_matches?.length ?? -Infinity
    return null
  })
  if (vals.every((v) => v === null)) return -1
  // Lower is better for price + arrival; higher otherwise.
  const lowerBetter = rowKey === 'price' || rowKey === 'arrival'
  let best = -1
  let bestVal = lowerBetter ? Infinity : -Infinity
  for (let i = 0; i < vals.length; i++) {
    const v = vals[i]
    if (v == null) continue
    if (lowerBetter ? v < bestVal : v > bestVal) {
      bestVal = v
      best = i
    }
  }
  return best
}

export default function ComparisonView({ products, onClose, onSelectProduct }) {
  if (!products || products.length < 2) return null
  const category = products[0].category
  const rows = ROWS_BY_CATEGORY[category] || SD_ROWS

  return (
    <div className="compare-overlay" onClick={onClose}>
      <div className="compare-panel" onClick={(e) => e.stopPropagation()}>
        <div className="compare-head">
          <h3>Compare {products.length} options</h3>
          <button className="btn-ghost" onClick={onClose}>✕</button>
        </div>

        <div className="compare-grid" style={{
          gridTemplateColumns: `auto repeat(${products.length}, 1fr)`,
        }}>
          <div className="compare-cell compare-corner"></div>
          {products.map((p, i) => (
            <div key={i} className="compare-header-cell">
              <div className="compare-header-image">
                {p.image_url
                  ? <img src={p.image_url} alt={p.title} onError={(e) => { e.target.style.display = 'none' }} />
                  : <span style={{ fontSize: 28, opacity: 0.5 }}>{
                      category === 'smart_display' ? '🖥️' : category === 'water_bottle' ? '🥤' : '🗂️'
                    }</span>}
              </div>
              <div className="compare-header-title" title={p.title}>{p.title}</div>
              {p.pick_label && <div className="compare-header-badge">{p.pick_label}</div>}
              <button
                className="see-why-btn"
                onClick={() => onSelectProduct(p)}
              >
                See why
              </button>
            </div>
          ))}

          {rows.map((row) => {
            const winner = winningColumn(row.key, products)
            return (
              <RowGroup key={row.key} row={row} products={products} winner={winner} />
            )
          })}
        </div>

        <div className="compare-footer">
          {products[0].rule_matches?.length > 0 && (
            <p className="compare-footer-note">
              "Rules matched" counts the category-specific scoring rules each product
              hit — a higher number means the product fits more of your stated
              preferences.
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

function RowGroup({ row, products, winner }) {
  return (
    <>
      <div className="compare-cell compare-rowlabel">{row.label}</div>
      {products.map((p, i) => {
        const v = row.fmt(p)
        const isWinner = i === winner
        return (
          <div
            key={i}
            className={'compare-cell compare-value' + (isWinner ? ' compare-winner' : '')}
          >
            {v ?? <span className="compare-unknown">—</span>}
          </div>
        )
      })}
    </>
  )
}

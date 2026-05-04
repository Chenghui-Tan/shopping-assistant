import { useState, useCallback } from 'react'
import Stage1 from './components/Stage1'
import Stage2 from './components/Stage2'
import Stage3 from './components/Stage3'
import Stage4 from './components/Stage4'
import Stage5 from './components/Stage5'
import ComparisonView from './components/ComparisonView'
import { saveProduct } from './api'

const SCENE_META = {
  1: {
    headerTitle: 'Shopping Assistant',
    headerSubtitle: 'Here to help you choose with confidence',
    caption: "Scene 1: Need Discovery — Start from the shopper's real situation, not a product category",
  },
  2: {
    headerTitle: 'Let me understand your needs better',
    headerSubtitle: 'This helps me find the right solution for you',
    caption: 'Scene 2: Needs Clarification — Interactive questions transform vague needs into structured inputs',
  },
  3: {
    headerTitle: 'Recommended for you',
    headerSubtitle: 'Based on your stated needs and lifestyle',
    caption: 'Scene 3: Constraint-Aware Recommendations — Ranked alternatives, decision-critical attributes visible',
  },
  4: {
    headerTitle: 'Why we recommend this',
    headerSubtitle: '',
    caption: 'Scene 4: Explainable Recommendation — Build trust through transparency, explain trade-offs, not just "best product"',
  },
  5: {
    headerTitle: 'Your Assistant, Every Day',
    headerSubtitle: 'Beyond shopping — supporting your life after purchase',
    caption: 'Scene 5: Post-Purchase Lifecycle Support — Reinforcing long-term value and lifecycle thinking, not just a transaction',
  },
}

export default function App() {
  const [stage, setStage] = useState(1)
  const [sessionId, setSessionId] = useState(null)
  const [products, setProducts] = useState([])
  const [picks, setPicks] = useState([])
  const [supplementLog, setSupplementLog] = useState([])
  const [startData, setStartData] = useState(null)
  const [rawInput, setRawInput] = useState(null)
  const [selectedProduct, setSelectedProduct] = useState(null)
  const [openingTurn, setOpeningTurn] = useState(null)
  const [relaxation, setRelaxation] = useState('strict')
  const [savedUrls, setSavedUrls] = useState(new Set())
  const [compareUrls, setCompareUrls] = useState([])  // ordered list, max 3
  // Presentation mode reveals evaluator-facing copy: scene captions
  // (which layer / scene we're on), the trust banner, and the rule-
  // matching commentary on Stage 4. Default OFF — the user-facing app
  // should feel like a real assistant, not a narrated prototype.
  const [presentationMode, setPresentationMode] = useState(false)
  const [showCompare, setShowCompare] = useState(false)

  const toggleCompare = useCallback((product) => {
    const url = product?.product_url
    if (!url) return
    setCompareUrls((prev) => {
      if (prev.includes(url)) return prev.filter((u) => u !== url)
      if (prev.length >= 3) return prev  // hard cap at 3
      return [...prev, url]
    })
  }, [])

  const compareProducts = compareUrls
    .map((u) => products.find((p) => p.product_url === u))
    .filter(Boolean)

  const toggleSave = useCallback(async (product) => {
    if (!sessionId || !product?.product_url) return
    try {
      const data = await saveProduct(sessionId, product)
      setSavedUrls(new Set((data.saved || []).map((p) => p.product_url)))
    } catch (e) {
      console.error('save failed', e)
    }
  }, [sessionId])

  const handleStage1Complete = (data, turn) => {
    setSessionId(data.session_id)
    setStartData(data)
    setOpeningTurn(turn)
    setStage(2)
  }

  const handleStage2Complete = (fetchedProducts, relaxationLevel, fetchedPicks, raw) => {
    setProducts(fetchedProducts)
    setPicks(fetchedPicks || [])
    setRelaxation(relaxationLevel || 'strict')
    if (raw) setRawInput(raw)
    setStage(3)
  }

  const handleSupplement = (fetchedProducts, aiResponse, relaxationLevel, diff, fetchedPicks) => {
    setProducts(fetchedProducts)
    setPicks(fetchedPicks || [])
    setRelaxation(relaxationLevel || 'strict')
    setSupplementLog((prev) => [{ aiResponse, diff: diff || {}, timestamp: Date.now() }, ...prev])
  }

  const handleSelectProduct = (product) => {
    setSelectedProduct(product)
    setStage(4)
  }

  const handleBackToGrid = () => setStage(3)
  const handleSeeLifecycle = () => setStage(5)

  const meta = SCENE_META[stage]

  return (
    <div className="app-shell">
      <div className="top-bar">
        <span>Shopping Assistant</span>
        <label className="presentation-toggle" title="Show scene captions + evaluator notes">
          <input
            type="checkbox"
            checked={presentationMode}
            onChange={(e) => setPresentationMode(e.target.checked)}
          />
          <span>Presentation mode</span>
        </label>
      </div>

      <div className="step-row">
        <span className="step-label">
          {presentationMode ? 'Human-Centered Shopping Assistant Demo' : ''}
        </span>
        <span className="step-right">
          {savedUrls.size > 0 && (
            <span className="saved-pill" title="Saved for later">
              ❤ {savedUrls.size} saved
            </span>
          )}
          <span className="step-text">Step {stage} of 5</span>
          <span className="step-dots">
            {[1, 2, 3, 4, 5].map((i) => (
              <span
                key={i}
                className={'dot ' + (i <= stage ? 'dot-active' : '')}
                onClick={() => i < stage && setStage(i)}
                role={i < stage ? 'button' : undefined}
                title={`Scene ${i}`}
              />
            ))}
          </span>
        </span>
      </div>

      <div className="scene-card">
        <header className="scene-header">
          <div className="scene-header-row">
            <span className="scene-header-icon" aria-hidden="true">
              {stage === 1 && '✨'}
              {stage === 2 && '✨'}
              {stage === 3 && '🛍️'}
              {stage === 4 && '✅'}
              {stage === 5 && '📅'}
            </span>
            <div>
              <div className="scene-header-title">{meta.headerTitle}</div>
              {meta.headerSubtitle && (
                <div className="scene-header-subtitle">{meta.headerSubtitle}</div>
              )}
            </div>
          </div>
        </header>

        <div className="scene-body">
          {stage === 1 && <Stage1 onComplete={handleStage1Complete} />}
          {stage === 2 && (
            <Stage2
              sessionId={sessionId}
              startData={startData}
              openingTurn={openingTurn}
              onComplete={handleStage2Complete}
            />
          )}
          {stage === 3 && (
            <Stage3
              sessionId={sessionId}
              products={products}
              picks={picks}
              supplementLog={supplementLog}
              onSupplement={handleSupplement}
              onSelectProduct={handleSelectProduct}
              relaxation={relaxation}
              savedUrls={savedUrls}
              onToggleSave={toggleSave}
              compareUrls={new Set(compareUrls)}
              onToggleCompare={toggleCompare}
            />
          )}
          {stage === 4 && (
            <Stage4
              product={selectedProduct}
              onBack={handleBackToGrid}
              onSeeLifecycle={handleSeeLifecycle}
              isSaved={selectedProduct && savedUrls.has(selectedProduct.product_url)}
              onToggleSave={toggleSave}
              rawInput={rawInput}
              presentationMode={presentationMode}
            />
          )}
          {stage === 5 && <Stage5 sessionId={sessionId} />}
        </div>
      </div>

      {presentationMode && (
        <div className="scene-caption">{meta.caption}</div>
      )}

      {/* Sticky compare bar visible whenever there are 2+ products selected
          to compare. Available across Scenes 3-5 so the user can compare from
          either the picks row, the full grid, or after seeing the why-page. */}
      {compareUrls.length >= 2 && stage >= 3 && (
        <div className="compare-bar">
          <span>{compareUrls.length} of 3 selected to compare</span>
          <button className="btn-ghost" onClick={() => setCompareUrls([])}>
            Clear
          </button>
          <button className="btn-primary" onClick={() => setShowCompare(true)}>
            Compare side-by-side →
          </button>
        </div>
      )}

      {showCompare && (
        <ComparisonView
          products={compareProducts}
          onClose={() => setShowCompare(false)}
          onSelectProduct={(p) => {
            setShowCompare(false)
            handleSelectProduct(p)
          }}
        />
      )}
    </div>
  )
}

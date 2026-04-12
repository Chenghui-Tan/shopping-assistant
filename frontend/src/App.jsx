import { useState } from 'react'
import Stage1 from './components/Stage1'
import Stage2 from './components/Stage2'
import Stage3 from './components/Stage3'

export default function App() {
  const [stage, setStage] = useState(1)
  const [sessionId, setSessionId] = useState(null)
  const [products, setProducts] = useState([])
  const [supplementLog, setSupplementLog] = useState([])
  const [startData, setStartData] = useState(null)

  const handleStage1Complete = (data) => {
    setSessionId(data.session_id)
    setStartData(data)
    setStage(2)
  }

  const handleStage2Complete = (fetchedProducts) => {
    setProducts(fetchedProducts)
    setStage(3)
  }

  const handleSupplement = (fetchedProducts, aiResponse) => {
    setProducts(fetchedProducts)
    setSupplementLog((prev) => [{ aiResponse, timestamp: Date.now() }, ...prev])
  }

  return (
    <>
      <nav>
        <span className="logo">ShopSmart</span>
        <span className="nav-subtitle">AI Assistant</span>
      </nav>
      <div className="page">
        {stage === 1 && <Stage1 onComplete={handleStage1Complete} />}
        {stage === 2 && (
          <Stage2
            sessionId={sessionId}
            startData={startData}
            onComplete={handleStage2Complete}
          />
        )}
        {stage === 3 && (
          <Stage3
            sessionId={sessionId}
            products={products}
            supplementLog={supplementLog}
            onSupplement={handleSupplement}
          />
        )}
      </div>
    </>
  )
}

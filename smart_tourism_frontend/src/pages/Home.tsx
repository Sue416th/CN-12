import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { createItinerary } from '../api'

const INTERESTS = [
  { key: 'culture', label: 'Culture', icon: '🏛️', color: '#f59e0b' },
  { key: 'food', label: 'Food', icon: '🍜', color: '#ef4444' },
  { key: 'nature', label: 'Nature', icon: '🌿', color: '#10b981' },
  { key: 'religion', label: 'Religion', icon: '🛕', color: '#8b5cf6' },
  { key: 'entertainment', label: 'Fun', icon: '🎭', color: '#ec4899' },
  { key: 'shopping', label: 'Shopping', icon: '🛍️', color: '#06b6d4' },
]

const BUDGETS = [
  { key: 'low', label: 'Budget', icon: '💰', desc: 'Economical' },
  { key: 'medium', label: 'Comfort', icon: '🏨', desc: 'Standard' },
  { key: 'high', label: 'Luxury', icon: '✨', desc: 'Premium' },
]

export default function Home() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const city = 'Hangzhou'
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [budget, setBudget] = useState('medium')
  const [interests, setInterests] = useState<string[]>([])
  const [step, setStep] = useState(1)

  // Set default dates to tomorrow and day after
  useEffect(() => {
    const today = new Date()
    const tomorrow = new Date(today)
    tomorrow.setDate(tomorrow.getDate() + 1)
    const dayAfter = new Date(tomorrow)
    dayAfter.setDate(dayAfter.getDate() + 1)

    const formatDate = (d: Date) => d.toISOString().split('T')[0]
    if (!startDate) setStartDate(formatDate(tomorrow))
    if (!endDate) setEndDate(formatDate(dayAfter))
  }, [])

  const toggleInterest = (v: string) => {
    setInterests((prev) =>
      prev.includes(v) ? prev.filter((x) => x !== v) : [...prev, v]
    )
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    if (!startDate || !endDate) {
      setError('Please select start and end dates')
      return
    }
    if (new Date(endDate) < new Date(startDate)) {
      setError('End date cannot be before start date')
      return
    }
    setLoading(true)
    try {
      const result = await createItinerary({
        city,
        start_date: startDate + 'T09:00:00',
        end_date: endDate + 'T18:00:00',
        budget_level: budget,
        interests,
      })
      navigate(`/itinerary/${result.itinerary_id}`, { state: { itinerary: result } })
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Generation failed')
    } finally {
      setLoading(false)
    }
  }

  const nextStep = () => {
    if (step < 3) setStep(step + 1)
  }

  const prevStep = () => {
    if (step > 1) setStep(step - 1)
  }

  return (
    <div className="page">
      <header className="header">
        <div className="logo-container">
          <span className="logo-icon">🗺️</span>
          <h1>Smart Tourism</h1>
        </div>
        <p className="tagline">AI-Powered Personalized Travel</p>
        <div className="step-indicator">
          <div className={`step ${step >= 1 ? 'active' : ''}`}>
            <span className="step-num">1</span>
            <span className="step-label">Date</span>
          </div>
          <div className="step-line" />
          <div className={`step ${step >= 2 ? 'active' : ''}`}>
            <span className="step-num">2</span>
            <span className="step-label">Budget</span>
          </div>
          <div className="step-line" />
          <div className={`step ${step >= 3 ? 'active' : ''}`}>
            <span className="step-num">3</span>
            <span className="step-label">Interests</span>
          </div>
        </div>
      </header>

      <main className="main">
        <form onSubmit={handleSubmit} className="form">
          {step === 1 && (
            <div className="step-content fade-in">
              <h2 className="step-title">Select Dates</h2>
              <p className="step-desc">Plan your Hangzhou trip</p>
              <div className="date-row">
                <div className="form-group">
                  <label><span>📅</span> Start Date</label>
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    required
                    min={new Date().toISOString().split('T')[0]}
                  />
                </div>
                <div className="form-group">
                  <label><span>📅</span> End Date</label>
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    required
                    min={startDate || new Date().toISOString().split('T')[0]}
                  />
                </div>
              </div>
              <div className="form-actions">
                <button type="button" className="btn-primary" onClick={nextStep}>
                  Next →
                </button>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="step-content fade-in">
              <h2 className="step-title">Select Budget</h2>
              <p className="step-desc">Customize your trip based on budget</p>
              <div className="budget-grid">
                {BUDGETS.map((b) => (
                  <button
                    key={b.key}
                    type="button"
                    className={`budget-card ${budget === b.key ? 'active' : ''}`}
                    onClick={() => setBudget(b.key)}
                  >
                    <span className="budget-icon">{b.icon}</span>
                    <span className="budget-label">{b.label}</span>
                    <span className="budget-desc">{b.desc}</span>
                  </button>
                ))}
              </div>
              <div className="form-actions">
                <button type="button" className="btn-secondary" onClick={prevStep}>
                  ← Back
                </button>
                <button type="button" className="btn-primary" onClick={nextStep}>
                  Next →
                </button>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="step-content fade-in">
              <h2 className="step-title">Select Interests</h2>
              <p className="step-desc">Choose your interests (multi-select)</p>
              <div className="interest-grid">
                {INTERESTS.map((item) => (
                  <button
                    key={item.key}
                    type="button"
                    className={`interest-card ${interests.includes(item.key) ? 'active' : ''}`}
                    onClick={() => toggleInterest(item.key)}
                    style={{ '--accent': item.color } as React.CSSProperties}
                  >
                    <span className="interest-icon">{item.icon}</span>
                    <span className="interest-label">{item.label}</span>
                  </button>
                ))}
              </div>
              {error && <p className="error">{error}</p>}
              <div className="form-actions">
                <button type="button" className="btn-secondary" onClick={prevStep}>
                  ← Back
                </button>
                <button type="submit" disabled={loading} className="btn-primary btn-generate">
                  {loading ? (
                    <>
                      <span className="loading-spinner" />
                      Planning...
                    </>
                  ) : (
                    <>🚀 Generate Trip</>
                  )}
                </button>
              </div>
            </div>
          )}
        </form>

        <nav className="nav-links">
          <Link to="/itineraries">📋 My Trips</Link>
          <Link to="/profile">👤 My Profile</Link>
        </nav>
      </main>
    </div>
  )
}

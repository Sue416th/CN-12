import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { listItineraries, deleteItinerary } from '../api'
import type { ItineraryListItem } from '../types'

function formatDate(s?: string) {
  if (!s) return '-'
  try {
    return new Date(s).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  } catch {
    return s
  }
}

function getTripDuration(name: string): string {
  if (name.includes('1日') || name.includes('1天') || name.includes('1 Day') || name.includes('-Day')) return '1 Day'
  if (name.includes('2日') || name.includes('2天') || name.includes('2 Day')) return '2 Days'
  if (name.includes('3日') || name.includes('3天') || name.includes('3 Day')) return '3 Days'
  return 'Multi-day'
}

export default function ItineraryList() {
  const navigate = useNavigate()
  const [list, setList] = useState<ItineraryListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [deletingId, setDeletingId] = useState<number | null>(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = () => {
    setLoading(true)
    listItineraries()
      .then(setList)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }

  const handleDelete = async (id: number, e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    
    if (!confirm('Are you sure you want to delete this trip?')) return
    
    setDeletingId(id)
    try {
      await deleteItinerary(id)
      setList(list.filter(item => item.id !== id))
    } catch (err) {
      alert('Delete failed')
    } finally {
      setDeletingId(null)
    }
  }

  if (loading) return (
    <div className="page loading">
      <div className="loading-content">
        <span className="loading-icon">⏳</span>
        <p>Loading...</p>
      </div>
    </div>
  )
  
  if (error) return (
    <div className="page error">
      <div className="error-content">
        <span className="error-icon">⚠️</span>
        <p>Error: {error}</p>
        <button className="btn-secondary" onClick={loadData}>Retry</button>
      </div>
    </div>
  )

  return (
    <div className="page">
      <header className="header">
        <button type="button" className="btn-back" onClick={() => navigate('/')}>
          ← Back
        </button>
        <div className="header-content">
          <h1>My Trips</h1>
          <p className="header-desc">{list.length} trip(s) planned</p>
        </div>
      </header>

      <main className="main">
        {list.length === 0 ? (
          <div className="empty-state">
            <span className="empty-icon">📝</span>
            <h3>No trips yet</h3>
            <p>Start planning your first Hangzhou adventure!</p>
            <Link to="/" className="btn-primary">Create Trip</Link>
          </div>
        ) : (
          <ul className="itinerary-list">
            {list.map((item, index) => (
              <li key={item.id}>
                <Link to={`/itinerary/${item.id}`} className="itinerary-card">
                  <div className="card-index">{String(index + 1).padStart(2, '0')}</div>
                  <div className="card-content">
                    <div className="card-header">
                      <span className="card-title">{item.name || 'Hangzhou Trip'}</span>
                      <span className="card-badge">{getTripDuration(item.name || '')}</span>
                    </div>
                    <div className="card-meta">
                      <span className="meta-item">
                        <span className="meta-icon">📍</span>
                        {item.city || 'Hangzhou'}
                      </span>
                      <span className="meta-item">
                        <span className="meta-icon">📅</span>
                        {formatDate(item.created_at)}
                      </span>
                    </div>
                  </div>
                  <button 
                    type="button" 
                    className="card-delete"
                    onClick={(e) => handleDelete(item.id, e)}
                    disabled={deletingId === item.id}
                  >
                    {deletingId === item.id ? '...' : '✕'}
                  </button>
                </Link>
              </li>
            ))}
          </ul>
        )}

        <div className="actions">
          <Link to="/" className="btn-primary">
            + New Trip
          </Link>
        </div>
      </main>
    </div>
  )
}

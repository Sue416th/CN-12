import { useEffect, useState } from 'react'
import { useParams, useNavigate, useLocation } from 'react-router-dom'
import { getItinerary, getPOIRealtime, getPOIHistory } from '../api'
import type { ItineraryResponse, POIRealtime, POIHistory } from '../types'
import MapView from '../components/MapView'

function formatTime(s: string) {
  try {
    const d = new Date(s)
    return d.toLocaleString('en-US', {
      month: 'numeric',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return s
  }
}

function formatDateOnly(s: string) {
  try {
    const d = new Date(s)
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  } catch {
    return s
  }
}

export default function ItineraryDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  const [data, setData] = useState<ItineraryResponse | null>(
    (location.state as { itinerary?: ItineraryResponse })?.itinerary ?? null
  )
  const [loading, setLoading] = useState(!data)
  const [error, setError] = useState('')
  const [selectedDay, setSelectedDay] = useState<number>(0)
  const [realtimeData, setRealtimeData] = useState<Record<number, POIRealtime>>({})
  const [historyData, setHistoryData] = useState<Record<number, POIHistory>>({})

  const weatherInfo = data?.weather_info
  const weatherAdvice = data?.weather_advice

  // Get all unique dates in the itinerary
  const getTripDates = () => {
    if (!data?.items || data.items.length === 0) return []
    const dates: string[] = []
    data.items.forEach(item => {
      if (item.start_time) {
        try {
          const d = new Date(item.start_time)
          const dateStr = d.getFullYear() + '-' + 
            String(d.getMonth() + 1).padStart(2, '0') + '-' + 
            String(d.getDate()).padStart(2, '0')
          if (!dates.includes(dateStr)) {
            dates.push(dateStr)
          }
        } catch {}
      }
    })
    return dates.sort()
  }

  // Get weather forecast for a specific date
  const getWeatherForDate = (dateStr: string) => {
    if (!weatherInfo?.forecast || weatherInfo.forecast.length === 0) {
      return null
    }
    const today = new Date()
    const targetDate = new Date(dateStr + 'T00:00:00')
    const diffDays = Math.round((targetDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24))
    if (diffDays >= 0 && diffDays < weatherInfo.forecast.length) {
      return weatherInfo.forecast[diffDays]
    }
    return null
  }

  // Group itinerary items by day
  const getItemsByDay = () => {
    if (!data?.items) return []
    const dates = getTripDates()
    if (selectedDay >= dates.length) return data.items
    
    const selectedDate = dates[selectedDay]
    return data.items.filter(item => {
      if (!item.start_time) return false
      const itemDate = new Date(item.start_time).toISOString().split('T')[0]
      return itemDate === selectedDate
    })
  }

  const tripDates = getTripDates()
  const dayItems = getItemsByDay()

  useEffect(() => {
    if (!id) return
    const stateItinerary = (location.state as { itinerary?: ItineraryResponse })?.itinerary
    if (stateItinerary && stateItinerary.itinerary_id === Number(id)) {
      setData(stateItinerary)
      setLoading(false)
      return
    }
    setLoading(true)
    setError('')
    getItinerary(Number(id))
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [id, location.state])

  // Load realtime data for each POI
  useEffect(() => {
    if (!data?.items || data.items.length === 0) return

    const loadRealtimeData = async () => {
      const poiIds = [...new Set(data.items.map(item => item.poi_id))]
      console.log('Loading realtime data for POIs:', poiIds)

      for (const poiId of poiIds) {
        try {
          const realtime = await getPOIRealtime(poiId)
          console.log('Realtime data for', poiId, realtime)
          if (realtime?.realtime) {
            setRealtimeData(prev => ({
              ...prev,
              [poiId]: realtime.realtime
            }))
          }

          const history = await getPOIHistory(poiId, 7)
          console.log('History data for', poiId, history)
          if (history?.history) {
            setHistoryData(prev => ({
              ...prev,
              [poiId]: history.history
            }))
          }
        } catch (e) {
          console.error(`Failed to load data for POI ${poiId}:`, e)
        }
      }
    }

    loadRealtimeData()
  }, [data?.items, data?.itinerary_id])

  if (loading) return (
    <div className="page loading">
      <div className="loading-content">
        <span className="loading-icon">⏳</span>
        <p>Loading trip...</p>
      </div>
    </div>
  )
  
  if (error) return (
    <div className="page error">
      <div className="error-content">
        <span className="error-icon">⚠️</span>
        <p>Error: {error}</p>
        <button className="btn-secondary" onClick={() => navigate(-1)}>Go Back</button>
      </div>
    </div>
  )
  
  if (!data) return (
    <div className="page error">
      <div className="error-content">
        <span className="error-icon">🔍</span>
        <p>Trip not found</p>
        <button className="btn-secondary" onClick={() => navigate('/')}>Home</button>
      </div>
    </div>
  )

  return (
    <div className="page">
      <header className="header">
        <button type="button" className="btn-back" onClick={() => navigate(-1)}>
          ← Back
        </button>
        <div className="header-content">
          <h1>{data.name || 'Smart Itinerary'}</h1>
          <p className="header-desc">
            {tripDates.length} Days · {data.city || 'Hangzhou'}
          </p>
        </div>
      </header>

      <main className="main">
        {/* Weather Section */}
        {(weatherInfo || weatherAdvice) && tripDates.length > 0 && (
          <div className="weather-section">
            <h3 className="section-title">📅 Weather Forecast</h3>
            
            {/* Day Tabs */}
            <div className="day-tabs">
              {tripDates.map((dateStr, idx) => {
                const weather = getWeatherForDate(dateStr)
                const isSelected = idx === selectedDay
                return (
                  <button
                    key={dateStr}
                    className={`day-tab ${isSelected ? 'active' : ''}`}
                    onClick={() => setSelectedDay(idx)}
                  >
                    <span className="day-label">Day {idx + 1}</span>
                    <span className="day-date">{formatDateOnly(dateStr)}</span>
                    {weather && (
                      <span className="day-weather">
                        {weather.temp}° {weather.weather}
                      </span>
                    )}
                  </button>
                )
              })}
            </div>

            {/* Weather Advice */}
            {weatherAdvice && weatherAdvice.length > 0 && (
              <div className="weather-advice-card">
                {weatherAdvice.map((advice: string, i: number) => (
                  <p key={i}>💡 {advice}</p>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Map Section */}
        {dayItems.some(item => item.location) && (
          <div className="map-section">
            <h3 className="section-title">🗺️ Route Map</h3>
            <MapView
              locations={dayItems.filter(item => item.location).map(item => item.location!)}
              pois={dayItems.filter(item => item.location).map(item => ({ name: item.poi_name || '', category: item.category }))}
            />
          </div>
        )}

        {/* Timeline Section */}
        <div className="timeline-section">
          <h3 className="section-title">🗓️ Itinerary</h3>
          <div className="timeline">
            {dayItems.length === 0 ? (
              <p className="empty-timeline">No itinerary items</p>
            ) : (
              dayItems.map((item, i) => {
                const cultureInfo = item.culture_info
                return (
                  <div key={i} className="timeline-item">
                    <div className="timeline-marker">
                      <div className="marker-dot" />
                      {i < dayItems.length - 1 && <div className="marker-line" />}
                    </div>
                    <div className="timeline-content">
                      <div className="time-slot">
                        {formatTime(item.start_time)} - {formatTime(item.end_time)}
                      </div>
                      <div className="poi-card">
                        <div className="poi-header">
                          <strong>{item.poi_name || item.note || `Spot #${item.poi_id}`}</strong>
                          <div className="poi-tags">
                            {item.category && <span className="category-tag">{item.category}</span>}
                            {item.rating && <span className="rating-tag">★ {item.rating}</span>}
                          </div>
                        </div>
                        {item.note && item.poi_name !== item.note && (
                          <p className="poi-note">{item.note}</p>
                        )}
                        {item.address && (
                          <p className="poi-address">📍 {item.address}</p>
                        )}

                        {/* Realtime Data */}
                        {realtimeData[item.poi_id] && (
                          <div className="realtime-card">
                            <div className="realtime-status">
                              <span className={`status-badge ${realtimeData[item.poi_id].is_open ? 'open' : 'closed'}`}>
                                {realtimeData[item.poi_id].open_status}
                              </span>
                              <span className={`crowd-badge crowd-${realtimeData[item.poi_id].crowd_level}`}>
                                {realtimeData[item.poi_id].crowd_text}
                              </span>
                            </div>
                            {realtimeData[item.poi_id].wait_time > 0 && (
                              <p className="wait-time">Wait: {realtimeData[item.poi_id].wait_time} min</p>
                            )}
                            {historyData[item.poi_id] && (
                              <div className="history-advice">
                                <p className="advice-text">{historyData[item.poi_id].best_time_advice}</p>
                              </div>
                            )}
                          </div>
                        )}
                        
                        {/* Culture Info */}
                        {cultureInfo && Object.keys(cultureInfo).length > 0 && (
                          <div className="culture-card">
                            {cultureInfo.dynasty && (
                              <span className="dynasty-badge">{cultureInfo.dynasty}</span>
                            )}
                            {cultureInfo.history && (
                              <p className="culture-history">{cultureInfo.history}</p>
                            )}
                            {cultureInfo.famous_poems && cultureInfo.famous_poems.length > 0 && (
                              <div className="poems-section">
                                {cultureInfo.famous_poems.map((poem: string, idx: number) => (
                                  <p key={idx} className="poem">"{poem}"</p>
                                ))}
                              </div>
                            )}
                            {cultureInfo.highlights && cultureInfo.highlights.length > 0 && (
                              <div className="highlights-section">
                                <span className="highlights-label">✨ Highlights: </span>
                                <span>{cultureInfo.highlights.join(', ')}</span>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )
              })
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="actions">
          <button type="button" className="btn-secondary" onClick={() => navigate('/')}>
            + New Trip
          </button>
          <button type="button" className="btn-primary" onClick={() => navigate('/itineraries')}>
            All Trips
          </button>
        </div>
      </main>
    </div>
  )
}

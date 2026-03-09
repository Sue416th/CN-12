import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { getUserProfile, updateUserProfile, getUserAnalysis } from '../api'
import type { UserProfile } from '../types'

const INTERESTS = [
  { key: 'culture', label: 'Culture', icon: '🏛️', color: '#f59e0b', desc: 'Museums, history, heritage' },
  { key: 'food', label: 'Food', icon: '🍜', color: '#ef4444', desc: 'Local cuisine, street food' },
  { key: 'nature', label: 'Nature', icon: '🌿', color: '#10b981', desc: 'Parks, mountains, lakes' },
  { key: 'religion', label: 'Religion', icon: '🛕', color: '#8b5cf6', desc: 'Temples, churches' },
  { key: 'entertainment', label: 'Fun', icon: '🎭', color: '#ec4899', desc: 'Shows, nightlife' },
  { key: 'shopping', label: 'Shopping', icon: '🛍️', color: '#06b6d4', desc: 'Markets, malls' },
  { key: 'photography', label: 'Photo', icon: '📷', color: '#f97316', desc: 'Scenic spots' },
  { key: 'sports', label: 'Sports', icon: '🏃', color: '#14b8a6', desc: 'Hiking, cycling' },
  { key: 'wellness', label: 'Wellness', icon: '🧘', color: '#a855f7', desc: 'Spa, hot springs' },
]

const BUDGETS = [
  { key: 'low', label: 'Budget', icon: '💰', desc: 'Economical travel' },
  { key: 'medium', label: 'Comfort', icon: '🏨', desc: 'Standard comfort' },
  { key: 'high', label: 'Luxury', icon: '✨', desc: 'Premium experience' },
]

const TRAVEL_STYLES = [
  { key: 'relaxed', label: 'Relaxed', icon: '🐢', desc: 'Slow pace, plenty of rest' },
  { key: 'balanced', label: 'Balanced', icon: '⚖️', desc: 'Mix of activities and rest' },
  { key: 'intensive', label: 'Intensive', icon: '🏃', desc: 'Maximize activities' },
]

const FITNESS_LEVELS = [
  { key: 'low', label: 'Light', icon: '🚶', desc: 'Limited walking, prefer vehicle' },
  { key: 'medium', label: 'Moderate', icon: '🚶🏃', desc: 'Can walk 4-6 hours daily' },
  { key: 'high', label: 'Active', icon: '🏃', desc: 'Full day activities, hiking OK' },
]

const GROUP_TYPES = [
  { key: 'solo', label: 'Solo', icon: '🧑', desc: 'Traveling alone' },
  { key: 'couple', label: 'Couple', icon: '💑', desc: 'With partner' },
  { key: 'family', label: 'Family', icon: '👨‍👩‍👧', desc: 'With children' },
  { key: 'friends', label: 'Friends', icon: '👥', desc: 'With friends' },
]

export default function UserProfilePage() {
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [analysis, setAnalysis] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')

  // Form state
  const [interests, setInterests] = useState<string[]>([])
  const [budgetLevel, setBudgetLevel] = useState('medium')
  const [travelStyle, setTravelStyle] = useState('balanced')
  const [fitnessLevel, setFitnessLevel] = useState('medium')
  const [groupType, setGroupType] = useState('solo')

  const userId = 1

  useEffect(() => {
    loadProfile()
  }, [])

  const loadProfile = async () => {
    try {
      const [profileData, analysisData] = await Promise.all([
        getUserProfile(userId),
        getUserAnalysis(userId)
      ])
      
      if (profileData) {
        setProfile(profileData)
        setInterests(profileData.interests || [])
        setBudgetLevel(profileData.budget_level || 'medium')
        setTravelStyle(profileData.travel_style || 'balanced')
        setFitnessLevel(profileData.fitness_level || 'medium')
        setGroupType(profileData.group_type || 'solo')
      }
      
      setAnalysis(analysisData.analysis)
    } catch (err) {
      console.error('Failed to load profile:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    setSaving(true)
    setMessage('')
    try {
      console.log('Saving profile with data:', {
        userId,
        interests,
        budget_level: budgetLevel,
        travel_style: travelStyle,
        fitness_level: fitnessLevel,
        group_type: groupType,
      })
      const result = await updateUserProfile(userId, {
        interests,
        budget_level: budgetLevel,
        travel_style: travelStyle,
        fitness_level: fitnessLevel,
        group_type: groupType,
      })
      console.log('Profile saved successfully:', result)
      setMessage('Profile saved successfully!')
      loadProfile()
    } catch (err) {
      console.error('Save profile error:', err)
      const errorMessage = err instanceof Error ? err.message : 'Failed to save profile'
      setMessage(errorMessage)
    } finally {
      setSaving(false)
    }
  }

  const toggleInterest = (key: string) => {
    setInterests(prev => 
      prev.includes(key) ? prev.filter(k => k !== key) : [...prev, key]
    )
  }

  if (loading) {
    return (
      <div className="page">
        <div className="loading">Loading profile...</div>
      </div>
    )
  }

  return (
    <div className="page">
      <header className="Header">
        <div className="logo-container">
          <Link to="/" className="logo-link">
            <span className="logo-icon">🗺️</span>
            <h1>Smart Tourism</h1>
          </Link>
        </div>
      </header>

      <main className="main profile-main">
        <div className="profile-container">
          <h2 className="profile-title">My Profile</h2>
          <p className="profile-desc">Customize your travel preferences for better recommendations</p>

          {message && (
            <div className={`message ${message.includes('success') ? 'success' : 'error'}`}>
              {message.includes('success') ? '✓ ' : '⚠️ '}
              {message}
            </div>
          )}

          {/* Stats */}
          <div className="stats-grid">
            <div className="stat-card">
              <span className="stat-icon">✈️</span>
              <span className="stat-value">{profile?.total_trips || 0}</span>
              <span className="stat-label">Trips</span>
            </div>
            <div className="stat-card">
              <span className="stat-icon">📍</span>
              <span className="stat-value">{profile?.total_pois_visited || 0}</span>
              <span className="stat-label">Places Visited</span>
            </div>
            <div className="stat-card">
              <span className="stat-icon">👀</span>
              <span className="stat-value">{analysis?.total_behaviors || 0}</span>
              <span className="stat-label">Activities</span>
            </div>
          </div>

          {/* Interests */}
          <section className="profile-section">
            <h3>Interests</h3>
            <p className="section-desc">What do you like to do when traveling?</p>
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
                  <span className="interest-desc">{item.desc}</span>
                </button>
              ))}
            </div>
          </section>

          {/* Budget */}
          <section className="profile-section">
            <h3>Budget Level</h3>
            <div className="option-grid">
              {BUDGETS.map((item) => (
                <button
                  key={item.key}
                  type="button"
                  className={`option-card ${budgetLevel === item.key ? 'active' : ''}`}
                  onClick={() => setBudgetLevel(item.key)}
                >
                  <span className="option-icon">{item.icon}</span>
                  <span className="option-label">{item.label}</span>
                  <span className="option-desc">{item.desc}</span>
                </button>
              ))}
            </div>
          </section>

          {/* Travel Style */}
          <section className="profile-section">
            <h3>Travel Style</h3>
            <div className="option-grid">
              {TRAVEL_STYLES.map((item) => (
                <button
                  key={item.key}
                  type="button"
                  className={`option-card ${travelStyle === item.key ? 'active' : ''}`}
                  onClick={() => setTravelStyle(item.key)}
                >
                  <span className="option-icon">{item.icon}</span>
                  <span className="option-label">{item.label}</span>
                  <span className="option-desc">{item.desc}</span>
                </button>
              ))}
            </div>
          </section>

          {/* Fitness Level */}
          <section className="profile-section">
            <h3>Physical Fitness</h3>
            <div className="option-grid">
              {FITNESS_LEVELS.map((item) => (
                <button
                  key={item.key}
                  type="button"
                  className={`option-card ${fitnessLevel === item.key ? 'active' : ''}`}
                  onClick={() => setFitnessLevel(item.key)}
                >
                  <span className="option-icon">{item.icon}</span>
                  <span className="option-label">{item.label}</span>
                  <span className="option-desc">{item.desc}</span>
                </button>
              ))}
            </div>
          </section>

          {/* Group Type */}
          <section className="profile-section">
            <h3>Traveling With</h3>
            <div className="option-grid">
              {GROUP_TYPES.map((item) => (
                <button
                  key={item.key}
                  type="button"
                  className={`option-card ${groupType === item.key ? 'active' : ''}`}
                  onClick={() => setGroupType(item.key)}
                >
                  <span className="option-icon">{item.icon}</span>
                  <span className="option-label">{item.label}</span>
                  <span className="option-desc">{item.desc}</span>
                </button>
              ))}
            </div>
          </section>

          {/* Save Button */}
          <div className="profile-actions">
            <button 
              className="btn-primary btn-save"
              onClick={handleSave}
              disabled={saving}
            >
              {saving ? 'Saving...' : 'Save Profile'}
            </button>
          </div>

          {/* Back Link */}
          <nav className="nav-links">
            <Link to="/">← Back to Home</Link>
            <Link to="/itineraries">My Trips →</Link>
          </nav>
        </div>
      </main>
    </div>
  )
}

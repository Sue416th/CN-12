// 开发时通过 Vite 代理到后端，避免 CORS
const BASE = '/api/v1/public'

export async function createItinerary(data: {
  user_id?: number
  city?: string
  start_date: string
  end_date: string
  budget_level?: string
  interests?: string[]
}) {
  const res = await fetch(`${BASE}/itineraries/pre_trip`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: data.user_id ?? 1,
      city: data.city ?? 'Hangzhou',
      start_date: data.start_date,
      end_date: data.end_date,
      budget_level: data.budget_level ?? 'medium',
      interests: data.interests ?? [],
    }),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function listItineraries(userId = 1) {
  const res = await fetch(`${BASE}/itineraries?user_id=${userId}`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function getItinerary(id: number, userId = 1) {
  const res = await fetch(`${BASE}/itineraries/${id}?user_id=${userId}`)
  if (!res.ok) {
    if (res.status === 404) return null
    throw new Error(await res.text())
  }
  return res.json()
}

export async function listPOIs() {
  const res = await fetch(`${BASE}/pois`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function deleteItinerary(id: number, userId = 1) {
  const res = await fetch(`${BASE}/itineraries/${id}?user_id=${userId}`, {
    method: 'DELETE',
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function getPOIRealtime(poiId: number) {
  const res = await fetch(`${BASE}/pois/${poiId}/realtime`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function getPOIHistory(poiId: number, days = 7) {
  const res = await fetch(`${BASE}/pois/${poiId}/history?days=${days}`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

// ============== User Profile APIs ==============

export interface UserProfile {
  id: number
  user_id: number
  interests: string[]
  budget_level: string
  travel_style: string
  group_type: string
  fitness_level: string
  cultural_preferences: Record<string, number>
  preferred_categories: string[]
  tags: string[]
  profile_vector_id?: string
  total_trips: number
  total_pois_visited: number
}

export async function getUserProfile(userId = 1): Promise<UserProfile | null> {
  const res = await fetch(`${BASE}/users/${userId}/profile`)
  if (!res.ok) {
    if (res.status === 404) return null
    throw new Error(await res.text())
  }
  return res.json()
}

export async function updateUserProfile(userId: number, data: Partial<UserProfile>) {
  const res = await fetch(`${BASE}/users/${userId}/profile`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, ...data }),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function getUserBehaviors(userId = 1, limit = 20) {
  const res = await fetch(`${BASE}/users/${userId}/behaviors?limit=${limit}`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function getUserAnalysis(userId = 1) {
  const res = await fetch(`${BASE}/users/${userId}/analysis`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function trackBehavior(
  userId: number,
  type: 'view' | 'visit' | 'rate' | 'bookmark' | 'feedback' | 'search',
  params: Record<string, unknown>
) {
  const res = await fetch(`${BASE}/users/${userId}/track/${type}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

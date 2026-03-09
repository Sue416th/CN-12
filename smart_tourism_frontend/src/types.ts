export interface ItineraryItem {
  poi_id: number
  poi_name?: string
  category?: string
  rating?: number
  address?: string
  start_time: string
  end_time: string
  note?: string
  location?: {
    lat: number
    lng: number
  }
  culture_info?: {
    dynasty?: string
    history?: string
    famous_poems?: string[]
    highlights?: string[]
  }
}

export interface ItineraryCreateRequest {
  user_id?: number
  city?: string
  start_date: string
  end_date: string
  budget_level?: string
  interests?: string[]
}

export interface WeatherDay {
  date?: string
  temp?: number
  tempMin?: number
  tempMax?: number
  weather?: string
  night_weather?: string
  wind?: string
}

export interface WeatherInfo {
  today?: WeatherDay
  tomorrow?: WeatherDay
  forecast?: WeatherDay[]
  source?: string
}

export interface ItineraryResponse {
  itinerary_id: number
  user_id: number
  name?: string
  city?: string
  weather_info?: WeatherInfo
  weather_advice?: string[]
  items: ItineraryItem[]
}

export interface ItineraryListItem {
  id: number
  user_id: number
  name?: string
  city?: string
  created_at?: string
}

export interface POI {
  id: number
  name: string
  city?: string
  category?: string
  description?: string
}

export interface POIRealtime {
  is_open: boolean
  open_status: string
  crowd_level: number
  crowd_text: string
  wait_time: number
  last_updated: string
}

export interface POIHistoryDay {
  date: string
  weekday: string
  crowd_level: number
  crowd_text: string
}

export interface POIHistory {
  historical: POIHistoryDay[]
  avg_crowd_level: number
  best_days: string[]
  best_time_advice: string
}

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

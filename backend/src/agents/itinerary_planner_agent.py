"""
Itinerary Planner Agent - Generate personalized travel itineraries with weather and POI info
"""
import json
import asyncio
import random
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional


class WeatherService:
    """Weather service using Open-Meteo API (free, no API key required)"""

    # City coordinates for weather
    CITY_COORDS = {
        "hangzhou": {"lat": 30.24, "lon": 120.15},
        "dali": {"lat": 25.59, "lon": 100.27},
        "beijing": {"lat": 39.90, "lon": 116.41},
        "xian": {"lat": 34.34, "lon": 108.94},
        "suzhou": {"lat": 31.30, "lon": 120.58},
        "chengdu": {"lat": 30.67, "lon": 104.07},
    }

    # Weather code mapping from Open-Meteo
    WEATHER_CODES = {
        0: "Clear",
        1: "Mainly Clear",
        2: "Partly Cloudy",
        3: "Overcast",
        45: "Foggy",
        48: "Foggy",
        51: "Light Drizzle",
        53: "Drizzle",
        55: "Heavy Drizzle",
        61: "Light Rain",
        63: "Rain",
        65: "Heavy Rain",
        71: "Light Snow",
        73: "Snow",
        75: "Heavy Snow",
        80: "Rain Showers",
        81: "Rain Showers",
        82: "Heavy Rain Showers",
        95: "Thunderstorm",
        96: "Thunderstorm",
        99: "Thunderstorm",
    }

    @staticmethod
    def get_weather(city: str, date: str) -> Dict[str, Any]:
        """Get real weather for a specific city and date"""
        city_lower = city.lower()

        # Check if city is supported
        if city_lower not in WeatherService.CITY_COORDS:
            return WeatherService._get_simulated_weather(city, date)

        coords = WeatherService.CITY_COORDS[city_lower]

        try:
            target_date = datetime.strptime(date, "%Y-%m-%d")
            today = datetime.now()
            days_ahead = (target_date.date() - today.date()).days

            if days_ahead < 0:
                return WeatherService._get_current_weather(coords)
            elif days_ahead <= 7:
                return WeatherService._get_forecast_weather(coords, days_ahead)
            else:
                return WeatherService._get_climate_weather(city_lower, target_date.month)

        except Exception as e:
            print(f"Weather API error: {e}, falling back to simulated")
            return WeatherService._get_simulated_weather(city, date)

    @staticmethod
    def _get_current_weather(coords: Dict) -> Dict[str, Any]:
        """Get current weather from Open-Meteo"""
        url = f"https://api.open-meteo.com/v1/forecast?latitude={coords['lat']}&longitude={coords['lon']}&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m"

        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                current = data.get("current", {})
                return {
                    "temp": round(current.get("temperature_2m", 20)),
                    "condition": WeatherService.WEATHER_CODES.get(current.get("weather_code", 0), "Clear"),
                    "humidity": round(current.get("relative_humidity_2m", 50)),
                    "wind": round(current.get("wind_speed_10m", 10)),
                    "source": "real-time"
                }
        except Exception as e:
            print(f"Current weather API error: {e}")

        return WeatherService._get_simulated_weather("unknown", datetime.now().strftime("%Y-%m-%d"))

    @staticmethod
    def _get_forecast_weather(coords: Dict, days_ahead: int) -> Dict[str, Any]:
        """Get weather forecast from Open-Meteo"""
        url = f"https://api.open-meteo.com/v1/forecast?latitude={coords['lat']}&longitude={coords['lon']}&daily=temperature_2m_max,temperature_2m_min,weather_code&forecast_days={days_ahead + 1}"

        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                daily = data.get("daily", {})

                temps_max = daily.get("temperature_2m_max", [20])
                temps_min = daily.get("temperature_2m_min", [15])
                weather_codes = daily.get("weather_code", [0])

                idx = min(days_ahead, len(temps_max) - 1)
                max_temp = temps_max[idx] if idx < len(temps_max) else 20
                min_temp = temps_min[idx] if idx < len(temps_min) else 15
                weather_code = weather_codes[idx] if idx < len(weather_codes) else 0

                return {
                    "temp": round((max_temp + min_temp) / 2),
                    "temp_max": round(max_temp),
                    "temp_min": round(min_temp),
                    "condition": WeatherService.WEATHER_CODES.get(weather_code, "Clear"),
                    "humidity": 55,
                    "wind": 12,
                    "source": "forecast"
                }
        except Exception as e:
            print(f"Forecast weather API error: {e}")

        return WeatherService._get_simulated_weather("unknown", datetime.now().strftime("%Y-%m-%d"))

    @staticmethod
    def _get_climate_weather(city: str, month: int) -> Dict[str, Any]:
        """Get typical weather for city and month (historical climate data)"""
        climate_data = {
            "hangzhou": {
                1: {"temp": 5, "condition": "Cloudy"}, 2: {"temp": 6, "condition": "Cloudy"},
                3: {"temp": 12, "condition": "Rainy"}, 4: {"temp": 18, "condition": "Cloudy"},
                5: {"temp": 23, "condition": "Cloudy"}, 6: {"temp": 27, "condition": "Rainy"},
                7: {"temp": 32, "condition": "Clear"}, 8: {"temp": 31, "condition": "Clear"},
                9: {"temp": 26, "condition": "Clear"}, 10: {"temp": 20, "condition": "Cloudy"},
                11: {"temp": 14, "condition": "Cloudy"}, 12: {"temp": 8, "condition": "Cloudy"},
            },
            "beijing": {
                1: {"temp": -2, "condition": "Clear"}, 2: {"temp": 1, "condition": "Clear"},
                3: {"temp": 8, "condition": "Cloudy"}, 4: {"temp": 15, "condition": "Clear"},
                5: {"temp": 21, "condition": "Clear"}, 6: {"temp": 26, "condition": "Clear"},
                7: {"temp": 28, "condition": "Rainy"}, 8: {"temp": 27, "condition": "Rainy"},
                9: {"temp": 22, "condition": "Clear"}, 10: {"temp": 14, "condition": "Clear"},
                11: {"temp": 6, "condition": "Clear"}, 12: {"temp": 0, "condition": "Clear"},
            },
            "dali": {
                1: {"temp": 8, "condition": "Clear"}, 2: {"temp": 10, "condition": "Clear"},
                3: {"temp": 14, "condition": "Clear"}, 4: {"temp": 17, "condition": "Clear"},
                5: {"temp": 20, "condition": "Clear"}, 6: {"temp": 21, "condition": "Rainy"},
                7: {"temp": 20, "condition": "Rainy"}, 8: {"temp": 20, "condition": "Rainy"},
                9: {"temp": 19, "condition": "Clear"}, 10: {"temp": 16, "condition": "Clear"},
                11: {"temp": 12, "condition": "Clear"}, 12: {"temp": 9, "condition": "Clear"},
            },
            "chengdu": {
                1: {"temp": 7, "condition": "Cloudy"}, 2: {"temp": 9, "condition": "Cloudy"},
                3: {"temp": 14, "condition": "Cloudy"}, 4: {"temp": 19, "condition": "Cloudy"},
                5: {"temp": 23, "condition": "Cloudy"}, 6: {"temp": 25, "condition": "Rainy"},
                7: {"temp": 27, "condition": "Rainy"}, 8: {"temp": 27, "condition": "Rainy"},
                9: {"temp": 23, "condition": "Cloudy"}, 10: {"temp": 18, "condition": "Cloudy"},
                11: {"temp": 13, "condition": "Cloudy"}, 12: {"temp": 8, "condition": "Cloudy"},
            },
            "xian": {
                1: {"temp": 1, "condition": "Clear"}, 2: {"temp": 4, "condition": "Clear"},
                3: {"temp": 10, "condition": "Cloudy"}, 4: {"temp": 16, "condition": "Cloudy"},
                5: {"temp": 21, "condition": "Clear"}, 6: {"temp": 27, "condition": "Clear"},
                7: {"temp": 29, "condition": "Rainy"}, 8: {"temp": 28, "condition": "Rainy"},
                9: {"temp": 23, "condition": "Clear"}, 10: {"temp": 16, "condition": "Clear"},
                11: {"temp": 9, "condition": "Clear"}, 12: {"temp": 3, "condition": "Clear"},
            },
            "suzhou": {
                1: {"temp": 4, "condition": "Cloudy"}, 2: {"temp": 6, "condition": "Cloudy"},
                3: {"temp": 11, "condition": "Rainy"}, 4: {"temp": 17, "condition": "Cloudy"},
                5: {"temp": 22, "condition": "Cloudy"}, 6: {"temp": 26, "condition": "Rainy"},
                7: {"temp": 31, "condition": "Clear"}, 8: {"temp": 30, "condition": "Clear"},
                9: {"temp": 25, "condition": "Clear"}, 10: {"temp": 19, "condition": "Cloudy"},
                11: {"temp": 13, "condition": "Cloudy"}, 12: {"temp": 7, "condition": "Cloudy"},
            },
        }

        city_data = climate_data.get(city, climate_data["beijing"])
        month_data = city_data.get(month, {"temp": 20, "condition": "Clear"})

        return {
            "temp": month_data["temp"],
            "condition": month_data["condition"],
            "humidity": 55,
            "wind": 12,
            "source": "climate"
        }

    @staticmethod
    def _get_simulated_weather(city: str, date: str) -> Dict[str, Any]:
        """Fallback: Generate simulated weather for unsupported cities or API failures"""
        WEATHER_CONDITIONS = [
            {"condition": "Sunny", "temp_range": (20, 30), "humidity": (40, 60), "wind": (5, 15)},
            {"condition": "Cloudy", "temp_range": (15, 25), "humidity": (50, 70), "wind": (10, 20)},
            {"condition": "Rainy", "temp_range": (15, 22), "humidity": (70, 90), "wind": (15, 25)},
            {"condition": "Partly Cloudy", "temp_range": (16, 26), "humidity": (45, 65), "wind": (8, 18)},
        ]

        date_hash = hash(f"{city}_{date}") % 1000
        weather_idx = date_hash % len(WEATHER_CONDITIONS)
        weather = WEATHER_CONDITIONS[weather_idx]

        temp = weather["temp_range"][0] + (date_hash % (weather["temp_range"][1] - weather["temp_range"][0]))
        humidity = weather["humidity"][0] + (date_hash % (weather["humidity"][1] - weather["humidity"][0]))
        wind = weather["wind"][0] + (date_hash % (weather["wind"][1] - weather["wind"][0]))

        return {
            "temp": temp,
            "condition": weather["condition"],
            "humidity": humidity,
            "wind": wind,
            "source": "simulated"
        }


class ItineraryPlannerAgent:
    """
    Itinerary Planner Agent - Generate personalized travel itineraries based on user profile
    Includes weather, crowd level, open status, and travel recommendations
    """

    # Sample POI database with detailed info
    SAMPLE_POIS = {
        "hangzhou": [
            {"name": "West Lake", "category": "nature", "time_needed": 3, "price_level": 0, "fitness": "low", "open_hours": "24h", "crowd_tip": "Best early morning or evening"},
            {"name": "Leifeng Pagoda", "category": "culture", "time_needed": 2, "price_level": 1, "fitness": "medium", "open_hours": "08:00-17:30", "crowd_tip": "Avoid weekends"},
            {"name": "Xixi Wetland", "category": "nature", "time_needed": 4, "price_level": 1, "fitness": "medium", "open_hours": "07:30-18:00", "crowd_tip": "Weekdays are better"},
            {"name": "Lingyin Temple", "category": "religion", "time_needed": 2, "price_level": 1, "fitness": "low", "open_hours": "07:00-18:00", "crowd_tip": "Arrive before 9am"},
            {"name": "Hefang Street", "category": "food", "time_needed": 2, "price_level": 1, "fitness": "low", "open_hours": "全天", "crowd_tip": "Evening is lively"},
            {"name": "Zhejiang Museum", "category": "culture", "time_needed": 2, "price_level": 0, "fitness": "low", "open_hours": "09:00-17:00", "crowd_tip": "Free admission"},
            {"name": "Qinghefang Street", "category": "shopping", "time_needed": 2, "price_level": 1, "fitness": "low", "open_hours": "全天", "crowd_tip": "Great for souvenirs"},
            {"name": "Longjing Tea Plantation", "category": "nature", "time_needed": 3, "price_level": 0, "fitness": "medium", "open_hours": "全天", "crowd_tip": "Best in spring"},
            {"name": "China Tea Museum", "category": "culture", "time_needed": 2, "price_level": 0, "fitness": "low", "open_hours": "09:00-16:30", "crowd_tip": "Very peaceful"},
            {"name": "Song Town", "category": "entertainment", "time_needed": 3, "price_level": 2, "fitness": "low", "open_hours": "09:00-22:00", "crowd_tip": "Night shows are great"},
        ],
        "dali": [
            {"name": "Dali Ancient Town", "category": "culture", "time_needed": 3, "price_level": 0, "fitness": "low", "open_hours": "24h", "crowd_tip": "Explore at night"},
            {"name": "Three Pagodas", "category": "culture", "time_needed": 2, "price_level": 1, "fitness": "medium", "open_hours": "08:00-18:00", "crowd_tip": "Morning is best"},
            {"name": "Erhai Lake", "category": "nature", "time_needed": 4, "price_level": 1, "fitness": "low", "open_hours": "全天", "crowd_tip": "Sunset cruise recommended"},
            {"name": "Shuanglang Old Town", "category": "culture", "time_needed": 2, "price_level": 0, "fitness": "low", "open_hours": "全天", "crowd_tip": "Photography paradise"},
            {"name": "Cangshan Mountain", "category": "nature", "time_needed": 5, "price_level": 0, "fitness": "high", "open_hours": "全天", "crowd_tip": "For adventure seekers"},
            {"name": "Dali Town", "category": "food", "time_needed": 2, "price_level": 1, "fitness": "low", "open_hours": "全天", "crowd_tip": "Try local cuisine"},
        ],
        "beijing": [
            {"name": "Forbidden City", "category": "culture", "time_needed": 4, "price_level": 1, "fitness": "medium", "open_hours": "08:30-17:00", "crowd_tip": "Book tickets in advance"},
            {"name": "Great Wall", "category": "culture", "time_needed": 4, "price_level": 1, "fitness": "high", "open_hours": "07:00-18:00", "crowd_tip": "Badaling is crowded"},
            {"name": "Temple of Heaven", "category": "religion", "time_needed": 2, "price_level": 0, "fitness": "low", "open_hours": "06:00-20:00", "crowd_tip": "Morning exercise locals"},
            {"name": "Summer Palace", "category": "nature", "time_needed": 4, "price_level": 1, "fitness": "medium", "open_hours": "06:30-18:00", "crowd_tip": "Large area, arrive early"},
            {"name": "Wangfujing Street", "category": "food", "time_needed": 2, "price_level": 1, "fitness": "low", "open_hours": "全天", "crowd_tip": "Night market is great"},
        ],
        "xian": [
            {"name": "Terracotta Warriors", "category": "culture", "time_needed": 3, "price_level": 1, "fitness": "low", "open_hours": "08:30-18:00", "crowd_tip": "Afternoon is better"},
            {"name": "City Wall", "category": "culture", "time_needed": 3, "price_level": 1, "fitness": "medium", "open_hours": "08:00-21:00", "crowd_tip": "Bike rental available"},
            {"name": "Bell Tower", "category": "culture", "time_needed": 1, "price_level": 1, "fitness": "low", "open_hours": "08:30-20:00", "crowd_tip": "Night view is beautiful"},
            {"name": "Muslim Quarter", "category": "food", "time_needed": 2, "price_level": 1, "fitness": "low", "open_hours": "全天", "crowd_tip": "Street food heaven"},
        ],
        "suzhou": [
            {"name": "Humble Administrator's Garden", "category": "culture", "time_needed": 2, "price_level": 1, "fitness": "low", "open_hours": "07:30-17:30", "crowd_tip": "World heritage site"},
            {"name": "Tiger Hill", "category": "culture", "time_needed": 2, "price_level": 1, "fitness": "medium", "open_hours": "07:30-18:00", "crowd_tip": "Historical site"},
            {"name": "Pingjiang Road", "category": "food", "time_needed": 2, "price_level": 0, "fitness": "low", "open_hours": "全天", "crowd_tip": "Ancient water town"},
        ],
        "chengdu": [
            {"name": "Chengdu Research Base of Giant Panda Breeding", "category": "nature", "time_needed": 3, "price_level": 1, "fitness": "low", "open_hours": "07:30-18:00", "crowd_tip": "Morning feeding time"},
            {"name": "Jinli Street", "category": "food", "time_needed": 2, "price_level": 0, "fitness": "low", "open_hours": "全天", "crowd_tip": "Try Sichuan snacks"},
            {"name": "Wenshu Monastery", "category": "religion", "time_needed": 2, "price_level": 0, "fitness": "low", "open_hours": "09:00-17:00", "crowd_tip": "Peaceful temple"},
            {"name": "People's Park", "category": "nature", "time_needed": 2, "price_level": 0, "fitness": "low", "open_hours": "全天", "crowd_tip": "Local life experience"},
        ],
    }

    # Weather conditions (simulated)
    WEATHER_CONDITIONS = [
        {"condition": "Sunny", "temp_range": (18, 28), "humidity": (40, 60), "wind": (5, 15)},
        {"condition": "Cloudy", "temp_range": (15, 25), "humidity": (50, 70), "wind": (10, 20)},
        {"condition": "Light Rain", "temp_range": (12, 20), "humidity": (70, 90), "wind": (15, 25)},
        {"condition": "Partly Cloudy", "temp_range": (16, 26), "humidity": (45, 65), "wind": (8, 18)},
    ]

    # City coordinates for weather
    CITY_COORDS = {
        "hangzhou": {"lat": 30.24, "lon": 120.15},
        "dali": {"lat": 25.59, "lon": 100.27},
        "beijing": {"lat": 39.90, "lon": 116.41},
        "xian": {"lat": 34.34, "lon": 108.94},
        "suzhou": {"lat": 31.30, "lon": 120.58},
        "chengdu": {"lat": 30.67, "lon": 104.07},
    }

    def __init__(self):
        pass

    def _get_weather_for_date(self, city: str, date: str) -> Dict[str, Any]:
        """Get real weather for a specific city and date using WeatherService"""
        try:
            return WeatherService.get_weather(city, date)
        except Exception as e:
            print(f"Weather service error: {e}, using simulated weather")
            return self._get_simulated_weather_fallback(city, date)

    def _get_simulated_weather_fallback(self, city: str, date: str) -> Dict[str, Any]:
        """Generate simulated weather (fallback)"""
        date_hash = hash(f"{city}_{date}") % 1000
        weather_idx = date_hash % len(self.WEATHER_CONDITIONS)
        weather = self.WEATHER_CONDITIONS[weather_idx]

        temp = weather["temp_range"][0] + (date_hash % (weather["temp_range"][1] - weather["temp_range"][0]))
        humidity = weather["humidity"][0] + (date_hash % (weather["humidity"][1] - weather["humidity"][0]))
        wind = weather["wind"][0] + (date_hash % (weather["wind"][1] - weather["wind"][0]))

        return {
            "temp": temp,
            "condition": weather["condition"],
            "humidity": humidity,
            "wind": wind,
            "source": "simulated"
        }

    def _get_crowd_level(self, activity_name: str, day_of_week: int) -> str:
        """Calculate crowd level based on activity and day"""
        # Popular activities are more crowded on weekends
        popular_activities = ["West Lake", "Forbidden City", "Great Wall", "Terracotta Warriors"]
        if activity_name in popular_activities:
            if day_of_week >= 5:  # Weekend
                return "high"
            return "medium"
        return "low"

    def _is_open(self, activity_name: str, current_hour: int) -> bool:
        """Check if attraction is open at given hour"""
        # Most attractions open 8am-6pm
        return 8 <= current_hour <= 18

    def _generate_tips(self, weather: Dict, activity: Dict, crowd_level: str) -> List[str]:
        """Generate travel tips based on weather, activity, and crowd"""
        tips = []

        # Weather-based tips
        condition = weather.get("condition", "Sunny")
        temp = weather.get("temp", 20)

        if "Rain" in condition:
            tips.append("🌧️ Rain expected - bring an umbrella and waterproof jacket")
        elif temp > 25:
            tips.append("☀️ Hot weather - stay hydrated and wear sunscreen")
        elif temp < 15:
            tips.append("🧥 Cool weather - bring a jacket")
        if weather.get("wind", 0) > 20:
            tips.append("💨 Strong winds - be careful near water")

        # Activity-based tips
        if activity.get("crowd_tip"):
            tips.append(f"💡 {activity['crowd_tip']}")
        if activity.get("open_hours"):
            tips.append(f"🕐 Open: {activity['open_hours']}")

        # Crowd-based tips
        if crowd_level == "high":
            tips.append("⚠️ High crowd - consider visiting early or at closing time")
        elif crowd_level == "low":
            tips.append("✅ Great time to visit - fewer crowds!")

        return tips[:2]  # Return max 2 tips

    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate personalized itinerary based on user profile"""
        user_id = context.get("user_id", 1)
        city = context.get("city", "hangzhou").lower()
        start_date = context.get("start_date")
        days = context.get("days", 3)

        # Get user profile from context
        refined_interests = context.get("refined_interests", context.get("interests", []))
        profile_info = context.get("profile_info", {})
        fitness_info = profile_info.get("fitness_info", {})
        budget_info = profile_info.get("budget_info", {})
        cultural_preferences = profile_info.get("cultural_preferences", {})
        preferred_categories = profile_info.get("preferred_categories", [])

        fitness_level = fitness_info.get("label", "Moderate").lower()
        budget_level = budget_info.get("label", "Comfort").lower()

        # Generate itinerary
        itinerary = self._generate_itinerary(
            city=city,
            days=days,
            interests=refined_interests,
            preferred_categories=preferred_categories,
            fitness_level=fitness_level,
            budget_level=budget_level,
            cultural_preferences=cultural_preferences,
            start_date=start_date,
        )

        context["itinerary"] = itinerary
        context["itinerary_id"] = f"trip_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        return context

    def _generate_itinerary(
        self,
        city: str,
        days: int,
        interests: List[str],
        preferred_categories: List[str],
        fitness_level: str,
        budget_level: str,
        cultural_preferences: Dict[str, float],
        start_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate daily itinerary with weather and POI info"""
        pois = self.SAMPLE_POIS.get(city, self.SAMPLE_POIS.get("default", []))

        filtered_pois = self._filter_pois(
            pois,
            interests,
            preferred_categories,
            fitness_level,
            budget_level
        )

        daily_plans = []
        for day in range(1, days + 1):
            # Calculate date
            date = None
            if start_date:
                try:
                    start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    date = (start + timedelta(days=day-1)).strftime('%Y-%m-%d')
                except:
                    date = f"Day {day}"
            else:
                date = f"Day {day}"

            # Get weather for this date
            weather = self._get_weather_for_date(city, date)

            # Get day of week for crowd calculation
            try:
                day_of_week = datetime.fromisoformat(date).weekday()
            except:
                day_of_week = random.randint(0, 6)

            day_plan = self._create_day_plan(
                day_num=day,
                date=date,
                available_pois=filtered_pois,
                fitness_level=fitness_level,
                budget_level=budget_level,
                weather=weather,
                day_of_week=day_of_week,
            )
            daily_plans.append(day_plan)

        return {
            "city": city,
            "total_days": days,
            "start_date": start_date,
            "days": daily_plans,
            "interests": interests,
            "budget_level": budget_level,
            "fitness_level": fitness_level,
            "generated_at": datetime.now().isoformat(),
        }

    def _filter_pois(
        self,
        pois: List[Dict],
        interests: List[str],
        preferred_categories: List[str],
        fitness_level: str,
        budget_level: str,
    ) -> List[Dict]:
        """Filter POIs based on user preferences"""
        filtered = []

        fitness_map = {"light": 0, "moderate": 1, "active": 2}
        user_fitness = fitness_map.get(fitness_level, 1)

        budget_map = {"budget": 0, "comfort": 1, "luxury": 2}
        max_price = budget_map.get(budget_level, 1)

        interests_lower = [i.lower() for i in interests]

        for poi in pois:
            if poi.get("price_level", 0) > max_price:
                continue

            poi_fitness = fitness_map.get(poi.get("fitness", "medium"), 1)
            if poi_fitness > user_fitness:
                continue

            category = poi.get("category", "")
            interest_score = 0
            if category in interests_lower:
                interest_score = 1.0
            elif any(cat in category for cat in interests_lower):
                interest_score = 0.7
            elif category in preferred_categories:
                interest_score = 0.5

            poi["interest_score"] = interest_score
            filtered.append(poi)

        filtered.sort(key=lambda x: x.get("interest_score", 0), reverse=True)
        return filtered

    def _create_day_plan(
        self,
        day_num: int,
        date: str,
        available_pois: List[Dict],
        fitness_level: str,
        budget_level: str,
        weather: Dict,
        day_of_week: int,
    ) -> Dict[str, Any]:
        """Create a single day's plan with all details"""
        fitness_activities = {"light": 2, "moderate": 3, "active": 4}
        num_activities = fitness_activities.get(fitness_level, 3)

        selected = []
        used_names = set()

        for poi in available_pois:
            if len(selected) >= num_activities:
                break
            if poi["name"] not in used_names:
                # Get crowd level and open status
                crowd_level = self._get_crowd_level(poi["name"], day_of_week)
                current_hour = datetime.now().hour
                open_status = "Open" if self._is_open(poi["name"], current_hour) else "Closed"

                # Generate tips
                tips_list = self._generate_tips(weather, poi, crowd_level)
                tips = " | ".join(tips_list) if tips_list else poi.get("crowd_tip", "")

                activity = {
                    "name": poi["name"],
                    "category": poi.get("category", "other"),
                    "time_needed": poi.get("time_needed", 2),
                    "price_level": poi.get("price_level", 0),
                    "tips": tips,
                    "crowd_level": crowd_level,
                    "open_status": open_status,
                    "open_hours": poi.get("open_hours", ""),
                }
                selected.append(activity)
                used_names.add(poi["name"])

        # Add free time if needed
        if len(selected) < num_activities:
            remaining = num_activities - len(selected)
            for i in range(remaining):
                tips_list = self._generate_tips(weather, {"crowd_tip": "Free time"}, "low")
                tips = " | ".join(tips_list) if tips_list else "Enjoy your free time!"
                selected.append({
                    "name": f"Free Time - {['Relax', 'Explore', 'Local Experience'][i]}",
                    "category": "free",
                    "time_needed": 2,
                    "price_level": 0,
                    "tips": tips,
                    "crowd_level": "low",
                    "open_status": "Open",
                    "open_hours": "",
                })

        total_hours = sum(a["time_needed"] for a in selected)

        # Generate weather-based travel advice for the day
        travel_advice = self._generate_travel_advice(weather, selected)

        return {
            "day": day_num,
            "date": date,
            "activities": selected,
            "total_hours": total_hours,
            "budget_estimate": sum(a["price_level"] for a in selected),
            "weather": weather,
            "travel_advice": travel_advice,
        }

    def _generate_travel_advice(self, weather: Dict, activities: List[Dict]) -> List[str]:
        """Generate overall travel advice for the day"""
        advice = []

        temp = weather.get("temp", 20)
        condition = weather.get("condition", "Sunny")

        # Temperature advice
        if temp > 28:
            advice.append("🌡️ High temperature today - stay hydrated and take breaks in AC")
        elif temp < 10:
            advice.append("🧥 Cold weather - dress warmly in layers")

        # Weather condition advice
        if "Rain" in condition:
            advice.append("🌧️ Rainy day - indoor activities recommended, bring umbrella")
        if "Sunny" in condition and temp > 25:
            advice.append("☀️ Sunny and warm - sunscreen and hat recommended")

        # Activity-based advice
        outdoor_count = sum(1 for a in activities if a.get("category") in ["nature", "culture"])
        if outdoor_count > 2:
            advice.append("🏃 Many outdoor activities - wear comfortable shoes")

        # Crowd advice
        high_crowd = sum(1 for a in activities if a.get("crowd_level") == "high")
        if high_crowd > 0:
            advice.append("⚠️ Some popular spots may be crowded - consider alternative times")

        return advice[:3]  # Return max 3 tips

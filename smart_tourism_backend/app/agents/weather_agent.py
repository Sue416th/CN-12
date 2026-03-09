from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from app.agents.base_agent import BaseAgent
from app.services.external_api import weather_api


class WeatherAgent(BaseAgent):
    """
    天气信息Agent - 考虑实时天气因素
    1. 获取目的地天气信息（真实API）
    2. 根据天气调整行程安排
    3. 提供出行建议
    """

    def __init__(self):
        super().__init__(name="weather")

    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        itinerary = context.get("itinerary", {})
        city = context.get("city", itinerary.get("city", "Hangzhou"))
        items = itinerary.get("items", [])

        # 获取行程的开始日期 - 从多个可能的来源读取
        start_date = None
        # 1. 从 context 顶层
        if not start_date:
            start_date = context.get("start_date")
        # 2. 从 constraints
        if not start_date:
            constraints = context.get("constraints", {})
            start_date = constraints.get("start_date")
        # 3. 从 itinerary
        if not start_date:
            start_date = itinerary.get("start_date")

        if start_date:
            try:
                start = datetime.strptime(str(start_date), "%Y-%m-%d")
            except:
                start = datetime.now()
        else:
            start = datetime.now()

        # 计算行程天数
        if items:
            dates = []
            for item in items:
                start_time_str = str(item.get("start_time", ""))
                # 支持两种格式: "2026-03-10T09:00:00" 或 "2026-03-10 09:00:00"
                for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]:
                    try:
                        dates.append(datetime.strptime(start_time_str, fmt))
                        break
                    except:
                        continue
            if dates:
                trip_days = (max(dates) - min(dates)).days + 1
            else:
                trip_days = 3
        else:
            trip_days = 3

        # 调用真实天气API，获取足够天数的预报
        # 高德API最多返回4天预报，增加请求天数
        weather_info = await weather_api.get_weather(city, days=7)

        # 根据开始日期重新组织天气数据
        weather_info = self._align_weather_with_dates(weather_info, start)

        # 获取profile信息用于个性化建议
        profile_info = context.get("profile_info", {})

        weather_advice = self._generate_advice(weather_info, items, profile_info)

        itinerary["weather_info"] = weather_info
        itinerary["weather_advice"] = weather_advice
        itinerary["start_date"] = start.strftime("%Y-%m-%d")

        adjusted_items = self._adjust_for_weather(items, weather_info, profile_info)
        itinerary["items"] = adjusted_items

        context["itinerary"] = itinerary
        return context

    def _align_weather_with_dates(self, weather: Dict[str, Any], start_date: datetime) -> Dict[str, Any]:
        """根据行程开始日期重新对齐天气数据"""
        today = datetime.now().date()
        start = start_date.date()
        day_diff = (start - today).days

        forecast = weather.get("forecast", [])
        if not forecast:
            return weather

        if day_diff <= 0:
            # 行程开始日期是今天或之前，使用原预报
            return weather

        # 行程开始日期是未来，需要从预报中跳过前面的天数
        # 如果行程日期超出预报范围，使用最后一天的天气
        if day_diff >= len(forecast):
            # 行程日期太远，使用最后一天的天气填充所有天数
            last_day = forecast[-1] if forecast else {}
            aligned_forecast = []
            for i in range(len(forecast)):
                day_date = start + timedelta(days=i)
                day_weather = dict(last_day)
                day_weather["date"] = day_date.strftime("%Y-%m-%d")
                day_weather["day_index"] = i
                aligned_forecast.append(day_weather)
        else:
            # 从正确的日期开始
            aligned_forecast = []
            for i, day_weather in enumerate(forecast[day_diff:]):
                day_date = start + timedelta(days=i)
                day_weather = dict(day_weather)
                day_weather["date"] = day_date.strftime("%Y-%m-%d")
                day_weather["day_index"] = i
                aligned_forecast.append(day_weather)

        # 找到行程第一天的天气
        first_day_weather = aligned_forecast[0] if aligned_forecast else {}

        weather["forecast"] = aligned_forecast
        weather["today"] = first_day_weather
        if len(aligned_forecast) > 1:
            weather["tomorrow"] = aligned_forecast[1]

        return weather

    def _generate_advice(self, weather: Dict[str, Any], items: List[Dict], profile_info: Dict = None) -> List[str]:
        """Generate weather travel advice based on weather and user profile"""
        advice = []
        today_weather = weather.get("today", {})
        temp = today_weather.get("temp", 20)
        weather_type = today_weather.get("weather", "Sunny")

        # Basic temperature advice
        if temp < 10:
            advice.append("Temperature is low, please bring warm clothing")
        elif temp > 28:
            advice.append("Temperature is high, please stay cool")

        # Weather condition advice
        if "雨" in weather_type or "rain" in weather_type.lower():
            advice.append("Rain expected today, please bring umbrella. Consider indoor activities.")
        elif "雪" in weather_type or "snow" in weather_type.lower():
            advice.append("Snow expected today, please watch for slippery roads")

        # Air quality advice
        aqi = today_weather.get("aqi", "Good")
        if aqi == "优" or aqi == "Good" or aqi == "Excellent":
            advice.append("Excellent air quality, great for outdoor activities")
        elif "污染" in aqi or "pollution" in aqi.lower() or aqi in ["Light", "Moderate", "Heavy"]:
            advice.append(f"Air quality: {aqi}, recommend wearing mask")

        # Profile-based advice
        if profile_info:
            fitness_info = profile_info.get("fitness_info", {})
            
            # Weather-sensitive advice for low fitness users
            if fitness_info.get("needs_rest_stops"):
                if temp > 25 or temp < 10:
                    advice.append("Take breaks during extreme temperatures")

            # Outdoor preference
            cultural_prefs = profile_info.get("cultural_preferences", {})
            if cultural_prefs.get("nature", 0) > 0.7:
                if "雨" not in weather_type and "rain" not in weather_type.lower():
                    advice.append("Great weather for outdoor scenic spots!")

        if not advice:
            advice.append("Good weather, perfect for travel")

        return advice

    def _adjust_for_weather(
        self, items: List[Dict], weather: Dict[str, Any], profile_info: Dict = None
    ) -> List[Dict]:
        """Adjust itinerary based on weather and user profile"""
        today_weather = weather.get("today", {}).get("weather", "Sunny")

        if "雨" in today_weather or "rain" in today_weather.lower() or "雪" in today_weather or "snow" in today_weather.lower():
            adjusted = []
            for item in items:
                category = item.get("category", "")
                
                # Check if outdoor POI - add alert
                if category in ["nature", "entertainment"]:
                    # Check if user prefers outdoor based on profile
                    is_outdoor_friendly = True
                    if profile_info:
                        cultural_prefs = profile_info.get("cultural_preferences", {})
                        # If user strongly prefers nature, suggest still going
                        if cultural_prefs.get("nature", 0) > 0.7:
                            item["weather_alert"] = "Rain expected but great for nature lovers!"
                        else:
                            item["weather_alert"] = "Weather not ideal, consider indoor activities"
                    else:
                        item["weather_alert"] = "Weather not ideal, consider indoor activities"
                adjusted.append(item)
            return adjusted

        return items

    async def get_weather_forecast(self, city: str = "Hangzhou", days: int = 3) -> List[Dict[str, Any]]:
        """获取多日天气预报"""
        weather = await weather_api.get_weather(city)
        forecast = []
        if days >= 1:
            forecast.append(weather.get("today", {}))
        if days >= 2:
            forecast.append(weather.get("tomorrow", {}))
        return forecast

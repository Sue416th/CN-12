"""
外部API服务 - 天气、地图等
"""
import httpx
from typing import Any, Dict, Optional
from app.config import settings


class WeatherAPI:
    """和风天气API / 高德地图天气"""

    # 中文到英文的天气映射
    WEATHER_MAP = {
        # 晴天
        "晴": "Sunny",
        "晴天": "Sunny",
        # 多云
        "多云": "Cloudy",
        "阴": "Overcast",
        # 雨
        "小雨": "Light Rain",
        "中雨": "Moderate Rain",
        "大雨": "Heavy Rain",
        "暴雨": "Rainstorm",
        "雷阵雨": "Thunderstorm",
        "阵雨": "Showers",
        "冻雨": "Freezing Rain",
        # 雪
        "小雪": "Light Snow",
        "中雪": "Moderate Snow",
        "大雪": "Heavy Snow",
        "暴雪": "Snowstorm",
        "雨夹雪": "Sleet",
        "阵雪": "Snow Showers",
        # 其他
        "雾": "Fog",
        "霾": "Haze",
        "沙尘暴": "Sandstorm",
        "扬沙": "Dust",
        "浮尘": "Dusty",
        "雾霾": "Haze",
    }

    # 风向翻译
    WIND_DIRECTION_MAP = {
        "北风": "N",
        "东北风": "NE",
        "东风": "E",
        "东南风": "SE",
        "南风": "S",
        "西南风": "SW",
        "西风": "W",
        "西北风": "NW",
        "微风": "Light Breeze",
        "无风": "Calm",
    }

    def __init__(self):
        self.api_key = settings.QWEATHER_API_KEY
        self.host = settings.QWEATHER_API_HOST
        self.amap_key = settings.AMAP_API_KEY

    def _translate_weather(self, weather: str) -> str:
        """将中文天气翻译成英文"""
        if not weather:
            return "Unknown"
        return self.WEATHER_MAP.get(weather, weather)

    def _translate_wind(self, wind: str) -> str:
        """将中文风向翻译成英文"""
        if not wind:
            return "Light Breeze"
        # 翻译已知风向
        for cn, en in self.WIND_DIRECTION_MAP.items():
            wind = wind.replace(cn, en)
        # 清理剩余的中文字符
        wind = wind.replace("风", " ")
        # 移除任何残留的中文字符
        import re
        wind = re.sub(r'[\u4e00-\u9fff]+', '', wind)
        # 清理多余的空格
        wind = ' '.join(wind.split())
        return wind if wind.strip() else "Light Breeze"

    def _translate_aqi(self, aqi: str) -> str:
        """将中文AQI翻译成英文"""
        if not aqi:
            return "Good"
        aqi_map = {
            "优": "Excellent",
            "良": "Good",
            "轻度污染": "Light Pollution",
            "中度污染": "Moderate Pollution",
            "重度污染": "Heavy Pollution",
            "严重污染": "Severe Pollution",
        }
        return aqi_map.get(aqi, aqi)

    async def get_weather(self, city: str = "hangzhou", days: int = 3) -> Dict[str, Any]:
        """
        获取实时天气和预报
        city: 城市名、城市ID或城市拼音
        days: 预报天数（1=今天+明天，2=今天+明天+后天，最多4天）
        """
        # 城市名映射到和风天气城市ID
        city_map = {
            "杭州": "101210101",
            "上海": "101020100",
            "北京": "101010100",
            "苏州": "101190401",
            "南京": "101190101",
            "宁波": "101210501",
            "温州": "101210801",
            "绍兴": "101210401",
            "嘉兴": "101210201",
            "湖州": "101210601",
        }
        location = city_map.get(city, city)

        # 优先尝试高德地图天气（API Key已配置）
        if self.amap_key and self.amap_key != "your_amap_api_key_here":
            amap_weather = await self._get_amap_weather(city, days=days)
            if amap_weather:
                return amap_weather

        # 备选：尝试和风天气（如果配置了API Key）
        # 注意：和风天气API暂时不可用，使用模拟数据

        # 最后使用模拟数据
        return self._get_mock_weather(city)

    async def _get_amap_weather(self, city: str, days: int = 3) -> Optional[Dict[str, Any]]:
        """使用高德地图API获取天气"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # 获取实时天气
                url = "https://restapi.amap.com/v3/weather/weatherInfo"
                params = {
                    "key": self.amap_key,
                    "city": self._get_amap_city_code(city),
                }
                resp = await client.get(url, params=params)
                data = resp.json() if resp.status_code == 200 else {}

                result = {
                    "today": {},
                    "tomorrow": {},
                    "source": "amap"
                }

                if data.get("status") == "1" and data.get("lives"):
                    live = data["lives"][0]
                    weather_cn = live.get("weather", "Sunny")
                    wind_cn = f"{live.get('winddirection', '')}风{live.get('windpower', '')}级"
                    result["today"] = {
                        "temp": int(float(live.get("temperature", 20))),
                        "weather": self._translate_weather(weather_cn),
                        "wind": self._translate_wind(wind_cn),
                        "aqi": self._translate_aqi(live.get("aqi", "良")),
                        "humidity": live.get("humidity", "50%"),
                    }

                # 获取天气预报 - 使用 extensions=all 获取多日预报
                forecast_params = {
                    "key": self.amap_key,
                    "city": self._get_amap_city_code(city),
                    "extensions": "all",
                }
                forecast_resp = await client.get(url, params=forecast_params)
                forecast_data = forecast_resp.json() if forecast_resp.status_code == 200 else {}

                if forecast_data.get("status") == "1" and forecast_data.get("forecasts"):
                    forecast_list = forecast_data["forecasts"]
                    if forecast_list and len(forecast_list) > 0:
                        casts = forecast_list[0].get("casts", [])
                        # casts[0] 是今天，[1] 是明天，[2] 是后天...
                        # 构建 forecast 列表
                        result["forecast"] = []
                        for i in range(min(days, len(casts))):
                            day = casts[i]
                            day_weather = {
                                "date": day.get("date", ""),
                                "temp": int((int(day.get("daytemp", 20)) + int(day.get("nighttemp", 15))) / 2),
                                "tempMin": int(day.get("nighttemp", 15)),
                                "tempMax": int(day.get("daytemp", 25)),
                                "weather": self._translate_weather(day.get("dayweather", "Sunny")),
                                "night_weather": self._translate_weather(day.get("nightweather", "Cloudy")),
                                "wind": self._translate_wind(day.get("daywind", "Light Breeze")),
                            }
                            if i == 0:
                                result["today"] = day_weather
                            elif i == 1:
                                result["tomorrow"] = day_weather
                            result["forecast"].append(day_weather)

                return result
        except Exception as e:
            print(f"高德天气API失败: {e}")
        return None

    def _get_amap_city_code(self, city: str) -> str:
        """城市名转高德城市编码"""
        amap_city_map = {
            "杭州": "330100",
            "上海": "310000",
            "北京": "110000",
            "天津": "120000",
            "重庆": "500000",
            "苏州": "320500",
            "南京": "320100",
            "宁波": "330200",
            "温州": "330300",
            "嘉兴": "330400",
            "湖州": "330500",
            "绍兴": "330600",
            "金华": "330700",
            "衢州": "330800",
            "舟山": "330900",
            "台州": "331000",
            "丽水": "331100",
            "深圳": "440300",
            "广州": "440100",
            "成都": "510100",
            "西安": "610100",
            "武汉": "420100",
            "长沙": "430100",
            "郑州": "410100",
            "青岛": "370200",
            "济南": "370100",
            "厦门": "350200",
            "福州": "350100",
            "昆明": "530100",
            "贵阳": "520100",
            "南昌": "360100",
            "合肥": "340100",
            "石家庄": "130100",
            "哈尔滨": "230100",
            "长春": "220100",
            "沈阳": "210100",
            "大连": "210200",
            "呼和浩特": "150100",
            "太原": "140100",
            "兰州": "620100",
            "银川": "640100",
            "西宁": "630100",
            "乌鲁木齐": "650100",
            "拉萨": "540100",
            "三亚": "460200",
            "海口": "460100",
            "东莞": "441900",
            "佛山": "440600",
            "无锡": "320200",
            "常州": "320400",
            "徐州": "320300",
            "南通": "320600",
            "扬州": "321000",
            "盐城": "320900",
            "淮安": "320800",
            "连云港": "320700",
            "泰州": "321200",
            "镇江": "321100",
            "宿迁": "321300",
            "温州": "330300",
            "芜湖": "340200",
            "蚌埠": "340300",
            "淮南": "340400",
            "马鞍山": "340500",
            "淮北": "340600",
            "铜陵": "340700",
            "安庆": "340800",
            "黄山": "341000",
            "滁州": "341100",
            "阜阳": "341200",
            "宿州": "341300",
            "六安": "341500",
            "亳州": "341600",
            "池州": "341700",
            "宣城": "341800",
            "莆田": "350300",
            "三明": "350400",
            "泉州": "350500",
            "漳州": "350600",
            "南平": "350700",
            "龙岩": "350800",
            "宁德": "350900",
            "景德镇": "360200",
            "萍乡": "360300",
            "九江": "360400",
            "新余": "360500",
            "鹰潭": "360600",
            "赣州": "360700",
            "吉安": "360800",
            "宜春": "360900",
            "抚州": "361000",
            "上饶": "361100",
            "烟台": "370600",
            "潍坊": "370700",
            "威海": "371000",
            "淄博": "370300",
            "临沂": "371300",
            "枣庄": "370400",
            "日照": "371100",
            "德州": "371400",
            "聊城": "371500",
            "滨州": "371600",
            "菏泽": "371700",
            "开封": "410200",
            "洛阳": "410300",
            "平顶山": "410400",
            "安阳": "410500",
            "鹤壁": "410600",
            "新乡": "410700",
            "焦作": "410800",
            "濮阳": "410900",
            "许昌": "411000",
            "漯河": "411100",
            "三门峡": "411200",
            "南阳": "411300",
            "商丘": "411400",
            "信阳": "411500",
            "周口": "411600",
            "驻马店": "411700",
            "济源": "419001",
        }
        # 尝试直接匹配
        if city in amap_city_map:
            return amap_city_map[city]
        # 尝试模糊匹配（包含关系）
        for key, code in amap_city_map.items():
            if key in city or city in key:
                return code
        # 尝试将城市名转换为拼音再匹配
        pinyin_map = {
            "hangzhou": "330100", "shanghai": "310000", "beijing": "110000",
            "suzhou": "320500", "nanjing": "320100", "ningbo": "330200",
            "shenzhen": "440300", "guangzhou": "440100", "chengdu": "510100",
            "xian": "610100", "wuhan": "420100", "changsha": "430100",
        }
        city_lower = city.lower().strip()
        if city_lower in pinyin_map:
            return pinyin_map[city_lower]
        # 默认返回杭州
        return "330100"

    def _parse_weather(self, now_data: Dict, forecast_data: Dict) -> Dict[str, Any]:
        """解析天气数据"""
        result = {
            "today": {},
            "tomorrow": {},
            "source": "qweather"
        }

        # 解析实时天气
        if now_data.get("code") == "200":
            now = now_data.get("now", {})
            result["today"] = {
                "temp": int(now.get("temp", 20)),
                "weather": now.get("text", "晴"),
                "wind": f"{now.get('windDir', '微风')}{now.get('windScale', '')}级",
                "aqi": "良",
                "humidity": now.get("humidity", "50%"),
                "updateTime": now_data.get("updateTime", "")
            }

        # 解析预报
        if forecast_data.get("code") == "200":
            daily = forecast_data.get("daily", [])
            for i, day in enumerate(daily[:3]):
                key = "today" if i == 0 else "tomorrow" if i == 1 else f"day{i}"
                result[key] = {
                    "temp": int((int(day.get("tempMax", 20)) + int(day.get("tempMin", 10))) / 2),
                    "tempMin": int(day.get("tempMin", 10)),
                    "tempMax": int(day.get("tempMax", 20)),
                    "weather": day.get("textDay", "晴"),
                    "wind": day.get("windDirDay", "微风"),
                    "aqi": "优"
                }

        return result

    def _get_mock_weather(self, city: str) -> Dict[str, Any]:
        """模拟天气数据（无API时使用）"""
        from datetime import datetime, timedelta

        city_weather = {
            "Hangzhou": {
                "today": {"temp": 18, "weather": "Sunny", "wind": "NE 3", "aqi": "Good"},
                "tomorrow": {"temp": 20, "weather": "Cloudy", "wind": "E 2", "aqi": "Excellent"},
            },
            "杭州": {
                "today": {"temp": 18, "weather": "Sunny", "wind": "NE 3", "aqi": "Good"},
                "tomorrow": {"temp": 20, "weather": "Cloudy", "wind": "E 2", "aqi": "Excellent"},
            },
        }

        base = city_weather.get(city, city_weather.get("Hangzhou", {
            "today": {"temp": 20, "weather": "Sunny", "wind": "Light Breeze", "aqi": "Good"},
            "tomorrow": {"temp": 22, "weather": "Cloudy", "wind": "Light Breeze", "aqi": "Excellent"},
        }))

        # 生成7天的预报
        forecast = []
        today = datetime.now()
        for i in range(7):
            day = today + timedelta(days=i)
            forecast.append({
                "date": day.strftime("%Y-%m-%d"),
                "temp": base["today"]["temp"] + (i % 3),
                "tempMin": base["today"]["temp"] - 3,
                "tempMax": base["today"]["temp"] + 5 + (i % 3),
                "weather": base["today"]["weather"] if i < 2 else base["tomorrow"]["weather"],
                "night_weather": "Cloudy" if i % 2 == 0 else "Clear",
                "wind": "Light Breeze",
            })

        return {
            "today": {**base["today"], "date": today.strftime("%Y-%m-%d")},
            "tomorrow": {**base["tomorrow"], "date": (today + timedelta(days=1)).strftime("%Y-%m-%d")},
            "forecast": forecast,
            "source": "mock",
        }


class MapAPI:
    """高德地图API"""

    def __init__(self):
        self.api_key = settings.AMAP_API_KEY
        self.host = "https://restapi.amap.com"
    """高德地图API"""

    def __init__(self):
        self.api_key = settings.AMAP_API_KEY
        self.host = "https://restapi.amap.com"

    async def get_poi_detail(self, poi_id: str) -> Optional[Dict[str, Any]]:
        """
        获取POI详细信息
        poi_id: 高德POI ID
        """
        if not self.api_key or self.api_key == "your_amap_api_key_here":
            return None

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = f"{self.host}/v5/place/detail"
                params = {
                    "key": self.api_key,
                    "id": poi_id,
                    "type": "200300|200200|150500|150600|100000"  # 景点、餐饮等
                }
                resp = await client.get(url, params=params)
                data = resp.json() if resp.status_code == 200 else {}

                if data.get("status") == "1" and data.get("pois"):
                    poi = data["pois"][0]
                    return {
                        "name": poi.get("name"),
                        "address": poi.get("address"),
                        "location": poi.get("location"),
                        "type": poi.get("type"),
                        "rating": float(poi.get("rating", 0)) if poi.get("rating") else None,
                        "open_hours": poi.get("opendays") or poi.get("opening_hours"),
                    }
        except Exception as e:
            print(f"高德API调用失败: {e}")
        return None

    async def search_pois(
        self,
        city: str,
        keywords: str = "",
        category: str = "",
        offset: int = 20
    ) -> list:
        """搜索POI"""
        if not self.api_key or self.api_key == "your_amap_api_key_here":
            return []

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = f"{self.host}/v5/place/text"
                params = {
                    "key": self.api_key,
                    "keywords": keywords,
                    "city": city,
                    "citylimit": "true",
                    "offset": offset,
                    "page": 1,
                }
                if category:
                    params["types"] = category

                resp = await client.get(url, params=params)
                data = resp.json() if resp.status_code == 200 else {}

                if data.get("status") == "1":
                    return data.get("pois", [])
        except Exception as e:
            print(f"高德搜索API失败: {e}")
        return []

    async def get_nearby_pois(
        self,
        location: str,  # "经度,纬度"
        radius: int = 3000,
        category: str = "风景名胜"
    ) -> list:
        """获取附近POI"""
        if not self.api_key or self.api_key == "your_amap_api_key_here":
            return []

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = f"{self.host}/v5/place/around"
                params = {
                    "key": self.api_key,
                    "location": location,
                    "radius": radius,
                    "keywords": category,
                }

                resp = await client.get(url, params=params)
                data = resp.json() if resp.status_code == 200 else {}

                if data.get("status") == "1":
                    return data.get("pois", [])
        except Exception as e:
            print(f"高德附近搜索失败: {e}")
        return []


class POIRealtimeAPI:
    """POI实时数据API - 人流量、开放状态等"""

    def __init__(self):
        self.amap_key = settings.AMAP_API_KEY

    def get_realtime_data(self, poi_name: str, poi_id: int = None) -> Dict[str, Any]:
        """
        Get POI realtime data
        - crowd_level: 0-Quiet, 1-Few, 2-Moderate, 3-Busy, 4-Crowded
        - is_open: true/false
        - wait_time: minutes
        """
        # Return mock data directly (real-time crowd data requires enterprise API)
        return self._get_mock_realtime(poi_name)

    def _get_mock_realtime(self, poi_name: str) -> Dict[str, Any]:
        """生成模拟的实时数据（基于时间和星期几）"""
        from datetime import datetime

        now = datetime.now()
        hour = now.hour
        weekday = now.weekday()  # 0=周一, 6=周日

        # 判断开放状态
        # 大部分景点 8:00-18:00 开放
        is_open = 8 <= hour < 18
        if weekday == 0:  # 周一
            # 很多博物馆周一闭馆
            if any(x in poi_name.lower() for x in ["museum", "博物馆", "展览"]):
                is_open = False

        # 判断人流 level (0-空闲, 1-较少, 2-一般, 3-较多, 4-拥挤)
        crowd_level = 2  # 默认一般

        # 周末比工作日人多
        if weekday >= 5:
            crowd_level += 1

        # 早上和中午人多
        if 10 <= hour <= 14:
            crowd_level = min(4, crowd_level + 1)
        # 傍晚17点后人少
        elif hour >= 17:
            crowd_level = max(0, crowd_level - 1)
        # 早上9点前人少
        elif hour < 9:
            crowd_level = max(0, crowd_level - 2)

        # 热门景点人更多
        popular_spots = ["west lake", "西湖", "lingyin", "灵隐", "forbidden city", "故宫"]
        if any(spot in poi_name.lower() for spot in popular_spots):
            crowd_level = min(4, crowd_level + 1)

        # 等待时间（分钟）
        wait_time = crowd_level * 15 if crowd_level >= 2 else 0

        crowd_text = ["Quiet", "Few", "Moderate", "Busy", "Crowded"][crowd_level]

        return {
            "is_open": is_open,
            "open_status": "Open" if is_open else "Closed",
            "crowd_level": crowd_level,
            "crowd_text": crowd_text,
            "wait_time": wait_time,
            "last_updated": now.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def get_historical_data(self, poi_name: str, days: int = 7) -> Dict[str, Any]:
        """
        获取历史数据
        - 过去几天的平均人流量
        - 最佳游览时间建议
        """
        from datetime import datetime, timedelta

        today = datetime.now().date()
        historical = []

        for i in range(days):
            date = today - timedelta(days=days - 1 - i)
            weekday = date.weekday()

            # 模拟历史数据
            base_crowd = 2  # 基础人流量
            if weekday >= 5:  # 周末
                base_crowd += 1
            if weekday == 0:  # 周一最少
                base_crowd -= 1

            historical.append({
                "date": date.strftime("%Y-%m-%d"),
                "weekday": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][weekday],
                "crowd_level": max(0, min(4, base_crowd)),
                "crowd_text": ["Quiet", "Few", "Moderate", "Busy", "Crowded"][max(0, min(4, base_crowd))],
            })

        avg_crowd = sum(h["crowd_level"] for h in historical) / len(historical)
        best_days = [h for h in historical if h["crowd_level"] <= 1]
        best_time = "Recommended: visit before 9 AM or after 4 PM to avoid crowds"

        return {
            "historical": historical,
            "avg_crowd_level": round(avg_crowd, 1),
            "best_days": [h["date"] for h in best_days] if best_days else [],
            "best_time_advice": best_time,
        }


# 全局实例
weather_api = WeatherAPI()
map_api = MapAPI()
poi_realtime_api = POIRealtimeAPI()
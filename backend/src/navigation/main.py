from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests
import json
import hashlib
import math
import re
from typing import Optional

# 创建路由器
router = APIRouter()

# 高德地图API密钥
API_KEY = "b455605867e22ee43f90103bca82bbe8"
# 安全密钥
SECURITY_KEY = "a919f774a32dceb294da000bfd975e08"

_TRANSLATION_CACHE = {}
_INSTRUCTION_TRANSLATION_CACHE = {}


def _contains_english(text: str) -> bool:
    return bool(re.search(r"[A-Za-z]", text or ""))


def _translate_with_public_api_to_chinese(text: str) -> Optional[str]:
    """
    Fallback translation provider when LLM is unavailable.
    """
    url = "https://api.mymemory.translated.net/get"
    params = {
        "q": text,
        "langpair": "en|zh-CN",
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            return None
        data = response.json()
        translated = (
            data.get("responseData", {})
            .get("translatedText", "")
            .strip()
        )
        return translated or None
    except Exception:
        return None


def _translate_text_with_public_api(text: str, source_lang: str, target_lang: str) -> Optional[str]:
    """
    Generic public translation helper.
    """
    if not text:
        return None
    url = "https://api.mymemory.translated.net/get"
    params = {
        "q": text,
        "langpair": f"{source_lang}|{target_lang}",
    }
    try:
        response = requests.get(url, params=params, timeout=3)
        if response.status_code != 200:
            return None
        data = response.json()
        translated = (
            data.get("responseData", {})
            .get("translatedText", "")
            .strip()
        )
        return translated or None
    except Exception:
        return None


def translate_instruction_to_english(text: str) -> str:
    """
    Translate route instruction to English when it contains Chinese.
    """
    raw = (text or "").strip()
    if not raw:
        return raw
    if raw in _INSTRUCTION_TRANSLATION_CACHE:
        return _INSTRUCTION_TRANSLATION_CACHE[raw]
    if re.search(r"[\u4e00-\u9fff]", raw):
        translated = _translate_text_with_public_api(raw, "zh-CN", "en")
        if translated:
            _INSTRUCTION_TRANSLATION_CACHE[raw] = translated
            return translated

        # Fallback rule-based conversion to keep output English-only.
        fallback = raw
        direction_map = {
            "东北": "northeast",
            "东南": "southeast",
            "西北": "northwest",
            "西南": "southwest",
            "东": "east",
            "西": "west",
            "南": "south",
            "北": "north",
        }
        for zh_dir, en_dir in direction_map.items():
            fallback = fallback.replace(f"向{zh_dir}行驶", f"head {en_dir}")
            fallback = fallback.replace(f"向{zh_dir}前进", f"go {en_dir}")

        replacements = {
            "到达目的地": "arrive at destination",
            "靠左": "keep left",
            "靠右": "keep right",
            "左转": "turn left",
            "右转": "turn right",
            "调头": "make a U-turn",
            "直行": "go straight",
            "沿": "along ",
            "途径": "via ",
            "进入": "enter ",
            "主路": "main road",
            "辅路": "side road",
            "米": "m",
            "公里": "km",
            "行驶": " drive",
        }
        for zh_text, en_text in replacements.items():
            fallback = fallback.replace(zh_text, en_text)

        fallback = re.sub(r"\s+", " ", fallback).strip()
        if re.search(r"[\u4e00-\u9fff]", fallback):
            fallback = "Follow the planned route and continue to the next step."
        _INSTRUCTION_TRANSLATION_CACHE[raw] = fallback
        return fallback

    _INSTRUCTION_TRANSLATION_CACHE[raw] = raw
    return raw


def translate_to_chinese_if_needed(text: str) -> str:
    raw = (text or "").strip()
    if not raw:
        return raw
    if not _contains_english(raw):
        return raw

    if raw in _TRANSLATION_CACHE:
        return _TRANSLATION_CACHE[raw]

    translated = _translate_with_public_api_to_chinese(raw)
    if not translated:
        translated = raw

    _TRANSLATION_CACHE[raw] = translated
    return translated


def normalize_address_for_amap(address: str, city: Optional[str] = None) -> str:
    normalized = (address or "").strip()
    if not normalized:
        return normalized

    normalized = translate_to_chinese_if_needed(normalized)

    # If still mostly English text, bias with city context and China.
    has_english = _contains_english(normalized)
    if has_english:
        if city:
            normalized = f"{city}{normalized}"
        if "中国" not in normalized and "China" not in normalized:
            normalized = f"中国{normalized}"

    return normalized

# 生成签名
def generate_sign(parameters):
    """
    生成高德地图API请求签名
    :param parameters: 请求参数
    :return: 签名
    """
    # 对参数按照key进行排序
    sorted_params = sorted(parameters.items(), key=lambda x: x[0])
    # 拼接参数字符串
    param_str = "".join([f"{k}{v}" for k, v in sorted_params])
    # 拼接安全密钥
    sign_str = param_str + SECURITY_KEY
    # 计算MD5签名
    sign = hashlib.md5(sign_str.encode('utf-8')).hexdigest().upper()
    return sign

# 地理编码
def geocode(address, city: Optional[str] = None):
    """
    将地址转换为经纬度坐标
    :param address: 地址字符串
    :return: (经度, 纬度)
    """
    url = "https://restapi.amap.com/v3/geocode/geo"
    resolved_address = normalize_address_for_amap(address, city=city)
    params = {
        "key": API_KEY,
        "address": resolved_address,
        "output": "json"
    }
    if city:
        params["city"] = city
    # 不使用签名，直接调用API
    response = requests.get(url, params=params)
    data = response.json()
    
    if data["status"] == "1" and data["count"] > "0":
        location = data["geocodes"][0]["location"]
        lon, lat = location.split(",")
        return float(lon), float(lat)
    else:
        raise Exception(f"地理编码失败: {data.get('info', '未知错误')}")

# 路径规划
def route_planning(start_lng, start_lat, end_lng, end_lat, mode="driving"):
    """
    路径规划
    :param start_lng: 起点经度
    :param start_lat: 起点纬度
    :param end_lng: 终点经度
    :param end_lat: 终点纬度
    :param mode: 交通方式（driving:驾车, walking:步行, transit:公交）
    :return: 路线信息
    """
    # 直接使用传入的经纬度坐标
    start_lon, start_lat = start_lng, start_lat
    end_lon, end_lat = end_lng, end_lat
    
    # 2. 调用路径规划API
    if mode == "driving":
        url = "https://restapi.amap.com/v3/direction/driving"
    elif mode == "walking":
        url = "https://restapi.amap.com/v3/direction/walking"
    elif mode == "transit":
        url = "https://restapi.amap.com/v3/direction/transit/integrated"
    else:
        raise Exception("不支持的交通方式")
    
    params = {
        "key": API_KEY,
        "origin": f"{start_lon},{start_lat}",
        "destination": f"{end_lon},{end_lat}",
        "output": "json"
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") == "1":
            return data
        else:
            raise Exception(f"路径规划失败: {data.get('info', '未知错误')}")
    except Exception as e:
        print(f"路径规划错误: {e}")
        return None

# 解析路线
def parse_route(route_data, mode="driving"):
    """
    解析路线信息，提取关键数据
    :param route_data: 路径规划API返回的数据
    :param mode: 交通方式
    :return: 格式化的路线信息
    """
    if mode == "driving" or mode == "walking":
        route = route_data["route"]
        paths = route["paths"][0]
        
        # 提取关键信息
        distance = paths.get("distance", "0")  # 距离（米）
        duration = paths.get("duration", "0")  # 预计时间（秒）
        steps = paths.get("steps", [])  # 导航步骤
        
        # 格式化导航步骤
        instructions = []
        for step in steps:
            instruction_text = step.get("instruction", "")
            instructions.append(translate_instruction_to_english(instruction_text))
        
        return {
            "distance": f"{int(distance)/1000:.2f}公里",
            "duration": f"{int(duration)//60}分钟{int(duration)%60}秒",
            "instructions": instructions
        }
    else:
        # 公交路线解析（略，可根据需要扩展）
        return route_data


def build_fallback_route(start_lon, start_lat, end_lon, end_lat, mode="driving"):
    """
    Build a simple fallback route when map provider cannot return a valid route.
    This avoids returning HTTP 500 to frontend real-time navigation.
    """
    # Approximate straight-line distance (km)
    lat_scale = 111.0
    lon_scale = 111.0 * math.cos(math.radians((start_lat + end_lat) / 2.0))
    dx = (end_lon - start_lon) * lon_scale
    dy = (end_lat - start_lat) * lat_scale
    distance_km = max(math.sqrt(dx * dx + dy * dy), 0.2)

    speed_kmh = {
        "walking": 5.0,
        "driving": 35.0,
        "transit": 22.0,
    }.get(mode, 22.0)
    minutes = max(int((distance_km / speed_kmh) * 60), 1)

    return {
        "distance": f"{distance_km:.2f}公里",
        "duration": f"{minutes}分钟",
        "instructions": [
            "Navigation provider returned limited results.",
            "Proceed towards destination and follow local traffic guidance.",
            "You can refresh route planning after moving closer.",
        ],
        "path": [
            [float(start_lon), float(start_lat)],
            [float(end_lon), float(end_lat)],
        ],
    }

# 请求模型
class NavigationRequest(BaseModel):
    start: str  # 起点（地址或经纬度）
    end: str  # 终点（地址或经纬度）
    mode: Optional[str] = "driving"  # 交通方式
    city: Optional[str] = None  # 城市提示（用于提升英文地名识别）

# 响应模型
class NavigationResponse(BaseModel):
    status: str
    route: dict

# 检查是否为经纬度格式
def is_coordinate(coord_str):
    try:
        parts = coord_str.split(',')
        if len(parts) == 2:
            float(parts[0])
            float(parts[1])
            return True
        return False
    except:
        return False

# 导航API端点
@router.post("/navigate", response_model=NavigationResponse)
async def get_navigation(request: NavigationRequest):
    """
    获取导航路线信息
    """
    start = request.start
    end = request.end
    mode = request.mode
    city_hint = request.city

    if not start or not end:
        raise HTTPException(status_code=400, detail="缺少起点或终点参数")

    try:
        # 处理起点
        if is_coordinate(start):
            start_lon, start_lat = map(float, start.split(','))
        else:
            try:
                start_lon, start_lat = geocode(start, city=city_hint)
            except Exception:
                # Default fallback center (Dali) when geocode fails
                start_lon, start_lat = 100.199716, 25.680272

        # 处理终点
        if is_coordinate(end):
            end_lon, end_lat = map(float, end.split(','))
        else:
            try:
                end_lon, end_lat = geocode(end, city=city_hint)
            except Exception:
                # Offset fallback endpoint near default center
                end_lon, end_lat = 100.209716, 25.690272

        # 路径规划
        route_data = route_planning(start_lon, start_lat, end_lon, end_lat, mode=mode)

        # When provider fails, return fallback route (still success).
        if not route_data:
            fallback = build_fallback_route(start_lon, start_lat, end_lon, end_lat, mode=mode)
            return {
                "status": "success",
                "route": {
                    "distance": fallback["distance"],
                    "time": fallback["duration"],
                    "steps": fallback["instructions"],
                    "path": fallback["path"],
                },
            }

        result = parse_route(route_data, mode=mode)

        # 提取路线坐标点
        path = []
        if mode == "driving" or mode == "walking":
            steps = route_data["route"]["paths"][0].get("steps", [])
            for step in steps:
                polyline = step.get("polyline", "")
                if polyline:
                    points = polyline.split(';')
                    for point in points:
                        if point:
                            lon, lat = point.split(',')
                            path.append([float(lon), float(lat)])
        else:
            path = []

        if not path:
            fallback = build_fallback_route(start_lon, start_lat, end_lon, end_lat, mode=mode)
            path = fallback["path"]

        response = {
            "status": "success",
            "route": {
                "distance": result.get("distance", "0公里"),
                "time": result.get("duration", "0分钟"),
                "steps": result.get("instructions", []),
                "path": path,
            },
        }
        return response
    except HTTPException:
        raise
    except Exception:
        # 最后兜底：避免前端实时导航因单次失败直接中断
        if is_coordinate(start) and is_coordinate(end):
            start_lon, start_lat = map(float, start.split(','))
            end_lon, end_lat = map(float, end.split(','))
            fallback = build_fallback_route(start_lon, start_lat, end_lon, end_lat, mode=mode)
            return {
                "status": "success",
                "route": {
                    "distance": fallback["distance"],
                    "time": fallback["duration"],
                    "steps": fallback["instructions"],
                    "path": fallback["path"],
                },
            }
        raise HTTPException(status_code=500, detail="路径规划失败，请稍后重试")

# 健康检查端点
@router.get("/health")
async def health_check():
    """
    导航服务健康检查
    """
    return {"status": "ok", "message": "Navigation service is running"}
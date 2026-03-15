from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests
import json
import hashlib
import math
import re
from typing import Optional

router = APIRouter()

API_KEY = "b455605867e22ee43f90103bca82bbe8"
SECURITY_KEY = "a919f774a32dceb294da000bfd975e08"

_TRANSLATION_CACHE = {}
_INSTRUCTION_TRANSLATION_CACHE = {}

LANDMARK_MAPPING = {
    "west lake": "杭州西湖",
    "West Lake": "杭州西湖",
    "xixi wetland": "杭州西溪湿地",
    "Xixi Wetland": "杭州西溪湿地",
    "leifeng pagoda": "杭州雷峰塔",
    "lingyin temple": "杭州灵隐寺",
}


def _contains_english(text: str) -> bool:
    return bool(re.search(r"[A-Za-z]", text or ""))


def _translate_with_public_api_to_chinese(text: str) -> Optional[str]:
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

    lower_text = raw.lower()
    if lower_text in LANDMARK_MAPPING:
        return LANDMARK_MAPPING[lower_text]

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

    lower_text = normalized.lower()
    if lower_text in LANDMARK_MAPPING:
        return LANDMARK_MAPPING[lower_text]

    normalized = translate_to_chinese_if_needed(normalized)

    has_english = _contains_english(normalized)
    if has_english:
        if city:
            normalized = f"{city}{normalized}"
        if "中国" not in normalized and "China" not in normalized:
            normalized = f"中国{normalized}"

    return normalized

def generate_sign(parameters):
    sorted_params = sorted(parameters.items(), key=lambda x: x[0])
    param_str = "".join([f"{k}{v}" for k, v in sorted_params])
    sign_str = param_str + SECURITY_KEY
    sign = hashlib.md5(sign_str.encode('utf-8')).hexdigest().upper()
    return sign

def geocode(address, city: Optional[str] = None):
    url = "https://restapi.amap.com/v3/geocode/geo"
    resolved_address = normalize_address_for_amap(address, city=city)
    params = {
        "key": API_KEY,
        "address": resolved_address,
        "output": "json"
    }
    if city:
        params["city"] = city
    response = requests.get(url, params=params, timeout=10)
    data = response.json()
    
    print(f"[GEOCODE] input='{address}' -> resolved='{resolved_address}' -> status={data.get('status')} count={data.get('count')}")
    
    if data["status"] == "1" and data["count"] > "0":
        geocode_info = data["geocodes"][0]
        location = geocode_info["location"]
        lon, lat = location.split(",")
        print(f"[GEOCODE] found: {geocode_info.get('formatted_address', 'N/A')} @ ({lon}, {lat})")
        return float(lon), float(lat)
    else:
        raise Exception(f"地理编码失败: {data.get('info', '未知错误')}")

def route_planning(start_lng, start_lat, end_lng, end_lat, mode="driving"):
    start_lon, start_lat = start_lng, start_lat
    end_lon, end_lat = end_lng, end_lat
    
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

def parse_route(route_data, mode="driving"):
    if mode == "driving" or mode == "walking":
        route = route_data["route"]
        paths = route["paths"][0]
        
        distance = paths.get("distance", "0")
        duration = paths.get("duration", "0")
        steps = paths.get("steps", [])
        
        instructions = []
        for step in steps:
            instruction_text = step.get("instruction", "")
            instructions.append(translate_instruction_to_english(instruction_text))
        
        distance_km = int(distance) / 1000
        duration_min = int(duration) // 60
        duration_sec = int(duration) % 60
        
        distance_str = f"{distance_km:.2f} km"
        if duration_min >= 60:
            hours = duration_min // 60
            mins = duration_min % 60
            duration_str = f"{hours} hr {mins} min"
        else:
            duration_str = f"{duration_min} min"
        
        return {
            "distance": distance_str,
            "duration": duration_str,
            "instructions": instructions
        }
    else:
        return route_data


def build_fallback_route(start_lon, start_lat, end_lon, end_lat, mode="driving"):
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
        "distance": f"{distance_km:.2f} km",
        "duration": f"{minutes} min",
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

class NavigationRequest(BaseModel):
    start: str
    end: str
    mode: Optional[str] = "driving"
    city: Optional[str] = None

class NavigationResponse(BaseModel):
    status: str
    route: dict

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

@router.post("/navigate", response_model=NavigationResponse)
async def get_navigation(request: NavigationRequest):
    start = request.start
    end = request.end
    mode = request.mode
    city_hint = request.city

    if not start or not end:
        raise HTTPException(status_code=400, detail="Missing start or end parameter")

    try:
        if is_coordinate(start):
            start_lon, start_lat = map(float, start.split(','))
        else:
            try:
                start_lon, start_lat = geocode(start, city=city_hint)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Cannot find start location: {start}")

        if is_coordinate(end):
            end_lon, end_lat = map(float, end.split(','))
        else:
            try:
                end_lon, end_lat = geocode(end, city=city_hint)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Cannot find end location: {end}")

        route_data = route_planning(start_lon, start_lat, end_lon, end_lat, mode=mode)

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
                "distance": result.get("distance", "0 km"),
                "time": result.get("duration", "0 min"),
                "steps": result.get("instructions", []),
                "path": path,
            },
        }
        return response
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Navigation failed: {e}")
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
        raise HTTPException(status_code=500, detail="Route planning failed, please try again later")

@router.get("/health")
async def health_check():
    return {"status": "ok", "message": "Navigation service is running"}

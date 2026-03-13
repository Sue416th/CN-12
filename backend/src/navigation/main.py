from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests
import json
import hashlib
from typing import Optional

# 创建路由器
router = APIRouter()

# 高德地图API密钥
API_KEY = "b455605867e22ee43f90103bca82bbe8"
# 安全密钥
SECURITY_KEY = "a919f774a32dceb294da000bfd975e08"

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
def geocode(address):
    """
    将地址转换为经纬度坐标
    :param address: 地址字符串
    :return: (经度, 纬度)
    """
    url = "https://restapi.amap.com/v3/geocode/geo"
    params = {
        "key": API_KEY,
        "address": address,
        "output": "json"
    }
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
            instructions.append(step.get("instruction", ""))
        
        return {
            "distance": f"{int(distance)/1000:.2f}公里",
            "duration": f"{int(duration)//60}分钟{int(duration)%60}秒",
            "instructions": instructions
        }
    else:
        # 公交路线解析（略，可根据需要扩展）
        return route_data

# 请求模型
class NavigationRequest(BaseModel):
    start: str  # 起点（地址或经纬度）
    end: str  # 终点（地址或经纬度）
    mode: Optional[str] = "driving"  # 交通方式

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
    try:
        start = request.start
        end = request.end
        mode = request.mode
        
        if not start or not end:
            raise HTTPException(status_code=400, detail="缺少起点或终点参数")
        
        # 处理起点
        if is_coordinate(start):
            start_lon, start_lat = map(float, start.split(','))
        else:
            start_lon, start_lat = geocode(start)
        
        # 处理终点
        if is_coordinate(end):
            end_lon, end_lat = map(float, end.split(','))
        else:
            end_lon, end_lat = geocode(end)
        
        # 路径规划
        route_data = route_planning(start_lon, start_lat, end_lon, end_lat, mode=mode)
        
        if route_data:
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
            
            response = {
                "status": "success",
                "route": {
                    "distance": result.get("distance", "0公里"),
                    "time": result.get("duration", "0分钟"),
                    "steps": result.get("instructions", []),
                    "path": path
                }
            }
            return response
        else:
            raise HTTPException(status_code=500, detail="路径规划失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 健康检查端点
@router.get("/health")
async def health_check():
    """
    导航服务健康检查
    """
    return {"status": "ok", "message": "Navigation service is running"}
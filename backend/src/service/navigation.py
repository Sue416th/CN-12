import requests
import json
import hashlib
import os
import urllib.parse

# 添加CORS头
def add_cors_headers():
    print("Content-Type: application/json")
    print("Access-Control-Allow-Origin: *")
    print("Access-Control-Allow-Methods: GET, POST, OPTIONS")
    print("Access-Control-Allow-Headers: Content-Type")
    print()  # 空行表示响应头结束

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

def get_route(start, end, mode="driving"):
    """
    获取路径规划结果
    :param start: 起点（地址或经纬度）
    :param end: 终点（地址或经纬度）
    :param mode: 交通方式
    :return: 路径信息
    """
    try:
        def is_coordinate(coord_str):
            """判断是否为经纬度坐标"""
            if ',' in coord_str:
                parts = coord_str.split(',')
                if len(parts) == 2:
                    try:
                        float(parts[0])
                        float(parts[1])
                        return True
                    except ValueError:
                        return False
            return False
        
        # 解析起点和终点
        if is_coordinate(start):
            start_lon, start_lat = map(float, start.split(','))
        else:
            start_lon, start_lat = geocode(start)
        
        if is_coordinate(end):
            end_lon, end_lat = map(float, end.split(','))
        else:
            end_lon, end_lat = geocode(end)
        
        # 调用路径规划
        route_data = route_planning(start_lon, start_lat, end_lon, end_lat, mode=mode)
        
        if route_data:
            # 解析路线数据
            result = parse_route(route_data, mode=mode)
            
            # 提取路径点
            path = []
            if mode == "driving" or mode == "walking":
                if "route" in route_data and "paths" in route_data["route"] and route_data["route"]["paths"]:
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
            
            # 构建响应
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
            return {"status": "error", "message": "路径规划失败"}
    except Exception as e:
        print(f"获取路径错误: {e}")
        return {"status": "error", "message": str(e)}

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

if __name__ == "__main__":
    # 处理HTTP请求
    import sys
    
    # 添加CORS头
    add_cors_headers()
    
    # 解析查询参数
    query_string = os.environ.get('QUERY_STRING', '')
    params = {}
    if query_string:
        for param in query_string.split('&'):
            if '=' in param:
                key, value = param.split('=', 1)
                # 对URL编码的参数进行解码
                params[key] = urllib.parse.unquote(value)
    
    start = params.get('start', '')
    end = params.get('end', '')
    mode = params.get('mode', 'driving')
    
    if not start or not end:
        print(json.dumps({"status": "error", "message": "缺少起点或终点参数"}))
        sys.exit()
    
    try:
        # 1. 处理起点和终点参数
        # 检查是否为经纬度格式（lon,lat）
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
        
        # 2. 路径规划
        route_data = route_planning(start_lon, start_lat, end_lon, end_lat, mode=mode)
        
        if route_data:
            result = parse_route(route_data, mode=mode)
            
            # 3. 提取路线坐标点
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
            
            # 4. 构建响应
            response = {
                "status": "success",
                "route": {
                    "distance": result.get("distance", "0公里"),
                    "time": result.get("duration", "0分钟"),
                    "steps": result.get("instructions", []),
                    "path": path
                }
            }
            print(json.dumps(response))
        else:
            print(json.dumps({"status": "error", "message": "路径规划失败"}))
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}))
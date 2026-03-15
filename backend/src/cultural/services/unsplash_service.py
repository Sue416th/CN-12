# -*- coding: utf-8 -*-
"""Unsplash 图片搜索服务"""
import os
import requests
from typing import List, Optional
from dotenv import load_dotenv

# 加载环境变量 - 指定 backend 目录下的 .env 文件
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), '.env')
load_dotenv(env_path)


class UnsplashService:
    def __init__(self):
        self.access_key = os.getenv("UNSPLASH_ACCESS_KEY", "")
        self.base_url = "https://api.unsplash.com"

    def search_photos(self, query: str, per_page: int = 3) -> List[str]:
        """
        搜索图片

        Args:
            query: 搜索关键词
            per_page: 返回图片数量

        Returns:
            图片URL列表
        """
        if not self.access_key:
            print("警告: UNSPLASH_ACCESS_KEY 未配置")
            return []

        headers = {
            "Authorization": f"Client-ID {self.access_key}"
        }

        # 先尝试搜索中国地标
        search_queries = [
            f"{query} China landmark",
            query,
            f"{query} 景点"
        ]

        for search_query in search_queries:
            try:
                url = f"{self.base_url}/search/photos"
                params = {
                    "query": search_query,
                    "per_page": per_page,
                    "orientation": "landscape"
                }

                response = requests.get(url, headers=headers, params=params, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    if data.get("results"):
                        urls = [result["urls"]["regular"] for result in data["results"][:per_page]]
                        return urls
                elif response.status_code == 401:
                    print("Unsplash API 认证失败，请检查 access key")
                    return []
            except Exception as e:
                print(f"搜索图片错误: {e}")
                continue

        return []

    def get_random_photo(self, query: Optional[str] = None) -> Optional[str]:
        """
        获取随机图片

        Args:
            query: 搜索关键词

        Returns:
            图片URL
        """
        if not self.access_key:
            return None

        headers = {
            "Authorization": f"Client-ID {self.access_key}"
        }

        try:
            url = f"{self.base_url}/photos/random"
            params = {}
            if query:
                params["query"] = query

            response = requests.get(url, headers=headers, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return data["urls"]["regular"]
        except Exception as e:
            print(f"获取随机图片错误: {e}")

        return None


# 全局实例
unsplash_service = UnsplashService()

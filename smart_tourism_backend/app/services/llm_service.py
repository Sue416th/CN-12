"""
LLM Service - Large Language Model Integration
支持多种LLM后端：GLM-4, GPT-4, GPT-3.5-Turbo, Qwen
"""
from typing import Any, Dict, List, Optional
import json
import asyncio
from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """LLM Provider Abstract Base Class"""
    
    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """Send chat request and get response"""
        pass
    
    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate text embedding"""
        pass


class GLMProvider(LLMProvider):
    """Zhipu AI GLM-4 Provider"""

    def __init__(self, api_key: str = "", base_url: str = "https://open.bigmodel.cn/api/paas/v4"):
        self.api_key = api_key
        self.base_url = base_url
        self.model = "glm-4"
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        import aiohttp
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                if response.status != 200:
                    error = await response.text()
                    raise Exception(f"GLM API Error: {error}")
                
                result = await response.json()
                return result["choices"][0]["message"]["content"]
    
    async def generate_embedding(self, text: str) -> List[float]:
        import aiohttp
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "embedding-2",
            "input": text
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/embeddings",
                headers=headers,
                json=payload
            ) as response:
                if response.status != 200:
                    error = await response.text()
                    raise Exception(f"GLM Embedding Error: {error}")
                
                result = await response.json()
                return result["data"][0]["embedding"]


class OpenAIProvider(LLMProvider):
    """OpenAI GPT Provider (GPT-4, GPT-3.5-Turbo)"""

    def __init__(self, api_key: str = "", model: str = "gpt-4", base_url: str = "https://api.openai.com/v1"):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        import aiohttp
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                if response.status != 200:
                    error = await response.text()
                    raise Exception(f"OpenAI API Error: {error}")
                
                result = await response.json()
                return result["choices"][0]["message"]["content"]
    
    async def generate_embedding(self, text: str) -> List[float]:
        import aiohttp
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "text-embedding-ada-002",
            "input": text
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/embeddings",
                headers=headers,
                json=payload
            ) as response:
                if response.status != 200:
                    error = await response.text()
                    raise Exception(f"OpenAI Embedding Error: {error}")
                
                result = await response.json()
                return result["data"][0]["embedding"]


class QwenProvider(LLMProvider):
    """Alibaba Qwen Provider"""

    def __init__(self, api_key: str = "", model: str = "qwen-turbo"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://dashscope.aliyuncs.com/api/v1"
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        import aiohttp
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "input": {"messages": messages},
            "parameters": {
                "temperature": temperature,
                "max_tokens": max_tokens,
                "result_format": "message"
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/services/aigc/text-generation/generation",
                headers=headers,
                json=payload
            ) as response:
                if response.status != 200:
                    error = await response.text()
                    raise Exception(f"Qwen API Error: {error}")
                
                result = await response.json()
                return result["output"]["choices"][0]["message"]["content"]
    
    async def generate_embedding(self, text: str) -> List[float]:
        import aiohttp
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "text-embedding-v2",
            "input": text
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/services/aigc/embeddings/text_embedding",
                headers=headers,
                json=payload
            ) as response:
                if response.status != 200:
                    error = await response.text()
                    raise Exception(f"Qwen Embedding Error: {error}")
                
                result = await response.json()
                return result["output"]["embeddings"][0]["embedding"]


class LLMService:
    """
    Unified LLM Service
    Provides natural language understanding and generation capabilities
    """

    # Provider factory
    PROVIDERS = {
        "glm": GLMProvider,
        "openai": OpenAIProvider,
        "qwen": QwenProvider,
    }

    def __init__(self, provider: str = "glm", api_key: str = "", **provider_kwargs):
        """Initialize LLM service with specified provider"""
        if provider not in self.PROVIDERS:
            raise ValueError(f"Unknown provider: {provider}. Available: {list(self.PROVIDERS.keys())}")

        # Check if API key is valid (not empty or placeholder)
        self._api_key_valid = bool(api_key and api_key.strip() and api_key != "your_llm_api_key_here")

        if not self._api_key_valid:
            print(f"Warning: LLM API key is empty or invalid. LLM features will be disabled.")
            self.provider = None
            self.provider_name = provider
            return

        self.provider = self.PROVIDERS[provider](api_key=api_key, **provider_kwargs)
        self.provider_name = provider

    def is_available(self) -> bool:
        """Check if LLM service is available (has valid API key)"""
        return self._api_key_valid and self.provider is not None
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """Send chat request"""
        return await self.provider.chat(messages, temperature, max_tokens)
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate text embedding"""
        return await self.provider.generate_embedding(text)
    
    # ==================== User Profile Specific Methods ====================
    
    async def analyze_user_input(
        self,
        user_text: str,
        structured_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze natural language user input to extract profile attributes
        
        Args:
            user_text: User's natural language description
            structured_data: Optional structured input (budget, dates, etc.)
        
        Returns:
            Analyzed profile attributes
        """
        system_prompt = """你是一个专业的旅行用户画像分析助手。
你的任务是从用户的输入中提取和推断用户的多维度特征。

请分析以下用户输入，提取以下信息：
1. interests - 兴趣偏好（如：历史、文化、美食、自然、艺术等）
2. budget_level - 预算级别（low/medium/high）
3. travel_style - 旅行风格（relaxed/balanced/intensive）
4. fitness_level - 体能水平（low/medium/high）
5. cultural_preferences - 文化偏好维度（history, art, tradition, modern, nature, food_culture, religion, nightlife）
6. special_requirements - 特殊需求（如：需要无障碍设施、带小孩、老人同行等）

请以JSON格式输出分析结果。"""
        
        user_prompt = f"""用户输入：{user_text}

结构化数据：{json.dumps(structured_data, ensure_ascii=False) if structured_data else '无'}

请分析并返回JSON格式的用户画像分析结果。"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.chat(messages, temperature=0.5, max_tokens=1000)
        
        # Parse JSON from response
        try:
            # Try to extract JSON from response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]
            else:
                json_str = response
            
            return json.loads(json_str)
        except:
            # Return raw response if parsing fails
            return {"raw_analysis": response, "interests": [], "budget_level": "medium"}
    
    async def generate_profile_description(
        self,
        profile: Dict[str, Any],
    ) -> str:
        """
        Generate human-readable description of user profile
        
        Args:
            profile: User profile dictionary
        
        Returns:
            Profile description in natural language
        """
        system_prompt = """你是一个专业的旅行顾问，负责为用户生成个性化的画像描述。
根据用户画像数据，生成一段生动、友好的用户画像描述。"""
        
        # Build profile summary
        interests = ", ".join(profile.get("interests", []))
        budget = profile.get("budget_level", "中等")
        budget_map = {"low": "经济型", "medium": "舒适型", "high": "豪华型"}
        budget_cn = budget_map.get(budget, "舒适型")
        
        fitness = profile.get("fitness_level", "中等")
        fitness_map = {"low": "轻松", "medium": "适中", "high": "活跃"}
        fitness_cn = fitness_map.get(fitness, "适中")
        
        cultural = profile.get("cultural_preferences", {})
        top_cultural = sorted(cultural.items(), key=lambda x: x[1], reverse=True)[:3] if cultural else []
        cultural_str = "、".join([f"{k}({v:.0%})" for k, v in top_cultural]) if top_cultural else "综合"
        
        user_prompt = f"""请为以下用户生成一段画像描述：

- 兴趣偏好：{interests}
- 预算级别：{budget_cn}
- 体能水平：{fitness_cn}
- 文化偏好：{cultural_str}

请用生动、友好的语言描述这位用户的特点（100字以内）。"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return await self.chat(messages, temperature=0.7, max_tokens=200)
    
    async def recommend_profile_adjustments(
        self,
        current_profile: Dict[str, Any],
        feedback: str,
    ) -> Dict[str, Any]:
        """
        Analyze user feedback and recommend profile adjustments
        
        Args:
            current_profile: Current user profile
            feedback: User's feedback text
        
        Returns:
            Recommended profile adjustments
        """
        system_prompt = """你是一个智能用户画像调整助手。
根据用户的反馈，分析并推荐画像调整方案。
        
输出JSON格式：
{
    "suggested_changes": {
        "interests": ["新增兴趣列表"],
        "budget_level": "调整后的预算级别",
        "cultural_preferences": {"维度": 0-1的值},
        ...
    },
    "confidence": 0.0-1.0,
    "reasoning": "调整原因说明"
}"""
        
        user_prompt = f"""当前用户画像：
{json.dumps(current_profile, ensure_ascii=False, indent=2)}

用户反馈：{feedback}

请分析反馈并推荐画像调整方案。"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.chat(messages, temperature=0.5, max_tokens=500)
        
        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]
            else:
                json_str = response
            
            return json.loads(json_str)
        except:
            return {"suggested_changes": {}, "confidence": 0.0, "raw_response": response}


# ==================== Singleton Instance ====================
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get LLM service singleton"""
    global _llm_service
    if _llm_service is None:
        from app.config import settings
        # Pass parameters based on provider type
        provider_kwargs = {}
        if settings.LLM_PROVIDER == "glm":
            provider_kwargs["base_url"] = settings.LLM_BASE_URL
        elif settings.LLM_PROVIDER == "openai":
            provider_kwargs["base_url"] = settings.LLM_BASE_URL
            provider_kwargs["model"] = settings.LLM_MODEL
        elif settings.LLM_PROVIDER == "qwen":
            provider_kwargs["model"] = settings.LLM_MODEL

        _llm_service = LLMService(
            provider=settings.LLM_PROVIDER,
            api_key=settings.LLM_API_KEY,
            **provider_kwargs,
        )
    return _llm_service

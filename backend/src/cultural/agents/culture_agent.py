import os
import re
from typing import Optional, Generator, List, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv

# 加载环境变量 - 指定 backend 目录下的 .env 文件
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), '.env')
load_dotenv(env_path)

from ..services.rag_retriever import RAGRetriever
from ..services.unsplash_service import unsplash_service


class CulturalInterpretationAgent:
    """Cultural interpretation AI agent - Q&A mode"""

    def __init__(self):
        self.retriever = RAGRetriever()
        self.client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        )

    def chat(self, message: str) -> str:
        """
        Process user message
        1. First search the knowledge base
        2. If relevant information is found (score >= 10), return knowledge base + LLM content
        3. If no relevant information is found, directly call LLM to generate answer
        """
        retrieved_results = self.retriever.retrieve(message, top_k=3)

        # 只有当检索结果的相关性分数 >= 10 时才使用知识库
        if retrieved_results and retrieved_results[0]['score'] >= 10:
            context = self.retriever.format_retrieved_context(retrieved_results)
            answer = self._generate_answer_from_context(message, context)
            return answer
        else:
            return self._generate_answer_from_llm(message)

    def chat_stream(self, message: str) -> Generator[str, None, None]:
        """Process user message in streaming mode"""
        retrieved_results = self.retriever.retrieve(message, top_k=3)

        if retrieved_results and retrieved_results[0]['score'] >= 10:
            context = self.retriever.format_retrieved_context(retrieved_results)
            yield from self._generate_stream_from_context(message, context)
        else:
            yield from self._generate_stream_from_llm(message)

    def _generate_answer_from_context(self, question: str, context: str) -> str:
        """Based on retrieved context to generate answer"""
        prompt = f"""The user's question is in Chinese: "{question}"

First, translate the question to English.
Then answer the translated question using the context below.

Context: {context}

Provide your final answer in English only."""

        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a cultural guide. Always reply in English."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.3
        )

        return response.choices[0].message.content

    def _generate_stream_from_context(self, question: str, context: str) -> Generator[str, None, None]:
        """Based on retrieved context to generate streaming answer"""
        prompt = f"""The user's question is in Chinese: "{question}"

First, translate the question to English.
Then answer the translated question using the context below.

Context: {context}

Provide your final answer in English only."""

        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a cultural guide. Always reply in English."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.3,
            stream=True
        )

        for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def _generate_stream_from_llm(self, question: str) -> Generator[str, None, None]:
        """When no relevant knowledge is found, use LLM to generate streaming answer"""
        prompt = f"""The user's question is in Chinese: "{question}"

First, translate the question to English.
Then answer the translated question.

Provide your final answer in English only."""

        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a cultural guide. Always reply in English."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.3,
            stream=True
        )

        for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def _generate_answer_from_llm(self, question: str) -> str:
        """When no relevant knowledge is found, use LLM to generate answer"""
        prompt = f"""The user's question is in Chinese: "{question}"

First, translate the question to English.
Then answer the translated question.

Provide your final answer in English only."""

        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a cultural guide. Always reply in English."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.3
        )

        return response.choices[0].message.content

    def _extract_keywords_for_images(self, question: str) -> str:
        """Extract keywords for image search from the question"""
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "You are a keyword extraction assistant. Extract keywords suitable for searching travel images from the user's question. Only return the keywords, nothing else."},
                    {"role": "user", "content": f"User question: {question}\nExtract 2-3 keywords suitable for image search, separated by commas. For example: Phoenix Ancient Town, Stilted Houses, West Lake"}
                ],
                max_tokens=100,
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except:
            return question[:20]

    def chat_with_images(self, message: str) -> Dict[str, Any]:
        """Chat with images, returns answer and image URL list"""
        retrieved_results = self.retriever.retrieve(message, top_k=3)

        # 判断是否需要图片：只有当问题涉及具体景点时才搜索图片
        need_images = self._should_include_images(message, retrieved_results)

        if need_images:
            # 提取关键词并搜索图片
            keywords = self._extract_keywords_for_images(message)
            keyword = keywords.split(',')[0].strip()
            image_urls = unsplash_service.search_photos(keyword, per_page=3)
        else:
            keywords = ""
            image_urls = []

        if retrieved_results and retrieved_results[0]['score'] >= 10:
            context = self.retriever.format_retrieved_context(retrieved_results)
            answer = self._generate_answer_from_context(message, context)
        else:
            answer = self._generate_answer_from_llm(message)

        return {
            "answer": answer,
            "images": image_urls,
            "keywords": keywords
        }

    def _should_include_images(self, question: str, retrieved_results: List[Dict]) -> bool:
        """Determine if images should be included"""
        question_lower = question.lower()

        # Exclude pure greetings and small talk
        greetings = ["你好", "您好", "hello", "hi", "hey", "在吗", "在不在", "你好啊", "您好啊", "谢谢", "感谢", "good morning", "good afternoon", "good evening", "thank you", "thanks"]
        for greeting in greetings:
            if question_lower.strip() == greeting or question_lower.strip() == greeting + "?":
                return False

        # If relevant attraction knowledge is retrieved, show images
        if retrieved_results and retrieved_results[0]['score'] >= 10:
            return True

        # If the question involves attractions, culture, history, etc., search for images
        image_related_keywords = [
            "景点", "地方", "风景", "古城", "古镇", "寺庙", "山", "湖", "公园",
            "传说", "历史", "文化", "建筑", "塔", "桥", "阁", "楼",
            "门票", "开放", "游览", "旅游", "推荐", "住宿", "美食",
            "attraction", "place", "scenery", "ancient town", "temple", "mountain", "lake", "park",
            "legend", "history", "culture", "building", "tower", "bridge", "ticket", "open", 
            "visit", "travel", "recommend", "hotel", "food", "restaurant"
        ]

        for keyword in image_related_keywords:
            if keyword in question_lower:
                return True

        return False

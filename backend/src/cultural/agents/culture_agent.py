import os

import re

from typing import Optional, Generator, List, Dict, Any

from openai import OpenAI

from dotenv import load_dotenv

import json



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



    def _translate_to_chinese(self, text: str) -> str:

        """翻译英文到中文"""

        response = self.client.chat.completions.create(

            model="deepseek-chat",

            messages=[

                {"role": "system", "content": "You are a translator. Translate the following text to Chinese. Only return the translation, nothing else."},

                {"role": "user", "content": text}

            ],

            max_tokens=500,

            temperature=0.3

        )

        return response.choices[0].message.content



    def _translate_to_english(self, text: str) -> str:

        """翻译中文到英文"""

        response = self.client.chat.completions.create(

            model="deepseek-chat",

            messages=[

                {"role": "system", "content": "You are a translator. Translate the following text to English. Only return the translation, nothing else."},

                {"role": "user", "content": text}

            ],

            max_tokens=2000,

            temperature=0.3

        )

        return response.choices[0].message.content



    def chat(self, message: str) -> str:

        """

        Process user message

        1. Translate user question from English to Chinese

        2. Search the knowledge base in Chinese

        3. If relevant information is found (score >= 10), combine knowledge base + LLM, then translate to English

        4. If no relevant information is found, use LLM directly, then translate to English

        """

        # Step 1: Translate user question to Chinese

        query_chinese = self._translate_to_chinese(message)

        

        # Step 2: Search knowledge base with Chinese query

        retrieved_results = self.retriever.retrieve(query_chinese, top_k=3)



        # Step 3 & 4: Generate answer and translate to English

        if retrieved_results and retrieved_results[0]['score'] >= 10:

            context = self.retriever.format_retrieved_context(retrieved_results)

            answer_chinese = self._generate_answer_from_context(query_chinese, context)

            answer_english = self._translate_to_english(answer_chinese)

            return answer_english

        else:

            answer_chinese = self._generate_answer_from_llm(query_chinese)

            answer_english = self._translate_to_english(answer_chinese)

            return answer_english



    def chat_stream(self, message: str) -> Generator[str, None, None]:

        """Process user message in streaming mode"""

        # Step 1: Translate user question to Chinese

        query_chinese = self._translate_to_chinese(message)

        

        # Step 2: Search knowledge base with Chinese query

        retrieved_results = self.retriever.retrieve(query_chinese, top_k=3)



        # Step 3 & 4: Generate answer and translate to English

        if retrieved_results and retrieved_results[0]['score'] >= 10:

            context = self.retriever.format_retrieved_context(retrieved_results)

            answer_chinese = ""

            for chunk in self._generate_stream_from_context(query_chinese, context):

                answer_chinese += chunk

            answer_english = self._translate_to_english(answer_chinese)

            yield answer_english

        else:

            answer_chinese = ""

            for chunk in self._generate_stream_from_llm(query_chinese):

                answer_chinese += chunk

            answer_english = self._translate_to_english(answer_chinese)

            yield answer_english



    def _generate_answer_from_context(self, question: str, context: str) -> str:

        """Based on retrieved context to generate answer (in Chinese)"""

        prompt = f"""你是一个专业的导游。请根据以下知识库信息，用简洁友好的语气回答游客的问题。



知识库信息：

{context}



游客问题：{question}



要求：

1. 只回答游客问的内容，不要展开不相关的信息

2. 像导游一样自然地回答

3. 如果知识库中有多个相关内容，优先回答最相关的

4. 用中文回答"""



        response = self.client.chat.completions.create(

            model="deepseek-chat",

            messages=[

                {"role": "system", "content": "你是一个热情专业的导游。用简洁友好的语气回答游客的问题。"},

                {"role": "user", "content": prompt}

            ],

            max_tokens=2000,

            temperature=0.3

        )



        return response.choices[0].message.content



    def _generate_stream_from_context(self, question: str, context: str) -> Generator[str, None, None]:

        """Based on retrieved context to generate streaming answer (in Chinese)"""

        prompt = f"""你是一个专业的导游。请根据以下知识库信息，用简洁友好的语气回答游客的问题。



知识库信息：

{context}



游客问题：{question}



要求：

1. 只回答游客问的内容，不要展开不相关的信息

2. 像导游一样自然地回答

3. 如果知识库中有多个相关内容，优先回答最相关的

4. 用中文回答"""



        response = self.client.chat.completions.create(

            model="deepseek-chat",

            messages=[

                {"role": "system", "content": "你是一个热情专业的导游。用简洁友好的语气回答游客的问题。"},

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

        """When no relevant knowledge is found, use LLM to generate streaming answer (in Chinese)"""

        prompt = f"""你是一个热情专业的导游。游客问了你一个问题，请用简洁友好的语气回答。



游客问题：{question}



要求：用中文回答，像导游一样自然地回答。"""



        response = self.client.chat.completions.create(

            model="deepseek-chat",

            messages=[

                {"role": "system", "content": "你是一个热情专业的导游。用简洁友好的语气回答游客的问题。"},

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

        """When no relevant knowledge is found, use LLM to generate answer (in Chinese)"""

        prompt = f"""你是一个热情专业的导游。游客问了你一个问题，请用简洁友好的语气回答。



游客问题：{question}



要求：用中文回答，像导游一样自然地回答。"""



        response = self.client.chat.completions.create(

            model="deepseek-chat",

            messages=[

                {"role": "system", "content": "你是一个热情专业的导游。用简洁友好的语气回答游客的问题。"},

                {"role": "user", "content": prompt}

            ],

            max_tokens=2000,

            temperature=0.3

        )



        return response.choices[0].message.content



    def _extract_keywords_for_images(self, question: str) -> str:

        """Extract keywords for image search from the question (in Chinese)"""

        try:

            response = self.client.chat.completions.create(

                model="deepseek-chat",

                messages=[

                    {"role": "system", "content": "你是一个关键词提取助手。从用户问题中提取适合搜索旅游图片的关键词。只返回关键词，用逗号分隔，最多3个。"},

                    {"role": "user", "content": f"用户问题: {question}\n提取2-3个适合图片搜索的关键词，用逗号分隔。例如：凤凰古城、吊脚楼、西湖"}

                ],

                max_tokens=100,

                temperature=0.3

            )

            return response.choices[0].message.content.strip()

        except:

            return question[:20]



    def chat_with_images(self, message: str) -> Dict[str, Any]:

        """Chat with images, returns answer and image URL list"""

        # Step 1: Translate user question to Chinese

        query_chinese = self._translate_to_chinese(message)

        

        # Step 2: Search knowledge base with Chinese query

        retrieved_results = self.retriever.retrieve(query_chinese, top_k=3)



        # 判断是否需要图片：只有当问题涉及具体景点时才搜索图片

        need_images = self._should_include_images(query_chinese, retrieved_results)



        if need_images:

            # 提取关键词并搜索图片

            keywords = self._extract_keywords_for_images(query_chinese)

            keyword = keywords.split(',')[0].strip()

            image_urls = unsplash_service.search_photos(keyword, per_page=3)

        else:

            keywords = ""

            image_urls = []



        # Step 3 & 4: Generate answer in Chinese and translate to English

        if retrieved_results and retrieved_results[0]['score'] >= 10:

            context = self.retriever.format_retrieved_context(retrieved_results)

            answer_chinese = self._generate_answer_from_context(query_chinese, context)

            answer_english = self._translate_to_english(answer_chinese)

        else:

            answer_chinese = self._generate_answer_from_llm(query_chinese)

            answer_english = self._translate_to_english(answer_chinese)



        return {

            "answer": answer_english,

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

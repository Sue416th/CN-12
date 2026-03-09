"""
Agent数据收集服务 - 用于训练数据收集
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
import json
import os


class TrainingDataCollector:
    """
    训练数据收集器
    
    收集以下数据用于训练LLM Agent:
    1. Agent输入输出对
    2. 用户行为轨迹
    3. 反馈数据
    
    输出格式: JSONL (每行一个JSON)
    """
    
    def __init__(self, output_dir: str = "./training_data"):
        self.output_dir = output_dir
        self.output_file = os.path.join(output_dir, "agent_training_data.jsonl")
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
    
    def collect_agent_execution(
        self,
        agent_name: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        execution_time_ms: float = 0,
    ):
        """收集单个Agent的执行数据"""
        sample = {
            "timestamp": datetime.now().isoformat(),
            "agent_name": agent_name,
            "input": input_data,
            "output": output_data,
            "execution_time_ms": execution_time_ms,
            "data_type": "agent_execution",
        }
        
        self._write_sample(sample)
    
    def collect_user_profile_data(
        self,
        user_id: int,
        user_input: Dict[str, Any],
        generated_profile: Dict[str, Any],
        llm_analysis: Optional[Dict[str, Any]] = None,
    ):
        """收集用户画像生成数据"""
        sample = {
            "timestamp": datetime.now().isoformat(),
            "data_type": "user_profile",
            "user_id": user_id,
            "user_input": user_input,
            "generated_profile": {
                "interests": generated_profile.get("interests", []),
                "budget_level": generated_profile.get("budget_level"),
                "fitness_level": generated_profile.get("fitness_level"),
                "cultural_preferences": generated_profile.get("cultural_preferences", {}),
                "preferred_categories": generated_profile.get("preferred_categories", []),
                "profile_scores": generated_profile.get("profile_scores", {}),
            },
            "llm_analysis": llm_analysis,
        }
        
        self._write_sample(sample)
    
    def collect_itinerary_data(
        self,
        user_id: int,
        city: str,
        dates: str,
        user_profile: Dict[str, Any],
        generated_itinerary: Dict[str, Any],
    ):
        """收集行程规划数据"""
        sample = {
            "timestamp": datetime.now().isoformat(),
            "data_type": "itinerary",
            "user_id": user_id,
            "city": city,
            "dates": dates,
            "user_profile": user_profile,
            "generated_itinerary": generated_itinerary,
        }
        
        self._write_sample(sample)
    
    def collect_feedback_data(
        self,
        user_id: int,
        feedback_type: str,
        content: str,
        before_profile: Dict[str, Any],
        after_profile: Optional[Dict[str, Any]] = None,
    ):
        """收集用户反馈数据"""
        sample = {
            "timestamp": datetime.now().isoformat(),
            "data_type": "feedback",
            "user_id": user_id,
            "feedback_type": feedback_type,
            "content": content,
            "before_profile": before_profile,
            "after_profile": after_profile,
        }
        
        self._write_sample(sample)
    
    def _write_sample(self, sample: Dict[str, Any]):
        """写入单条样本到JSONL文件"""
        try:
            with open(self.output_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(sample, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"Warning: Failed to write training sample: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取收集的统计数据"""
        if not os.path.exists(self.output_file):
            return {"total_samples": 0}
        
        stats = {
            "total_samples": 0,
            "by_type": {},
        }
        
        try:
            with open(self.output_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        sample = json.loads(line)
                        stats["total_samples"] += 1
                        
                        data_type = sample.get("data_type", "unknown")
                        stats["by_type"][data_type] = stats["by_type"].get(data_type, 0) + 1
        except Exception as e:
            print(f"Warning: Failed to read statistics: {e}")
        
        return stats


# 全局实例
_training_collector: Optional[TrainingDataCollector] = None


def get_training_collector() -> TrainingDataCollector:
    """获取训练数据收集器单例"""
    global _training_collector
    if _training_collector is None:
        _training_collector = TrainingDataCollector()
    return _training_collector

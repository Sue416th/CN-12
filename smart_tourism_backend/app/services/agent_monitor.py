from typing import Any, Dict, List, Optional
from datetime import datetime
import time
import json
from pathlib import Path


class AgentMonitor:
    """
    Agent性能监控器
    记录各Agent的执行时间、成功率、调用次数等指标
    """

    def __init__(self):
        self.metrics_file = Path("data/agent_metrics.json")
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_metrics_file()

    def _ensure_metrics_file(self):
        """确保metrics文件存在"""
        if not self.metrics_file.exists():
            self._save_metrics({
                "agents": {},
                "total_requests": 0,
                "total_errors": 0,
            })

    def _load_metrics(self) -> Dict:
        """加载指标数据"""
        try:
            with open(self.metrics_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"agents": {}, "total_requests": 0, "total_errors": 0}

    def _save_metrics(self, metrics: Dict):
        """保存指标数据"""
        try:
            with open(self.metrics_file, 'w', encoding='utf-8') as f:
                json.dump(metrics, f, ensure_ascii=False, indent=2)
        except:
            pass

    def record_start(self, agent_name: str) -> str:
        """记录Agent开始执行，返回execution_id"""
        execution_id = f"{agent_name}_{int(time.time() * 1000)}"
        return execution_id

    def record_end(
        self,
        agent_name: str,
        execution_id: str,
        success: bool = True,
        error: str = None,
        context: Dict = None,
    ):
        """记录Agent执行完成"""
        metrics = self._load_metrics()

        # 更新总体统计
        metrics["total_requests"] = metrics.get("total_requests", 0) + 1
        if not success:
            metrics["total_errors"] = metrics.get("total_errors", 0) + 1

        # 更新单个Agent的统计
        if agent_name not in metrics["agents"]:
            metrics["agents"][agent_name] = {
                "call_count": 0,
                "success_count": 0,
                "error_count": 0,
                "total_duration_ms": 0,
                "avg_duration_ms": 0,
                "last_call": None,
            }

        agent_metrics = metrics["agents"][agent_name]
        agent_metrics["call_count"] = agent_metrics.get("call_count", 0) + 1

        if success:
            agent_metrics["success_count"] = agent_metrics.get("success_count", 0) + 1
        else:
            agent_metrics["error_count"] = agent_metrics.get("error_count", 0) + 1

        # 提取执行时间
        if execution_id:
            try:
                # 从execution_id提取时间戳
                timestamp = int(execution_id.split("_")[-1])
                duration = int(time.time() * 1000) - timestamp
                agent_metrics["total_duration_ms"] = agent_metrics.get("total_duration_ms", 0) + duration
                agent_metrics["avg_duration_ms"] = (
                    agent_metrics["total_duration_ms"] / agent_metrics["call_count"]
                )
            except:
                pass

        agent_metrics["last_call"] = datetime.now().isoformat()

        # 保存
        self._save_metrics(metrics)

    def get_agent_stats(self, agent_name: str = None) -> Dict:
        """获取Agent统计信息"""
        metrics = self._load_metrics()

        if agent_name:
            return metrics["agents"].get(agent_name, {})

        return {
            "overall": {
                "total_requests": metrics.get("total_requests", 0),
                "total_errors": metrics.get("total_errors", 0),
                "success_rate": (
                    (metrics.get("total_requests", 0) - metrics.get("total_errors", 0))
                    / max(1, metrics.get("total_requests", 1))
                ) * 100,
            },
            "agents": metrics.get("agents", {}),
        }

    def get_health_status(self) -> Dict:
        """获取系统健康状态"""
        metrics = self._load_metrics()
        total = metrics.get("total_requests", 0)
        errors = metrics.get("total_errors", 0)

        if total == 0:
            return {"status": "no_data", "message": "No requests yet"}

        error_rate = errors / total * 100

        if error_rate < 5:
            status = "healthy"
        elif error_rate < 20:
            status = "degraded"
        else:
            status = "unhealthy"

        return {
            "status": status,
            "total_requests": total,
            "error_rate": f"{error_rate:.1f}%",
            "message": f"{total} requests, {errors} errors",
        }


# 全局单例
_monitor = None


def get_monitor() -> AgentMonitor:
    """获取监控器单例"""
    global _monitor
    if _monitor is None:
        _monitor = AgentMonitor()
    return _monitor

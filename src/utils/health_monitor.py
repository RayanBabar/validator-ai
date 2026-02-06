"""
Health Monitoring Service.
Tracks status, latency, success rate, uptime, and daily usage for external services.
"""

import time
import logging
import asyncio
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Services to monitor
MONITORED_SERVICES = ["openai", "claude", "tavily"]


@dataclass
class ServiceMetrics:
    """Metrics for a single service."""
    
    # Latency tracking (last 100 samples for percentile calculation)
    latency_samples: List[float] = field(default_factory=list)
    
    # Success/failure counts for success rate
    success_count: int = 0
    failure_count: int = 0
    
    # Daily usage (resets at midnight UTC)
    daily_usage: int = 0
    last_reset_date: str = ""
    
    # Uptime tracking
    first_call_time: float = 0.0  # When we first called this service
    total_uptime_seconds: float = 0.0  # Time service was "up"
    total_downtime_seconds: float = 0.0  # Time service was "down"
    last_status_change_time: float = 0.0  # When status last changed
    last_known_status: str = "unknown"  # "up", "down", or "unknown"

    # Cost & Usage Tracking
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost: float = 0.0
    # Breakdown by specific model: { "gpt-5.2": {"input": 0, "output": 0, "cost": 0.0, ...} }
    model_usage: Dict[str, dict] = field(default_factory=dict)


class HealthMonitor:
    """
    Singleton health monitor that tracks metrics for external services.
    Thread-safe for concurrent access.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._metrics: Dict[str, ServiceMetrics] = {
            service: ServiceMetrics() for service in MONITORED_SERVICES
        }
        self._metrics_lock = asyncio.Lock()
        self._start_time = time.time()
        self._initialized = True
        logger.info("HealthMonitor initialized")
    
    async def record_call(
        self, 
        service: str, 
        latency_ms: float, 
        success: bool,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost: float = 0.0,
        model_name: str = None
    ) -> None:
        """
        Record a service call with its latency, success status, and usage metrics.
        
        Args:
            service: Service name (openai, claude, tavily)
            latency_ms: Latency in milliseconds
            success: Whether the call succeeded
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            cost: Estimated cost in USD
            model_name: Specific model used (e.g. gpt-5.2)
        """
        if service not in self._metrics:
            return
        
        current_time = time.time()
        
        async with self._metrics_lock:
            metrics = self._metrics[service]
            
            # Initialize first call time
            if metrics.first_call_time == 0.0:
                metrics.first_call_time = current_time
                metrics.last_status_change_time = current_time
            
            # Update uptime/downtime tracking
            if metrics.last_status_change_time > 0:
                elapsed = current_time - metrics.last_status_change_time
                if metrics.last_known_status == "up":
                    metrics.total_uptime_seconds += elapsed
                elif metrics.last_known_status == "down":
                    metrics.total_downtime_seconds += elapsed
            
            # Update status based on this call
            new_status = "up" if success else "down"
            metrics.last_known_status = new_status
            metrics.last_status_change_time = current_time
            
            # Track latency (keep last 100 samples)
            metrics.latency_samples.append(latency_ms)
            if len(metrics.latency_samples) > 100:
                metrics.latency_samples.pop(0)
            
            # Track success/failure
            if success:
                metrics.success_count += 1
            else:
                metrics.failure_count += 1
            
            # Track daily usage (reset at midnight UTC)
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            if metrics.last_reset_date != today:
                metrics.daily_usage = 0
                metrics.last_reset_date = today
            metrics.daily_usage += 1

            # Update Cost & Usage
            metrics.total_input_tokens += input_tokens
            metrics.total_output_tokens += output_tokens
            metrics.total_cost += cost
            
            # Update Model Breakdown
            if model_name:
                if model_name not in metrics.model_usage:
                    metrics.model_usage[model_name] = {
                        "calls": 0, "input": 0, "output": 0, "cost": 0.0
                    }
                m_stats = metrics.model_usage[model_name]
                m_stats["calls"] += 1
                m_stats["input"] += input_tokens
                m_stats["output"] += output_tokens
                m_stats["cost"] += cost
    
    async def get_metrics(self) -> Dict[str, dict]:
        """
        Get metrics for all monitored services.
        
        Returns:
            Dictionary with service metrics including status, latency, success rate, uptime, and daily usage.
        """
        result = {}
        current_time = time.time()
        
        async with self._metrics_lock:
            for service, metrics in self._metrics.items():
                total_calls = metrics.success_count + metrics.failure_count
                
                if total_calls == 0:
                    # No calls made yet
                    result[service] = {
                        "status": "not used",
                        "latency_min_ms": 0,
                        "latency_max_ms": 0,
                        "latency_avg_ms": 0,
                        "latency_p95_ms": 0,
                        "success_rate": 0,
                        "uptime_percent": 0,
                        "daily_usage": 0,
                        "total_cost": 0.0,
                        "total_input_tokens": 0,
                        "total_output_tokens": 0
                    }
                else:
                    # Calculate latency stats
                    samples = metrics.latency_samples
                    min_latency = round(min(samples), 1) if samples else 0
                    max_latency = round(max(samples), 1) if samples else 0
                    avg_latency = round(sum(samples) / len(samples), 1) if samples else 0
                    p95_latency = round(sorted(samples)[int(len(samples) * 0.95)] if samples else 0, 1)
                    
                    # Calculate success rate
                    success_rate = round(metrics.success_count / total_calls, 3)
                    
                    # Calculate uptime percentage
                    # Add current period to the calculation
                    total_uptime = metrics.total_uptime_seconds
                    total_downtime = metrics.total_downtime_seconds
                    
                    # Add elapsed time since last status change
                    if metrics.last_status_change_time > 0:
                        elapsed = current_time - metrics.last_status_change_time
                        if metrics.last_known_status == "up":
                            total_uptime += elapsed
                        elif metrics.last_known_status == "down":
                            total_downtime += elapsed
                    
                    total_time = total_uptime + total_downtime
                    uptime_percent = round((total_uptime / total_time) * 100, 1) if total_time > 0 else 0
                    
                    # Determine status based on success rate
                    if success_rate >= 0.8:
                        status = "healthy"
                    elif success_rate >= 0.5:
                        status = "degraded"
                    else:
                        status = "unhealthy"
                    
                    result[service] = {
                        "status": status,
                        "latency_min_ms": min_latency,
                        "latency_max_ms": max_latency,
                        "latency_avg_ms": avg_latency,
                        "latency_p95_ms": p95_latency,
                        "success_rate": success_rate,
                        "uptime_percent": uptime_percent,
                        "daily_usage": metrics.daily_usage,
                        "total_cost": round(metrics.total_cost, 4),
                        "total_input_tokens": metrics.total_input_tokens,
                        "total_output_tokens": metrics.total_output_tokens,
                        "models": metrics.model_usage # Include raw model usage breakdown
                    }
        
        return result

    async def generate_cost_report(self) -> Dict[str, Any]:
        """Generate a detailed cost and usage report."""
        report = {
            "total_project_cost": 0.0,
            "services": {}
        }
        
        async with self._metrics_lock:
            for service, metrics in self._metrics.items():
                service_cost = metrics.total_cost
                report["total_project_cost"] += service_cost
                
                report["services"][service] = {
                    "total_cost": round(service_cost, 4),
                    "total_input": metrics.total_input_tokens,
                    "total_cache_read": metrics.total_cache_read_tokens,
                    "total_output": metrics.total_output_tokens,
                    "models": metrics.model_usage
                }
        
        report["total_project_cost"] = round(report["total_project_cost"], 4)
        return report
    



# Singleton instance
health_monitor = HealthMonitor()

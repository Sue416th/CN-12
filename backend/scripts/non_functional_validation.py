#!/usr/bin/env python3
import argparse
import concurrent.futures
import json
import statistics
import time
import urllib.error
import urllib.request
from typing import Dict, List, Tuple


def call_json(url: str, timeout: float) -> Tuple[bool, float, int]:
    started = time.perf_counter()
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            _ = resp.read()
            latency_ms = (time.perf_counter() - started) * 1000
            return 200 <= resp.status < 400, latency_ms, resp.status
    except urllib.error.HTTPError as exc:
        latency_ms = (time.perf_counter() - started) * 1000
        return False, latency_ms, exc.code
    except Exception:
        latency_ms = (time.perf_counter() - started) * 1000
        return False, latency_ms, 0


def run_load_test(url: str, requests_total: int, concurrency: int, timeout: float) -> Dict:
    latencies: List[float] = []
    statuses: Dict[int, int] = {}
    success = 0

    def single_call():
        ok, latency, status = call_json(url, timeout)
        return ok, latency, status

    started = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(single_call) for _ in range(requests_total)]
        for fut in concurrent.futures.as_completed(futures):
            ok, latency, status = fut.result()
            latencies.append(latency)
            statuses[status] = statuses.get(status, 0) + 1
            if ok:
                success += 1
    elapsed = time.perf_counter() - started

    sorted_lat = sorted(latencies) if latencies else [0.0]
    p95_idx = min(len(sorted_lat) - 1, max(0, int(len(sorted_lat) * 0.95) - 1))
    p99_idx = min(len(sorted_lat) - 1, max(0, int(len(sorted_lat) * 0.99) - 1))
    error_count = requests_total - success

    return {
        "target_url": url,
        "requests": requests_total,
        "concurrency": concurrency,
        "elapsed_seconds": round(elapsed, 3),
        "throughput_rps": round(requests_total / elapsed, 2) if elapsed > 0 else 0.0,
        "success_rate_pct": round((success / requests_total) * 100, 2) if requests_total else 0.0,
        "error_rate_pct": round((error_count / requests_total) * 100, 2) if requests_total else 0.0,
        "latency_ms": {
            "avg": round(statistics.mean(latencies), 2) if latencies else 0.0,
            "p95": round(sorted_lat[p95_idx], 2),
            "p99": round(sorted_lat[p99_idx], 2),
            "max": round(max(sorted_lat), 2),
        },
        "status_codes": statuses,
    }


def run_recovery_check(url: str, timeout: float, retries: int) -> Dict:
    first_ok, first_latency, _ = call_json(url, timeout)
    if first_ok:
        return {
            "first_try_success": True,
            "recovered_after_retry": False,
            "attempts_used": 1,
            "first_latency_ms": round(first_latency, 2),
        }

    for attempt in range(2, retries + 2):
        ok, latency, _ = call_json(url, timeout)
        if ok:
            return {
                "first_try_success": False,
                "recovered_after_retry": True,
                "attempts_used": attempt,
                "recovery_latency_ms": round(latency, 2),
            }
    return {
        "first_try_success": False,
        "recovered_after_retry": False,
        "attempts_used": retries + 1,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Non-functional validation for API endpoints")
    parser.add_argument("--url", default="http://127.0.0.1:3204/", help="Target URL")
    parser.add_argument("--requests", type=int, default=100, help="Total requests")
    parser.add_argument("--concurrency", type=int, default=20, help="Concurrent workers")
    parser.add_argument("--timeout", type=float, default=5.0, help="Per request timeout")
    parser.add_argument("--retries", type=int, default=2, help="Recovery retries")
    args = parser.parse_args()

    load_metrics = run_load_test(args.url, args.requests, args.concurrency, args.timeout)
    recovery_metrics = run_recovery_check(args.url, args.timeout, args.retries)
    output = {
        "load_test": load_metrics,
        "stability": recovery_metrics,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))

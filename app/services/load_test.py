import httpx
import asyncio
import time
import matplotlib.pyplot as plt
import os

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Connection": "keep-alive"
}


async def hit(client, url):
    start = time.time()
    try:
        response = await client.get(url, headers=HEADERS)
        latency = time.time() - start
        return latency, response.status_code
    except Exception:
        return None, "ERROR"


async def run_load_test(url: str, requests: int = 100):
    latencies = []
    status_codes = []

    try:
        async with httpx.AsyncClient(timeout=15) as client:

            tasks = [hit(client, url) for _ in range(requests)]
            results = await asyncio.gather(*tasks)

        for latency, status in results:
            if latency:
                latencies.append(latency)
            status_codes.append(status)

        if not latencies:
            raise Exception("All requests failed")

        avg_latency = sum(latencies) / len(latencies)

        # 🔹 Generate Graph
        graph_path = generate_graph(latencies)

    except Exception as e:
        return {
            "test": "LOAD_TEST",
            "status": "SKIPPED",
            "error": repr(e)
        }

    return {
        "test": "LOAD_TEST",
        "status": "COMPLETED",
        "avg_latency": round(avg_latency, 3),
        "total_requests": requests,
        "successful_requests": len(latencies),
        "failed_requests": requests - len(latencies),
        "graph": graph_path
    }


def generate_graph(latencies):
    if not os.path.exists("app/static"):
        os.makedirs("app/static")

    path = "app/static/load_test_graph.png"

    plt.figure()
    plt.plot(latencies)
    plt.xlabel("Request Number")
    plt.ylabel("Response Time (seconds)")
    plt.title("Load Test Latency Graph")

    plt.savefig(path)
    plt.close()

    return "/static/load_test_graph.png"
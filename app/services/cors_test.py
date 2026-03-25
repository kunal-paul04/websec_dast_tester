import httpx

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Origin": "http://evil.com",
    "Connection": "keep-alive"
}

async def run_cors_test(url: str):
    issues = []
    details = {}

    try:
        async with httpx.AsyncClient(timeout=15) as client:

            try:
                response = await client.options(url, headers=HEADERS)

            except Exception as e:
                response = await client.get(url, headers=HEADERS)

        headers = response.headers

        allow_origin = headers.get("access-control-allow-origin")
        allow_credentials = headers.get("access-control-allow-credentials")

        details["allow_origin"] = allow_origin
        details["allow_credentials"] = allow_credentials

        if allow_origin == "*":
            issues.append("Wildcard (*) origin allowed")

        if allow_origin == "http://evil.com":
            issues.append("Reflected arbitrary origin")

        if allow_credentials == "true":
            issues.append("Credentials allowed")

        status = "FAIL" if issues else "PASS"

    except Exception as e:
        return {
            "test": "CORS",
            "status": "SKIPPED",
            "note": "Target did not respond (possible blocking or timeout)",
            "error": repr(e)
        }

    return {
        "test": "CORS",
        "status": status,
        "issues": issues,
        "details": details
    }
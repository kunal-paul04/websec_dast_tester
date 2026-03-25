import httpx

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Connection": "keep-alive"
}

SECURITY_HEADERS = [
    "x-frame-options",
    "content-security-policy",
    "x-content-type-options",
    "strict-transport-security",
    "x-xss-protection"
]


async def run_header_test(url: str):
    missing = []
    present = {}

    try:
        async with httpx.AsyncClient(timeout=15) as client:

            # Retry logic
            for i in range(2):
                try:
                    response = await client.get(url, headers=HEADERS)
                    break
                except Exception as e:
                    if i == 1:
                        raise
                    import asyncio
                    await asyncio.sleep(1)

        headers = response.headers

        for header in SECURITY_HEADERS:
            value = headers.get(header)
            if value:
                present[header] = value
            else:
                missing.append(header)

        status = "FAIL" if missing else "PASS"

    except Exception as e:
        return {
            "test": "HEADER_SECURITY",
            "status": "SKIPPED",
            "note": "Target did not respond or blocked request",
            "error": repr(e)
        }

    return {
        "test": "HEADER_SECURITY",
        "status": status,
        "missing_headers": missing,
        "present_headers": present
    }
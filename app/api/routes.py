from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse

from app.core.logger import get_logger
from app.core.dependencies import templates
# Import modules related to CORS and header tests
from app.services.cors_test import run_cors_test
from app.services.header_test import run_header_test
# Import module related to SQL Injection test
from app.services.sqli_test import run_sqli_test
# Import module related to Load Test
from app.services.load_test import run_load_test
# Import module related to PDF generation
from app.reports.pdf_generator import generate_pdf_report

router = APIRouter()
logger = get_logger()


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request, "index.html", {"request": request})


@router.post("/scan", response_class=HTMLResponse)
async def scan(
    request: Request,
    url: str = Form(...),
    test_type: str = Form(...)
):
    request_id = request.state.request_id

    logger.info(
        f"Scan requested for {url} with test {test_type}",
        extra={"request_id": request_id}
    )

    results = []

    if test_type == "cors":
        cors_result = await run_cors_test(url)
        results.append(cors_result)

    elif test_type == "header":
        header_result = await run_header_test(url)
        results.append(header_result)
    
    elif test_type == "sqli":
        sqli_result = await run_sqli_test(url)
        results.append(sqli_result)
    
    elif test_type == "load":
        load_result = await run_load_test(url)
        results.append(load_result)

    elif test_type == "all":
        cors_result = await run_cors_test(url)
        header_result = await run_header_test(url)
        sqli_result = await run_sqli_test(url)
        load_result = await run_load_test(url)

        results.extend([cors_result, header_result, sqli_result, load_result])
    
    pdf_path = generate_pdf_report(results, url)

    return templates.TemplateResponse(
        request,
        "report.html",
        {
            "request": request,
            "status": "COMPLETED",
            "results": results,
            "url": url,
            "test_type": test_type,
            "pdf_path": pdf_path
        }
    )
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
import os

def generate_pdf_report(results, url, filename="websec_scan_analysis_report.pdf"):
    path = f"app/static/{filename}"

    doc = SimpleDocTemplate(path)
    styles = getSampleStyleSheet()

    elements = []

    # Title
    elements.append(Paragraph("Web Security Test Report", styles["Title"]))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph(f"Target URL: {url}", styles["Normal"]))
    elements.append(Spacer(1, 10))

    for r in results:
        elements.append(Paragraph(f"Test: {r['test']}", styles["Heading2"]))
        elements.append(Paragraph(f"Status: {r['status']}", styles["Normal"]))
        elements.append(Spacer(1, 8))

        # CORS
        if r["test"] == "CORS":
            if r.get("issues"):
                elements.append(Paragraph("Issues:", styles["Normal"]))
                for issue in r["issues"]:
                    elements.append(Paragraph(f"- {issue}", styles["Normal"]))

            if r.get("details"):
                for k, v in r["details"].items():
                    elements.append(Paragraph(f"{k}: {v}", styles["Normal"]))

        # HEADER
        if r["test"] == "HEADER_SECURITY":
            if r.get("missing_headers"):
                elements.append(Paragraph("Missing Headers:", styles["Normal"]))
                for h in r["missing_headers"]:
                    elements.append(Paragraph(f"- {h}", styles["Normal"]))

        # SQLi
        if r["test"] == "SQL_INJECTION":
            if r.get("findings"):
                elements.append(Paragraph("Findings:", styles["Normal"]))
                for f in r["findings"]:
                    elements.append(Paragraph(f"- {f}", styles["Normal"]))

        # LOAD TEST
        if r["test"] == "LOAD_TEST":
            elements.append(Paragraph(f"Avg Latency: {r.get('avg_latency')} sec", styles["Normal"]))
            elements.append(Paragraph(f"Success: {r.get('successful_requests')}", styles["Normal"]))

            # Add graph
            if r.get("graph"):
                img_path = "app" + r["graph"]  # convert /static/... to app/static/...
                if os.path.exists(img_path):
                    elements.append(Spacer(1, 10))
                    elements.append(Image(img_path, width=400, height=200))

        elements.append(Spacer(1, 15))

    doc.build(elements)

    return f"/static/{filename}"
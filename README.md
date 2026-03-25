# 🔐 WebSec DAST Platform (FastAPI + Docker)

A lightweight **Dynamic Application Security Testing (DAST)** platform built with **FastAPI**, supporting vulnerability scanning, performance testing, and report generation.

---

# 🚀 Features

## 🔍 Security Testing
- ✅ CORS Misconfiguration Detection
- ✅ Security Headers Analysis
- ✅ SQL Injection Detection (Safe Heuristic)

## ⚡ Performance Testing
- ✅ Async Load Testing
- ✅ Latency Graph Visualization

## 📊 Reporting
- ✅ Web UI (Jinja)
- ✅ Graphical output
- ✅ Downloadable PDF reports

## 🏗️ Infrastructure
- ✅ Dockerized setup
- ✅ Background workers (Redis + RQ)
- ✅ Structured logging with Request ID

---

# 🧱 Architecture Overview
            ┌──────────────┐
            │   Browser UI │
            └──────┬───────┘
                   │
            ┌──────▼───────┐
            │   FastAPI    │
            │  (Web Layer) │
            └──────┬───────┘
                   │
         ┌─────────┼──────────────┐
         │         │              │
    ┌────▼────┐ ┌──▼───────┐ ┌────▼────┐
    │ CORS    │ │ SQLi     │ │ Load    │
    │ Scanner │ │ Scanner  │ │ Tester  │
    └─────────┘ └──────────┘ └─────────┘
    └──────────────┼──────────────┘
            ┌──────▼───────┐
            │ Reports      │
            │ (PDF/Graph)  │
            └──────────────┘

---

# 🔄 End-to-End Flow
User Input (URL + Test Type)
↓
FastAPI Route (/scan)
↓
Scanner Engine Executes:

CORS Test
Header Test
SQLi Test
Load Test
↓
Results Aggregated
↓
Graph Generated (if load test)
↓
PDF Report Generated
↓
User Fetches Result via Job Status API
↓
UI Displays Results + Download Option

---

# ⚙️ Setup Instructions

## 🔧 Local Setup

```bash
git clone <repo-url>
cd websec_tester

python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload
```
---

# 🌐 Usage
1. Open:
```bash
http://localhost:8000
```
2. Enter:
- Target URL
- Select test type
- Submit →
- View:
- - Results
- - Graphs
- - Download PDF
---

# 📊 Sample Output
## CORS
```bash
FAIL
- Wildcard (*) origin allowed
```
## Header Security
```bash
Missing:
- x-frame-options
```
## SQL Injection
```bash
Possible SQL Injection detected
```
## Load Test
```bash
Avg Latency: 0.23s
Graph: displayed
```
---

# ⚠️ Security Disclaimer

This tool is for:
- ✅ Learning
- ✅ Testing owned systems
- ✅ Authorized environments

Do NOT use against:
- ❌ Unauthorized targets
- ❌ Production systems without permission
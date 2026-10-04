"""Start the Report Desk web app: python -m agency_report_agent.web"""
import uvicorn

if __name__ == "__main__":
    print("\n  Report Desk running at http://127.0.0.1:8000\n")
    uvicorn.run("agency_report_agent.web.app:app", host="127.0.0.1", port=8000, reload=False)

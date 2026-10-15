"""
Converzia — AI B2B Sales Outreach Platform
Root Entrypoint & Launcher
------------------------------------------
This launcher seamlessly routes between the FastAPI REST backend
and the Streamlit Interactive Demonstration Dashboard.

USAGE:
1. To launch the FastAPI REST API with Swagger Docs:
   $ uvicorn app.main:app --reload --port 8000

2. To launch the Interactive Visual Command Center:
   $ streamlit run app.py
"""

import sys
import os

# Ensure current working directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Check if running under Streamlit
is_streamlit = "streamlit" in sys.modules or any("streamlit" in arg for arg in sys.argv)

if is_streamlit:
    # Delegate cleanly to modular dashboard
    import dashboard.app
else:
    if __name__ == "__main__":
        import uvicorn
        print("=" * 60)
        print("⚡ Starting Converzia FastAPI Outbound Engine...")
        print("API Documentation: http://localhost:8000/docs")
        print("Alternative Dashboard: run 'streamlit run app.py'")
        print("=" * 60)
        uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
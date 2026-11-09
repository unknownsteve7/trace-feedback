import sys
import traceback
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from app.main import app
except Exception as e:
    err_trace = traceback.format_exc()
    print("FATAL STARTUP EXCEPTION ON VERCEL:\n", err_trace, flush=True)
    
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse

    app = FastAPI(title="TRACE Startup Error Diagnostic")

    @app.api_route("/{full_path:path}", methods=["GET", "POST"])
    async def diagnose(full_path: str):
        html = f"""
        <html>
        <body style="font-family: monospace; padding: 20px; background: #fff1f0; color: #a8071a;">
            <h2>TRACE FastAPI Startup Exception on Vercel</h2>
            <p>The application encountered an error during cold start:</p>
            <pre style="background: #fff; padding: 15px; border: 1px solid #ffa39e; border-radius: 6px; overflow-x: auto;">{err_trace}</pre>
        </body>
        </html>
        """
        return HTMLResponse(content=html, status_code=500)

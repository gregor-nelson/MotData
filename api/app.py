"""MOT Insights - Single entry point for API and Frontend."""

import uvicorn
from fastapi.staticfiles import StaticFiles

from backend.main import app

# Mount frontend static files at root
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

if __name__ == "__main__":
    print("Starting MOT Insights...")
    print("  API:      http://localhost:8010/api")
    print("  Frontend: http://localhost:8010")
    print()
    uvicorn.run(app, host="0.0.0.0", port=8010)

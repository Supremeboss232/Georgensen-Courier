"""
Georgensen Courier API Server - No Reload
"""
import subprocess
import sys

if __name__ == "__main__":
    # Run Uvicorn without the watch mode
    subprocess.call([
        sys.executable, "-m", "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", "4000"
    ])

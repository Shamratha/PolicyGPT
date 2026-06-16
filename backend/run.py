import os
import sys
import uvicorn

# Ensure the backend root folder is in the Python search path
# This prevents 'ModuleNotFoundError: No module named app' when executing locally
backend_dir = os.path.abspath(os.path.dirname(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

if __name__ == "__main__":
    print("Starting PolicyGPT Backend Server...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

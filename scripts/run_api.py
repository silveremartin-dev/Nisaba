"""
Executable script to launch the Nisaba FastAPI server using Uvicorn.
Usage:
    py scripts/run_api.py --port 8000 --host 127.0.0.1
"""

import argparse
import uvicorn


def main():
    parser = argparse.ArgumentParser(description="Run Nisaba REST API Server")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host address")
    parser.add_argument("--port", type=int, default=8000, help="Bind port number")
    parser.add_argument("--reload", action="store_true", help="Enable hot reload")
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.storage.chunker import FileSharder
    FileSharder.auto_bootstrap_database()

    print(f"🚀 Starting Nisaba API server on http://{args.host}:{args.port}")
    print(f"📖 Interactive Swagger documentation at http://{args.host}:{args.port}/docs")
    print(f"📚 ReDoc alternative documentation at http://{args.host}:{args.port}/redoc")
    uvicorn.run("src.api.app:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()

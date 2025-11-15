
import os
import sys
import subprocess
import argparse
import webbrowser
from time import sleep


def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import streamlit
        import langchain
        import langgraph
        import openai
        import pymupdf
        import docx
        import sqlalchemy
        import loguru

        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install dependencies with: pip install -r requirements.txt")
        return False


def check_env_file():
    """Check if .env file exists and has required variables"""
    if not os.path.exists(".env"):
        print("❌ .env file not found")
        print("Please copy .env.example to .env and configure your settings")
        return False

    with open(".env", "r") as f:
        content = f.read()

    required_vars = ["DATABASE_URL", "OPENAI_API_KEY"]
    missing_vars = []

    for var in required_vars:
        if f"{var}=" not in content:
            missing_vars.append(var)

    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please update your .env file with the required variables")
        return False

    print("✅ Environment configuration is complete")
    return True


def start_backend(port=8000):
    """Start the FastAPI backend server"""
    print(f"🚀 Starting FastAPI backend on port {port}")

    try:

        import socket

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("localhost", port)) == 0:
                print(f"⚠️  Port {port} is already in use")
                choice = input("Do you want to use port 8001 instead? (y/n): ")
                if choice.lower() == "y":
                    port = 8001
                else:
                    sys.exit(1)

        cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            str(port),
            "--reload",
        ]

        print(f"Backend will be available at: http://localhost:{port}")
        print("Press Ctrl+C to stop the server")

        subprocess.run(cmd)

    except KeyboardInterrupt:
        print("\n🛑 Stopping backend server...")
    except Exception as e:
        print(f"❌ Error starting backend: {e}")
        sys.exit(1)


def start_frontend(port=8501):
    """Start the Streamlit frontend"""
    print(f"🎨 Starting Streamlit frontend on port {port}")

    try:

        import socket

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("localhost", port)) == 0:
                print(f"⚠️  Port {port} is already in use")
                choice = input("Do you want to use port 8502 instead? (y/n): ")
                if choice.lower() == "y":
                    port = 8502
                else:
                    sys.exit(1)

        os.environ["STREAMLIT_SERVER_PORT"] = str(port)
        os.environ["STREAMLIT_SERVER_HEADLESS"] = "false"

        cmd = [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "ui/streamlit_app.py",
            "--server.port",
            str(port),
            "--server.headless",
            "false",
        ]

        print(f"Frontend will be available at: http://localhost:{port}")
        print("Press Ctrl+C to stop the frontend")

        subprocess.run(cmd)

    except KeyboardInterrupt:
        print("\n🛑 Stopping frontend...")
    except Exception as e:
        print(f"❌ Error starting frontend: {e}")
        sys.exit(1)


def start_both(backend_port=8000, frontend_port=8501):
    """Start both backend and frontend"""
    print("🌟 Starting Resume Parser Application")
    print("=" * 50)

    if not check_dependencies():
        sys.exit(1)

    if not check_env_file():
        sys.exit(1)

    print("\n🔧 Starting services...")

    backend_process = subprocess.Popen(
        [
            sys.executable,
            "-c",
            f"""
import subprocess
import sys
cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "{backend_port}", "--reload"]
subprocess.run(cmd)
""",
        ]
    )

    print(f"⏳ Waiting for backend to start on port {backend_port}...")
    sleep(3)

    try:
        start_frontend(frontend_port)
    finally:

        backend_process.terminate()
        backend_process.wait()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Resume Parser Application",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_app.py --backend          
  python run_app.py --frontend         
  python run_app.py                    
  python run_app.py --backend-port 9000 --frontend-port 9001
        """,
    )

    parser.add_argument(
        "--backend", action="store_true", help="Start only the FastAPI backend"
    )
    parser.add_argument(
        "--frontend", action="store_true", help="Start only the Streamlit frontend"
    )
    parser.add_argument(
        "--backend-port",
        type=int,
        default=8000,
        help="Port for backend server (default: 8000)",
    )
    parser.add_argument(
        "--frontend-port",
        type=int,
        default=8501,
        help="Port for frontend server (default: 8501)",
    )

    args = parser.parse_args()

    if args.backend and args.frontend:
        start_both(args.backend_port, args.frontend_port)
    elif args.backend:
        start_backend(args.backend_port)
    elif args.frontend:
        start_frontend(args.frontend_port)
    else:

        start_both(args.backend_port, args.frontend_port)


if __name__ == "__main__":
    main()

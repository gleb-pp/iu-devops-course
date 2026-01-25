from fastapi import FastAPI, Request
import platform
import socket
from datetime import datetime
import os
import uvicorn
import logging

logger = logging.getLogger("devops-info-service")


HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

app = FastAPI(
    title="Python Web Application",
    description="Simple production-ready Python"
    "web service with comprehensive system information",
    version="1.0",
)

start_time = datetime.now()


def get_service_info() -> dict[str, str]:
    """Return basic service information."""
    logger.info("Gathering service information")
    return {
        "name": app.title,
        "version": app.version,
        "description": app.description,
        "framework": "FastAPI",
    }


def get_system_info() -> dict[str, str | int | None]:
    """Return basic system information."""
    logger.info("Gathering system information")
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count(),
        "python_version": platform.python_version(),
    }


def get_runtime_info() -> dict[str, str | int | None]:
    """Return runtime information such as uptime and current time."""
    logger.info("Gathering runtime information")
    current_time = datetime.now()
    uptime = current_time - start_time
    return {
        "uptime_seconds": int(uptime.total_seconds()),
        "uptime_human": f"{int(uptime.total_seconds() // 3600)} hours, {int((uptime.total_seconds() % 3600) // 60)} minutes",
        "current_time": current_time.isoformat(),
        "timezone": current_time.astimezone().tzname(),
    }


def get_request_info(request: Request) -> dict[str, str]:
    """Return information about the incoming request."""
    logger.info("Gathering request information")
    return {
        "client_ip": request.client.host if request.client else "Unknown",
        "user_agent": request.headers.get("user-agent", "Unknown"),
        "method": request.method,
        "path": request.url.path,
    }


def get_endpoints_info() -> list[dict[str, str]]:
    """Return a list of available endpoints."""
    logger.info("Gathering endpoints information")
    return [
        {"path": "/", "method": "GET", "description": "Service information"},
        {"path": "/health", "method": "GET", "description": "Health check"},
    ]


@app.get("/")
async def root(request: Request):
    """
    Return comprehensive service and system information.
    """
    logger.info("Root endpoint requested")
    return {
        "service": get_service_info(),
        "system": get_system_info(),
        "runtime": get_runtime_info(),
        "request": get_request_info(request),
        "endpoints": get_endpoints_info(),
    }


@app.get("/health")
async def health():
    """
    Health check endpoint.
    """
    logger.info("Health check requested")
    runtime_info = get_runtime_info()
    return {
        "status": "healthy",
        "timestamp": runtime_info["current_time"],
        "uptime_seconds": runtime_info["uptime_seconds"],
    }


if __name__ == "__main__":
    logger.info(f"Starting FastAPI app on {HOST}:{PORT}, debug={DEBUG}")
    uvicorn.run(app, host=HOST, port=PORT, reload=DEBUG)

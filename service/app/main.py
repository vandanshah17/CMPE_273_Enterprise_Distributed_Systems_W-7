import os
import socket
import time
from contextlib import asynccontextmanager

import requests
from fastapi import FastAPI

SERVICE_NAME = os.getenv("SERVICE_NAME", "python-hello-service")
SERVICE_ID = os.getenv("SERVICE_ID", f"{SERVICE_NAME}-{socket.gethostname()}")
SERVICE_HOST = os.getenv("SERVICE_HOST", "localhost")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8000"))
CONSUL_HOST = os.getenv("CONSUL_HOST", "consul")
CONSUL_PORT = int(os.getenv("CONSUL_PORT", "8500"))
MAX_RETRIES = int(os.getenv("CONSUL_REGISTER_RETRIES", "20"))
RETRY_DELAY_SECONDS = float(os.getenv("CONSUL_REGISTER_RETRY_DELAY", "1.5"))
ENABLE_CONSUL_REGISTRATION = os.getenv("ENABLE_CONSUL_REGISTRATION", "true").lower() == "true"


def consul_url(path: str) -> str:
    return f"http://{CONSUL_HOST}:{CONSUL_PORT}{path}"


def register_with_consul() -> None:
    payload = {
        "ID": SERVICE_ID,
        "Name": SERVICE_NAME,
        "Address": SERVICE_HOST,
        "Port": SERVICE_PORT,
        "Tags": ["python", "fastapi"],
        "Check": {
            "HTTP": f"http://{SERVICE_HOST}:{SERVICE_PORT}/health",
            "Interval": "10s",
            "Timeout": "2s",
            "DeregisterCriticalServiceAfter": "30s",
        },
    }

    last_error = None
    for _ in range(MAX_RETRIES):
        try:
            response = requests.put(consul_url("/v1/agent/service/register"), json=payload, timeout=4)
            response.raise_for_status()
            return
        except requests.RequestException as exc:
            last_error = exc
            time.sleep(RETRY_DELAY_SECONDS)

    raise RuntimeError(f"Failed to register service with Consul: {last_error}")


def deregister_from_consul() -> None:
    try:
        requests.put(consul_url(f"/v1/agent/service/deregister/{SERVICE_ID}"), timeout=4)
    except requests.RequestException:
        pass


@asynccontextmanager
async def lifespan(_: FastAPI):
    if ENABLE_CONSUL_REGISTRATION:
        register_with_consul()
    yield
    if ENABLE_CONSUL_REGISTRATION:
        deregister_from_consul()


app = FastAPI(title="Discovered Service", version="1.0.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service_id": SERVICE_ID}


@app.get("/hello")
def hello() -> dict:
    return {
        "message": "Hello from discovered instance",
        "service_name": SERVICE_NAME,
        "service_id": SERVICE_ID,
        "host": SERVICE_HOST,
        "port": SERVICE_PORT,
    }

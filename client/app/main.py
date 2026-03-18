import os
import random

import requests
from fastapi import FastAPI, HTTPException

CONSUL_HOST = os.getenv("CONSUL_HOST", "consul")
CONSUL_PORT = int(os.getenv("CONSUL_PORT", "8500"))
TARGET_SERVICE = os.getenv("TARGET_SERVICE", "python-hello-service")

app = FastAPI(title="Discovery Client", version="1.0.0")


def consul_url(path: str) -> str:
    return f"http://{CONSUL_HOST}:{CONSUL_PORT}{path}"


def discover_instances() -> list[dict]:
    response = requests.get(
        consul_url(f"/v1/health/service/{TARGET_SERVICE}?passing=true"),
        timeout=4,
    )
    response.raise_for_status()
    raw_entries = response.json()

    instances = []
    for entry in raw_entries:
        service = entry.get("Service", {})
        address = service.get("Address")
        port = service.get("Port")
        service_id = service.get("ID")
        if address and port:
            instances.append({"address": address, "port": port, "id": service_id})

    return instances


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "target_service": TARGET_SERVICE}


@app.get("/instances")
def instances() -> dict:
    try:
        discovered = discover_instances()
        return {"target_service": TARGET_SERVICE, "instances": discovered}
    except requests.RequestException as exc:
        raise HTTPException(status_code=503, detail=f"Failed to query registry: {exc}") from exc


@app.get("/invoke")
def invoke() -> dict:
    try:
        discovered = discover_instances()
    except requests.RequestException as exc:
        raise HTTPException(status_code=503, detail=f"Failed to query registry: {exc}") from exc

    if not discovered:
        raise HTTPException(status_code=404, detail="No healthy service instances discovered")

    chosen = random.choice(discovered)
    target_url = f"http://{chosen['address']}:{chosen['port']}/hello"

    try:
        response = requests.get(target_url, timeout=4)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Call to discovered instance failed: {exc}") from exc

    return {
        "selected_instance": chosen,
        "target_url": target_url,
        "response": response.json(),
    }

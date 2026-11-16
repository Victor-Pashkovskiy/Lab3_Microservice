from fastapi import FastAPI, HTTPException, Header
import httpx
import uuid
from datetime import datetime
from pydantic import BaseModel
from services.shared.event_bus import event_bus
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
async def problem_details_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        media_type="application/problem+json",
        content={
            "type": "about:blank",
            "title": "Error",
            "status": exc.status_code,
            "detail": exc.detail,
            "instance": request.url.path
        }
    )

app = FastAPI(title="build-service")
app.add_exception_handler(HTTPException, problem_details_handler)
BUILDS_DB = {}
IDEMPOTENCY_KEYS = set()

class CreateBuildRequest(BaseModel):
    name: str

class AddItemRequest(BaseModel):
    componentId: str
    category: str

@app.post("/api/v1/builds", status_code=201)
async def create_build(req: CreateBuildRequest, idempotency_key: str = Header(...)):
    if idempotency_key in IDEMPOTENCY_KEYS:
        raise HTTPException(status_code=409, detail="Build already created")
    IDEMPOTENCY_KEYS.add(idempotency_key)
    build_id = str(uuid.uuid4())
    BUILDS_DB[build_id] = {"id": build_id, "name": req.name, "status": "DRAFT", "items": [], "compatible": None}
    return BUILDS_DB[build_id]

@app.post("/api/v1/builds/{id}/items")
async def add_item(id: str, req: AddItemRequest):
    if id not in BUILDS_DB:
        raise HTTPException(status_code=404, detail="Build not found")
    build = BUILDS_DB[id]
    build["items"].append(req.componentId)
    
    #Синхронный вызов compatibility-service
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post("http://compatibility_service:8000/internal/v1/check", json={"buildId": id, "componentIds": build["items"]}, timeout=2.0)
            if resp.status_code == 200:
                check_res = resp.json()
                build["compatible"] = check_res["compatible"]
                if not check_res["compatible"]:
                    raise HTTPException(status_code=409, detail="Incompatible components")
        except httpx.TimeoutException:
            print("[BuildService] Compatibility service timeout! Saving draft.")
            build["compatible"] = False

    #  Имитация асинхронной отправки 
    event_payload = {
        "eventId": str(uuid.uuid4()), 
        "eventType": "build.saved", 
        "payload": {"buildId": id}
    }
    async with httpx.AsyncClient() as client:
        try:
            # Стреляем в recommendation-service, как будто это брокер сообщений
            await client.post("http://recommendation_service:8000/internal/v1/recommendations/rebuild", json={"buildId": id})
            print(f"[Mock-Kafka] Событие build.saved доставлено в recommendation-service")
        except Exception as e:
            print(f"[Mock-Kafka] Не удалось доставить событие: {e}")

    return build
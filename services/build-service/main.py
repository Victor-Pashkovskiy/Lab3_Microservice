
from fastapi import FastAPI, HTTPException, Header
import httpx
import uuid
from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional
from services.shared.event_bus import event_bus

app = FastAPI(title="build-service")

# Имитация БД сборок
BUILDS_DB = {}
IDEMPOTENCY_KEYS = set() # Для защиты от дублей

class CreateBuildRequest(BaseModel):
    name: str

class AddItemRequest(BaseModel):
    componentId: str
    category: str

@app.post("/api/v1/builds", status_code=201)
async def create_build(req: CreateBuildRequest, idempotency_key: str = Header(...)):
    # 1. Проверка идемпотентности
    if idempotency_key in IDEMPOTENCY_KEYS:
        raise HTTPException(status_code=409, detail="Build already created with this key")
    IDEMPOTENCY_KEYS.add(idempotency_key)
    
    build_id = str(uuid.uuid4())
    BUILDS_DB[build_id] = {
        "id": build_id, "name": req.name, "status": "DRAFT", 
        "items": [], "compatible": None
    }
    return BUILDS_DB[build_id]

@app.post("/api/v1/builds/{id}/items")
async def add_item(id: str, req: AddItemRequest):
    if id not in BUILDS_DB:
        raise HTTPException(status_code=404, detail="Build not found")
    
    build = BUILDS_DB[id]
    build["items"].append(req.componentId)
    
    # 2. Синхронный вызов compatibility-service
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post("http://localhost:8002/internal/v1/check", json={
                "buildId": id, "componentIds": build["items"]
            }, timeout=2.0) 
            
            if resp.status_code == 200:
                check_res = resp.json()
                build["compatible"] = check_res["compatible"]
                if not check_res["compatible"]:
                    # Сборка несовместима, возвращаем 409 Conflict
                    raise HTTPException(status_code=409, detail=check_res["violations"])
        except httpx.TimeoutException:
            # 3. Обработка СБОЯ 
            print("[BuildService] Compatibility service timeout! Saving draft.")
            build["compatible"] = False # Пока не знаем
            # В реальности тут мы бы публиковали compatibility.failed
            pass

    # 4. Публикация асинхронного события
    event = {
        "eventId": str(uuid.uuid4()),
        "eventType": "build.saved",
        "schemaVersion": 1,
        "occurredAt": datetime.utcnow().isoformat() + "Z",
        "payload": {"buildId": id, "userId": "u-123"}
    }
    await event_bus.publish("build.saved", event)
    
    return build
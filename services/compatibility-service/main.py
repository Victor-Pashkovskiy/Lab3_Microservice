
from fastapi import FastAPI, HTTPException
import httpx
from pydantic import BaseModel
from typing import List
app = FastAPI(title="compatibility-service")
class CheckRequest(BaseModel):
    buildId: str
    componentIds: List[str]

@app.post("/internal/v1/check")
async def check_compatibility(req: CheckRequest):
    #Синхронный вызов catalog-service
    async with httpx.AsyncClient() as client:
        ids_str = ",".join(req.componentIds)
        # В реальности URL берется из env, тут хардкод для локалки
        resp = await client.get(f"http://localhost:8001/internal/v1/components?ids={ids_str}")
        components = resp.json()
    # проверка
    sockets = set([c.get("socket") for c in components if "socket" in c])
    if len(sockets) > 1:
        return {
            "compatible": False,
            "totalTdp": 0, "totalHeatW": 0,
            "warnings": [], "violations": [{"rule": "socket-match", "message": "Сокеты не совпадают"}]
        }

    total_tdp = sum(c.get("tdp", 0) for c in components)
    return {
        "compatible": True,
        "totalTdp": total_tdp,
        "totalHeatW": total_tdp - 10,
        "warnings": [], "violations": []
    }

from fastapi import FastAPI, HTTPException
import httpx
from pydantic import BaseModel
from typing import List
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

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

app = FastAPI(title="compatibility-service")
app.add_exception_handler(HTTPException, problem_details_handler)

class CheckRequest(BaseModel):
    buildId: str
    componentIds: List[str]

@app.post("/internal/v1/check")
async def check_compatibility(req: CheckRequest):
    #Синхронный вызов catalog-service
    async with httpx.AsyncClient() as client:
        ids_str = ",".join(req.componentIds)
        # В реальности URL берется из env, тут хардкод для локалки
        resp = await client.get(f"http://catalog_service:8000/internal/v1/components?ids={ids_str}")
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
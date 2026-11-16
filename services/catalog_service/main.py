
from fastapi import FastAPI, HTTPException
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
app = FastAPI(title="catalog-service")
app.add_exception_handler(HTTPException, problem_details_handler)
#  БД
COMPONENTS_DB = {
    "cpu-1": {"id": "cpu-1", "name": "Ryzen 5", "category": "CPU", "tdp": 65, "socket": "AM4", "price": 15000},
    "mb-1": {"id": "mb-1", "name": "B550", "category": "MOTHERBOARD", "socket": "AM4", "price": 10000},
    "gpu-1": {"id": "gpu-1", "name": "RTX 4060", "category": "GPU", "tdp": 115, "length_mm": 200, "price": 35000},
}
@app.get("/internal/v1/components/{id}")
async def get_component(id: str):
    if id not in COMPONENTS_DB:
        raise HTTPException(status_code=404, detail="Component not found")
    return COMPONENTS_DB[id]

@app.get("/internal/v1/components")
async def get_batch_components(ids: str):
    id_list = ids.split(",")
    return [COMPONENTS_DB[i] for i in id_list if i in COMPONENTS_DB]
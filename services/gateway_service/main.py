from fastapi import FastAPI, Request
from fastapi.responses import Response
import httpx

app = FastAPI(title="API Gateway")

# --- Явные маршруты для Build Service (порт 8004) ---

@app.post("/api/v1/builds", tags=["builds"])
async def create_build_proxy(request: Request):
    return await proxy_request(request, "http://build_service:8000/api/v1/builds")

@app.post("/api/v1/builds/{build_id}/items", tags=["builds"])
async def add_item_proxy(build_id: str, request: Request):
    return await proxy_request(request, f"http://build_service:8000/api/v1/builds/{build_id}/items")

@app.get("/api/v1/builds/{build_id}", tags=["builds"])
async def get_build_proxy(build_id: str, request: Request):
    return await proxy_request(request, f"http://build_service:8000/api/v1/builds/{build_id}")


# --- Явные маршруты для Catalog Service (порт 8001) ---

@app.get("/api/v1/components", tags=["catalog"])
async def get_components_proxy(request: Request):
    return await proxy_request(request, "http://catalog_service:8000/api/v1/components")

@app.get("/api/v1/components/{component_id}", tags=["catalog"])
async def get_component_proxy(component_id: str, request: Request):
    return await proxy_request(request, f"http://catalog_service:8000/api/v1/components/{component_id}")


# --- Вспомогательная функция ---
async def proxy_request(request: Request, url: str):
    async with httpx.AsyncClient() as client:
        body = await request.body()
        headers = dict(request.headers)
        headers.pop("host", None)
        
        response = await client.request(
            method=request.method,
            url=url,
            headers=headers,
            content=body,
            follow_redirects=True
        )
        
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.headers.get("content-type")
        )
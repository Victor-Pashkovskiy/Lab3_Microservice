from fastapi import FastAPI, Request
from fastapi.responses import Response
import httpx

app = FastAPI(title="API Gateway")

@app.api_route("/api/v1/builds/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_builds(path: str, request: Request):
    if path and path.startswith("/"):
        path = path[1:]
    
    url = f"http://build_service:8000/api/v1/builds/{path}" if path else "http://localhost:8004/api/v1/builds"
    return await proxy_request(request, url)

@app.api_route("/api/v1/components/{path:path}", methods=["GET", "POST"])
async def proxy_catalog(path: str, request: Request):
    if path and path.startswith("/"):
        path = path[1:]
    url = f"http://catalog_service:8000/api/v1/components/{path}" if path else "http://localhost:8001/api/v1/components"
    return await proxy_request(request, url)

async def proxy_request(request: Request, url: str):
    async with httpx.AsyncClient() as client:
        body = await request.body()
        headers = dict(request.headers)
        headers.pop("host", None) # Обязательно убираем host!
        
        # Добавляем follow_redirects=True, чтобы httpx сам переходил по редиректам
        response = await client.request(
            method=request.method,
            url=url,
            headers=headers,
            content=body,
            follow_redirects=True
        )
        
        # Возвращаем ответ как есть (сохраняя статус-код и headers)
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.headers.get("content-type")
        )
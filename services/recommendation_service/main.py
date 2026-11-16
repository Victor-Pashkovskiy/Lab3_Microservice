from fastapi import FastAPI
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

app = FastAPI(title="recommendation-service")
app.add_exception_handler(HTTPException, problem_details_handler)
RECOMMENDATIONS_DB = {}

class RebuildRequest(BaseModel):
    buildId: str


async def handle_build_saved(event: dict):
    build_id = event["payload"]["buildId"]
    print(f"[Recommendation] Generating tips for build {build_id}")
    RECOMMENDATIONS_DB[build_id] = [
        {"code": "thermal-paste", "title": "Замените термопасту", "text": "Раз в 1-2 года..."}
    ]

#  имитируем получение события из Kafka
@app.post("/internal/v1/recommendations/rebuild")
async def rebuild_recs(req: RebuildRequest):
    await handle_build_saved({"payload": {"buildId": req.buildId}})
    return {"status": "ok"}

@app.on_event("startup")
async def startup_event():
    event_bus.subscribe("build.saved", handle_build_saved)

@app.get("/api/v1/builds/{id}/recommendations")
async def get_recommendations(id: str):
    return {"buildId": id, "items": RECOMMENDATIONS_DB.get(id, [])}
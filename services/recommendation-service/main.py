
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse
from services.shared.event_bus import event_bus
from pydantic import BaseModel

app = FastAPI(title="recommendation-service")

#  БД рекомендаций
RECOMMENDATIONS_DB = {}

# Обработчик события 
async def handle_build_saved(event: dict):
    build_id = event["payload"]["buildId"]
    print(f"[Recommendation] Generating tips for build {build_id}")
    # типо рекомендации
    RECOMMENDATIONS_DB[build_id] = [
        {"code": "thermal-paste", "title": "Замените термопасту", "text": "Раз в 1-2 года..."}
    ]

# Подписываемся на топик при старте
@app.on_event("startup")
async def startup_event():
    event_bus.subscribe("build.saved", handle_build_saved)

@app.get("/api/v1/builds/{id}/recommendations")
async def get_recommendations(id: str):
    return {"buildId": id, "items": RECOMMENDATIONS_DB.get(id, [])}
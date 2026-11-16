from fastapi.testclient import TestClient
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.catalog_service.main import app as catalog_app
from services.compatibility_service.main import app as compat_app

client_catalog = TestClient(catalog_app)
client_compat = TestClient(compat_app)

def test_get_cpu_component():
    # проверка что  каталог отдает деталь
    response = client_catalog.get("/internal/v1/components/cpu-1")
    assert response.status_code == 200
    assert response.json()["name"] == "Ryzen 5"

def test_get_nonexistent_component():
    #  на несуществующую деталь отдается 404
    response = client_catalog.get("/internal/v1/components/unknown-999")
    assert response.status_code == 404
    # единая модель ошибок
    assert response.json()["title"] == "Error"
# Демонстрационные сценарии (Лаба 4)

## 1. Успешный сквозной сценарий (Happy Path)
**Участники:** API Gateway (8000), build-service (8004), catalog-service (8001), compatibility-service (8002), recommendation-service (8003).
**Все взаимодействия реальные (кроме брокера).**

1. Клиент отправляет `POST http://localhost:8000/api/v1/builds` (через Gateway) с заголовком `Idempotency-Key: test-1`. Gateway перенаправляет запрос в `build-service`. Сборка создается, возвращается `id`.
2. Клиент отправляет `POST http://localhost:8000/api/v1/builds/{id}/items` с деталью `cpu-1`. 
   * `build-service` синхронно вызывает `compatibility-service`. 
   * `compatibility-service` синхронно вызывает `catalog-service` для получения TDP и сокета.
   * `build-service` сохраняет деталь, возвращает `200 OK` с `compatible: true`.
   * `build-service` **асинхронно** отправляет мок-событие `build.saved` в `recommendation-service`.
3. Клиент делает `GET http://localhost:8003/api/v1/builds/{id}/recommendations`.
   * Возвращаются сгенерированные рекомендации (например, про замену термопасты), что доказывает работу асинхронного события.

## 2. Сценарий со сбоем (Сага)
**Участники:** build-service (8004), compatibility-service (8002).

1. Сервис `compatibility-service` принудительно останавливается (Ctrl+C).
2. Клиент отправляет `POST /api/v1/builds/{id}/items` (добавляет `gpu-1`).
3. `build-service` пытается вызвать `compatibility-service`, но получает таймаут (2 секунды).
4. **Компенсация:** `build-service` не выдает ошибку 500, а переводит сборку в статус черновика (`compatible: false`), сохраняя данные пользователя. В логах появляется сообщение `[BuildService] Compatibility service timeout! Saving draft.`

## Моки и заглушки
* **API Gateway** реализован на FastAPI и является реальным сервисом.
* **Kafka (Брокер сообщений)** заменена мок-брокером (HTTP-вызов вместо отправки в топик).
* **Базы данных** заменены in-memory словарями (dict).
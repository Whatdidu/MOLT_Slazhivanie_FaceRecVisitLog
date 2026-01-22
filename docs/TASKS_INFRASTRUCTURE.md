# Задачи модуля Infrastructure (Татьяна)

**Ветка:** `feature/infrastructure`

## Статусы
- [ ] Не начато
- [x] Выполнено
- [~] В процессе

---

## Фаза 1: Базовая структура проекта

- [x] **TASK-INF-001**: Создать структуру папок `app/core/`
- [x] **TASK-INF-002**: Настроить конфигурацию через `.env` (`app/core/config.py`)
- [x] **TASK-INF-003**: Создать `.env.example` с примерами переменных окружения
- [x] **TASK-INF-004**: Настроить логгер с форматированием и уровнями (`app/core/logger.py`)

## Фаза 2: FastAPI каркас

- [x] **TASK-INF-005**: Создать точку входа `app/main.py` с базовым FastAPI приложением
- [x] **TASK-INF-006**: Настроить CORS middleware
- [x] **TASK-INF-007**: Реализовать подключение роутеров модулей (recognition, employees, attendance)
- [x] **TASK-INF-008**: Создать health-check эндпоинт (`GET /health`)

## Фаза 3: Приемный шлюз (Image Gateway)

- [x] **TASK-INF-009**: Создать эндпоинт приема изображений от камеры (`POST /api/v1/gateway/snapshot`)
- [x] **TASK-INF-010**: Реализовать парсинг и валидацию входящих изображений (размер, формат)
- [x] **TASK-INF-011**: Добавить проверку качества изображения (минимальное разрешение)
- [x] **TASK-INF-012**: Реализовать генерацию Trace ID для сквозного отслеживания запросов

## Фаза 4: Docker и Infrastructure

- [x] **TASK-INF-013**: Создать `Dockerfile` для Python-приложения
- [x] **TASK-INF-014**: Создать `docker-compose.yml` (App + PostgreSQL)
- [x] **TASK-INF-015**: Настроить Docker-порты и сетевую связность между сервисами
- [x] **TASK-INF-016**: Добавить volume для персистентного хранения данных БД

## Фаза 5: Утилиты и константы

- [x] **TASK-INF-017**: Создать файл констант (`app/core/constants.py`)
- [x] **TASK-INF-018**: Реализовать middleware для Trace ID (добавление в каждый запрос)
- [x] **TASK-INF-019**: Настроить обработку ошибок и exception handlers
- [x] **TASK-INF-020**: Создать `requirements.txt` с зависимостями проекта

## Фаза 6: Интеграция с другими модулями

- [ ] **TASK-INF-021**: Интегрировать роутер модуля Recognition (после готовности Мансура)
- [ ] **TASK-INF-022**: Интегрировать роутер модуля Employees (после готовности Ольги)
- [ ] **TASK-INF-023**: Интегрировать роутер модуля Attendance (после готовности Лили)
- [ ] **TASK-INF-024**: Настроить pipeline: Gateway → Recognition → Attendance

## Фаза 7: Деплой и мониторинг

- [ ] **TASK-INF-025**: Настроить деплой на VPS сервер
- [ ] **TASK-INF-026**: Настроить nginx reverse proxy (опционально)
- [ ] **TASK-INF-027**: Добавить мониторинг логов
- [ ] **TASK-INF-028**: Провести нагрузочное тестирование

---

## Внутренний API (контракт для других модулей)

### Структура Core

```python
from app.core.config import settings      # Доступ к настройкам
from app.core.logger import get_logger    # Получение логгера
from app.core.constants import *          # Константы проекта
from app.core.exceptions import AppException  # Базовое исключение
```

### Trace ID Middleware

```python
# Каждый запрос получает уникальный trace_id
# Доступен через request.state.trace_id
# Добавляется в заголовок ответа X-Trace-ID
# Используется для логирования и отладки
```

### Gateway Service

```python
# POST /api/v1/gateway/snapshot
# Принимает: UploadFile (image/jpeg, image/png, image/webp)
# Возвращает: SnapshotResponse с trace_id и статусом
# Валидация: размер до 10MB, минимум 100x100px
```

---

## API Endpoints

```
GET  /health                        - Проверка работоспособности сервиса
GET  /api/v1/info                   - Информация о версии и статусе
POST /api/v1/gateway/snapshot       - Прием снапшота от камеры
GET  /api/v1/gateway/health         - Проверка Gateway
```

---

## Структура файлов модуля

```text
app/
├── main.py                    # Точка входа FastAPI
├── api/
│   ├── __init__.py
│   └── gateway.py             # Gateway router (прием изображений)
├── core/
│   ├── __init__.py            # Экспорты модуля
│   ├── config.py              # Pydantic Settings (загрузка .env)
│   ├── logger.py              # Настройка логирования
│   ├── constants.py           # Константы (TTL, пороги, пути)
│   ├── middleware.py          # Trace ID middleware
│   └── exceptions.py          # Кастомные исключения и handlers
```

```text
# Корень проекта
├── docker-compose.yml         # Оркестрация App + PostgreSQL
├── Dockerfile                 # Multi-stage сборка образа
├── requirements.txt           # Зависимости Python
└── .env.example               # Пример переменных окружения
```

---

## Переменные окружения (.env)

```env
# Application
APP_NAME=SputnikFaceID
APP_VERSION=0.1.0
DEBUG=true

# Server
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=postgresql://sputnik:sputnik_password@db:5432/sputnik_faceid

# Logging
LOG_LEVEL=INFO

# Storage
STATIC_PATH=app/static
DEBUG_PHOTOS_TTL_DAYS=7

# Recognition thresholds
RECOGNITION_MATCH_THRESHOLD=0.55
RECOGNITION_LOW_CONFIDENCE_THRESHOLD=0.40
```

---

## Зависимости (requirements.txt)

```txt
# Web Framework
fastapi>=0.104.0
uvicorn[standard]>=0.24.0

# Configuration
python-dotenv>=1.0.0
pydantic>=2.0.0
pydantic-settings>=2.0.0

# File uploads
python-multipart>=0.0.6

# Database
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.9
alembic>=1.12.0

# HTTP Client
httpx>=0.25.0
```

---

## Прогресс выполнения

| Фаза | Статус | Задачи |
|------|--------|--------|
| Фаза 1: Базовая структура | ✅ Выполнено | 4/4 |
| Фаза 2: FastAPI каркас | ✅ Выполнено | 4/4 |
| Фаза 3: Image Gateway | ✅ Выполнено | 4/4 |
| Фаза 4: Docker | ✅ Выполнено | 4/4 |
| Фаза 5: Утилиты | ✅ Выполнено | 4/4 |
| Фаза 6: Интеграция | ⏳ Ожидание | 0/4 |
| Фаза 7: Деплой | ⏳ Ожидание | 0/4 |

**Общий прогресс: 20/28 задач (71%)**

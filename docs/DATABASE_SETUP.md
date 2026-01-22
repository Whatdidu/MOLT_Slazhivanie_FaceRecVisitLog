# Database & Backend Setup Guide

## Что уже реализовано

### 1. Инфраструктура БД
- `app/db/session.py` - Подключение к PostgreSQL через SQLAlchemy
- `app/db/base.py` - Базовый класс для моделей с timestamps
- `app/db/models.py` - Модели: Employee, Embedding, AttendanceLog
- `app/db/__init__.py` - Экспорты для удобного импорта

### 2. Конфигурация
- `app/core/config.py` - Настройки приложения через Pydantic
- `.env` - Переменные окружения (DATABASE_URL, DB_*)
- `alembic/` - Настроенные миграции БД

### 3. Модуль Employees
- `app/modules/employees/schemas.py` - Pydantic schemas для валидации
- `app/modules/employees/crud.py` - CRUD операции
- `app/modules/employees/router.py` - REST API endpoints
- `app/modules/employees/__init__.py` - Экспорты модуля

### 4. Docker & Dependencies
- `docker-compose.yml` - PostgreSQL контейнер
- `requirements.txt` - Python зависимости

---

## Следующие шаги

### Шаг 1: Запуск PostgreSQL

```bash
# Запустить PostgreSQL через Docker
docker-compose up -d postgres

# Проверить, что БД запущена
docker ps
```

### Шаг 2: Создание миграций

```bash
# Создать первую миграцию
alembic revision --autogenerate -m "Initial migration - employees, embeddings, attendance_log"

# Применить миграции
alembic upgrade head
```

### Шаг 3: Создание FastAPI приложения

Создайте `app/main.py`:

```python
from fastapi import FastAPI
from app.core.config import settings
from app.modules.employees import router as employees_router
from app.db import init_db, close_db

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug
)

# Подключение роутеров
app.include_router(employees_router)

@app.on_event("startup")
async def startup():
    """Initialize database on startup."""
    init_db()

@app.on_event("shutdown")
async def shutdown():
    """Close database connections on shutdown."""
    close_db()

@app.get("/")
def root():
    return {"message": "Sputnik Face ID API", "status": "running"}

@app.get("/health")
def health():
    return {"status": "healthy"}
```

### Шаг 4: Запуск приложения

```bash
# Запустить FastAPI сервер
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Шаг 5: Тестирование API

Откройте в браузере:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

Доступные endpoints:
```
POST   /api/v1/employees/          - Создать сотрудника
GET    /api/v1/employees/{id}      - Получить сотрудника
GET    /api/v1/employees/          - Список сотрудников
PUT    /api/v1/employees/{id}      - Обновить сотрудника
DELETE /api/v1/employees/{id}      - Удалить сотрудника
GET    /api/v1/employees/embeddings/all - Все эмбеддинги
```

---

## Интеграция с другими модулями

### С модулем Recognition (Мансур)

```python
# В модуле employees при регистрации
from app.modules.recognition import get_recognition_service

service = get_recognition_service()
embedding_result = await service.create_embedding(photo_bytes)

# Сохранить вектор в БД
embedding = Embedding(
    employee_id=employee.id,
    vector=embedding_result.vector,
    model_version=embedding_result.model_version
)
db.add(embedding)
db.commit()
```

### С модулем Attendance (Лиля)

```python
# Получить все эмбеддинги для распознавания
from app.modules.employees import employee_crud

embeddings = employee_crud.get_all_embeddings(db)
# Returns: [(employee_id, vector), ...]
```

---

## Что нужно доделать

### Фаза 4: Enrollment (регистрация с фото)

- [ ] Создать endpoint `POST /api/v1/employees/enroll`
- [ ] Реализовать загрузку фото через multipart/form-data
- [ ] Интегрировать с Recognition для создания эмбеддинга
- [ ] Сохранить фото во временное хранилище
- [ ] Автоматически удалить фото после создания эмбеддинга

### Фаза 5: Управление хранилищем (TTL)

- [ ] Создать `app/core/storage.py` для управления файлами
- [ ] Реализовать автоудаление старых снапшотов (7 дней)
- [ ] Добавить фоновую задачу или cron для очистки
- [ ] Настроить структуру папок `/static/debug_photos/`

### Фаза 6: Тесты

- [ ] Написать unit-тесты для CRUD операций
- [ ] Написать integration tests для API
- [ ] Создать тестовые fixtures
- [ ] Настроить pytest

---

## Структура БД

### Таблица `employees`
```sql
CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    department VARCHAR(100),
    photo_path VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

### Таблица `embeddings`
```sql
CREATE TABLE embeddings (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES employees(id) ON DELETE CASCADE,
    vector FLOAT[],  -- Array of floats
    model_version VARCHAR(50) DEFAULT 'arcface',
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

### Таблица `attendance_log`
```sql
CREATE TABLE attendance_log (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES employees(id) ON DELETE SET NULL,
    timestamp TIMESTAMP NOT NULL,
    event_type VARCHAR(20) DEFAULT 'entry',
    confidence FLOAT,
    trace_id VARCHAR(36) NOT NULL,
    photo_path VARCHAR(500),
    status VARCHAR(20) DEFAULT 'unknown',
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

---

## Полезные команды

### Alembic
```bash
# Создать новую миграцию
alembic revision --autogenerate -m "description"

# Применить все миграции
alembic upgrade head

# Откатить последнюю миграцию
alembic downgrade -1

# Посмотреть текущую ревизию
alembic current

# История миграций
alembic history
```

### Docker
```bash
# Запустить все сервисы
docker-compose up -d

# Остановить все сервисы
docker-compose down

# Посмотреть логи PostgreSQL
docker-compose logs -f postgres

# Подключиться к PostgreSQL
docker exec -it sputnik_faceid_db psql -U sputnik_user -d sputnik_faceid
```

### FastAPI
```bash
# Запустить с автоперезагрузкой
uvicorn app.main:app --reload

# Запустить на другом порту
uvicorn app.main:app --port 8080

# Запустить с логами
uvicorn app.main:app --log-level debug
```

---

## Примеры использования API

### Создать сотрудника
```bash
curl -X POST http://localhost:8000/api/v1/employees/ \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Иван Иванов",
    "email": "ivan@example.com",
    "department": "Engineering"
  }'
```

### Получить список сотрудников
```bash
curl http://localhost:8000/api/v1/employees/?skip=0&limit=10
```

### Обновить сотрудника
```bash
curl -X PUT http://localhost:8000/api/v1/employees/1 \
  -H "Content-Type: application/json" \
  -d '{
    "department": "Management"
  }'
```

### Удалить сотрудника (soft delete)
```bash
curl -X DELETE http://localhost:8000/api/v1/employees/1
```

# Quick Start Guide - Database Module

## Предварительные требования

1. **Docker Desktop** - для запуска PostgreSQL
   - Скачать: https://www.docker.com/products/docker-desktop/
   - Установить и запустить Docker Desktop

2. **Python 3.10+** - уже установлен ✓

3. **Установленные зависимости** - уже установлены ✓
   ```bash
   pip install -r requirements.txt
   ```

---

## Шаг 1: Установка Docker (если не установлен)

### Windows
1. Скачайте Docker Desktop: https://www.docker.com/products/docker-desktop/
2. Запустите установщик
3. Перезагрузите компьютер
4. Запустите Docker Desktop

### Проверка установки
```bash
docker --version
docker compose version
```

---

## Шаг 2: Запуск PostgreSQL

```bash
# Запустить PostgreSQL контейнер
docker compose up -d postgres

# Проверить статус
docker ps

# Посмотреть логи (опционально)
docker compose logs -f postgres
```

Вы должны увидеть:
```
✓ Container sputnik_faceid_db  Running
```

---

## Шаг 3: Создание миграций БД

```bash
# Создать первую миграцию
alembic revision --autogenerate -m "Initial migration - employees, embeddings, attendance_log"

# Применить миграцию
alembic upgrade head
```

Должны появиться таблицы:
- `employees`
- `embeddings`
- `attendance_log`

---

## Шаг 4: Запуск FastAPI приложения

```bash
# Запустить сервер
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Или через Python:
```bash
python -m app.main
```

Вы должны увидеть:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

---

## Шаг 5: Проверка работы API

### Открыть Swagger UI
http://localhost:8000/docs

### Открыть ReDoc
http://localhost:8000/redoc

### Проверить health
```bash
curl http://localhost:8000/health
```

Ответ:
```json
{
  "status": "healthy",
  "service": "Sputnik Face ID"
}
```

---

## Шаг 6: Тестирование API

### 1. Создать сотрудника

**Через Swagger UI:**
1. Откройте http://localhost:8000/docs
2. Найдите `POST /api/v1/employees/`
3. Нажмите "Try it out"
4. Введите данные:
```json
{
  "full_name": "Иван Иванов",
  "email": "ivan.ivanov@sputnik.com",
  "department": "Engineering"
}
```
5. Нажмите "Execute"

**Через curl:**
```bash
curl -X POST http://localhost:8000/api/v1/employees/ \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Иван Иванов",
    "email": "ivan.ivanov@sputnik.com",
    "department": "Engineering"
  }'
```

### 2. Получить список сотрудников

```bash
curl http://localhost:8000/api/v1/employees/
```

### 3. Получить сотрудника по ID

```bash
curl http://localhost:8000/api/v1/employees/1
```

### 4. Обновить сотрудника

```bash
curl -X PUT http://localhost:8000/api/v1/employees/1 \
  -H "Content-Type: application/json" \
  -d '{
    "department": "Management"
  }'
```

### 5. Удалить сотрудника (soft delete)

```bash
curl -X DELETE http://localhost:8000/api/v1/employees/1
```

---

## Полезные команды

### Docker
```bash
# Запустить все сервисы
docker compose up -d

# Остановить все сервисы
docker compose down

# Посмотреть логи PostgreSQL
docker compose logs -f postgres

# Перезапустить PostgreSQL
docker compose restart postgres

# Подключиться к PostgreSQL CLI
docker exec -it sputnik_faceid_db psql -U sputnik_user -d sputnik_faceid
```

### Alembic
```bash
# Посмотреть текущую версию БД
alembic current

# История миграций
alembic history

# Откатить последнюю миграцию
alembic downgrade -1

# Применить все миграции
alembic upgrade head
```

### FastAPI
```bash
# Запустить с автоперезагрузкой
uvicorn app.main:app --reload

# Запустить на другом порту
uvicorn app.main:app --port 8080

# Запустить с debug логами
uvicorn app.main:app --log-level debug
```

---

## Проверка БД напрямую

### Подключиться через psql
```bash
docker exec -it sputnik_faceid_db psql -U sputnik_user -d sputnik_faceid
```

### SQL запросы
```sql
-- Посмотреть все таблицы
\dt

-- Посмотреть структуру таблицы employees
\d employees

-- Получить всех сотрудников
SELECT * FROM employees;

-- Выход
\q
```

---

## Troubleshooting

### PostgreSQL не запускается
```bash
# Проверить, что порт 5432 свободен
netstat -an | find "5432"

# Если порт занят, измените порт в docker-compose.yml
# Например: "5433:5432"
```

### Ошибка подключения к БД
```bash
# Проверить, что PostgreSQL запущен
docker ps

# Проверить переменные окружения
cat .env

# Проверить DATABASE_URL
echo $DATABASE_URL  # Linux/Mac
echo %DATABASE_URL%  # Windows CMD
```

### Alembic не видит модели
```bash
# Убедитесь, что models.py импортируется в alembic/env.py
# Проверьте строку: from app.db import models
```

---

## Что дальше?

После успешного запуска:

1. **Фаза 4: Enrollment** - реализовать загрузку фото и создание эмбеддингов
2. **Фаза 5: TTL** - автоудаление старых файлов
3. **Фаза 6: Tests** - написать тесты
4. **Интеграция** - связать с модулями Recognition, Attendance, Infrastructure

См. подробности в `docs/TASKS_DATABASE.md`

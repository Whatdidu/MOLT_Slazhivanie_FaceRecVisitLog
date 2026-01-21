# Задачи модуля Database & Backend (Ольга)

**Ветка:** `feature/database`
**Эпик:** [#53 EPIC-DB: Database & Employee Management Module](https://github.com/Whatdidu/MOLT_Slazhivanie_FaceRecVisitLog/issues/53)

## Статусы
- [ ] Не начато
- [x] Выполнено
- [~] В процессе

## Прогресс

- **Фаза 1:** ✓ 3/4 завершено (75%)
- **Фаза 2:** ✓ 4/4 завершено (100%)
- **Фаза 3:** ✓ 4/4 завершено (100%)
- **Фаза 4:** 0/4 завершено (0%)
- **Фаза 5:** 0/4 завершено (0%)
- **Фаза 6:** 1/4 завершено (25%)

**Общий прогресс:** 12/24 задач (50%)

---

## Фаза 1: Инфраструктура БД

- [x] **TASK-DB-001**: Настроить подключение к PostgreSQL (`app/db/session.py`) - [#54](https://github.com/Whatdidu/MOLT_Slazhivanie_FaceRecVisitLog/issues/54)
- [x] **TASK-DB-002**: Создать базовый класс для моделей (`app/db/base.py`) - [#55](https://github.com/Whatdidu/MOLT_Slazhivanie_FaceRecVisitLog/issues/55)
- [x] **TASK-DB-003**: Настроить Alembic для миграций - [#56](https://github.com/Whatdidu/MOLT_Slazhivanie_FaceRecVisitLog/issues/56)
- [ ] **TASK-DB-004**: Создать первую миграцию (init)

## Фаза 2: Модели данных

- [x] **TASK-DB-005**: Создать модель `Employee` (`app/db/models.py`) - [#57](https://github.com/Whatdidu/MOLT_Slazhivanie_FaceRecVisitLog/issues/57)
  - id, full_name, email, department, photo_path
  - created_at, updated_at, is_active
- [x] **TASK-DB-006**: Создать модель `Embedding` - [#58](https://github.com/Whatdidu/MOLT_Slazhivanie_FaceRecVisitLog/issues/58)
  - id, employee_id, vector (ARRAY), model_version
  - created_at
- [x] **TASK-DB-007**: Создать модель `AttendanceLog` - [#59](https://github.com/Whatdidu/MOLT_Slazhivanie_FaceRecVisitLog/issues/59)
  - id, employee_id, timestamp, event_type
  - confidence, trace_id, photo_path
- [x] **TASK-DB-008**: Добавить индексы для оптимизации запросов

## Фаза 3: CRUD API для сотрудников

- [x] **TASK-DB-009**: Создать Pydantic schemas (`app/modules/employees/schemas.py`) - [#60](https://github.com/Whatdidu/MOLT_Slazhivanie_FaceRecVisitLog/issues/60)
  - EmployeeCreate, EmployeeUpdate, EmployeeResponse
- [x] **TASK-DB-010**: Реализовать CRUD операции (`app/modules/employees/crud.py`) - [#61](https://github.com/Whatdidu/MOLT_Slazhivanie_FaceRecVisitLog/issues/61)
  - create_employee, get_employee, update_employee, delete_employee
  - list_employees (с пагинацией)
- [x] **TASK-DB-011**: Создать FastAPI router (`app/modules/employees/router.py`) - [#62](https://github.com/Whatdidu/MOLT_Slazhivanie_FaceRecVisitLog/issues/62)
- [x] **TASK-DB-012**: Добавить валидацию данных и обработку ошибок

## Фаза 4: Enrollment (регистрация сотрудников)

- [ ] **TASK-DB-013**: Реализовать сервис регистрации (`app/modules/employees/service.py`) - [#63](https://github.com/Whatdidu/MOLT_Slazhivanie_FaceRecVisitLog/issues/63)
- [ ] **TASK-DB-014**: Интегрировать с модулем Recognition для создания эмбеддингов - [#64](https://github.com/Whatdidu/MOLT_Slazhivanie_FaceRecVisitLog/issues/64)
- [ ] **TASK-DB-015**: Реализовать сохранение фото во временное хранилище
- [ ] **TASK-DB-016**: Добавить endpoint для загрузки фото (`POST /api/v1/employees/enroll`) - [#65](https://github.com/Whatdidu/MOLT_Slazhivanie_FaceRecVisitLog/issues/65)

## Фаза 5: Управление хранилищем

- [ ] **TASK-DB-017**: Создать утилиту для управления TTL (`app/core/storage.py`) - [#66](https://github.com/Whatdidu/MOLT_Slazhivanie_FaceRecVisitLog/issues/66)
- [ ] **TASK-DB-018**: Реализовать автоудаление старых снапшотов (7 дней) - [#67](https://github.com/Whatdidu/MOLT_Slazhivanie_FaceRecVisitLog/issues/67)
- [ ] **TASK-DB-019**: Добавить фоновую задачу для очистки (или cron)
- [ ] **TASK-DB-020**: Настроить структуру папок в `/static/debug_photos`

## Фаза 6: Тесты и документация

- [ ] **TASK-DB-021**: Написать unit-тесты для CRUD операций - [#68](https://github.com/Whatdidu/MOLT_Slazhivanie_FaceRecVisitLog/issues/68)
- [ ] **TASK-DB-022**: Написать тесты для Enrollment flow - [#69](https://github.com/Whatdidu/MOLT_Slazhivanie_FaceRecVisitLog/issues/69)
- [ ] **TASK-DB-023**: Создать тестовые данные (fixtures)
- [x] **TASK-DB-024**: Документация API (OpenAPI/Swagger) - автогенерируется FastAPI

---

## Внутренний API (контракт для других модулей)

### Методы EmployeeService

```python
from app.modules.employees import get_employee_service

service = get_employee_service()

# CRUD операции
await service.create_employee(data: EmployeeCreate) -> Employee
await service.get_employee(employee_id: int) -> Employee | None
await service.update_employee(employee_id: int, data: EmployeeUpdate) -> Employee
await service.delete_employee(employee_id: int) -> bool
await service.list_employees(skip: int = 0, limit: int = 100) -> list[Employee]

# Enrollment
await service.enroll_employee(full_name: str, email: str, photo: bytes) -> Employee

# Вспомогательные методы
await service.get_all_embeddings() -> list[tuple[int, list[float]]]
await service.get_employee_by_email(email: str) -> Employee | None
```

### Структура БД

| Таблица | Основные поля | Описание |
|---------|---------------|----------|
| `employees` | id, full_name, email, department | Информация о сотрудниках |
| `embeddings` | id, employee_id, vector | Векторы лиц (для распознавания) |
| `attendance_log` | id, employee_id, timestamp, confidence | Журнал посещений |

---

## API Endpoints

```
POST   /api/v1/employees/           - Создать сотрудника
GET    /api/v1/employees/{id}       - Получить сотрудника
PUT    /api/v1/employees/{id}       - Обновить сотрудника
DELETE /api/v1/employees/{id}       - Удалить сотрудника
GET    /api/v1/employees/           - Список сотрудников

POST   /api/v1/employees/enroll     - Регистрация с фото
GET    /api/v1/employees/embeddings - Получить все эмбеддинги
```

---

## Зависимости

```txt
sqlalchemy>=2.0.0
alembic>=1.12.0
psycopg2-binary>=2.9.0
pydantic>=2.0.0
python-multipart>=0.0.6  # для загрузки файлов
```

---

## Модели данных (SQLAlchemy)

### Employee
```python
class Employee(Base):
    __tablename__ = "employees"

    id: int (PK)
    full_name: str (NOT NULL)
    email: str (UNIQUE, NOT NULL)
    department: str | None
    photo_path: str | None
    is_active: bool (default=True)
    created_at: datetime
    updated_at: datetime
```

### Embedding
```python
class Embedding(Base):
    __tablename__ = "embeddings"

    id: int (PK)
    employee_id: int (FK -> employees.id)
    vector: list[float] (ARRAY)
    model_version: str
    created_at: datetime
```

### AttendanceLog
```python
class AttendanceLog(Base):
    __tablename__ = "attendance_log"

    id: int (PK)
    employee_id: int | None (FK -> employees.id)
    timestamp: datetime (NOT NULL)
    event_type: str (entry/exit)
    confidence: float | None
    trace_id: str (UUID)
    photo_path: str | None
```

---

## Миграции Alembic

### Структура
```
alembic/
├── versions/
│   ├── 001_initial.py          - Создание таблиц
│   ├── 002_add_indexes.py      - Индексы для оптимизации
│   └── ...
├── env.py
└── alembic.ini
```

### Команды
```bash
# Создать миграцию
alembic revision --autogenerate -m "description"

# Применить миграции
alembic upgrade head

# Откатить миграцию
alembic downgrade -1
```

---

## Интеграция с другими модулями

### С модулем Recognition (Мансур)
- При регистрации сотрудника вызывается `create_embedding()` для генерации вектора
- Вектор сохраняется в таблицу `embeddings`

### С модулем Attendance (Лиля)
- Предоставляется метод для записи в `attendance_log`
- Доступ к информации о сотрудниках для отображения в админке

### С модулем Infrastructure (Татьяна)
- Использование общего подключения к БД
- Логирование через `app/core/logger.py`
- Trace ID для отслеживания запросов

---

## Политика безопасности

- **Пароли БД:** Хранятся в `.env`, не коммитятся в репозиторий
- **Email:** Уникальность на уровне БД (UNIQUE constraint)
- **Фото:** Оригиналы фото удаляются после создания эмбеддинга
- **TTL:** Снапшоты с камеры хранятся максимум 7 дней

---

## Примечания

- Для хранения векторов используется тип `ARRAY` в PostgreSQL
- При большом количестве сотрудников рассмотреть использование pgvector для оптимизации поиска
- Все даты хранятся в UTC
- Soft delete для сотрудников (is_active=False)

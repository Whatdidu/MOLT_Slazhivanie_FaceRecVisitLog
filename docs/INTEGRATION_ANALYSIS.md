# Анализ интеграции модулей - Финальная доводка

**Дата:** 2026-01-23
**Цель:** Подготовка к запуску enrollment и распознавания лиц

---

## 📊 Текущее состояние модулей

### ✅ Recognition Module (Мансур) - 95% готов

**Локация:** `app/modules/recognition/`

**Реализовано:**
- ✅ `RecognitionService` - главный сервис
- ✅ `DlibFaceProvider` - провайдер на face_recognition (128-dim embeddings)
- ✅ `create_embedding(image: bytes)` → EmbeddingResult
- ✅ `recognize_face(image, embeddings_db)` → RecognitionResponse
- ✅ Cosine similarity, find_best_match
- ✅ Пороги: MATCH=0.55, LOW_CONFIDENCE=0.40

**Статус:** Полностью функционален, готов к использованию

---

### ✅ Employees Module (Ольга) - 90% готов

**Локация:** `app/modules/employees/`

**Реализовано:**
- ✅ `EmployeeService.enroll_employee()` - полный enrollment flow
- ✅ CRUD операции (create, read, update, delete)
- ✅ Валидация email, photo quality checks
- ✅ Сохранение фото в `static/employee_photos/`
- ⚠️ `enrollment.py` - использует MOCK вместо реального Recognition

**Проблемы:**
1. `enrollment.py:142-156` - возвращает mock-вектор вместо реального embedding
2. `router.py` - дублирующийся `/enroll` endpoint (строки 32-113 и 289-334)
3. Несоответствие моделей БД: `vector` (ARRAY) vs `vector_blob` (BINARY)

---

### ✅ Attendance Module (Лиля) - 100% готов

**Локация:** `app/modules/attendance/`

**Реализовано:**
- ✅ `AttendanceService` - полностью функционален
- ✅ `log_entry()`, `log_exit()` - логирование событий
- ✅ `can_log_entry()` - анти-спам фильтр (300 сек cooldown)
- ✅ `get_present_employees()` - кто в офисе
- ✅ `get_attendance_history()` - история с фильтрами
- ✅ `get_attendance_stats()` - агрегированная статистика

**Статус:** Полностью готов, ждет интеграции с Recognition

---

### ⚠️ Gateway API (Татьяна) - 70% готов

**Локация:** `app/api/gateway.py`

**Реализовано:**
- ✅ Валидация изображений (тип, размер, формат)
- ✅ Trace ID генерация
- ✅ Error handling
- ❌ **НЕТ интеграции с Recognition** (строка 155-167)

**Код, который нужно реализовать:**
```python
# app/api/gateway.py:155-167
# TODO: Интеграция с модулем recognition
# from app.modules.recognition import get_recognition_service
# service = get_recognition_service()
# result = await service.recognize_face(image_bytes, embeddings_db)
```

---

### ⚠️ Admin UI (Лиля) - 95% готов

**Локация:** `app/modules/admin/router.py`

**Реализовано:**
- ✅ Dashboard, Present, Attendance, Employees, Reports страницы
- ✅ Jinja2 templates с Bootstrap 5
- ⚠️ Форма enrollment не использует EmployeeService

**Проблема:** `router.py:142-184`
```python
@router.post("/employees/new")
async def create_employee(..., photo: UploadFile):
    # TODO: Обработка фото и создание embedding через модуль Recognition
    # photo_content = await photo.read()
    # embedding = await recognition_service.create_embedding(photo_content)
```

---

## 🔴 Критические проблемы для исправления

### 1. **Recognition Service не инициализируется при старте**

**Локация:** `app/main.py` lifespan

**Проблема:** ML-модель не загружается при запуске приложения

**Решение:**
```python
from app.modules.recognition import init_recognition_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting application...")

    # Initialize recognition service
    recognition = await init_recognition_service()
    if recognition.is_ready():
        logger.info("✅ Recognition service initialized successfully")
    else:
        logger.warning("⚠️ Recognition service not ready (mock mode)")

    yield
    # Shutdown
```

---

### 2. **Gateway не интегрирован с Recognition и Attendance**

**Локация:** `app/api/gateway.py:113-168`

**Текущий код:**
```python
@router.post("/snapshot")
async def receive_snapshot(...):
    # ... валидация ...

    # TODO: Интеграция с модулем recognition
    return SnapshotResponse(
        status="received",
        message="Recognition pending integration.",
    )
```

**Нужно заменить на:**
```python
from app.modules.recognition import get_recognition_service
from app.modules.employees.crud import employee_crud
from app.modules.attendance.service import get_attendance_service
from app.db.session import get_db

@router.post("/snapshot")
async def receive_snapshot(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    trace_id = generate_trace_id()
    timestamp = datetime.utcnow()

    # ... валидация ...

    # 1. Получить все embeddings из БД
    embeddings_raw = employee_crud.get_all_embeddings(db)

    # 2. Конвертировать в формат для Recognition
    from app.modules.recognition.models import EmployeeEmbedding
    embeddings_db = [
        EmployeeEmbedding(
            person_id=emp_id,
            person_name=f"Employee #{emp_id}",  # TODO: get real name
            embedding=vector
        )
        for emp_id, vector in embeddings_raw
    ]

    # 3. Распознать лицо
    recognition_service = get_recognition_service()
    result = await recognition_service.recognize_face(image_bytes, embeddings_db)

    # 4. Если найден сотрудник - записать в журнал
    if result.status == "match" and result.person_id:
        attendance_service = get_attendance_service()

        # Проверить анти-спам
        if await attendance_service.can_log_entry(result.person_id):
            # Записать вход
            await attendance_service.log_entry(
                employee_id=result.person_id,
                confidence=result.confidence,
                trace_id=trace_id
            )

    return SnapshotResponse(
        trace_id=trace_id,
        status=result.status,
        message=f"Recognition completed: {result.status}",
        timestamp=timestamp,
        recognition_result={
            "person_id": result.person_id,
            "person_name": result.person_name,
            "confidence": result.confidence,
        }
    )
```

---

### 3. **Enrollment использует Mock вместо реального Recognition**

**Локация:** `app/modules/employees/enrollment.py:135-156`

**Текущий код:**
```python
async def _get_face_embedding(self, photo_path: Path):
    # MOCK: Возвращаем случайный вектор для тестирования
    import random
    random.seed(str(photo_path))
    vector = [random.uniform(-1, 1) for _ in range(512)]
    return vector
```

**Нужно заменить на:**
```python
async def _get_face_embedding(self, photo_path: Path) -> Optional[List[float]]:
    """Получить face embedding из фото через Recognition сервис."""
    from app.modules.recognition import get_recognition_service

    # Читаем фото
    with open(photo_path, 'rb') as f:
        image_bytes = f.read()

    # Создаём embedding через Recognition сервис
    recognition_service = get_recognition_service()
    result = await recognition_service.create_embedding(image_bytes)

    if not result.face_detected:
        return None

    if result.face_quality < 0.3:  # Минимальный порог качества
        return None

    return result.embedding
```

---

### 4. **EmployeeService.enroll также использует Mock**

**Локация:** `app/modules/employees/service.py:17-18`

**Проблема:** Уже импортирует `get_recognition_service`, но нужно убедиться что используется правильно

**Проверить:** Метод `enroll_employee()` в строках 52-128 использует:
```python
embedding_result = await self._recognition_service.create_embedding(photo)
```

Это ПРАВИЛЬНО! ✅ Но нужно убедиться что `_recognition_service` инициализируется.

---

### 5. **Дублирующийся /enroll endpoint**

**Локация:** `app/modules/employees/router.py`

**Проблема:** Endpoint `/enroll` определен ДВАЖДЫ:
1. Строки 32-113 - использует `EmployeeService` ✅ (правильный)
2. Строки 289-334 - использует `enrollment_service` ⚠️ (старый mock)

**Решение:** Удалить второй endpoint (строки 283-334)

---

### 6. **Admin UI форма не использует EmployeeService**

**Локация:** `app/modules/admin/router.py:142-184`

**Текущий код:**
```python
@router.post("/employees/new")
async def create_employee(..., photo: UploadFile):
    # Создаём сотрудника
    employee = Employee(...)
    session.add(employee)

    # TODO: Обработка фото и создание embedding
```

**Нужно заменить на:**
```python
from app.modules.employees.service import get_employee_service

@router.post("/employees/new")
async def create_employee(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    department: str = Form(None),
    photo: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    full_name = f"{first_name} {last_name}"
    email = f"{first_name.lower()}.{last_name.lower()}@sputnik.com"  # TODO: получать из формы

    # Читаем фото
    photo_bytes = await photo.read()

    # Используем EmployeeService для enrollment
    service = get_employee_service()

    try:
        employee, embedding = await service.enroll_employee(
            db=db,
            full_name=full_name,
            email=email,
            photo=photo_bytes,
            department=department,
        )

        return RedirectResponse(url="/admin/employees", status_code=303)

    except Exception as e:
        error = str(e)
        return templates.TemplateResponse("admin/employee_form.html", {
            "request": request,
            "error": error,
        })
```

---

### 7. **Database models несоответствие**

**Проблема:**
- `enrollment.py` использует `vector_blob` (BINARY)
- `employee_crud.py` использует `vector` (ARRAY в PostgreSQL)
- `service.py` использует `vector` (список)

**Локация:** `app/db/models.py`

**Проверить:** Модель `Embedding` должна использовать единообразный формат

**Текущая модель (нужно проверить):**
```python
class Embedding(Base):
    __tablename__ = "embeddings"

    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    vector = Column(ARRAY(Float))  # PostgreSQL ARRAY
    model_version = Column(String(50))
```

**Решение:** Использовать `ARRAY(Float)` везде (PostgreSQL native)

---

## 📋 План исправления (последовательность шагов)

### **ШАГ 1: Подготовка окружения**
- [ ] Создать папку `app/static/employee_photos/`
- [ ] Установить `face_recognition` (если еще не установлен)
- [ ] Проверить что PostgreSQL запущен
- [ ] Проверить миграции БД (таблица `embeddings` должна иметь `vector` ARRAY)

### **ШАГ 2: Инициализация Recognition при старте**
- [ ] Исправить `app/main.py` lifespan
- [ ] Добавить вызов `init_recognition_service()`
- [ ] Проверить что модель загружается

### **ШАГ 3: Исправить Enrollment Mock**
- [ ] Исправить `app/modules/employees/enrollment.py:135-156`
- [ ] Заменить mock на реальный вызов Recognition
- [ ] Удалить дублирующийся endpoint из `router.py:283-334`

### **ШАГ 4: Интеграция Gateway**
- [ ] Исправить `app/api/gateway.py:113-168`
- [ ] Добавить вызов Recognition service
- [ ] Добавить интеграцию с Attendance service
- [ ] Добавить получение имени сотрудника из БД

### **ШАГ 5: Исправить Admin UI форму**
- [ ] Исправить `app/modules/admin/router.py:142-184`
- [ ] Использовать `EmployeeService.enroll_employee()`
- [ ] Добавить поле email в HTML форму (если нужно)

### **ШАГ 6: Тестирование**
- [ ] Запустить приложение
- [ ] Проверить `/docs` - Swagger UI
- [ ] Тест 1: Enrollment через Admin UI
- [ ] Тест 2: Enrollment через API `/api/v1/employees/enroll`
- [ ] Тест 3: Распознавание через Gateway `/api/v1/gateway/snapshot`
- [ ] Тест 4: Проверить запись в attendance_log
- [ ] Тест 5: Проверить Dashboard отображает входы

---

## 🎯 Полный Flow (как должно работать после исправлений)

### **Flow 1: Регистрация сотрудника (Enrollment)**

```
[Admin UI] /admin/employees/new
     ↓ POST (first_name, last_name, department, photo)
[Admin Router] → get_employee_service().enroll_employee()
     ↓
[EmployeeService] → check email → save photo temporarily
     ↓
[EmployeeService] → recognition_service.create_embedding(photo_bytes)
     ↓
[RecognitionService] → _decode_image() → provider.detect_faces()
     ↓
[DlibProvider] → HOG detector → face_locations
     ↓
[DlibProvider] → extract_embedding() → 128-dim vector
     ↓ returns: EmbeddingResult(embedding, face_detected=True, quality)
[EmployeeService] → check quality >= 0.3
     ↓
[EmployeeService] → create Employee record → save to DB
     ↓
[EmployeeService] → create Embedding record → save vector to DB
     ↓
[БД] employees + embeddings таблицы ✅
     ↓
[Admin UI] → Redirect to /admin/employees (список обновлен)
```

### **Flow 2: Распознавание с камеры**

```
[Камера/Тест] → POST /api/v1/gateway/snapshot
     ↓ multipart/form-data: file (JPEG/PNG)
[Gateway] → validate_content_type() → validate_file_size() → validate_dimensions()
     ↓ image_bytes
[Gateway] → employee_crud.get_all_embeddings(db)
     ↓ returns: [(employee_id, vector), ...]
[Gateway] → convert to EmployeeEmbedding list
     ↓
[Gateway] → recognition_service.recognize_face(image_bytes, embeddings_db)
     ↓
[RecognitionService] → create_embedding(image)
     ↓ new_embedding
[RecognitionService] → find_best_match(new_embedding, embeddings_db)
     ↓ uses cosine_similarity()
[RecognitionService] → determine_status(similarity)
     ↓ returns: RecognitionResponse(status="match", person_id, confidence)
[Gateway] → if status == "match":
     ↓
[Gateway] → attendance_service.can_log_entry(person_id)
     ↓ check cooldown (300 sec)
[Gateway] → YES → attendance_service.log_entry(employee_id, confidence, trace_id)
     ↓
[AttendanceService] → create AttendanceLog record
     ↓
[БД] attendance_log ✅
     ↓
[Gateway] → return SnapshotResponse(status, person_id, confidence)
     ↓
[Admin Dashboard] → auto-refresh (30 sec) → отображает новый вход ✅
```

---

## 🔧 Технические детали

### **Формат vector в БД**

PostgreSQL ARRAY format:
```sql
CREATE TABLE embeddings (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES employees(id),
    vector REAL[],  -- PostgreSQL ARRAY of floats
    model_version VARCHAR(50)
);
```

Python:
```python
# Сохранение
embedding.vector = [0.1, 0.2, 0.3, ...]  # list[float]

# Чтение
vector = embedding.vector  # list[float]
```

### **Размерность векторов**

- **DlibProvider (face_recognition):** 128-dim
- **Mock (enrollment.py старый):** 512-dim

После исправления все будут использовать 128-dim от dlib.

### **Пороги распознавания**

```python
THRESHOLD_MATCH = 0.55           # "match" - уверены что это сотрудник
THRESHOLD_LOW_CONFIDENCE = 0.40  # "low_confidence" - похож, но не уверены
# < 0.40 = "unknown" - не найден
```

### **Anti-spam cooldown**

```python
COOLDOWN_SECONDS = 300  # 5 минут между записями одного сотрудника
```

---

## 📦 Зависимости

**Требуется установить:**
```bash
pip install face_recognition
```

**Зависимости face_recognition:**
- dlib
- numpy
- opencv-python (уже установлен)

**Примечание:** На macOS/Linux установка простая. На Windows может потребоваться Visual Studio Build Tools.

---

## 🚨 Известные риски

1. **face_recognition установка:** Может быть сложной на Windows
   - **Решение:** Использовать Docker или WSL2

2. **Память:** dlib требует ~400-600 MB RAM
   - **Решение:** На VPS с 2GB это приемлемо

3. **Производительность:** HOG детектор работает на CPU
   - **Решение:** Для офиса до 100 человек - достаточно

4. **Точность:** 128-dim embedding менее точен чем 512-dim ArcFace
   - **Решение:** Для контролируемой среды офиса - приемлемо

---

## ✅ Критерии готовности

### **Минимально работающая система (MVP):**
- [x] Recognition service инициализируется при старте
- [ ] Можно зарегистрировать сотрудника через Admin UI
- [ ] Embedding создается через real Recognition (не mock)
- [ ] Можно отправить фото на `/api/v1/gateway/snapshot`
- [ ] Распознавание работает и возвращает person_id
- [ ] Вход записывается в attendance_log
- [ ] Dashboard отображает входы

### **Production-ready:**
- [ ] Все 6 шагов исправлений выполнены
- [ ] Unit-тесты для каждого модуля
- [ ] Integration тесты для flow
- [ ] Error handling для всех edge cases
- [ ] Логирование всех операций
- [ ] Мониторинг производительности

---

## 📝 Следующие действия

**Сейчас:**
1. Определить последовательность шагов исправления
2. Начать с Шага 1 (подготовка окружения)
3. Пошагово исправлять код

**После исправлений:**
1. Тестирование на локальной машине
2. Деплой на VPS
3. Тестирование на реальных данных
4. Мониторинг и оптимизация

---

**Готово к исправлению! 🚀**

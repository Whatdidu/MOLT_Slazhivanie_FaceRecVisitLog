# Задачи модуля Attendance + Admin UI (Лиля)

**Ветки:** `feature/attendance`, `feature/admin-ui`

## Статусы
- [ ] Не начато
- [x] Выполнено
- [~] В процессе

---

## Фаза 1: Инфраструктура модуля Attendance

- [x] **TASK-ATT-001**: Создать структуру папок `app/modules/attendance/`
- [x] **TASK-ATT-002**: Написать Pydantic models (`models.py`)
- [x] **TASK-ATT-003**: Создать базовый сервис с заглушками (`service.py`)
- [x] **TASK-ATT-004**: Создать FastAPI router (`router.py`)

## Фаза 2: Бизнес-логика журнала посещений

- [x] **TASK-ATT-005**: Реализовать `log_entry()` — запись входа сотрудника
- [x] **TASK-ATT-006**: Реализовать `log_exit()` — запись выхода сотрудника
- [x] **TASK-ATT-007**: Реализовать анти-спам фильтр (cooldown между записями)
- [x] **TASK-ATT-008**: Реализовать `get_current_status()` — кто сейчас в офисе
- [x] **TASK-ATT-009**: Реализовать `get_history()` — история посещений за период

## Фаза 3: Отчёты и экспорт

- [x] **TASK-ATT-010**: Реализовать экспорт в JSON
- [x] **TASK-ATT-011**: Реализовать экспорт в Excel (openpyxl)
- [x] **TASK-ATT-012**: Добавить фильтры по дате/сотруднику/отделу
- [x] **TASK-ATT-013**: Реализовать агрегированную статистику (часы работы)

## Фаза 4: Веб-админка (Admin UI)

- [x] **TASK-UI-001**: Настроить Jinja2 templates + статические файлы
- [x] **TASK-UI-002**: Создать базовый layout (header, sidebar, footer)
- [x] **TASK-UI-003**: Страница Dashboard — общий статус офиса
- [x] **TASK-UI-004**: Страница "Кто в офисе" — список присутствующих
- [x] **TASK-UI-005**: Страница "Журнал посещений" — таблица с фильтрами
- [x] **TASK-UI-006**: Страница "Сотрудники" — список и карточки
- [x] **TASK-UI-007**: Форма регистрации сотрудника (загрузка фото)
- [x] **TASK-UI-008**: Страница "Отчёты" — выбор периода и экспорт

## Фаза 5: Интеграция и тесты

- [x] **TASK-ATT-014**: Интеграция с модулем Recognition (обработка событий)
- [x] **TASK-ATT-015**: Интеграция с модулем Employees (получение данных)
- [x] **TASK-ATT-016**: Написать unit-тесты для сервиса
- [x] **TASK-ATT-017**: Написать integration-тесты для API

---

## Внутренний API (контракт для других модулей)

### Методы AttendanceService

```python
from app.modules.attendance import get_attendance_service

service = get_attendance_service()

# Вызывается после успешного распознавания
await service.log_entry(employee_id: int, confidence: float, trace_id: str) -> AttendanceLog

# Вызывается при выходе (если реализовано)
await service.log_exit(employee_id: int, trace_id: str) -> AttendanceLog

# Проверка анти-спам (можно ли записать новый вход)
await service.can_log_entry(employee_id: int, cooldown_seconds: int = 300) -> bool

# Текущий статус сотрудника
await service.get_employee_status(employee_id: int) -> EmployeeStatus

# Список всех в офисе
await service.get_present_employees() -> list[EmployeeStatus]

# История за период
await service.get_attendance_history(
    start_date: date,
    end_date: date,
    employee_id: int | None = None
) -> list[AttendanceLog]
```

### Статусы присутствия

| Статус | Описание |
|--------|----------|
| `in_office` | Сотрудник в офисе |
| `left` | Сотрудник ушёл |
| `unknown` | Статус неизвестен (не было событий сегодня) |

### Конфигурация анти-спам

| Параметр | Значение | Описание |
|----------|----------|----------|
| `COOLDOWN_SECONDS` | 300 (5 мин) | Минимальный интервал между записями |
| `WORK_DAY_START` | 06:00 | Начало рабочего дня |
| `WORK_DAY_END` | 23:00 | Конец рабочего дня |

---

## API Endpoints

### Attendance API
```
POST /api/v1/attendance/log          - Записать событие (вход/выход)
GET  /api/v1/attendance/status       - Список сотрудников со статусом
GET  /api/v1/attendance/status/{id}  - Статус конкретного сотрудника
GET  /api/v1/attendance/history      - История посещений (с фильтрами)
GET  /api/v1/attendance/export/json  - Экспорт в JSON
GET  /api/v1/attendance/export/excel - Экспорт в Excel
GET  /api/v1/attendance/stats        - Агрегированная статистика
```

### Admin UI Routes
```
GET  /admin/                    - Dashboard
GET  /admin/present             - Кто в офисе
GET  /admin/attendance          - Журнал посещений
GET  /admin/employees           - Список сотрудников
GET  /admin/employees/new       - Форма регистрации
POST /admin/employees/new       - Создание сотрудника
GET  /admin/reports             - Страница отчётов
```

---

## Зависимости

```txt
jinja2>=3.1.0
python-multipart>=0.0.6
openpyxl>=3.1.0
```

---

## Примечания

### Логика анти-спам фильтра
```python
# Псевдокод
def can_log_entry(employee_id: int) -> bool:
    last_log = get_last_log(employee_id)
    if last_log is None:
        return True
    elapsed = now() - last_log.timestamp
    return elapsed.seconds >= COOLDOWN_SECONDS
```

### Связь с другими модулями
- **Recognition** → вызывает `log_entry()` после успешного распознавания
- **Employees** → используется для получения информации о сотрудниках
- **Core** → использует trace_id для сквозного логирования

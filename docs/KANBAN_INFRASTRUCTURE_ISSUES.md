# Задачи Infrastructure для канбан-доски

**Канбан-доска:** https://github.com/users/Whatdidu/projects/2
**Создание issue:** https://github.com/Whatdidu/MOLT_Slazhivanie_FaceRecVisitLog/issues/new

---

## Epic: Infrastructure Module

**Title:** `EPIC: Infrastructure Module (Татьяна)`

**Labels:** `epic`, `infrastructure`

**Body:**
```markdown
## Описание
Модуль инфраструктуры: FastAPI каркас, Docker, конфигурация, Gateway API.

## Ответственный
Татьяна

## Ветка
`feature/infrastructure`

## Фазы
- [x] Фаза 1: Базовая структура проекта (4 задачи)
- [x] Фаза 2: FastAPI каркас (4 задачи)
- [x] Фаза 3: Приемный шлюз Gateway (4 задачи)
- [x] Фаза 4: Docker и Infrastructure (4 задачи)
- [x] Фаза 5: Утилиты и константы (4 задачи)
- [ ] Фаза 6: Интеграция с модулями (4 задачи)
- [ ] Фаза 7: Деплой и мониторинг (4 задачи)

## Прогресс
20/28 задач выполнено (71%)
```

---

## Фаза 6: Интеграция с другими модулями

### TASK-INF-021

**Title:** `TASK-INF-021: Интегрировать роутер модуля Recognition`

**Labels:** `infrastructure`, `phase-3`

**Body:**
```markdown
## Описание
Подключить роутер модуля Recognition в main.py после готовности модуля Мансура.

## Acceptance Criteria
- [ ] Импортирован router из app.modules.recognition
- [ ] Router подключен с prefix /api/v1/recognition
- [ ] Endpoint /api/v1/recognition/health работает
- [ ] Протестирована интеграция с Gateway

## Связанный эпик
#[EPIC_NUMBER]

## Ветка
`feature/infrastructure`

## Зависимости
- Требуется готовность модуля Recognition (Мансур)
```

---

### TASK-INF-022

**Title:** `TASK-INF-022: Интегрировать роутер модуля Employees`

**Labels:** `infrastructure`, `phase-3`

**Body:**
```markdown
## Описание
Подключить роутер модуля Employees в main.py после готовности модуля Ольги.

## Acceptance Criteria
- [ ] Импортирован router из app.modules.employees
- [ ] Router подключен с prefix /api/v1/employees
- [ ] CRUD endpoints работают
- [ ] Протестирована интеграция с БД

## Связанный эпик
#[EPIC_NUMBER]

## Ветка
`feature/infrastructure`

## Зависимости
- Требуется готовность модуля Employees (Ольга)
```

---

### TASK-INF-023

**Title:** `TASK-INF-023: Интегрировать роутер модуля Attendance`

**Labels:** `infrastructure`, `phase-3`

**Body:**
```markdown
## Описание
Подключить роутер модуля Attendance в main.py после готовности модуля Лили.

## Acceptance Criteria
- [ ] Импортирован router из app.modules.attendance
- [ ] Router подключен с prefix /api/v1/attendance
- [ ] Endpoints журнала посещений работают
- [ ] Протестирована интеграция

## Связанный эпик
#[EPIC_NUMBER]

## Ветка
`feature/infrastructure`

## Зависимости
- Требуется готовность модуля Attendance (Лиля)
```

---

### TASK-INF-024

**Title:** `TASK-INF-024: Настроить pipeline Gateway → Recognition → Attendance`

**Labels:** `infrastructure`, `phase-3`

**Body:**
```markdown
## Описание
Настроить полный pipeline обработки снапшота:
1. Gateway принимает изображение
2. Recognition распознаёт лицо
3. Attendance записывает посещение

## Acceptance Criteria
- [ ] Gateway вызывает RecognitionService
- [ ] Результат распознавания передаётся в AttendanceService
- [ ] Полный flow работает end-to-end
- [ ] Добавлено логирование всего pipeline
- [ ] Trace ID проходит через все сервисы

## Связанный эпик
#[EPIC_NUMBER]

## Ветка
`feature/infrastructure`

## Зависимости
- Все модули должны быть готовы
```

---

## Фаза 7: Деплой и мониторинг

### TASK-INF-025

**Title:** `TASK-INF-025: Настроить деплой на VPS сервер`

**Labels:** `infrastructure`, `phase-4`

**Body:**
```markdown
## Описание
Настроить деплой приложения на VPS сервер.

## Acceptance Criteria
- [ ] Docker и docker-compose установлены на VPS
- [ ] Приложение запускается через docker-compose
- [ ] База данных PostgreSQL работает
- [ ] Приложение доступно по внешнему IP

## Связанный эпик
#[EPIC_NUMBER]

## Ветка
`feature/infrastructure`
```

---

### TASK-INF-026

**Title:** `TASK-INF-026: Настроить nginx reverse proxy`

**Labels:** `infrastructure`, `phase-4`

**Body:**
```markdown
## Описание
Настроить nginx как reverse proxy перед FastAPI приложением.

## Acceptance Criteria
- [ ] nginx установлен и настроен
- [ ] Проксирование на порт 8000
- [ ] SSL сертификат (опционально)
- [ ] Статические файлы отдаются через nginx

## Связанный эпик
#[EPIC_NUMBER]

## Ветка
`feature/infrastructure`
```

---

### TASK-INF-027

**Title:** `TASK-INF-027: Добавить мониторинг логов`

**Labels:** `infrastructure`, `phase-4`

**Body:**
```markdown
## Описание
Настроить централизованный сбор и просмотр логов.

## Acceptance Criteria
- [ ] Логи пишутся в файл/stdout
- [ ] Настроена ротация логов
- [ ] Можно просматривать логи в реальном времени
- [ ] Алерты на критические ошибки (опционально)

## Связанный эпик
#[EPIC_NUMBER]

## Ветка
`feature/infrastructure`
```

---

### TASK-INF-028

**Title:** `TASK-INF-028: Провести нагрузочное тестирование`

**Labels:** `infrastructure`, `phase-4`

**Body:**
```markdown
## Описание
Провести нагрузочное тестирование API для проверки производительности.

## Acceptance Criteria
- [ ] Выбран инструмент (locust/k6/ab)
- [ ] Написаны сценарии нагрузки
- [ ] Проведено тестирование
- [ ] Зафиксированы метрики (RPS, latency)
- [ ] Выявлены и устранены узкие места

## Связанный эпик
#[EPIC_NUMBER]

## Ветка
`feature/infrastructure`
```

---

## Инструкция по созданию

### Вариант 1: Через GitHub CLI (после установки gh)

```bash
cd scripts
chmod +x create_infrastructure_issues.sh
./create_infrastructure_issues.sh
```

### Вариант 2: Через веб-интерфейс

1. Перейти на https://github.com/Whatdidu/MOLT_Slazhivanie_FaceRecVisitLog/issues/new
2. Скопировать Title и Body из этого документа
3. Добавить Labels
4. Создать issue
5. Добавить issue в проект: Projects → Add to project → Выбрать "MOLT Kanban"

### После создания issues

Добавить каждый issue в канбан-доску:
```bash
gh project item-add 2 --owner Whatdidu --url [URL_ISSUE]
```

Или через веб-интерфейс:
1. Открыть issue
2. В правой панели найти "Projects"
3. Нажать "Add to project"
4. Выбрать проект

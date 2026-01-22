#!/bin/bash
# =============================================================================
# Скрипт создания задач модуля Infrastructure на канбан-доске
# Репозиторий: Whatdidu/MOLT_Slazhivanie_FaceRecVisitLog
# Проект: https://github.com/users/Whatdidu/projects/2
# =============================================================================

REPO="Whatdidu/MOLT_Slazhivanie_FaceRecVisitLog"
PROJECT_NUMBER=2
OWNER="Whatdidu"

echo "=== Создание Epic для модуля Infrastructure ==="

# Создаём Epic
EPIC_URL=$(gh issue create \
  --repo $REPO \
  --title "EPIC: Infrastructure Module (Татьяна)" \
  --body "## Описание
Модуль инфраструктуры: FastAPI каркас, Docker, конфигурация, Gateway API.

## Ответственный
Татьяна

## Ветка
\`feature/infrastructure\`

## Фазы
- [x] Фаза 1: Базовая структура проекта (4 задачи)
- [x] Фаза 2: FastAPI каркас (4 задачи)
- [x] Фаза 3: Приемный шлюз Gateway (4 задачи)
- [x] Фаза 4: Docker и Infrastructure (4 задачи)
- [x] Фаза 5: Утилиты и константы (4 задачи)
- [ ] Фаза 6: Интеграция с модулями (4 задачи)
- [ ] Фаза 7: Деплой и мониторинг (4 задачи)

## Прогресс
20/28 задач выполнено (71%)" \
  --label "epic,infrastructure")

echo "Epic создан: $EPIC_URL"
EPIC_NUMBER=$(echo $EPIC_URL | grep -oE '[0-9]+$')

# Добавляем Epic в проект
gh project item-add $PROJECT_NUMBER --owner $OWNER --url $EPIC_URL
echo "Epic добавлен в проект"

echo ""
echo "=== Создание задач Фазы 6: Интеграция ==="

# TASK-INF-021
ISSUE_URL=$(gh issue create \
  --repo $REPO \
  --title "TASK-INF-021: Интегрировать роутер модуля Recognition" \
  --body "## Описание
Подключить роутер модуля Recognition в main.py после готовности модуля Мансура.

## Acceptance Criteria
- [ ] Импортирован router из app.modules.recognition
- [ ] Router подключен с prefix /api/v1/recognition
- [ ] Endpoint /api/v1/recognition/health работает
- [ ] Протестирована интеграция с Gateway

## Связанный эпик
#$EPIC_NUMBER

## Ветка
\`feature/infrastructure\`

## Зависимости
- Требуется готовность модуля Recognition (Мансур)" \
  --label "infrastructure,phase-3")
gh project item-add $PROJECT_NUMBER --owner $OWNER --url $ISSUE_URL
echo "Создана задача: TASK-INF-021"

# TASK-INF-022
ISSUE_URL=$(gh issue create \
  --repo $REPO \
  --title "TASK-INF-022: Интегрировать роутер модуля Employees" \
  --body "## Описание
Подключить роутер модуля Employees в main.py после готовности модуля Ольги.

## Acceptance Criteria
- [ ] Импортирован router из app.modules.employees
- [ ] Router подключен с prefix /api/v1/employees
- [ ] CRUD endpoints работают
- [ ] Протестирована интеграция с БД

## Связанный эпик
#$EPIC_NUMBER

## Ветка
\`feature/infrastructure\`

## Зависимости
- Требуется готовность модуля Employees (Ольга)" \
  --label "infrastructure,phase-3")
gh project item-add $PROJECT_NUMBER --owner $OWNER --url $ISSUE_URL
echo "Создана задача: TASK-INF-022"

# TASK-INF-023
ISSUE_URL=$(gh issue create \
  --repo $REPO \
  --title "TASK-INF-023: Интегрировать роутер модуля Attendance" \
  --body "## Описание
Подключить роутер модуля Attendance в main.py после готовности модуля Лили.

## Acceptance Criteria
- [ ] Импортирован router из app.modules.attendance
- [ ] Router подключен с prefix /api/v1/attendance
- [ ] Endpoints журнала посещений работают
- [ ] Протестирована интеграция

## Связанный эпик
#$EPIC_NUMBER

## Ветка
\`feature/infrastructure\`

## Зависимости
- Требуется готовность модуля Attendance (Лиля)" \
  --label "infrastructure,phase-3")
gh project item-add $PROJECT_NUMBER --owner $OWNER --url $ISSUE_URL
echo "Создана задача: TASK-INF-023"

# TASK-INF-024
ISSUE_URL=$(gh issue create \
  --repo $REPO \
  --title "TASK-INF-024: Настроить pipeline Gateway → Recognition → Attendance" \
  --body "## Описание
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
#$EPIC_NUMBER

## Ветка
\`feature/infrastructure\`

## Зависимости
- Все модули должны быть готовы" \
  --label "infrastructure,phase-3")
gh project item-add $PROJECT_NUMBER --owner $OWNER --url $ISSUE_URL
echo "Создана задача: TASK-INF-024"

echo ""
echo "=== Создание задач Фазы 7: Деплой ==="

# TASK-INF-025
ISSUE_URL=$(gh issue create \
  --repo $REPO \
  --title "TASK-INF-025: Настроить деплой на VPS сервер" \
  --body "## Описание
Настроить деплой приложения на VPS сервер.

## Acceptance Criteria
- [ ] Docker и docker-compose установлены на VPS
- [ ] Приложение запускается через docker-compose
- [ ] База данных PostgreSQL работает
- [ ] Приложение доступно по внешнему IP

## Связанный эпик
#$EPIC_NUMBER

## Ветка
\`feature/infrastructure\`" \
  --label "infrastructure,phase-4")
gh project item-add $PROJECT_NUMBER --owner $OWNER --url $ISSUE_URL
echo "Создана задача: TASK-INF-025"

# TASK-INF-026
ISSUE_URL=$(gh issue create \
  --repo $REPO \
  --title "TASK-INF-026: Настроить nginx reverse proxy" \
  --body "## Описание
Настроить nginx как reverse proxy перед FastAPI приложением.

## Acceptance Criteria
- [ ] nginx установлен и настроен
- [ ] Проксирование на порт 8000
- [ ] SSL сертификат (опционально)
- [ ] Статические файлы отдаются через nginx

## Связанный эпик
#$EPIC_NUMBER

## Ветка
\`feature/infrastructure\`" \
  --label "infrastructure,phase-4")
gh project item-add $PROJECT_NUMBER --owner $OWNER --url $ISSUE_URL
echo "Создана задача: TASK-INF-026"

# TASK-INF-027
ISSUE_URL=$(gh issue create \
  --repo $REPO \
  --title "TASK-INF-027: Добавить мониторинг логов" \
  --body "## Описание
Настроить централизованный сбор и просмотр логов.

## Acceptance Criteria
- [ ] Логи пишутся в файл/stdout
- [ ] Настроен ротация логов
- [ ] Можно просматривать логи в реальном времени
- [ ] Алерты на критические ошибки (опционально)

## Связанный эпик
#$EPIC_NUMBER

## Ветка
\`feature/infrastructure\`" \
  --label "infrastructure,phase-4")
gh project item-add $PROJECT_NUMBER --owner $OWNER --url $ISSUE_URL
echo "Создана задача: TASK-INF-027"

# TASK-INF-028
ISSUE_URL=$(gh issue create \
  --repo $REPO \
  --title "TASK-INF-028: Провести нагрузочное тестирование" \
  --body "## Описание
Провести нагрузочное тестирование API для проверки производительности.

## Acceptance Criteria
- [ ] Выбран инструмент (locust/k6/ab)
- [ ] Написаны сценарии нагрузки
- [ ] Проведено тестирование
- [ ] Зафиксированы метрики (RPS, latency)
- [ ] Выявлены и устранены узкие места

## Связанный эпик
#$EPIC_NUMBER

## Ветка
\`feature/infrastructure\`" \
  --label "infrastructure,phase-4")
gh project item-add $PROJECT_NUMBER --owner $OWNER --url $ISSUE_URL
echo "Создана задача: TASK-INF-028"

echo ""
echo "=== Готово! ==="
echo "Epic и 8 задач созданы и добавлены на канбан-доску"
echo "Канбан-доска: https://github.com/users/Whatdidu/projects/2"

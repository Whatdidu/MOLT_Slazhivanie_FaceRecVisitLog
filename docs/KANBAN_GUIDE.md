# Руководство по ведению задач в канбан-доске

## Канбан-доска проекта

**URL:** https://github.com/users/Whatdidu/projects/2

**Репозиторий:** https://github.com/Whatdidu/MOLT_Slazhivanie_FaceRecVisitLog

---

## Настройка доступа

### 1. Установка GitHub CLI

```bash
# macOS
brew install gh

# Ubuntu/Debian
sudo apt install gh

# Windows
winget install GitHub.cli
```

### 2. Авторизация

```bash
# Базовая авторизация
gh auth login

# Выбрать:
# - GitHub.com
# - HTTPS
# - Login with a web browser
```

### 3. Добавление прав для работы с проектами

```bash
gh auth refresh -h github.com -s project,read:project
```

После выполнения команды:
1. Скопируйте код из терминала
2. Откройте https://github.com/login/device
3. Введите код и подтвердите доступ

### 4. Проверка доступа

```bash
gh auth status
gh project list --owner Whatdidu
```

---

## Структура задач

### Типы задач

| Тип | Лейбл | Описание |
|-----|-------|----------|
| Эпик | `epic` | Крупная функциональность, объединяющая несколько задач |
| Задача | - | Конкретная работа, которую можно выполнить за 1-3 дня |
| Баг | `bug` | Исправление ошибки |

### Лейблы по модулям

| Лейбл | Ответственный | Модуль |
|-------|---------------|--------|
| `recognition` | Мансур | ML и распознавание лиц |
| `attendance` | Лиля | Журнал посещений |
| `admin-ui` | Лиля | Веб-админка |
| `employees` | Ольга | CRUD сотрудников, БД |
| `infrastructure` | Татьяна | FastAPI, Docker, Core |

### Лейблы по фазам

- `phase-1` — Инфраструктура модуля
- `phase-2` — Основная реализация
- `phase-3` — Интеграция
- `phase-4` — Тесты и документация

---

## Создание задач

### Формат заголовка

```
TASK-{MODULE}-{NUMBER}: Краткое описание
```

Примеры:
- `TASK-ML-005: Реализовать DeepFace провайдер`
- `TASK-DB-001: Создать модель Employee`
- `TASK-UI-003: Страница списка сотрудников`

### Коды модулей

| Код | Модуль |
|-----|--------|
| ML | Recognition (Мансур) |
| ATT | Attendance (Лиля) |
| UI | Admin UI (Лиля) |
| DB | Database/Employees (Ольга) |
| INF | Infrastructure (Татьяна) |

### Создание через GitHub CLI

```bash
gh issue create \
  --repo Whatdidu/MOLT_Slazhivanie_FaceRecVisitLog \
  --title "TASK-ML-005: Реализовать DeepFace провайдер" \
  --body "## Описание
Реализовать провайдер для детекции лиц на базе DeepFace.

## Acceptance Criteria
- [ ] Провайдер создан в providers/deepface.py
- [ ] Метод detect_face() работает
- [ ] Добавлены тесты

## Связанный эпик
#6" \
  --label "recognition,phase-2"
```

### Создание через веб-интерфейс

1. Перейти в https://github.com/Whatdidu/MOLT_Slazhivanie_FaceRecVisitLog/issues
2. Нажать "New issue"
3. Заполнить по шаблону (см. ниже)
4. Добавить лейблы и milestone

### Шаблон задачи

```markdown
## Описание
[Что нужно сделать]

## Acceptance Criteria
- [ ] Критерий 1
- [ ] Критерий 2
- [ ] Критерий 3

## Связанный эпик
#[номер эпика]

## Ветка
`feature/[название]`
```

---

## Добавление задачи в канбан-доску

После создания issue добавьте его в проект:

```bash
gh project item-add 2 --owner Whatdidu \
  --url https://github.com/Whatdidu/MOLT_Slazhivanie_FaceRecVisitLog/issues/[НОМЕР]
```

---

## Статусы задач (колонки доски)

| Статус | Описание |
|--------|----------|
| **Todo** | Задача запланирована, ещё не начата |
| **In Progress** | Задача в работе |
| **Done** | Задача выполнена |

---

## Работа с Claude Code

Claude Code может автоматически управлять задачами на доске. Для этого используйте следующие команды в диалоге:

### Просмотр задач

> "Покажи мои открытые задачи"
> "Какие задачи в статусе In Progress?"

### Взять задачу в работу

> "Возьми задачу #15 в работу"
> "Начни работу над TASK-ML-005"

Claude выполнит:
```bash
gh project item-edit --project-id [ID] --id [ITEM_ID] --field-id [STATUS_FIELD] --single-select-option-id [IN_PROGRESS_ID]
```

### Завершить задачу

> "Закрой задачу #15"
> "Отметь TASK-ML-005 как выполненную"

Claude выполнит:
```bash
gh issue close [НОМЕР] --repo Whatdidu/MOLT_Slazhivanie_FaceRecVisitLog
```

### Создать задачу

> "Создай задачу для реализации функции X в модуле recognition"

Claude создаст issue с правильными лейблами и добавит в проект.

---

## Workflow разработки

### 1. Выбор задачи

```bash
# Посмотреть свои задачи
gh issue list --repo Whatdidu/MOLT_Slazhivanie_FaceRecVisitLog \
  --label "recognition" --state open
```

### 2. Создание ветки

```bash
git checkout -b feature/task-ml-005-deepface-provider
```

### 3. Работа над задачей

- Переместить задачу в "In Progress" на доске
- Делать коммиты с референсом на issue: `git commit -m "feat: add deepface provider #15"`

### 4. Создание PR

```bash
gh pr create --title "feat: DeepFace provider" \
  --body "Closes #15" \
  --base master
```

### 5. После merge

- Задача автоматически закроется (если в PR есть `Closes #15`)
- Или закрыть вручную: `gh issue close 15`

---

## Полезные команды

### Список открытых issues

```bash
gh issue list --repo Whatdidu/MOLT_Slazhivanie_FaceRecVisitLog --state open
```

### Фильтр по лейблу

```bash
gh issue list --repo Whatdidu/MOLT_Slazhivanie_FaceRecVisitLog --label "epic"
```

### Просмотр деталей issue

```bash
gh issue view 15 --repo Whatdidu/MOLT_Slazhivanie_FaceRecVisitLog
```

### Список задач в проекте

```bash
gh project item-list 2 --owner Whatdidu --format json
```

---

## Ответственные по модулям

| Участник | Модуль | Ветка | Лейблы |
|----------|--------|-------|--------|
| **Мансур** | Recognition (ML) | `feature/ml-recognition` | `recognition`, `phase-*` |
| **Лиля** | Attendance, Admin UI | `feature/attendance`, `feature/admin-ui` | `attendance`, `admin-ui` |
| **Ольга** | Employees, DB | `feature/database` | `employees` |
| **Татьяна** | Infrastructure, Core | `feature/infrastructure` | `infrastructure` |

---

## Правила

1. **Одна задача = один PR** — не смешивайте несколько задач в одном PR
2. **Обновляйте статус** — перемещайте задачу в "In Progress" когда начинаете работу
3. **Связывайте PR с issue** — используйте `Closes #N` в описании PR
4. **Используйте лейблы** — это помогает фильтровать и отслеживать прогресс
5. **Пишите acceptance criteria** — чтобы было понятно, когда задача готова

---

## Помощь

При возникновении вопросов:
- Спросите Claude Code: "Как создать задачу для модуля X?"
- Документация GitHub CLI: https://cli.github.com/manual/
- Issues проекта: https://github.com/Whatdidu/MOLT_Slazhivanie_FaceRecVisitLog/issues

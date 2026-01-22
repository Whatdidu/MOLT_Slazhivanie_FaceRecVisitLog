# Инструкция по настройке GitHub CLI и работе с канбан-доской

**Автор:** Лиля Афанасева
**Дата:** 21.01.2026

---

## Зачем это нужно

GitHub CLI (gh) позволяет:
- Создавать задачи (issues) из терминала
- Добавлять задачи на канбан-доску
- Закрывать задачи при завершении
- Автоматизировать работу с Claude Code

---

## Шаг 1: Установка GitHub CLI

### macOS

**Вариант А: Через Homebrew (если работает)**
```bash
brew install gh
```

**Вариант Б: Ручная установка (если Homebrew не работает)**
```bash
# Скачать архив
curl -L -o /tmp/gh.zip "https://github.com/cli/cli/releases/download/v2.43.1/gh_2.43.1_macOS_amd64.zip"

# Распаковать
cd /tmp && unzip -o gh.zip

# Проверить установку
/tmp/gh_2.43.1_macOS_amd64/bin/gh --version
```

> **Совет:** Для удобства добавьте путь в PATH или создайте alias:
> ```bash
> echo 'alias gh="/tmp/gh_2.43.1_macOS_amd64/bin/gh"' >> ~/.zshrc
> source ~/.zshrc
> ```

### Windows
```bash
winget install GitHub.cli
```

### Ubuntu/Debian
```bash
sudo apt install gh
```

---

## Шаг 2: Авторизация через браузер

### 2.1 Базовая авторизация

```bash
gh auth login -h github.com -p https -w
```

Появится сообщение:
```
! First copy your one-time code: XXXX-XXXX
Open this URL to continue in your web browser: https://github.com/login/device
```

**Действия:**
1. Скопируйте код (например, `3FF1-A172`)
2. Откройте в браузере: https://github.com/login/device
3. Введите код
4. Нажмите "Authorize GitHub CLI"
5. Дождитесь сообщения `✓ Authentication complete`

### 2.2 Добавление прав для работы с Projects

```bash
gh auth refresh -h github.com -s project,read:project
```

Снова появится код — повторите процесс авторизации через браузер.

### 2.3 Проверка авторизации

```bash
gh auth status
```

Ожидаемый результат:
```
github.com
  ✓ Logged in to github.com account ВашеИмя (keyring)
  - Active account: true
```

---

## Шаг 3: Проверка доступа к проекту

```bash
# Список проектов
gh project list --owner Whatdidu

# Ожидаемый результат:
# 2    Sputnik Face ID: MVP Development    open    PVT_kwHOAYsxQs4BNHMM
```

---

## Шаг 4: Создание задач

### Формат заголовка задачи
```
TASK-{MODULE}-{NUMBER}: Краткое описание
```

**Коды модулей:**
| Код | Модуль | Ответственный |
|-----|--------|---------------|
| ML | Recognition | Мансур |
| ATT | Attendance | Лиля |
| UI | Admin UI | Лиля |
| DB | Database/Employees | Ольга |
| INF | Infrastructure | Татьяна |

### Пример создания задачи

```bash
gh issue create \
  --repo Whatdidu/MOLT_Slazhivanie_FaceRecVisitLog \
  --title "TASK-DB-001: Создать модель Employee" \
  --body "## Описание
Создать SQLAlchemy модель для таблицы employees.

## Acceptance Criteria
- [ ] Модель создана
- [ ] Поля: id, first_name, last_name, department
- [ ] Добавлены индексы

## Связанный эпик
#[номер_эпика]" \
  --label "employees,phase-1"
```

### Доступные лейблы
- По модулям: `recognition`, `attendance`, `admin-ui`, `employees`, `infrastructure`
- По фазам: `phase-1`, `phase-2`, `phase-3`, `phase-4`
- Специальные: `epic`, `bug`

---

## Шаг 5: Добавление задачи на канбан-доску

После создания issue добавьте его в проект:

```bash
gh project item-add 2 --owner Whatdidu \
  --url https://github.com/Whatdidu/MOLT_Slazhivanie_FaceRecVisitLog/issues/[НОМЕР]
```

**Пример:**
```bash
gh project item-add 2 --owner Whatdidu \
  --url https://github.com/Whatdidu/MOLT_Slazhivanie_FaceRecVisitLog/issues/43
```

---

## Шаг 6: Закрытие задачи

Когда задача выполнена:

```bash
gh issue close [НОМЕР] \
  --repo Whatdidu/MOLT_Slazhivanie_FaceRecVisitLog \
  --comment "✅ Выполнено в PR #[номер_PR]"
```

**Пример:**
```bash
gh issue close 43 \
  --repo Whatdidu/MOLT_Slazhivanie_FaceRecVisitLog \
  --comment "✅ Выполнено в PR #18"
```

---

## Полезные команды

### Просмотр своих задач
```bash
# Открытые задачи по лейблу
gh issue list --repo Whatdidu/MOLT_Slazhivanie_FaceRecVisitLog \
  --label "employees" --state open

# Все задачи (включая закрытые)
gh issue list --repo Whatdidu/MOLT_Slazhivanie_FaceRecVisitLog \
  --label "employees" --state all
```

### Просмотр деталей задачи
```bash
gh issue view 43 --repo Whatdidu/MOLT_Slazhivanie_FaceRecVisitLog
```

### Список задач на доске
```bash
gh project item-list 2 --owner Whatdidu
```

### Создание PR
```bash
gh pr create --title "feat: описание" \
  --body "Closes #43" \
  --base master
```

---

## Работа с Claude Code

Claude Code может автоматически управлять задачами. Примеры команд:

- *"Покажи мои открытые задачи"*
- *"Создай задачу для реализации функции X"*
- *"Закрой задачу #43"*
- *"Добавь задачу на канбан-доску"*

---

## Troubleshooting

### Ошибка "Resource not accessible by personal access token"
**Причина:** Недостаточно прав у токена
**Решение:** Выполните `gh auth refresh -h github.com -s project,read:project`

### Ошибка "context deadline exceeded"
**Причина:** Таймаут при ожидании авторизации в браузере
**Решение:** Повторите команду и быстрее введите код в браузере

### Лейбл не найден
**Причина:** Лейбл не существует в репозитории
**Решение:** Используйте только существующие лейблы или создайте нужный в GitHub UI

### gh command not found
**Причина:** gh не в PATH
**Решение:** Используйте полный путь `/tmp/gh_2.43.1_macOS_amd64/bin/gh` или добавьте alias

---

## Ссылки

- **Репозиторий:** https://github.com/Whatdidu/MOLT_Slazhivanie_FaceRecVisitLog
- **Канбан-доска:** https://github.com/users/Whatdidu/projects/2
- **GitHub CLI документация:** https://cli.github.com/manual/
- **KANBAN_GUIDE:** [docs/KANBAN_GUIDE.md](./KANBAN_GUIDE.md)

---

## Краткая шпаргалка

```bash
# Установка (macOS, ручная)
curl -L -o /tmp/gh.zip "https://github.com/cli/cli/releases/download/v2.43.1/gh_2.43.1_macOS_amd64.zip"
cd /tmp && unzip -o gh.zip
alias gh="/tmp/gh_2.43.1_macOS_amd64/bin/gh"

# Авторизация
gh auth login -h github.com -p https -w
gh auth refresh -h github.com -s project,read:project

# Создать задачу
gh issue create --repo Whatdidu/MOLT_Slazhivanie_FaceRecVisitLog \
  --title "TASK-XXX-001: Описание" --label "ваш_лейбл"

# Добавить на доску
gh project item-add 2 --owner Whatdidu \
  --url https://github.com/Whatdidu/MOLT_Slazhivanie_FaceRecVisitLog/issues/XX

# Закрыть задачу
gh issue close XX --repo Whatdidu/MOLT_Slazhivanie_FaceRecVisitLog
```

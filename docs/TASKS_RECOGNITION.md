# Задачи модуля Recognition (Мансур)

**Ветка:** `feature/ml-recognition`
**Прогресс:** 15/15 (100%) ✅

## Статусы
- [ ] Не начато
- [x] Выполнено
- [~] В процессе

---

## Фаза 1: Инфраструктура модуля ✅ 100%

- [x] **TASK-ML-001**: Создать структуру папок `app/modules/recognition/`
- [x] **TASK-ML-002**: Написать Pydantic models (`models.py`)
- [x] **TASK-ML-003**: Создать базовый класс провайдера (`providers/base.py`)
- [x] **TASK-ML-004**: Создать сервис распознавания (`service.py`)

## Фаза 2: ML Pipeline ✅ 100%

- [x] **TASK-ML-005**: Реализовать провайдер для детекции лиц
- [x] **TASK-ML-006**: Реализовать извлечение embeddings
- [x] **TASK-ML-007**: Написать функцию cosine similarity
- [x] **TASK-ML-008**: Определить и протестировать пороги (thresholds)

## Фаза 3: Сервис распознавания ✅ 100%

- [x] **TASK-ML-009**: Реализовать `create_embedding()`
- [x] **TASK-ML-010**: Реализовать `recognize_face()` с поиском по базе
- [x] **TASK-ML-011**: Добавить валидацию качества изображения
- [x] **TASK-ML-012**: Добавить кэширование модели (singleton pattern)

## Фаза 4: API и провайдеры ✅ 100%

- [x] **TASK-ML-013**: Создать FastAPI router (`router.py`)
- [x] **TASK-ML-014**: Добавить dlib провайдер (lightweight, 2GB RAM)
- [x] **TASK-ML-015**: Добавить выбор провайдера через конфиг

---

## Провайдеры распознавания

### Доступные провайдеры

| Провайдер | RAM | Точность | Embedding | Статус |
|-----------|-----|----------|-----------|--------|
| **dlib** (по умолчанию) | ~500 MB | 99.3% | 128-dim | ✅ Реализован |
| mock | ~0 MB | — | — | ✅ Для тестов |

### Настройка провайдера

```env
# В .env файле:
RECOGNITION_PROVIDER=dlib   # Lightweight (по умолчанию)
RECOGNITION_PROVIDER=mock   # Без ML (для тестирования)
```

### Файлы провайдеров

```
app/modules/recognition/providers/
├── __init__.py           # Экспорты
├── base.py               # Абстрактный базовый класс
└── dlib_provider.py      # Dlib/face_recognition провайдер
```

---

## Внутренний API (контракт для других модулей)

### Методы RecognitionService

```python
from app.modules.recognition import get_recognition_service

service = get_recognition_service()

# Используется модулем employees при регистрации
async def create_embedding(image: bytes) -> EmbeddingResult

# Используется при распознавании с камеры
async def recognize_face(image: bytes, embeddings_db: list) -> RecognitionResponse

# Вспомогательный метод сравнения
async def compare_faces(embedding1: list, embedding2: list) -> float
```

### Статусы распознавания

| Статус | Confidence | Описание |
|--------|------------|----------|
| `match` | >= 0.55 | Лицо распознано |
| `low_confidence` | 0.40 - 0.55 | Низкая уверенность |
| `unknown` | < 0.40 | Не найдено в базе |
| `no_face` | - | Лицо не обнаружено |
| `error` | - | Ошибка обработки |

---

## Зависимости

```txt
# Lightweight (по умолчанию)
face_recognition>=1.3.0
dlib>=19.24.0
opencv-python-headless>=4.7.0
numpy>=1.23.0
```

---

## История изменений

| Дата | Изменение |
|------|-----------|
| 2026-01-23 | Добавлен dlib провайдер для работы на 2GB RAM серверах |
| 2026-01-22 | Завершены все основные задачи модуля |
| 2026-01-21 | Реализован сервис распознавания |

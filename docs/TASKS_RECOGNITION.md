# Задачи модуля Recognition (Мансур)

**Ветка:** `feature/ml-recognition`

## Статусы
- [ ] Не начато
- [x] Выполнено
- [~] В процессе

---

## Фаза 1: Инфраструктура модуля

- [x] **TASK-ML-001**: Создать структуру папок `app/modules/recognition/`
- [ ] **TASK-ML-002**: Написать Pydantic models (`models.py`)
- [ ] **TASK-ML-003**: Создать базовый класс провайдера (`providers/base.py`)
- [ ] **TASK-ML-004**: Создать заглушки сервиса с mock-ответами

## Фаза 2: ML Pipeline (DeepFace)

- [ ] **TASK-ML-005**: Реализовать DeepFace провайдер для детекции лиц
- [ ] **TASK-ML-006**: Реализовать извлечение embeddings (ArcFace модель)
- [ ] **TASK-ML-007**: Написать функцию cosine similarity
- [ ] **TASK-ML-008**: Определить и протестировать пороги (thresholds)

## Фаза 3: Сервис распознавания

- [ ] **TASK-ML-009**: Реализовать `create_embedding()`
- [ ] **TASK-ML-010**: Реализовать `recognize_face()` с поиском по базе
- [ ] **TASK-ML-011**: Добавить валидацию качества изображения
- [ ] **TASK-ML-012**: Добавить кэширование модели (singleton pattern)

## Фаза 4: API и тесты

- [ ] **TASK-ML-013**: Создать FastAPI router (`router.py`)
- [ ] **TASK-ML-014**: Написать unit-тесты
- [ ] **TASK-ML-015**: Подготовить тестовые изображения

---

## Внутренний API (контракт для других модулей)

### Методы RecognitionService

```python
from app.modules.recognition import get_recognition_service

service = get_recognition_service()

# Используется модулем employees при регистрации
await service.create_embedding(image: bytes) -> EmbeddingResult

# Используется при распознавании с камеры
await service.recognize_face(image: bytes, embeddings_db: list) -> RecognitionResult

# Вспомогательный метод сравнения
await service.compare_faces(embedding1: list, embedding2: list) -> float
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

## API Endpoints

```
POST /api/v1/recognition/detect     - Распознать лицо
POST /api/v1/recognition/embedding  - Создать эмбеддинг
POST /api/v1/recognition/compare    - Сравнить два вектора
GET  /api/v1/recognition/health     - Проверка сервиса
```

---

## Зависимости

```txt
deepface>=0.0.79
opencv-python-headless>=4.7.0
numpy>=1.23.0
tf-keras>=2.15.0
```

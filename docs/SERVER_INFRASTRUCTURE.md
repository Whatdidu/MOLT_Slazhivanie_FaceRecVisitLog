# Серверная инфраструктура SK-MOLT

**Дата обновления:** 2026-01-23

---

## Сервер SmartApe VPS

### Доступы

| Параметр | Значение |
|----------|----------|
| **IP адрес** | `109.172.9.137` |
| **Домен** | `s1465303.smartape-vps.com` |
| **SSH пользователь** | `root` |
| **Пароль** | См. `.env` файл (`SMARTAPE_PASSWORD`) |

### Подключение

```bash
ssh root@109.172.9.137
# или
ssh root@s1465303.smartape-vps.com
```

---

## Характеристики сервера

| Параметр | Значение | Статус для ML |
|----------|----------|---------------|
| **CPU** | 4 ядра Intel Xeon (Icelake) @ 2.0 GHz | ✅ Достаточно |
| **RAM** | 2 GB (доступно ~1.3 GB) | ✅ Достаточно для dlib |
| **Диск** | 20 GB SSD (свободно ~13 GB) | ✅ Достаточно |
| **ОС** | Ubuntu 24.04.3 LTS (Noble Numbat) | ✅ OK |
| **Docker** | v28.2.2 | ✅ OK |

---

## Провайдеры распознавания лиц

### Доступные провайдеры

| Провайдер | RAM | Точность | Embedding | Для 2 GB VPS |
|-----------|-----|----------|-----------|--------------|
| **dlib** (по умолчанию) | ~500 MB | 99.3% | 128-dim | ✅ **Да** |
| mock | ~0 MB | — | — | ✅ Для тестов |

### Переключение провайдера

```bash
# В .env файле:
RECOGNITION_PROVIDER=dlib   # Lightweight (рекомендуется)
RECOGNITION_PROVIDER=mock   # Без ML (для тестирования)
```

### Оценка RAM для dlib провайдера

| Компонент | Потребление RAM |
|-----------|-----------------|
| face_recognition (dlib) | ~400-500 MB |
| PostgreSQL | ~100-200 MB |
| FastAPI + uvicorn | ~100-150 MB |
| Другие сервисы на сервере | ~700 MB |
| **ИТОГО** | **~1.3-1.5 GB** |
| **Доступно на VPS** | **~1.3 GB** |
| **Статус** | ✅ **Достаточно** |

---

## Запущенные сервисы

### Docker контейнеры

| Контейнер | Порт | Проект | Статус |
|-----------|------|--------|--------|
| `sputnik-faceid-db` | 5433 | SK-MOLT (FaceID) | ✅ Healthy |
| `sk_lk_payment_postgres` | 5432 | sk_lk_payment | ✅ Healthy |
| `sk_lk_payment_postgrest` | 3000 (внутр.) | sk_lk_payment | ✅ Running |
| `sk_lk_payment_nginx` | 8080 | sk_lk_payment | ⚠️ Unhealthy |
| `watchtower` | — | Автообновление | ✅ Healthy |
| `shadowbox` | — | Outline VPN | ✅ Running |

---

## Сетевая конфигурация

### Открытые порты

| Порт | Сервис | Доступ |
|------|--------|--------|
| 22 | SSH | Внешний |
| 5432 | PostgreSQL (sk_lk_payment) | Внешний |
| 5433 | PostgreSQL (sputnik_faceid) | Внешний |
| 8080 | Nginx (sk_lk_payment API) | Внешний |
| 8000 | FastAPI (sputnik_faceid) | **Не запущен** |

---

## База данных Sputnik FaceID

### Подключение

```bash
# Connection string
postgresql://sputnik:SputnikFace2024!Secure@109.172.9.137:5433/sputnik_faceid

# Через Docker на сервере
docker exec -it sputnik-faceid-db psql -U sputnik -d sputnik_faceid
```

### Параметры

| Параметр | Значение |
|----------|----------|
| Host | 109.172.9.137 |
| Port | 5433 |
| Database | sputnik_faceid |
| User | sputnik |
| Password | См. `.env` (`SPUTNIK_DB_PASSWORD`) |

---

## Деплой приложения

### Команды для деплоя

```bash
# 1. Подключиться к серверу
ssh root@109.172.9.137

# 2. Клонировать репозиторий
cd /opt
git clone https://github.com/Whatdidu/MOLT_Slazhivanie_FaceRecVisitLog.git sputnik-faceid
cd sputnik-faceid

# 3. Создать .env файл
cp .env.example .env
nano .env  # Настроить переменные

# 4. Запустить через Docker Compose
docker compose up -d

# 5. Проверить статус
docker compose ps
docker compose logs -f app
```

---

## Мониторинг

### Проверка состояния

```bash
# SSH на сервер
ssh root@109.172.9.137

# Проверить RAM
free -h

# Проверить Docker контейнеры
docker ps
docker stats --no-stream
```

### Health-check endpoints (после деплоя)

```bash
# API health
curl http://109.172.9.137:8000/health

# Database health
curl http://109.172.9.137:8000/api/v1/info
```

---

## История изменений

| Дата | Изменение |
|------|-----------|
| 2026-01-23 | Добавлен dlib провайдер для работы на 2 GB RAM |
| 2026-01-22 | Первичный аудит сервера |
| 2026-01-16 | Развернут PostgreSQL для sputnik_faceid (порт 5433) |

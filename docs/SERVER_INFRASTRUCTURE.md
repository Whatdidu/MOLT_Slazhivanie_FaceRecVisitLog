# Серверная инфраструктура SK-MOLT

**Дата обновления:** 2026-01-24

---

## Yandex Cloud VM

### Доступы

| Параметр | Значение |
|----------|----------|
| **IP адрес** | `158.160.62.149` |
| **VM Name** | `beemos-api` |
| **VM ID** | `fhm301iskprq0ur79j8c` |
| **Zone** | `ru-central1-a` |
| **SSH пользователь** | `yc-user` |

### Подключение

```bash
# Через yc CLI (рекомендуется)
yc compute ssh --id fhm301iskprq0ur79j8c --login yc-user

# Напрямую по SSH
ssh yc-user@158.160.62.149
```

---

## Характеристики сервера

| Параметр | Значение |
|----------|----------|
| **Платформа** | Yandex Cloud Compute |
| **ОС** | Ubuntu 22.04.5 LTS |
| **RAM** | 4 GB |
| **Disk** | 20 GB SSD |
| **IP** | Статический |
| **Docker** | v29.1.5 + Compose v5.0.2 |

---

## Провайдеры распознавания лиц

### Доступные провайдеры

| Провайдер | RAM | Точность | Embedding | Рекомендация |
|-----------|-----|----------|-----------|--------------|
| **dlib** (по умолчанию) | ~500 MB | 99.3% | 128-dim | ✅ Рекомендуется |
| mock | ~0 MB | — | — | Для тестов |

### Переключение провайдера

```bash
# В .env файле:
RECOGNITION_PROVIDER=dlib   # Lightweight (рекомендуется)
RECOGNITION_PROVIDER=mock   # Без ML (для тестирования)
```

---

## База данных Sputnik FaceID

### Подключение

```bash
# Connection string
postgresql://sputnik:SputnikFace2024!Secure@158.160.62.149:5432/sputnik_faceid

# Через Docker на сервере
docker exec -it sputnik-faceid-db psql -U sputnik -d sputnik_faceid
```

### Параметры

| Параметр | Значение |
|----------|----------|
| Host | 158.160.62.149 |
| Port | 5432 |
| Database | sputnik_faceid |
| User | sputnik |
| Password | См. `.env` (`DB_PASSWORD`) |

---

## Деплой приложения

### Команды для деплоя

```bash
# 1. Подключиться к серверу
ssh yc-user@158.160.62.149

# 2. Перейти в директорию проекта
cd /opt/sputnik-faceid

# 3. Обновить код
git pull origin master

# 4. Перезапустить через Docker Compose
docker compose down
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
ssh yc-user@158.160.62.149

# Проверить RAM
free -h

# Проверить Docker контейнеры
docker ps
docker stats --no-stream
```

### Health-check endpoints

```bash
# API health
curl http://158.160.62.149:8000/health

# Database health
curl http://158.160.62.149:8000/api/v1/info
```

---

## Yandex Cloud CLI

### Полезные команды

```bash
# Список VM
yc compute instance list --folder-id b1gk0154cjiik7qgvokr

# Статус VM
yc compute instance get fhm301iskprq0ur79j8c

# Подключение по SSH
yc compute ssh --id fhm301iskprq0ur79j8c --login yc-user

# Логи VM
yc compute instance get-serial-port-output fhm301iskprq0ur79j8c
```

---

## FileBrowser (просмотр снапшотов)

### Доступ

| Параметр | Значение |
|----------|----------|
| **URL** | `http://158.160.62.149:8080` |
| **Логин** | `admin` |
| **Пароль** | `2E3ma-KqseolsMOY` |

### Описание

Веб-интерфейс для просмотра снапшотов с камеры в реальном времени.

---

## История изменений

| Дата | Изменение |
|------|-----------|
| 2026-01-27 | Добавлен FileBrowser для просмотра снапшотов |
| 2026-01-24 | Миграция на Yandex Cloud (158.160.62.149) |
| 2026-01-23 | Добавлен dlib провайдер для работы на 2 GB RAM |
| 2026-01-22 | Первичный аудит сервера |

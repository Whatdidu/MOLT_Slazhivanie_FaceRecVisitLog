# Инструкция по деплою Sputnik FaceID

**Дата:** 2026-01-24

---

## Данные сервера (Yandex Cloud)

| Параметр | Значение |
|----------|----------|
| **IP** | `158.160.62.149` |
| **VM Name** | `beemos-api` |
| **VM ID** | `fhm301iskprq0ur79j8c` |
| **SSH** | `ssh yc-user@158.160.62.149` |
| **Zone** | `ru-central1-a` |

---

## Шаг 1: Подключиться к серверу

```bash
# Через yc CLI (рекомендуется)
yc compute ssh --id fhm301iskprq0ur79j8c --login yc-user

# Или напрямую
ssh yc-user@158.160.62.149
```

---

## Шаг 2: Клонировать проект

```bash
cd /opt
sudo git clone https://github.com/Whatdidu/MOLT_Slazhivanie_FaceRecVisitLog.git sputnik-faceid
cd sputnik-faceid/deploy
```

---

## Шаг 3: Настроить .env файл

```bash
cp .env.example .env
nano .env
```

**Обязательно заполнить:**

```env
DB_HOST=158.160.62.149
DB_PORT=5432
DB_NAME=sputnik_faceid
DB_USER=sputnik
DB_PASSWORD=SputnikFace2024!Secure
DATABASE_URL=postgresql://sputnik:SputnikFace2024!Secure@158.160.62.149:5432/sputnik_faceid
RECOGNITION_PROVIDER=dlib
DEBUG=false
```

---

## Шаг 4: Запустить приложение

```bash
chmod +x deploy.sh
./deploy.sh start
```

---

## Шаг 5: Проверить работу

```bash
# Статус контейнеров
./deploy.sh status

# Health check
curl http://localhost/health

# Логи приложения
./deploy.sh logs app
```

---

## Команды управления

| Команда | Описание |
|---------|----------|
| `./deploy.sh start` | Запуск всех сервисов |
| `./deploy.sh stop` | Остановка |
| `./deploy.sh restart` | Перезапуск |
| `./deploy.sh status` | Статус контейнеров |
| `./deploy.sh logs` | Все логи |
| `./deploy.sh logs app` | Логи приложения |
| `./deploy.sh logs nginx` | Логи Nginx |
| `./deploy.sh logs db` | Логи PostgreSQL |
| `./deploy.sh update` | Обновить из git и перезапустить |
| `./deploy.sh backup` | Бэкап базы данных |
| `./deploy.sh migrate` | Применить миграции БД |

---

## Endpoints после деплоя

| URL | Описание |
|-----|----------|
| `http://158.160.62.149/` | Админ-панель |
| `http://158.160.62.149/health` | Health check |
| `http://158.160.62.149/docs` | Swagger API (если DEBUG=true) |
| `http://158.160.62.149/api/v1/employees/` | API сотрудников |
| `http://158.160.62.149/api/v1/attendance/` | API посещаемости |
| `http://158.160.62.149/api/v1/recognition/` | API распознавания |

---

## Troubleshooting

### Посмотреть ошибки

```bash
./deploy.sh logs app
./scripts/logs.sh errors
```

### Перезапустить всё

```bash
./deploy.sh restart
```

### Полная очистка и перезапуск

```bash
./deploy.sh stop
docker system prune -f
./deploy.sh start
```

### Проверить базу данных

```bash
docker exec -it sputnik-faceid-db psql -U sputnik -d sputnik_faceid
```

### Nginx 502 Bad Gateway

```bash
./scripts/logs.sh errors nginx
./deploy.sh status  # Проверить что app запущен
```

---

## Yandex Cloud CLI

### Полезные команды

```bash
# Список VM
yc compute instance list --folder-id b1gk0154cjiik7qgvokr

# Статус VM
yc compute instance get fhm301iskprq0ur79j8c

# Перезагрузить VM
yc compute instance restart fhm301iskprq0ur79j8c

# Serial console (логи загрузки)
yc compute instance get-serial-port-output fhm301iskprq0ur79j8c
```

---

## Важная информация

- Платформа: Yandex Cloud Compute
- База данных: PostgreSQL на порту 5432
- Провайдер распознавания: **dlib** (работает на серверах с ограниченной RAM)

---

## Контакты

При возникновении проблем обращаться к:
- **Татьяна** — Infrastructure, деплой
- **Мансур** — Recognition, ML
- **Ольга** — Database, миграции

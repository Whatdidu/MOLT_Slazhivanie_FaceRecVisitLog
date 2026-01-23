# Инструкция по деплою Sputnik FaceID

**Дата:** 2026-01-23

---

## Данные сервера

| Параметр | Значение |
|----------|----------|
| **IP** | `109.172.9.137` |
| **Домен** | `s1465303.smartape-vps.com` |
| **SSH** | `ssh root@109.172.9.137` |
| **Пароль** | См. `.env` файл в корне проекта (`SMARTAPE_PASSWORD`) |

---

## Шаг 1: Подключиться к серверу

```bash
ssh root@109.172.9.137
```

---

## Шаг 2: Клонировать проект

```bash
cd /opt
git clone https://github.com/Whatdidu/MOLT_Slazhivanie_FaceRecVisitLog.git sputnik-faceid
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
SPUTNIK_DB_PASSWORD=SputnikFace2024!Secure
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
| `http://109.172.9.137/` | Админ-панель |
| `http://109.172.9.137/health` | Health check |
| `http://109.172.9.137/docs` | Swagger API (если DEBUG=true) |
| `http://109.172.9.137/api/v1/employees/` | API сотрудников |
| `http://109.172.9.137/api/v1/attendance/` | API посещаемости |
| `http://109.172.9.137/api/v1/recognition/` | API распознавания |

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

## Важная информация

- Docker уже установлен на сервере (v28.2.2)
- PostgreSQL уже работает на порту 5433
- Используется **dlib** провайдер распознавания (работает на 2GB RAM)
- Сервер: 4 ядра CPU, 2GB RAM, 20GB SSD

---

## Контакты

При возникновении проблем обращаться к:
- **Татьяна** — Infrastructure, деплой
- **Мансур** — Recognition, ML
- **Ольга** — Database, миграции

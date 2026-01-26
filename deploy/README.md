# Sputnik FaceID - Руководство по деплою

## Быстрый старт

### 1. Подготовка сервера

```bash
# Установка Docker и Docker Compose
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Установка docker-compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. Клонирование проекта

```bash
git clone https://github.com/Whatdidu/MOLT_Slazhivanie_FaceRecVisitLog.git
cd MOLT_Slazhivanie_FaceRecVisitLog/deploy
```

### 3. Настройка окружения

```bash
cp .env.example .env
nano .env  # Заполните переменные (особенно SPUTNIK_DB_PASSWORD!)
```

### 4. Запуск

```bash
chmod +x deploy.sh
./deploy.sh start
```

## Структура директории

```
deploy/
├── docker-compose.prod.yml   # Production compose файл
├── deploy.sh                 # Главный скрипт деплоя
├── .env.example              # Пример переменных окружения
├── nginx/
│   ├── nginx.conf            # Главный конфиг nginx
│   ├── conf.d/
│   │   └── sputnik.conf      # Конфиг сайта
│   └── ssl/                  # SSL сертификаты (создать вручную)
├── scripts/
│   └── logs.sh               # Скрипт мониторинга логов
├── logrotate/
│   └── docker-logs           # Конфиг ротации логов
└── backups/                  # Бэкапы БД и логов
```

## Команды управления

### Основные операции

```bash
./deploy.sh start      # Запуск всех сервисов
./deploy.sh stop       # Остановка
./deploy.sh restart    # Перезапуск
./deploy.sh status     # Статус сервисов
./deploy.sh update     # Обновление из git + перезапуск
```

### Работа с БД

```bash
./deploy.sh backup     # Создать бэкап БД
./deploy.sh migrate    # Выполнить миграции
```

### Мониторинг логов

```bash
./deploy.sh logs           # Все логи
./deploy.sh logs app       # Логи приложения
./deploy.sh logs nginx     # Логи nginx
./deploy.sh logs db        # Логи PostgreSQL

# Расширенный мониторинг
./scripts/logs.sh health       # Проверка здоровья
./scripts/logs.sh errors       # Поиск ошибок
./scripts/logs.sh stats        # Статистика запросов
./scripts/logs.sh monitor      # Мониторинг в реальном времени
```

## Настройка SSL (HTTPS)

### Вариант 1: Let's Encrypt (рекомендуется)

```bash
./deploy.sh ssl_setup your-domain.com
```

Затем раскомментируйте SSL секцию в `nginx/conf.d/sputnik.conf`.

### Вариант 2: Свой сертификат

```bash
mkdir -p nginx/ssl
cp /path/to/fullchain.pem nginx/ssl/
cp /path/to/privkey.pem nginx/ssl/
```

## Порты

| Сервис | Внутренний | Внешний |
|--------|------------|---------|
| App    | 8000       | -       |
| Nginx  | 80, 443    | 80, 443 |
| DB     | 5432       | -       |

### Интеграция с IP камерой

Приложение подключается к камере по TCP (порт 8091) и слушает события.
При получении alarm-события делает RTSP снапшот и отправляет на распознавание.

Настройки камеры в `.env`:
```
CAMERA_ENABLED=true
CAMERA_IP=192.168.x.x
CAMERA_USER=admin
CAMERA_PASSWORD=xxx
CAMERA_RTSP_PORT=554
CAMERA_EVENT_PORT=8091
```

**Важно:** Камера и сервер должны быть в одной сети или иметь VPN/туннель.

## Endpoints

- `http://your-server/` — Админ-панель
- `http://your-server/health` — Health check
- `http://your-server/docs` — Swagger (только в DEBUG)
- `http://your-server/api/v1/...` — API

## Бэкапы

Бэкапы создаются в директории `backups/`:

```bash
./deploy.sh backup                # Ручной бэкап
ls -la backups/                   # Список бэкапов
```

### Автоматические бэкапы (cron)

```bash
# Добавить в crontab
0 3 * * * /path/to/deploy/deploy.sh backup
```

## Мониторинг

### Ротация логов

```bash
sudo cp logrotate/docker-logs /etc/logrotate.d/sputnik-faceid
sudo logrotate -f /etc/logrotate.d/sputnik-faceid  # Тест
```

### Проверка здоровья

```bash
./scripts/logs.sh health
```

## Troubleshooting

### Контейнер не запускается

```bash
./deploy.sh logs app           # Смотрим логи
docker-compose -f docker-compose.prod.yml logs --tail=50
```

### Ошибки подключения к БД

```bash
./deploy.sh logs db            # Логи PostgreSQL
docker exec -it sputnik-faceid-db psql -U sputnik -d sputnik_faceid
```

### Nginx 502 Bad Gateway

```bash
./scripts/logs.sh errors nginx
./deploy.sh status             # Проверить что app запущен
```

### Очистка и перезапуск

```bash
./deploy.sh stop
docker system prune -f
./deploy.sh start
```

#!/bin/bash

# Sputnik FaceID - Скрипт деплоя на VPS
# Использование: ./deploy.sh [команда]
# Команды: start, stop, restart, status, logs, backup, update

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Директория проекта
DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$DEPLOY_DIR")"
COMPOSE_FILE="$DEPLOY_DIR/docker-compose.prod.yml"

# Функции вывода
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Проверка наличия .env файла
check_env() {
    if [ ! -f "$DEPLOY_DIR/.env" ]; then
        log_warn ".env файл не найден в $DEPLOY_DIR"
        if [ -f "$PROJECT_DIR/.env.example" ]; then
            log_info "Копирую .env.example -> .env"
            cp "$PROJECT_DIR/.env.example" "$DEPLOY_DIR/.env"
            log_warn "Отредактируйте $DEPLOY_DIR/.env перед запуском!"
            exit 1
        fi
    fi
}

# Запуск сервисов
start() {
    log_info "Запуск Sputnik FaceID..."
    check_env
    cd "$DEPLOY_DIR"
    docker-compose -f "$COMPOSE_FILE" up -d --build
    log_success "Сервисы запущены!"
    status
}

# Остановка сервисов
stop() {
    log_info "Остановка Sputnik FaceID..."
    cd "$DEPLOY_DIR"
    docker-compose -f "$COMPOSE_FILE" down
    log_success "Сервисы остановлены"
}

# Перезапуск сервисов
restart() {
    log_info "Перезапуск Sputnik FaceID..."
    stop
    start
}

# Статус сервисов
status() {
    log_info "Статус сервисов:"
    cd "$DEPLOY_DIR"
    docker-compose -f "$COMPOSE_FILE" ps
    echo ""
    log_info "Health checks:"
    docker-compose -f "$COMPOSE_FILE" ps --format "table {{.Name}}\t{{.Status}}"
}

# Просмотр логов
logs() {
    local service="${1:-}"
    cd "$DEPLOY_DIR"
    if [ -n "$service" ]; then
        docker-compose -f "$COMPOSE_FILE" logs -f "$service"
    else
        docker-compose -f "$COMPOSE_FILE" logs -f
    fi
}

# Бэкап базы данных
backup() {
    local backup_name="sputnik_backup_$(date +%Y%m%d_%H%M%S).sql"
    log_info "Создание бэкапа БД: $backup_name"
    cd "$DEPLOY_DIR"

    docker-compose -f "$COMPOSE_FILE" exec -T db pg_dump \
        -U "${SPUTNIK_DB_USER:-sputnik}" \
        "${SPUTNIK_DB_NAME:-sputnik_faceid}" > "$DEPLOY_DIR/backups/$backup_name"

    log_success "Бэкап создан: $DEPLOY_DIR/backups/$backup_name"
}

# Обновление из git и перезапуск
update() {
    log_info "Обновление Sputnik FaceID..."
    cd "$PROJECT_DIR"

    log_info "Получение изменений из git..."
    git fetch origin
    git pull origin master

    log_info "Пересборка и перезапуск..."
    cd "$DEPLOY_DIR"
    docker-compose -f "$COMPOSE_FILE" up -d --build

    log_success "Обновление завершено!"
    status
}

# Выполнение миграций
migrate() {
    log_info "Запуск миграций БД..."
    cd "$DEPLOY_DIR"
    docker-compose -f "$COMPOSE_FILE" exec app alembic upgrade head
    log_success "Миграции выполнены"
}

# Создание SSL сертификатов (Let's Encrypt)
ssl_setup() {
    local domain="$1"
    if [ -z "$domain" ]; then
        log_error "Укажите домен: ./deploy.sh ssl_setup example.com"
        exit 1
    fi

    log_info "Настройка SSL для домена: $domain"
    mkdir -p "$DEPLOY_DIR/nginx/ssl"

    # Установка certbot если не установлен
    if ! command -v certbot &> /dev/null; then
        log_info "Установка certbot..."
        apt-get update && apt-get install -y certbot
    fi

    # Получение сертификата
    certbot certonly --standalone -d "$domain" \
        --non-interactive --agree-tos \
        --email admin@"$domain"

    # Копирование сертификатов
    cp /etc/letsencrypt/live/"$domain"/fullchain.pem "$DEPLOY_DIR/nginx/ssl/"
    cp /etc/letsencrypt/live/"$domain"/privkey.pem "$DEPLOY_DIR/nginx/ssl/"

    log_success "SSL сертификаты установлены"
    log_warn "Раскомментируйте SSL секцию в nginx/conf.d/sputnik.conf"
}

# Помощь
show_help() {
    echo "Sputnik FaceID - Скрипт деплоя"
    echo ""
    echo "Использование: ./deploy.sh [команда]"
    echo ""
    echo "Команды:"
    echo "  start       - Запустить все сервисы"
    echo "  stop        - Остановить все сервисы"
    echo "  restart     - Перезапустить все сервисы"
    echo "  status      - Показать статус сервисов"
    echo "  logs [svc]  - Показать логи (опционально: конкретный сервис)"
    echo "  backup      - Создать бэкап базы данных"
    echo "  update      - Обновить из git и перезапустить"
    echo "  migrate     - Выполнить миграции БД"
    echo "  ssl_setup   - Настроить SSL (Let's Encrypt)"
    echo "  help        - Показать эту справку"
    echo ""
    echo "Примеры:"
    echo "  ./deploy.sh start"
    echo "  ./deploy.sh logs app"
    echo "  ./deploy.sh ssl_setup example.com"
}

# Создание директории для бэкапов
mkdir -p "$DEPLOY_DIR/backups"

# Обработка команд
case "${1:-help}" in
    start)   start ;;
    stop)    stop ;;
    restart) restart ;;
    status)  status ;;
    logs)    logs "$2" ;;
    backup)  backup ;;
    update)  update ;;
    migrate) migrate ;;
    ssl_setup) ssl_setup "$2" ;;
    help|*)  show_help ;;
esac

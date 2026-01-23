#!/bin/bash

# Sputnik FaceID - Скрипт мониторинга и анализа логов
# Использование: ./logs.sh [команда] [опции]

set -e

DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$DEPLOY_DIR/docker-compose.prod.yml"

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Вывод
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Просмотр логов в реальном времени
follow_logs() {
    local service="${1:-}"
    cd "$DEPLOY_DIR"
    if [ -n "$service" ]; then
        docker-compose -f "$COMPOSE_FILE" logs -f --tail=100 "$service"
    else
        docker-compose -f "$COMPOSE_FILE" logs -f --tail=100
    fi
}

# Просмотр последних N строк логов
tail_logs() {
    local lines="${1:-100}"
    local service="${2:-}"
    cd "$DEPLOY_DIR"
    if [ -n "$service" ]; then
        docker-compose -f "$COMPOSE_FILE" logs --tail="$lines" "$service"
    else
        docker-compose -f "$COMPOSE_FILE" logs --tail="$lines"
    fi
}

# Поиск ошибок в логах
find_errors() {
    local service="${1:-app}"
    log_info "Поиск ошибок в логах сервиса: $service"
    cd "$DEPLOY_DIR"
    docker-compose -f "$COMPOSE_FILE" logs "$service" 2>&1 | \
        grep -iE "(error|exception|critical|fatal|traceback)" --color=always | \
        tail -50
}

# Статистика запросов (из nginx логов)
request_stats() {
    log_info "Статистика запросов за последний час:"
    cd "$DEPLOY_DIR"

    echo ""
    echo "=== Топ-10 URL по количеству запросов ==="
    docker-compose -f "$COMPOSE_FILE" logs nginx 2>&1 | \
        grep -oP '"request":"[^"]*"' | \
        cut -d'"' -f4 | \
        sort | uniq -c | sort -rn | head -10

    echo ""
    echo "=== Распределение HTTP статусов ==="
    docker-compose -f "$COMPOSE_FILE" logs nginx 2>&1 | \
        grep -oP '"status":\d+' | \
        cut -d':' -f2 | \
        sort | uniq -c | sort -rn

    echo ""
    echo "=== Медленные запросы (>1s) ==="
    docker-compose -f "$COMPOSE_FILE" logs nginx 2>&1 | \
        grep -oP '"request_time":[0-9.]+' | \
        awk -F':' '$2 > 1 {print $0}' | \
        head -10
}

# Статистика ошибок
error_stats() {
    log_info "Статистика ошибок:"
    cd "$DEPLOY_DIR"

    echo ""
    echo "=== Количество ошибок по типам ==="
    docker-compose -f "$COMPOSE_FILE" logs app 2>&1 | \
        grep -iE "(error|exception|warning)" | \
        grep -oP '\[(ERROR|WARNING|CRITICAL)\]' | \
        sort | uniq -c | sort -rn

    echo ""
    echo "=== HTTP ошибки (4xx, 5xx) ==="
    docker-compose -f "$COMPOSE_FILE" logs nginx 2>&1 | \
        grep -oP '"status":[45]\d\d' | \
        cut -d':' -f2 | \
        sort | uniq -c | sort -rn
}

# Мониторинг в реальном времени с фильтрацией
monitor() {
    local filter="${1:-}"
    log_info "Запуск мониторинга логов... (Ctrl+C для выхода)"
    cd "$DEPLOY_DIR"

    if [ -n "$filter" ]; then
        docker-compose -f "$COMPOSE_FILE" logs -f 2>&1 | \
            grep --line-buffered -iE "$filter" --color=always
    else
        docker-compose -f "$COMPOSE_FILE" logs -f 2>&1 | \
            grep --line-buffered -iE "(error|warn|info)" --color=always
    fi
}

# Экспорт логов в файл
export_logs() {
    local output_file="${1:-logs_export_$(date +%Y%m%d_%H%M%S).log}"
    log_info "Экспорт логов в файл: $output_file"
    cd "$DEPLOY_DIR"

    docker-compose -f "$COMPOSE_FILE" logs --no-color > "$DEPLOY_DIR/backups/$output_file"
    log_info "Логи сохранены: $DEPLOY_DIR/backups/$output_file"
}

# Очистка старых логов
cleanup_logs() {
    log_info "Очистка контейнерных логов..."
    cd "$DEPLOY_DIR"

    # Truncate docker logs
    docker-compose -f "$COMPOSE_FILE" ps -q | xargs -I {} sh -c \
        'truncate -s 0 $(docker inspect --format="{{.LogPath}}" {})'

    log_info "Логи очищены"
}

# Проверка здоровья сервисов
health_check() {
    log_info "Проверка здоровья сервисов:"
    cd "$DEPLOY_DIR"

    echo ""
    echo "=== Статус контейнеров ==="
    docker-compose -f "$COMPOSE_FILE" ps

    echo ""
    echo "=== Health endpoints ==="
    echo -n "App: "
    curl -s http://localhost:8000/health | jq -r '.status' 2>/dev/null || echo "недоступен"

    echo -n "Nginx: "
    curl -s -o /dev/null -w "%{http_code}" http://localhost/health 2>/dev/null || echo "недоступен"

    echo ""
    echo ""
    echo "=== Использование ресурсов ==="
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
}

# Помощь
show_help() {
    echo "Sputnik FaceID - Мониторинг логов"
    echo ""
    echo "Использование: ./logs.sh [команда] [опции]"
    echo ""
    echo "Команды:"
    echo "  follow [service]    - Логи в реальном времени"
    echo "  tail [N] [service]  - Последние N строк логов"
    echo "  errors [service]    - Поиск ошибок"
    echo "  stats               - Статистика запросов (nginx)"
    echo "  error-stats         - Статистика ошибок"
    echo "  monitor [filter]    - Мониторинг с фильтром"
    echo "  export [filename]   - Экспорт логов в файл"
    echo "  cleanup             - Очистка старых логов"
    echo "  health              - Проверка здоровья сервисов"
    echo "  help                - Эта справка"
    echo ""
    echo "Примеры:"
    echo "  ./logs.sh follow app"
    echo "  ./logs.sh tail 200 nginx"
    echo "  ./logs.sh monitor 'error|warning'"
    echo "  ./logs.sh errors"
}

# Создание директории для бэкапов
mkdir -p "$DEPLOY_DIR/backups"

# Обработка команд
case "${1:-help}" in
    follow)      follow_logs "$2" ;;
    tail)        tail_logs "$2" "$3" ;;
    errors)      find_errors "$2" ;;
    stats)       request_stats ;;
    error-stats) error_stats ;;
    monitor)     monitor "$2" ;;
    export)      export_logs "$2" ;;
    cleanup)     cleanup_logs ;;
    health)      health_check ;;
    help|*)      show_help ;;
esac

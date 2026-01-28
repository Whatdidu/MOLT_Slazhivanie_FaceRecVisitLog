# Claude Code - Инструкции для проекта Sputnik FaceID

## Подключение к серверу

**Сервер:** Yandex Cloud VPS
**IP:** 158.160.62.149
**Пользователь:** yc-user
**SSH ключ:** ~/.ssh/id_ed25519
**Путь к проекту:** /opt/sputnik-faceid

### SSH подключение
```bash
ssh -i ~/.ssh/id_ed25519 yc-user@158.160.62.149
```

### Деплой (pull + rebuild + restart)
```bash
ssh -i ~/.ssh/id_ed25519 yc-user@158.160.62.149 "cd /opt/sputnik-faceid && sudo git pull && sudo docker compose down && sudo docker compose up -d --build"
```

### Просмотр логов
```bash
ssh -i ~/.ssh/id_ed25519 yc-user@158.160.62.149 "sudo docker compose -f /opt/sputnik-faceid/docker-compose.yml logs --tail=50 app"
```

### Выполнение команды в контейнере
```bash
ssh -i ~/.ssh/id_ed25519 yc-user@158.160.62.149 "sudo docker exec sputnik-faceid-app <команда>"
```

## Порты и сервисы

| Сервис | Порт | Описание |
|--------|------|----------|
| FastAPI | 8000 | Основное приложение |
| FTP | 2121 | Приём снапшотов с камеры |
| FTP Passive | 60000-60010 | Пассивный режим FTP |
| PostgreSQL | 5434 | База данных (внешний порт) |

## URL приложения

- **Админка:** http://158.160.62.149:8000/admin/
- **API Docs:** http://158.160.62.149:8000/docs (только в debug режиме)
- **Снапшоты:** http://158.160.62.149:8000/snapshots/

## Камера

**Модель:** YCX YM5A1
**IP камеры:** зависит от сети (192.168.0.117 или 192.168.31.179)
**Веб-интерфейс:** http://<IP камеры>/
**Логин:** admin
**Пароль:** 123456

### FTP настройки (в веб-интерфейсе камеры)
- **Сервер:** 158.160.62.149
- **Порт:** 2121
- **Логин:** camera
- **Пароль:** camera123
- **Режим:** Passive

**FTP загрузка:** Камера отправляет снапшоты на сервер при детекции движения

## База данных

**Контейнер:** sputnik-faceid-db
**Подключение изнутри docker-сети:** db:5432
**Подключение извне:** 158.160.62.149:5434

### Полезные SQL команды
```bash
# Проверить эмбеддинги
ssh -i ~/.ssh/id_ed25519 yc-user@158.160.62.149 "sudo docker exec sputnik-faceid-app python -c \"
import asyncio
from app.db import get_session
from sqlalchemy import text
async def check():
    async with get_session() as db:
        result = await db.execute(text('SELECT COUNT(*) FROM embeddings'))
        print(f'Embeddings: {result.scalar()}')
asyncio.run(check())
\""

# Удалить все эмбеддинги (для пересоздания)
ssh -i ~/.ssh/id_ed25519 yc-user@158.160.62.149 "sudo docker exec sputnik-faceid-app python -c \"
import asyncio
from app.db import get_session
from sqlalchemy import text
async def delete():
    async with get_session() as db:
        await db.execute(text('DELETE FROM embeddings'))
        await db.commit()
        print('All embeddings deleted')
asyncio.run(delete())
\""
```

## Снапшоты с камеры

### Посмотреть количество снапшотов
```bash
ssh -i ~/.ssh/id_ed25519 yc-user@158.160.62.149 "sudo docker exec sputnik-faceid-app find /app/snapshots -name '*.jpg' | wc -l"
```

### Удалить все снапшоты
```bash
ssh -i ~/.ssh/id_ed25519 yc-user@158.160.62.149 "sudo docker exec sputnik-faceid-app find /app/snapshots -name '*.jpg' -delete"
```

### Список последних снапшотов
```bash
ssh -i ~/.ssh/id_ed25519 yc-user@158.160.62.149 "sudo docker exec sputnik-faceid-app find /app/snapshots -name '*.jpg' | sort -V | tail -10"
```

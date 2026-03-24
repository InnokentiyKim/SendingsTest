# Тестовое задание "Sendings" — Импорт и отправка рассылок

Django-проект для импорта email-рассылок из XLSX-файла с последующей отправкой писем.

[![Coverage Status](https://img.shields.io/badge/coverage-98%25-success)](https://github.com/InnokentiyKim/)
[![Django](https://img.shields.io/badge/Django-4.2+-092E20?logo=django)](https://www.djangoproject.com/)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker)](https://www.docker.com/)
[![Redis](https://img.shields.io/badge/Redis-required-DC382D?logo=redis)](https://redis.io/)
[![Celery](https://img.shields.io/badge/Celery-required-389E0D?logo=celery)](https://docs.celeryproject.org/)

## Требования

- Python 3.10+
- Django 4.2+
- Docker (опционально)
- Redis (для Celery, при локальном запуске)

## Установка и запуск

**Клонируйте репозиторий**
```bash
git clone <repository-url>
cd <project-directory>
```

### Вариант 1: Через Docker (рекомендуется)

```bash
# Собрать и запустить контейнеры
docker-compose up -d --build     

# Запустить команду импорта внутри контейнера
docker exec -it myapp python manage.py import_sendings path/to/file.xlsx --batch-size 100

# Можно использовать тестовый файл в data/test_sendings.xlsx
docker exec -it myapp python manage.py import_sendings data/test_sendings.xlsx

# Запуск тестов внутри контейнера
docker exec -it myapp pytest

# Просмотр логов внутри контейнера (проверка рассылок)
docker logs myapp
````


### Вариант 2: Локально

Для локального запуска необходимо установить и запустить брокер (Redis или RabbitMQ) для работы Celery. Установить URL брокера можно в .env файле (смотреть пример в .env.template)

```bash
# Создать виртуальное окружение и активировать
python -m venv venv
source venv/bin/activate  # macOS / Linux

# Установить зависимости
pip install -r requirements.txt

# Применить миграции
python manage.py migrate

# Запустить Celery (в отдельном терминале)
celery -A sendings worker -l info

# Импортировать рассылки из XLSX-файла
python manage.py import_sendings path/to/file.xlsx --batch-size 1000

# Можно использовать тестовый файл в data/test_sendings.xlsx
python manage.py import_sendings data/test_sendings.xlsx

# Запустить тесты
pytest
# Запуск тестов с покрытием
pytest --cov=sendings_app --cov-report=json:coverage.json 
```

## Формат XLSX-файла

Первая строка — заголовки колонок:

| Колонка       | Описание                                          |
|---------------|---------------------------------------------------|
| `external_id` | Уникальный идентификатор записи во внешней системе |
| `user_id`     | Идентификатор пользователя                        |
| `email`       | Email получателя                                  |
| `subject`     | Тема письма                                       |
| `message`     | Текст письма                                      |

## Вывод результата

После завершения команда выводит статистику:

- Количество обработанных строк
- Количество созданных записей
- Количество пропущенных записей (дубликаты по `external_id`)
- Количество ошибочных строк (невалидные данные)
- Количество проигнорированных строк (при наличии дубликатов внутри файла)

## Примечания

- Отправка письма реализована как запись в лог с задержкой `sleep(randint(5, 20))`.
- Дедупликация по `external_id` — повторный импорт того же файла не создаёт дубликатов.
- При наличии дубликатов внутри файла — сохраняется только первая запись, остальные игнорируются.
- Невалидные email-адреса фиксируются как ошибки и пропускаются.

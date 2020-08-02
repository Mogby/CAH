# Cards Against Humanity

Веб версия Cards Against Humanity.

## Требования

Понадобятся docker и docker-compose

## Запуск

Клонируем репозиторий, переходим в его корень, выполняем

```shell
docker-compose up --build -d
```

После этого докер должен запустить контейнеры с PostgreSQL и Django.

Чтобы начать играть открываем в бразуере `website/index.html`.

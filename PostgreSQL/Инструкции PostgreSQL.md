# Инструкции PostgreSQL

## Статьи
[Про файл postrgesql.conf](https://edu.postgrespro.ru/dba1/dba1_03_tools_configuration.html)

[PGTune](https://pgtune.leopard.in.ua/#/)

[Рекомендации 1С](https://its.1c.ru/db/metod8dev/content/5866/hdoc)

[Держи данные в тепле, транзакции в холоде, а VACUUM в голоде](https://infostart.ru/public/1191667/)

[Настройка параметров PostgreSQL для оптимизации производительности](https://habr.com/ru/post/458952/)

### Настройки

#### Перезагрузка настроек
```sh
SELECT pg_reload_conf();
```

#### Чтени настроек запросом
```sh
SELECT name, setting
FROM pg_settings;
```

#### Установка настройки
```sh
ALTER SYSTEM SET autovacuum_vacuum_cost_limit TO 400;
```

### Служебные команды

#### Завершение процесса
```sh
SELECT *, pg_terminate_backend(procpid)
FROM pg_stat_activity
WHERE usename='username';
```

#### Размер базы
```sh
SELECT pg_size_pretty(pg_database_size('db_name'));
```

#### Бэкап
```sh
pg_dump --help
pg_dump -U user_name db_name | gzip > file_name.gz
pg_dump -U user_name db_name > file_name 
```

#### Восстановление
```sh
psql -U user_name -d db_name -1 -f file_name
```

#### Цепочка команд для бэкапа и восстановления
```sh
dropdb -U postgres --if-exists db_name && createdb -U postgres -O postgres db_name && pg_dump -U postgres db_backup_name > file_name && psql -U postgres -d db_name -1 -f file_name && rm file_name 
```

#### Описание скрипта для бэкапа и восстановления базы данных
Скрипт находится в домашней папке пользователя admin

Подключение:
```sh
ssh admin@srv-pgsql-test1 
```
Пример вызова:
```sh
./backup_and_restore db_name db_backup_name
./backup_and_restore UAS_BACKUP UAS 
```
Где:
```sh
db_name - база в которую нам нужно восстановить бэкап
db_backup_name - база из которой мы делаем бэкап
После завершения работы скрипта файл бэкапа удаляется
```
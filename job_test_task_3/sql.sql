-- product_directory
CCREATE TABLE "product_directory" ("name_store" VARCHAR(20),"nomenclature" VARCHAR(10) PRIMARY KEY,"print" VARCHAR(10),"barcode" VARCHAR(10));
INSERT INTO "product_directory" ("name_store","nomenclature","print","barcode") VALUES 
 ('Магазин 1','mag_11','art_1','Code_1'), 
 ('Магазин 2','mag_21','art_1','Code_2'), 
 ('Магазин 1','mag_12','art_2','Code_1'), 
 ('Магазин 3','mag_31','art_2','Code_2'), 
 ('Магазин 2','mag_22','art_1','Code_1');
 
-- orders_directory
CREATE TABLE "orders_directory" ("date" VARCHAR(10),"nomenclature" VARCHAR(10) REFERENCES product_directory(nomenclature),"orders_type" VARCHAR(10),"price" SMALLINT,"quantity_product" SMALLINT);
INSERT INTO "orders_directory" ("date","nomenclature","orders_type","price","quantity_product") VALUES 
 ('2024-10-17','mag_11',' Тип 1','150','2'), 
 ('2024-10-17','mag_22',' Тип 1','120','7'), 
 ('2024-10-16','mag_31',' Тип 2','300','1'), 
 ('2024-10-15','mag_21',' Тип 1','175','2'), 
 ('2024-10-15','mag_11',' Тип 2','150','1');

-- print_directory
CREATE TABLE "print_directory" ("print" VARCHAR(10) primary key,"name_print_1" VARCHAR(30),"name_print_2" VARCHAR(30),"price" SMALLINT,"quantity_product" SMALLINT);
INSERT INTO "print_directory" ("print","name_print_1","name_print_2","price","quantity_product") VALUES 
 ('art_1','Цветочек','Цветочек в поле','150','2'), 
 ('art_2','Белое облачко','','120','7'), 
 ('art_3','Машина','Спорткар','300','1'), 
 ('art_4','Тигр','Тигр в цветочках','175','2');

-- stocks_directory
CREATE TABLE "stocks_directory" ("date" VARCHAR(10),"nomenclature" VARCHAR(10) REFERENCES product_directory(nomenclature),"warehouse" VARCHAR(20),"value_stocks" SMALLINT);
INSERT INTO "stocks_directory" ("date","nomenclature","warehouse","value_stocks") VALUES 
 ('2024-10-18','mag_11','Склад 1','10'), 
 ('2024-10-18','mag_12','Склад 1','5'), 
 ('2024-10-18','mag_21','Склад 2','7'), 
 ('2024-10-17','mag_31','Склад 2','20'), 
 ('2024-10-17','mag_12','Склад 1','12'), 
 ('2024-10-17','mag_22','Склад 2','7');
-- Задание 1:
-- Выведите все заказы Магазина 1 с расчетом выручки (Цена единицы товара * количество заказанного товара)
-- Необходимо вывести:
-- -Название магазина;
-- -Номенклатура;
-- -Дата заказа;
-- -Выручка.

SELECT pd.name_store, pd.nomenclature, od.date, od.price * od.quantity_product AS revenue
FROM product_directory AS pd
RIGHT JOIN orders_directory AS od ON pd.nomenclature = od.nomenclature
WHERE pd.name_store = "Магазин 1"

-- Задание 2:
-- Выведите информацию о принтах, которые не используются в product_dictionary
-- Необходимо вывести всю информацию о принтах из print_directory 

SELECT prd.print, prd.name_print_1, prd.name_print_2, prd.price, prd.quantity_product
FrOM print_directory as prd
WHERE prd.print NOT in (SELECT product_directory.print FROM product_directory)

-- Задание 3:
-- Выведите все номенклатуры, у которых есть оба названия принта
-- Необходимо вывести:
-- -Номенклатура;
-- -Артикул принта;
-- -Название принта.

SELECT pd.nomenclature, pd.print, prd.name_print_1, prd.name_print_2
FrOM product_directory as pd
left JOIN print_directory as prd on pd.print = prd.print
WHERE (NULLIF(prd.name_print_2, '') is NOT NULL) and (NULLIF(prd.name_print_2, '') is not NULL)

-- Задание 4:
-- Выведите номенклатуры, у которых есть остатки на «Складе 1» на 2024-10-18.
-- Необходимо вывести:
-- -Название магазина;
-- -Номенклатуру;
-- -Название склада;
-- -Количество остатков.

SELECT pd.name_store, sd.nomenclature, sd.warehouse, sd.value_stocks
FROM stocks_directory AS sd 
LEFT JOIN product_directory AS pd ON pd.nomenclature = sd.nomenclature
GROUP BY sd.nomenclature
HAVING (sd.date <= DATE('2024-10-18')) AND (sd.value_stocks > 0)

-- Задание 5:
-- Выведите количество заказов за каждую дату (где они есть), выручку, прибыль с учетом налога для магазинов 5% с выручки для товаров со штрихкодом Code_1.
-- Необходимо вывести:
-- -Штрихкод товара;
-- -Дата;
-- -Количество заказов;
-- -Выручка;
-- -Прибыль с учетом налога.

SELECT pd.barcode, od.date, od.quantity_product, (od.price * od.quantity_product) as profit,
CASE WHEN barcode = 'Code_1' THEN od.price * od.quantity_product * 0.95 
ELSE od.price * od.quantity_product END
AS revenue
FROM orders_directory AS od
LEFT JOIN product_directory AS pd ON pd.nomenclature = od.nomenclature

-- Задание 6:
-- Выведите самый продаваемый принт с количеством продаж за весь известный период.
-- Необходимо вывести:
-- -Артикул принта;
-- -Название принта №1;
-- -Количество продаж.
SELECT prd.print, prd.name_print_1, Count(*) as "sold_count"
FROM print_directory as prd
INNER JOIN product_directory as pd ON prd.print = pd.print
INNER JOIN orders_directory as od on pd.nomenclature = od.nomenclature
GROUP BY prd.print
ORDER BY sold_count
LIMIT 1

-- 2.	Создайте триггер, который будет логировать DDL действия пользователя (ALTER, CREATE, DROP…)
-- Таблица логов
CREATE TABLE IF NOT EXISTS ddl_log (
    id SERIAL PRIMARY KEY,
    command_tag TEXT,
    object_type TEXT,
    schema_name TEXT,
    object_name TEXT,
    statement TEXT,
    username TEXT,
    log_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE OR REPLACE FUNCTION log_ddl_commands()
RETURNS EVENT_TRIGGER AS $$
DECLARE
    obj RECORD;
BEGIN
    FOR obj IN
        SELECT * FROM pg_event_trigger_ddl_commands()
    LOOP
        INSERT INTO ddl_log (
            command_tag,
            object_type,
            schema_name,
            object_name,
            statement,
            username
        )
        VALUES (
            obj.command_tag,
            obj.object_type,
            obj.schema_name,
            obj.object_name,
            current_query(),
            session_user
        );
    END LOOP;
END;
$$ LANGUAGE plpgsql;

CREATE EVENT TRIGGER log_ddl_trigger
ON ddl_command_end
EXECUTE FUNCTION log_ddl_commands();

-- 3.	Создайте триггер, который будет логировать изменения (UPDATE) в таблице product_directory

-- Таблица логов
CREATE TABLE product_directory_log (
    id SERIAL PRIMARY KEY,
    name_store TEXT,
    nomenclature TEXT,
    print TEXT,
    barcode TEXT,
    operation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    operation_type TEXT,
    -- Поля для старых значений
    old_name_store TEXT,
    old_nomenclature TEXT,
    old_print TEXT,
    old_barcode TEXT
);

-- Функция триггера
CREATE OR REPLACE FUNCTION log_product_directory_update()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO product_directory_log (
        name_store,
        Nomenclature,
        print,
        barcode,
        operation_type,
        old_name_store,
        old_nomenclature,
        old_print,
        old_barcode
    )
    VALUES (
        NEW.name_store,
        NEW.nomenclature,
        NEW.print,
        NEW.barcode,
        'UPDATE',
        OLD.name_store,
        OLD.Nomenclature,
        OLD.print,
        OLD.barcode
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Создание триггера
CREATE TRIGGER trg_log_update_product_directory
AFTER UPDATE ON product_directory
FOR EACH ROW
EXECUTE FUNCTION log_product_directory_update();

-- тест
UPDATE product_directory
SET barcode = 'Code_123'
WHERE name_store = 'Магазин 1';

SELECT * FROM product_directory_log ORDER BY operation_time;
-- 4.	Создайте новую базу данных company_db и двух пользователей:
-- - admin_user с полными правами
-- - read_user с правами только на чтение

-- Требования:
-- - Создать базу данных company_db
-- - Создать схему business в company_db
-- - Создать пользователя admin_user с полными правами на business
-- - Создать пользователя read_user, который может только читать данные из схемы business
-- - Проверить права пользователей

-- - Создать базу данных company_db
CREATE DATABASE company_db;

-- - Создать схему business в company_db
CREATE SCHEMA business;

-- - Создать пользователя admin_user с полными правами на business
CREATE USER admin_user WITH PASSWORD 'admin_user';
-- для уже созданных таблиц
GRANT ALL ON ALL TABLES IN SCHEMA business TO admin_user;
-- для будущих таблиц
ALTER DEFAULT PRIVILEGES IN SCHEMA business GRANT ALL ON TABLES TO admin_user;

-- - Создать пользователя read_user, который может только читать данные из схемы business
CREATE USER read_user WITH PASSWORD 'read_user';
GRANT USAGE ON SCHEMA business TO read_user;
-- для уже созданных таблиц
GRANT SELECT ON ALL TABLES IN SCHEMA business TO read_user;
-- для будущих таблиц
ALTER DEFAULT PRIVILEGES IN SCHEMA business GRANT SELECT ON TABLES TO read_user;

-- - Проверить права пользователей
-- psql -U admin_user -d company_db
SELECT has_schema_privilege('admin_user', 'business', 'USAGE');
-- psql -U read_user -d company_db
SELECT has_schema_privilege('read_user', 'business', 'USAGE');
SELECT has_table_privilege('read_user', 'some_table', 'SELECT');

-- 5.	Есть таблица orders:
-- CREATE TABLE orders (
--     order_id SERIAL PRIMARY KEY,
--     customer_id INT NOT NULL,
--     product_id INT NOT NULL,
--     quantity INT NOT NULL CHECK (quantity > 0),
--     order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );
-- В таблице 10 миллионов записей, и запрос на поиск заказов за последний месяц выполняется медленно:

-- SELECT * FROM orders WHERE order_date >= CURRENT_DATE - INTERVAL'1 month';
-- Вопросы:

-- - Какие индексы могут улучшить выполнение запроса?
-- - Как можно проверить, что индекс действительно улучшил производительность?
-- - Как влияет VACUUM ANALYZE на производительность этого запроса?
-- - Какими ещё способами можно оптимизировать выполнение запросов к этой таблице?

-- - Какие индексы могут улучшить выполнение запроса?
-- Индекс на PRIMARY KEY в PostrgreSQL создается по умолчанию. Определенно скорость улучшить индексирование order_date через B-tree. Точность типа timestamp в 1 микросекунду, позволяет допустить, что order_date содержит лишь уникальные значения, а значит может быть захеширован, однако в данном случае это невозможно потому в запросе используются интервалы. Может подойти BRIN, потому что значения по order_date выстраиваются во временную последовательность.

-- - Как можно проверить, что индекс действительно улучшил производительность?
-- Запустить
EXPLAIN ANALYZE SELECT * FROM orders WHERE order_date >= CURRENT_DATE - INTERVAL '1 month';
-- Создать индекс и вновь выполнить запрос
СREATE INDEX idx_orders_order_date ON orders (order_date);
EXPLAIN ANALYZE SELECT * FROM orders WHERE order_date >= CURRENT_DATE - INTERVAL '1 month';

-- - Как влияет VACUUM ANALYZE на производительность этого запроса?
-- VACUUM вероятно сократит количество записей в таблице, избавившись "мертвых" записей (удалены в базе данных, но физически занимают место. То есть по аналогии "находятся в корзине")

-- - Какими ещё способами можно оптимизировать выполнение запросов к этой таблице?
-- Можно выделять из таблицы с некой периодичностью записи, пренадлежащие определенному интервалу(например помесячно или последние 3 месяца). Это значительно уменьшит количество записей, а значит запросы будут выполняться быстрее. Можно сделать индексы на customer_id, product_id или сразу на часто используемые связки столбцов

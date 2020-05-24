# sql-aggregator
sql-aggregator (MultiDB) позволяет в одном запросе манипулировать данными из различных баз данных.
Например, производить JOIN таблицы из MySQL на таблицу из PostgreSQL

# Версия 0.1 (в разработке)
Инициализирующая версия

В данной версии реализована возможность производить INNER JOIN между таблицами из различных источников

Поддерживаются следующие источники: PostgreSQL, MySQL, SQLite

# Нерабочие конструкции
1) `<boolean value expression> + <boolean value expression>`. `<boolean value expression>` необходимо указать в скобках
2) Не поддерживается объявление одной и той же таблицы в запросе более чем 1 раз, в том числе и self join
3) Колонки необходимо называть ссылаясь на таблицу `select a.b from a`
4) Сочетания логических и арифметических операций `not(-(not(-column))) -> column`

# Полезные ссылки
* [SQL стандарт 1999](http://web.cecs.pdx.edu/~len/sql1999.pdf)
* [Документация PostgreSQL](https://www.postgresql.org/docs/)
* [Документация MySQL](https://dev.mysql.com/doc/)
* [Документация SQLite](https://www.sqlite.org/docs.html)

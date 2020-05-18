Изменения грамматики
====================

`<table_reference>` (Стр. 232)
------------------------------
Причина изменения - левая рекурсия и невозможность свести к правой (для `qualified join`)

Раньше:
```
<table reference> ::=
         <table primary>
       | <joined table>
       
<table primary> ::=
         <table or query name> [ [ AS ] <correlation name> ]
       | <derived table> [ AS ] <correlation name>
       | <left paren> <joined table> <right paren>

<table or query name> ::=
         <table name>
       | <query name>

<joined table> ::=
         <cross join>
       | <qualified join>

<cross join> ::=
         <table reference> CROSS JOIN <table primary>
         
<qualified join> ::=
         <table reference> [ <join type> ] JOIN <table reference> <join specification>

<join specification> ::=
         <join condition>
       | <named_columns_join>
       
<join condition> ::= ON <search condition>

<join type> ::=
         INNER
       | <outer join type> [ OUTER ]

<outer join type> ::=
         LEFT
       | RIGHT
       | FULL
```
Новая грамматика:
```
<table reference> ::= 
         <join factor> [ { <joined table> }... ]

<joined table> ::=
         <cross join>
       | <qualified join>

<cross join> ::= CROSS JOIN <join factor>

<qualified join> ::=
         [ <join type> ] JOIN <join factor> <join specification>

<join specification> ::=
         <join condition>
       | <named_columns_join>
       
<join condition> ::= ON <search condition>

<join type> ::=
         INNER
       | <outer join type> [ OUTER ]

<outer join type> ::=
         LEFT
       | RIGHT
       | FULL

<join factor> ::=
         <table primary>
       | <left paren> <table reference> <right paren>
```

`comparison_predicate` (Стр. 287)
------------------------------
Причина изменения - левая рекурсия (для `comparison predicate`)

Раньше:
```
<comparison predicate> ::=
         <row value expression> <comp op> <row value expression>

<comp op> ::=
         <equals operator>
       | <not equals operator>
       | <less than operator>
       | <greater than operator>
       | <less than or equals operator>
       | <greater than or equals operator>
```
Новая грамматика:
```
<comparison predicate> ::=
         <operand comparison> <comp op> <operand comparison>

<operand comparison> ::=
         <parenthesized value expression>
       | <not boolean value expression>

<not boolean value expression> ::=
         <numeric value expression>
       | <string value expression>
       | <datetime value expression>

<comp op> ::=
         <equals operator>
       | <not equals operator>
       | <less than operator>
       | <greater than operator>
       | <less than or equals operator>
       | <greater than or equals operator>
```
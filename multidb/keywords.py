from itertools import chain

# Ключевые слова взяты из стандарта SQL 1999

NON_RESERVED_WORDS = {
    'ABS', 'ADA', 'ASENSITIVE', 'ASSIGNMENT', 'ASYMMETRIC', 'ATOMIC', 'AVG',

    'BETWEEN', 'BIT_LENGTH', 'BITVAR',

    'C', 'CALLED', 'CARDINALITY', 'CATALOG_NAME', 'CHAIN', 'CHAR_LENGTH',
    'CHARACTER_LENGTH', 'CHARACTER_SET_CATALOG', 'CHARACTER_SET_NAME',
    'CHARACTER_SET_SCHEMA', 'CHECKED', 'CLASS_ORIGIN', 'COALESCE', 'COBOL',
    'COLLATION_CATALOG', 'COLLATION_NAME', 'COLLATION_SCHEMA', 'COLUMN_NAME',
    'COMMAND_FUNCTION', 'COMMAND_FUNCTION_CODE', 'COMMITTED', 'CONDITION_NUMBER',
    'CONNECTION_NAME', 'CONSTRAINT_CATALOG', 'CONSTRAINT_NAME', 'CONSTRAINT_SCHEMA',
    'CONTAINS', 'CONVERT', 'COUNT', 'CURSOR_NAME',

    'DATETIME_INTERVAL_CODE', 'DATETIME_INTERVAL_PRECISION', 'DEFINED', 'DEFINER',
    'DISPATCH', 'DYNAMIC_FUNCTION', 'DYNAMIC_FUNCTION_CODE',

    'EXISTING', 'EXISTS', 'EXTRACT',

    'FINAL', 'FORTRAN',

    'G', 'GENERATED', 'GRANTED',

    'HIERARCHY', 'HOLD',

    'IMPLEMENTATION', 'INFIX', 'INSENSITIVE', 'INSTANCE', 'INSTANTIABLE', 'INVOKER',

    'K', 'KEY_MEMBER', 'KEY_TYPE',

    'LENGTH', 'LOWER',

    'M', 'MAX', 'MIN', 'MESSAGE_LENGTH', 'MESSAGE_OCTET_LENGTH', 'MESSAGE_TEXT',
    'METHOD', 'MOD', 'MORE', 'MUMPS',
    'NAME', 'NULLABLE', 'NUMBER', 'NULLIF',

    'OCTET_LENGTH', 'OPTIONS', 'OVERLAPS', 'OVERLAY', 'OVERRIDING',

    'PASCAL', 'PARAMETER_MODE', 'PARAMETER_NAME', 'PARAMETER_ORDINAL_POSITION',
    'PARAMETER_SPECIFIC_CATALOG', 'PARAMETER_SPECIFIC_NAME',
    'PARAMETER_SPECIFIC_SCHEMA', 'PLI', 'POSITION',

    'REPEATABLE', 'RETURNED_LENGTH', 'RETURNED_OCTET_LENGTH', 'RETURNED_SQLSTATE',
    'ROUTINE_CATALOG', 'ROUTINE_NAME', 'ROUTINE_SCHEMA', 'ROW_COUNT',

    'SCALE', 'SCHEMA_NAME', 'SECURITY', 'SELF', 'SENSITIVE', 'SERIALIZABLE', 'SERVER_NAME',
    'SIMPLE', 'SOURCE', 'SPECIFIC_NAME', 'SIMILAR', 'SUBLIST', 'SUBSTRING', 'SUM', 'STYLE',
    'SUBCLASS_ORIGIN', 'SYMMETRIC', 'SYSTEM',

    'TABLE_NAME', 'TRANSACTIONS_COMMITTED', 'TRANSACTIONS_ROLLED_BACK',
    'TRANSACTION_ACTIVE', 'TRANSFORM', 'TRANSFORMS', 'TRANSLATE', 'TRIGGER_CATALOG',
    'TRIGGER_SCHEMA', 'TRIGGER_NAME', 'TRIM', 'TYPE',

    'UNCOMMITTED', 'UNNAMED', 'UPPER', 'USER_DEFINED_TYPE_CATALOG',
    'USER_DEFINED_TYPE_NAME', 'USER_DEFINED_TYPE_SCHEMA',
}

RESERVED_WORDS = {
    'ABSOLUTE', 'ACTION', 'ADD', 'ADMIN', 'AFTER', 'AGGREGATE',
    'ALIAS', 'ALL', 'ALLOCATE', 'ALTER', 'AND', 'ANY', 'ARE', 'ARRAY', 'AS', 'ASC',
    'ASSERTION', 'AT', 'AUTHORIZATION',

    'BEFORE', 'BEGIN', 'BINARY', 'BIT', 'BLOB', 'BOOLEAN', 'BOTH', 'BREADTH', 'BY',

    'CALL', 'CASCADE', 'CASCADED', 'CASE', 'CAST', 'CATALOG', 'CHAR', 'CHARACTER',
    'CHECK', 'CLASS', 'CLOB', 'CLOSE', 'COLLATE', 'COLLATION', 'COLUMN', 'COMMIT',
    'COMPLETION', 'CONNECT', 'CONNECTION', 'CONSTRAINT', 'CONSTRAINTS',
    'CONSTRUCTOR', 'CONTINUE', 'CORRESPONDING', 'CREATE', 'CROSS', 'CUBE', 'CURRENT',
    'CURRENT_DATE', 'CURRENT_PATH', 'CURRENT_ROLE', 'CURRENT_TIME', 'CURRENT_TIMESTAMP',
    'CURRENT_USER', 'CURSOR', 'CYCLE',

    'DATA', 'DATE', 'DAY', 'DEALLOCATE', 'DEC', 'DECIMAL', 'DECLARE', 'DEFAULT',
    'DEFERRABLE', 'DEFERRED', 'DELETE', 'DEPTH', 'DEREF', 'DESC', 'DESCRIBE', 'DESCRIPTOR',
    'DESTROY', 'DESTRUCTOR', 'DETERMINISTIC', 'DICTIONARY', 'DIAGNOSTICS', 'DISCONNECT',
    'DISTINCT', 'DOMAIN', 'DOUBLE', 'DROP', 'DYNAMIC',

    'EACH', 'ELSE', 'END', 'END-EXEC', 'EQUALS', 'ESCAPE', 'EVERY', 'EXCEPT',
    'EXCEPTION', 'EXEC', 'EXECUTE', 'EXTERNAL',

    'FALSE', 'FETCH', 'FIRST', 'FLOAT', 'FOR', 'FOREIGN', 'FOUND', 'FROM', 'FREE', 'FULL',
    'FUNCTION',

    'GENERAL', 'GET', 'GLOBAL', 'GO', 'GOTO', 'GRANT', 'GROUP', 'GROUPING',

    'HAVING', 'HOST', 'HOUR',

    'IDENTITY', 'IGNORE', 'IMMEDIATE', 'IN', 'INDICATOR', 'INITIALIZE', 'INITIALLY',
    'INNER', 'INOUT', 'INPUT', 'INSERT', 'INT', 'INTEGER', 'INTERSECT', 'INTERVAL',
    'INTO', 'IS', 'ISOLATION', 'ITERATE',

    'JOIN',

    'KEY',

    'LANGUAGE', 'LARGE', 'LAST', 'LATERAL', 'LEADING', 'LEFT', 'LESS', 'LEVEL', 'LIKE',
    'LIMIT',
    'LOCAL', 'LOCALTIME', 'LOCALTIMESTAMP', 'LOCATOR',

    'MAP', 'MATCH', 'MINUTE', 'MODIFIES', 'MODIFY', 'MODULE', 'MONTH',

    'NAMES', 'NATIONAL', 'NATURAL', 'NCHAR', 'NCLOB', 'NEW', 'NEXT', 'NO', 'NONE',
    'NOT', 'NULL', 'NUMERIC',

    'OBJECT', 'OF', 'OFF', 'OLD', 'ON', 'ONLY', 'OPEN', 'OPERATION', 'OPTION',
    'OR', 'ORDER', 'ORDINALITY', 'OUT', 'OUTER', 'OUTPUT',

    'PAD', 'PARAMETER', 'PARAMETERS', 'PARTIAL', 'PATH', 'POSTFIX', 'PRECISION', 'PREFIX',
    'PREORDER', 'PREPARE', 'PRESERVE', 'PRIMARY',
    'PRIOR', 'PRIVILEGES', 'PROCEDURE', 'PUBLIC',

    'READ', 'READS', 'REAL', 'RECURSIVE', 'REF', 'REFERENCES', 'REFERENCING', 'RELATIVE',
    'RESTRICT', 'RESULT', 'RETURN', 'RETURNS', 'REVOKE', 'RIGHT',
    'ROLE', 'ROLLBACK', 'ROLLUP', 'ROUTINE', 'ROW', 'ROWS',

    'SAVEPOINT', 'SCHEMA', 'SCROLL', 'SCOPE', 'SEARCH', 'SECOND', 'SECTION', 'SELECT',
    'SEQUENCE', 'SESSION', 'SESSION_USER', 'SET', 'SETS', 'SIZE', 'SMALLINT', 'SOME| SPACE',
    'SPECIFIC', 'SPECIFICTYPE', 'SQL', 'SQLEXCEPTION', 'SQLSTATE', 'SQLWARNING', 'START',
    'STATE', 'STATEMENT', 'STATIC', 'STRUCTURE', 'SYSTEM_USER',

    'TABLE', 'TEMPORARY', 'TERMINATE', 'THAN', 'THEN', 'TIME', 'TIMESTAMP',
    'TIMEZONE_HOUR', 'TIMEZONE_MINUTE', 'TO', 'TRAILING', 'TRANSACTION', 'TRANSLATION',
    'TREAT', 'TRIGGER', 'TRUE',

    'UNDER', 'UNION', 'UNIQUE', 'UNKNOWN',
    'UNNEST', 'UPDATE', 'USAGE', 'USER', 'USING',
    'VALUE', 'VALUES', 'VARCHAR', 'VARIABLE', 'VARYING', 'VIEW',

    'WHEN', 'WHENEVER', 'WHERE', 'WITH', 'WITHOUT', 'WORK', 'WRITE',

    'YEAR',

    'ZONE',
}

globals().update({
    k: k
    for k in chain(RESERVED_WORDS, NON_RESERVED_WORDS)
})
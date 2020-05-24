from itertools import chain

# noinspection PyUnresolvedReferences
__all__ = ['ABS', 'ABSOLUTE', 'ACTION', 'ADA', 'ADD', 'ADMIN', 'AFTER', 'AGGREGATE', 'ALIAS', 'ALL', 'ALLOCATE',
           'ALTER', 'AND', 'ANY', 'ARE', 'ARRAY', 'AS', 'ASC', 'ASENSITIVE', 'ASSERTION', 'ASSIGNMENT', 'ASYMMETRIC',
           'AT', 'ATOMIC', 'AUTHORIZATION', 'AVG', 'BEFORE', 'BEGIN', 'BETWEEN', 'BINARY', 'BIT', 'BITVAR',
           'BIT_LENGTH', 'BLOB', 'BOOLEAN', 'BOTH', 'BREADTH', 'BY', 'C', 'CALL', 'CALLED', 'CARDINALITY', 'CASCADE',
           'CASCADED', 'CASE', 'CAST', 'CATALOG', 'CATALOG_NAME', 'CHAIN', 'CHAR', 'CHARACTER', 'CHARACTER_LENGTH',
           'CHARACTER_SET_CATALOG', 'CHARACTER_SET_NAME', 'CHARACTER_SET_SCHEMA', 'CHAR_LENGTH', 'CHECK', 'CHECKED',
           'CLASS', 'CLASS_ORIGIN', 'CLOB', 'CLOSE', 'COALESCE', 'COBOL', 'COLLATE', 'COLLATION', 'COLLATION_CATALOG',
           'COLLATION_NAME', 'COLLATION_SCHEMA', 'COLUMN', 'COLUMN_NAME', 'COMMAND_FUNCTION', 'COMMAND_FUNCTION_CODE',
           'COMMIT', 'COMMITTED', 'COMPLETION', 'CONDITION_NUMBER', 'CONNECT', 'CONNECTION', 'CONNECTION_NAME',
           'CONSTRAINT', 'CONSTRAINTS', 'CONSTRAINT_CATALOG', 'CONSTRAINT_NAME', 'CONSTRAINT_SCHEMA', 'CONSTRUCTOR',
           'CONTAINS', 'CONTINUE', 'CONVERT', 'CORRESPONDING', 'COUNT', 'CREATE', 'CROSS', 'CUBE', 'CURRENT',
           'CURRENT_DATE', 'CURRENT_PATH', 'CURRENT_ROLE', 'CURRENT_TIME', 'CURRENT_TIMESTAMP', 'CURRENT_USER',
           'CURSOR', 'CURSOR_NAME', 'CYCLE', 'DATA', 'DATE', 'DATETIME_INTERVAL_CODE', 'DATETIME_INTERVAL_PRECISION',
           'DAY', 'DEALLOCATE', 'DEC', 'DECIMAL', 'DECLARE', 'DEFAULT', 'DEFERRABLE', 'DEFERRED', 'DEFINED', 'DEFINER',
           'DELETE', 'DEPTH', 'DEREF', 'DESC', 'DESCRIBE', 'DESCRIPTOR', 'DESTROY', 'DESTRUCTOR', 'DETERMINISTIC',
           'DIAGNOSTICS', 'DICTIONARY', 'DISCONNECT', 'DISPATCH', 'DISTINCT', 'DOMAIN', 'DOUBLE', 'DROP', 'DYNAMIC',
           'DYNAMIC_FUNCTION', 'DYNAMIC_FUNCTION_CODE', 'EACH', 'ELSE', 'END', 'END-EXEC', 'EQUALS', 'ESCAPE', 'EVERY',
           'EXCEPT', 'EXCEPTION', 'EXEC', 'EXECUTE', 'EXISTING', 'EXISTS', 'EXTERNAL', 'EXTRACT', 'FALSE', 'FETCH',
           'FINAL', 'FIRST', 'FLOAT', 'FOR', 'FOREIGN', 'FORTRAN', 'FOUND', 'FREE', 'FROM', 'FULL', 'FUNCTION', 'G',
           'GENERAL', 'GENERATED', 'GET', 'GLOBAL', 'GO', 'GOTO', 'GRANT', 'GRANTED', 'GROUP', 'GROUPING', 'HAVING',
           'HIERARCHY', 'HOLD', 'HOST', 'HOUR', 'IDENTITY', 'IGNORE', 'IMMEDIATE', 'IMPLEMENTATION', 'IN', 'INDICATOR',
           'INFIX', 'INITIALIZE', 'INITIALLY', 'INNER', 'INOUT', 'INPUT', 'INSENSITIVE', 'INSERT', 'INSTANCE',
           'INSTANTIABLE', 'INT', 'INTEGER', 'INTERSECT', 'INTERVAL', 'INTO', 'INVOKER', 'IS', 'ISOLATION', 'ITERATE',
           'JOIN', 'K', 'KEY', 'KEY_MEMBER', 'KEY_TYPE', 'LANGUAGE', 'LARGE', 'LAST', 'LATERAL', 'LEADING', 'LEFT',
           'LENGTH', 'LESS', 'LEVEL', 'LIKE', 'LIMIT', 'LOCAL', 'LOCALTIME', 'LOCALTIMESTAMP', 'LOCATOR', 'LOWER', 'M',
           'MAP', 'MATCH', 'MAX', 'MESSAGE_LENGTH', 'MESSAGE_OCTET_LENGTH', 'MESSAGE_TEXT', 'METHOD', 'MIN', 'MINUTE',
           'MOD', 'MODIFIES', 'MODIFY', 'MODULE', 'MONTH', 'MORE', 'MUMPS', 'NAME', 'NAMES', 'NATIONAL', 'NATURAL',
           'NCHAR', 'NCLOB', 'NEW', 'NEXT', 'NO', 'NONE', 'NOT', 'NULL', 'NULLABLE', 'NULLIF', 'NUMBER', 'NUMERIC',
           'OBJECT', 'OCTET_LENGTH', 'OF', 'OFF', 'OLD', 'ON', 'ONLY', 'OPEN', 'OPERATION', 'OPTION', 'OPTIONS', 'OR',
           'ORDER', 'ORDINALITY', 'OUT', 'OUTER', 'OUTPUT', 'OVERLAPS', 'OVERLAY', 'OVERRIDING', 'PAD', 'PARAMETER',
           'PARAMETERS', 'PARAMETER_MODE', 'PARAMETER_NAME', 'PARAMETER_ORDINAL_POSITION', 'PARAMETER_SPECIFIC_CATALOG',
           'PARAMETER_SPECIFIC_NAME', 'PARAMETER_SPECIFIC_SCHEMA', 'PARTIAL', 'PASCAL', 'PATH', 'PLI', 'POSITION',
           'POSTFIX', 'PRECISION', 'PREFIX', 'PREORDER', 'PREPARE', 'PRESERVE', 'PRIMARY', 'PRIOR', 'PRIVILEGES',
           'PROCEDURE', 'PUBLIC', 'READ', 'READS', 'REAL', 'RECURSIVE', 'REF', 'REFERENCES', 'REFERENCING', 'RELATIVE',
           'REPEATABLE', 'RESTRICT', 'RESULT', 'RETURN', 'RETURNED_LENGTH', 'RETURNED_OCTET_LENGTH',
           'RETURNED_SQLSTATE', 'RETURNS', 'REVOKE', 'RIGHT', 'ROLE', 'ROLLBACK', 'ROLLUP', 'ROUTINE',
           'ROUTINE_CATALOG', 'ROUTINE_NAME', 'ROUTINE_SCHEMA', 'ROW', 'ROWS', 'ROW_COUNT', 'SAVEPOINT', 'SCALE',
           'SCHEMA', 'SCHEMA_NAME', 'SCOPE', 'SCROLL', 'SEARCH', 'SECOND', 'SECTION', 'SECURITY', 'SELECT', 'SELF',
           'SENSITIVE', 'SEQUENCE', 'SERIALIZABLE', 'SERVER_NAME', 'SESSION', 'SESSION_USER', 'SET', 'SETS', 'SIMILAR',
           'SIMPLE', 'SIZE', 'SMALLINT', 'SOME| SPACE', 'SOURCE', 'SPECIFIC', 'SPECIFICTYPE', 'SPECIFIC_NAME', 'SQL',
           'SQLEXCEPTION', 'SQLSTATE', 'SQLWARNING', 'START', 'STATE', 'STATEMENT', 'STATIC', 'STRUCTURE', 'STYLE',
           'SUBCLASS_ORIGIN', 'SUBLIST', 'SUBSTRING', 'SUM', 'SYMMETRIC', 'SYSTEM', 'SYSTEM_USER', 'TABLE',
           'TABLE_NAME', 'TEMPORARY', 'TERMINATE', 'THAN', 'THEN', 'TIME', 'TIMESTAMP', 'TIMEZONE_HOUR',
           'TIMEZONE_MINUTE', 'TO', 'TRAILING', 'TRANSACTION', 'TRANSACTIONS_COMMITTED', 'TRANSACTIONS_ROLLED_BACK',
           'TRANSACTION_ACTIVE', 'TRANSFORM', 'TRANSFORMS', 'TRANSLATE', 'TRANSLATION', 'TREAT', 'TRIGGER',
           'TRIGGER_CATALOG', 'TRIGGER_NAME', 'TRIGGER_SCHEMA', 'TRIM', 'TRUE', 'TYPE', 'UNCOMMITTED', 'UNDER', 'UNION',
           'UNIQUE', 'UNKNOWN', 'UNNAMED', 'UNNEST', 'UPDATE', 'UPPER', 'USAGE', 'USER', 'USER_DEFINED_TYPE_CATALOG',
           'USER_DEFINED_TYPE_NAME', 'USER_DEFINED_TYPE_SCHEMA', 'USING', 'VALUE', 'VALUES', 'VARCHAR', 'VARIABLE',
           'VARYING', 'VIEW', 'WHEN', 'WHENEVER', 'WHERE', 'WITH', 'WITHOUT', 'WORK', 'WRITE', 'YEAR', 'ZONE',

           'INDEX', 'IF', 'NULLS', 'INCLUDE', 'TABLESPACE', 'BTREE', 'HASH', 'GIST', 'SPGIST', 'GIN', 'BRIN']

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
    'PARAMETER_SPECIFIC_SCHEMA', 'PLI', 'POSITION', 'PUBLIC',

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

    # FOR PARSE INDEX
    'INDEX', 'IF', 'INCLUDE', 'TABLESPACE', 'BTREE', 'HASH', 'GIST', 'SPGIST', 'GIN', 'BRIN',
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
    'PRIOR', 'PRIVILEGES', 'PROCEDURE',

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

    # FOR PARSE INDEX
    'NULLS'
}

globals().update({
    k: k
    for k in chain(RESERVED_WORDS, NON_RESERVED_WORDS)
})

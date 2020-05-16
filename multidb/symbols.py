# Важно сохранить порядок по уменьшению длины спецсимволов
# Необходимо для корректной работы регулярного выражения
SPEC_SYMBOLS = (
    ('concatenation_operator',             '||'),
    ('double_colon',                       '::'),
    ('greater_than_or_equals_operator',    '>='),
    ('less_than_or_equals_operator',       '<='),
    ('not_equals_operator',                '<>'),
    ('right_arrow',                        '->'),
    ('ampersand',                          '&'),
    ('asterisk',                           '*'),
    ('circumflex',                         '^'),
    ('colon',                              ':'),
    ('comma',                              ','),
    ('double_quote',                       '"'),
    ('equals_operator',                    '='),
    ('greater_than_operator',              '>'),
    ('left_brace',                         '{'),
    ('left_bracket',                       '['),
    ('left_paren',                         '('),
    ('less_than_operator',                 '<'),
    ('minus_sign',                         '-'),
    ('percent',                            '%'),
    ('period',                             '.'),
    ('plus_sign',                          '+'),
    ('question_mark',                      '?'),
    ('quote',                              "'"),
    ('right_brace',                        '}'),
    ('right_bracket',                      ']'),
    ('right_paren',                        ')'),
    ('semicolon',                          ';'),
    ('solidus',                            '/'),
    ('underscore',                         '_'),
    ('vertical_bar',                       '|'),
)

SYMBOL_TO_NAME = {
    v: k
    for k, v in SPEC_SYMBOLS
}

NAME_TO_SYMBOL = {
    k: v
    for k, v in SPEC_SYMBOLS
}

globals().update(NAME_TO_SYMBOL)

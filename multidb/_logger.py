import logging
import logging.config
import os

import yaml

CURRENT_DIR = os.path.dirname(__file__)


def setup_logging(
        default_path=os.path.join(CURRENT_DIR, 'logging.yaml'),
        default_level=logging.DEBUG,
        env_key='LOG_CFG'
):
    path = os.getenv(env_key, default_path)
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = yaml.safe_load(f)
        try:
            os.remove(config['handlers']['file']['filename'])
        except Exception as ex:
            logging.error(ex)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)


class ParserLogger(logging.Logger):
    is_crashed = False
    parser = None
    log_position = True
    buffer = []

    def __init__(self, name, level=logging.NOTSET):
        super().__init__(name, level)
        self.mode = 0
        # -1 not log pos
        #  0 last token
        #  1 current token

    @classmethod
    def pop_line_buffer(cls, dev=None):
        if cls.buffer:
            data = cls.buffer.pop()
            if dev:
                if cls.buffer:
                    cls.buffer[-1].extend(data)
                else:
                    for slf, *args in data:
                        logging.Logger._log(slf, *args)

    @classmethod
    def append_line_buffer(cls, data=None):
        cls.buffer.append(data or [])

    @classmethod
    def set_is_crashed(cls, is_crashed):
        cls.is_crashed = is_crashed

    @classmethod
    def set_parser(cls, parser):
        cls.parser = parser

    @property
    def do_not_display_pos(self):
        self.log_position = False
        return self

    @property
    def current_token(self):
        self.mode = 1
        return self

    @property
    def pass_token_info(self):
        self.mode = -1
        return self

    def _log(self, level, msg, args, exc_info=None, extra=None, stack_info=False):
        lexer = self.parser.token

        if level >= logging.ERROR:
            self.__class__.is_crashed = True
        if self.log_position and self.mode >= 0 and lexer:
            pos = lexer.interval if self.mode else lexer.last_interval
            msg = '{!r} {}'.format(pos, msg)
        self.mode = 0
        self.log_position = True
        if self.__class__.buffer:
            self.__class__.buffer[-1].append((self, level, msg, args, exc_info, extra, stack_info))
        else:
            super()._log(level, msg, args, exc_info, extra, stack_info)


logging.setLoggerClass(ParserLogger)

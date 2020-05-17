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
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)


class ParserLogger(logging.Logger):
    is_crashed = False
    lexer = None
    log_position = True

    def __init__(self, name, level=logging.NOTSET):
        super().__init__(name, level)
        self.mode = 0
        # -1 not log pos
        #  0 last token
        #  1 current token

    @classmethod
    def set_lexer(cls, lexer):
        cls.lexer = lexer

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
        if level >= logging.ERROR:
            self.__class__.is_crashed = True
        if self.log_position and self.mode >= 0 and self.lexer:
            pos = self.lexer.interval if self.mode else self.lexer.last_interval
            msg = '{!r} {}'.format(pos, msg)
        self.mode = 0
        self.log_position = True
        super()._log(level, msg, args, exc_info, extra, stack_info)


logging.setLoggerClass(ParserLogger)

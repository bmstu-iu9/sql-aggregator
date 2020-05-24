import re

import yaml

from . import structures as st
from . import dialect


class ControlCenter:
    USE_REGEXP = re.compile(
        r'^\s+use\s+([a-zA-Z_][a-zA-Z0-9_. ]*)\s+as\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+$',
        re.IGNORECASE
    )
    EXIT_REGEXP = re.compile(r'^\s*exit\s*$', re.IGNORECASE)

    def __init__(self, path_to_config):
        with open(path_to_config, encoding='utf-8') as f:
            self.raw_data = yaml.safe_load(f)
        self.sources = {
            name: st.DBMS(name, connection_data)
            for name, connection_data in self.raw_data.items()
        }

        self.local_alias = dict(dbms={}, db={}, schema={}, table={})

    def execute(self, query):
        pass

    def cycle(self):
        buffer = []
        while True:
            try:
                line = input()
            except KeyboardInterrupt:
                buffer = []
                continue

            if not line:
                continue
            if buffer:
                buffer.append(line)
                if line.rstrip().endswith(';'):
                    query = '\n'.join(line)
                    buffer = []
                    self.execute(query)
            else:
                use = self.USE_REGEXP.match(line)
                if use:
                    left = use.group(1).lower()
                    right = use.group(2).lower()
                    left = [
                        word.strip()
                        for word in left.split('.')

                    ]
                    if len(left) == 4:    # Alias table
                        kind = 'table'
                    elif len(left) == 3:  # Alias schema
                        kind = 'schema'
                    elif len(left) == 2:  # Alias db
                        kind = 'db'
                    elif len(left) == 1:  # Alias dbms
                        kind = 'dbms'
                    else:
                        print('Wrong naming chain {}'.format('.'.join(left)))
                        continue
                    self.local_alias[kind][right] = tuple(left)
                    continue
                ext = self.EXIT_REGEXP.match(line)
                if ext:
                    return
                buffer.append(line)

from IPython.core.magic import (Magics, magics_class, line_magic,
                                cell_magic, needs_local_scope)
from IPython.display import display, HTML

from pycozo.client import Client, QueryException


@magics_class
class CozoMagics(Magics):
    def __init__(self, shell, **kwargs):
        super().__init__(shell, **kwargs)
        self.client = Client()
        self.params = {}

    @line_magic
    def cozo_auth(self, line: str):
        args = line.split()
        if len(args) != 1:
            raise Exception('Wrong number of arguments: one required')
        self.client.auth = args[0]
        try:
            self.client.run('?[a] := a = 1 + 1', self.params)
        except QueryException as e:
            return e
        except Exception as e:
            return e

    @line_magic
    def cozo_host(self, line: str):
        self.client.host = line.strip()

    @cell_magic
    def cozo(self, line, cell):
        try:
            res, time_taken = self.client.run(cell, self.params)
        except QueryException as e:
            return e
        except Exception as e:
            return e
        var = line.strip()
        if var:
            self.shell.user_ns[var] = res
        if time_taken is not None:
            display(HTML(f'<p style="font-size: 75%">Completed in {time_taken}ms</p>'))
        return res

    @line_magic
    @needs_local_scope
    def cozo_run_string(self, line, local_ns):
        script = eval(line, self.shell.user_ns, local_ns)
        if not isinstance(script, str):
            raise Exception('a string is required')
        try:
            return self.client.run(script, self.params)
        except QueryException as e:
            return e

    @line_magic
    def cozo_run_file(self, line):
        filename = line.strip()
        with open(filename, encoding='utf-8') as f:
            script = f.read()
        try:
            return self.client.run(script, self.params)
        except QueryException as e:
            return e

    @line_magic
    def cozo_clear(self, _line):
        self.params.clear()

    @line_magic
    @needs_local_scope
    def cozo_set(self, line, local_ns):
        var, val = line.split(maxsplit=1)
        val = eval(val, self.shell.user_ns, local_ns)
        try:
            import pandas
            if isinstance(val, pandas.DataFrame):
                self.params[var] = val.values.tolist()
            else:
                self.params[var] = val
        except ImportError:
            self.params[var] = val

    @line_magic
    @needs_local_scope
    def cozo_set_params(self, line, local_ns):
        val = eval(line, self.shell.user_ns, local_ns)
        if isinstance(val, dict):
            self.params = val
        else:
            raise Exception('params must be specified as a dict')

    @line_magic
    def cozo_params(self, _line):
        return self.params

    @line_magic
    def cozo_client(self, _line):
        return self.client

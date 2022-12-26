#  Copyright 2022, The Cozo Project Authors.
#
#  This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0.
#  If a copy of the MPL was not distributed with this file,
#  You can obtain one at https://mozilla.org/MPL/2.0/.

import json

from IPython.core.magic import (Magics, magics_class, line_magic,
                                cell_magic, needs_local_scope)

from pycozo.client import Client, QueryException


@magics_class
class CozoMagics(Magics):
    """Cozo magics for Jupyter notebooks"""

    def __init__(self, shell, **kwargs):
        super().__init__(shell, **kwargs)
        self.client = None
        self.params = {}

    def _ensure_client(self):
        if self.client is None:
            self.client = Client()
            self.shell.user_ns['COZO_CLIENT'] = self.client

    @line_magic
    def cozo_open(self, line: str):
        """Open a database client. The magic should be followed by two or three arguments:
        ```
        %cozo_open <ENGINE>, <PATH>
        ```
        or
        ```
        %cozo_open <ENGINE>, <PATH>, <OPTIONS>
        ```
        """
        args = eval(line)
        engine = args[0]
        path = args[1]
        options = args[2] if len(args) > 2 else {}
        self.client = Client(engine, path, options)
        self.shell.user_ns['COZO_CLIENT'] = self.client

    @cell_magic
    def cozo(self, line, cell):
        """Run CozoScript"""
        self._ensure_client()
        try:
            res = self.client.run(cell, self.params)
        except QueryException as e:
            return e
        except Exception as e:
            return e
        var = line.strip()
        if var:
            self.shell.user_ns[var] = res
        try:
            return res.style.applymap(_colour_code_type)
        except:
            return res

    @line_magic
    @needs_local_scope
    def cozo_run_string(self, line, local_ns):
        """Run CozoScript contained in a string expression"""
        self._ensure_client()
        script = eval(line, self.shell.user_ns, local_ns)
        if not isinstance(script, str):
            raise Exception('a string is required')
        try:
            return self.client.run(script, self.params)
        except QueryException as e:
            return e

    @line_magic
    def cozo_run_file(self, line):
        """Run CozoScript contained in a file"""
        self._ensure_client()
        filename = eval(line)
        with open(filename, encoding='utf-8') as f:
            script = f.read()
        try:
            return self.client.run(script, self.params)
        except QueryException as e:
            return e

    @line_magic
    def cozo_clear(self, _line):
        """Clear all parameters"""
        self.params.clear()

    @line_magic
    @needs_local_scope
    def cozo_set(self, line, local_ns):
        """Set a parameter
        ```
        %cozo_set <PARAM_NAME> <PARAM_EXPR>
        ```
        """
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
        """Set all parameters, takes a dict"""
        val = eval(line, self.shell.user_ns, local_ns)
        if isinstance(val, dict):
            self.params = val
        else:
            raise Exception('params must be specified as a dict')

    @line_magic
    def cozo_params(self, _line):
        """Returns the current parameters"""
        return self.params

    @line_magic
    def cozo_import_local_file(self, line):
        """Import data saved in a local file"""
        self._ensure_client()
        file = eval(line)
        with open(file, encoding='utf-8') as f:
            data = json.load(f)

        self.client.import_relations(data)


    @line_magic
    def cozo_import_remote_file(self, line):
        """Import data saved in a local file"""
        import requests
        self._ensure_client()
        url = eval(line)
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json()
        self.client.import_relations(data)

def _colour_code_type(val):
    if isinstance(val, int) or isinstance(val, float):
        colour = '#307fc1'
    elif isinstance(val, str):
        colour = 'black'
    else:
        colour = '#bf5b3d'
    return f'color: {colour}'

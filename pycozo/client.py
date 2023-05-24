#  Copyright 2022, The Cozo Project Authors.
#
#  This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0.
#  If a copy of the MPL was not distributed with this file,
#  You can obtain one at https://mozilla.org/MPL/2.0/.

import json
import logging

logger = logging.getLogger(__name__)


class Client:
    """Python client for CozoDB

    This client can either operate on an embedded database, or a remote database via HTTP.
    """

    def __init__(self, engine='mem', path='', options=None, *, dataframe=True):
        """Constructor for the client. The behaviour depends on the argument.

        If the database `db` is an embedded one, and you do not intend it to live as long as your program, you **must**
        call `db.close()` when you are done with it. Simply `del db` is not enough to clean up the native parts.

        :param engine: if 'http', then a remote client is constructed, otherwise an embedded one is constructed.
                       For 'http', the `requests` package must be installed. For the embedded engines,
                       the `cozo-embedded` package must be installed.
                       What engines can be used depends on what was compiled in. Use 'mem' for in-memory, non-persistent
                       databases, 'sqlite' for lightweight persistent databases, and 'rocksdb' for databases
                       that expects high concurrency.
        :param path: the path to store the database on disk, only makes sense for those engines that are persistent.
        :param options: options for the database, the expected values depend on the engine of the database.
                        Currently only the 'http' engine expect options of the form:
                        `{'host': <HOST:PORT>, 'auth': <AUTH_STR>}`.
        :param dataframe: if true, output will be transformed into pandas dataframes. The `pandas` package
                          must be installed.
        """
        self.pandas = None
        if engine == 'http':
            self.host = options['host']
            self.auth = options.get('auth')
            self.embedded = None
            self._remote_sse = {}
            self._remote_cb_id = 0
        else:
            from cozo_embedded import CozoDbPy
            self.embedded = CozoDbPy(engine, path, json.dumps(options or {}))

        if dataframe:
            try:
                import pandas
                self.pandas = pandas
            except ImportError:
                logger.exception('`pandas` feature was requested, but pandas is not installed')
                pass

    def close(self):
        """Close the embedded database. After closing, the database can no longer be used.

        For embedded databases, this method must be called, otherwise the native resources associated with it
        may live as long as your program.

        This is a no-op for HTTP-based clients.
        """
        if self.embedded:
            self.embedded.close()

    def _headers(self):
        return {
            'x-cozo-auth': self.auth
        }

    def _client_request(self, script, params=None, immutable=False):
        import requests

        r = requests.post(f'{self.host}/text-query', headers=self._headers(), json={
            'script': script,
            'params': params or {},
            'immutable': immutable
        })
        res = r.json()
        return self._format_return(res)

    def _format_return(self, res):
        if not res['ok']:
            raise QueryException(res)

        if self.pandas:
            return self.pandas.DataFrame(columns=res['headers'], data=res['rows'])
        else:
            return res

    def _embedded_request(self, script, params=None, immutable=False):
        try:
            res = self.embedded.run_script(script, params or {}, immutable)
        except Exception as e:
            raise QueryException(e.args[0]) from None
        if self.pandas:
            return self.pandas.DataFrame(columns=res['headers'], data=res['rows'])
        else:
            return res

    def run(self, script, params=None, immutable=False):
        """Run a given CozoScript query.

        :param script: the query in CozoScript
        :param params: the named parameters for the query. If specified, must be a dict with string keys.
        :return: the query result as a dict, or a pandas dataframe if the `dataframe` option was true.
        """
        if self.embedded is None:
            return self._client_request(script, params, immutable)
        else:
            return self._embedded_request(script, params, immutable)

    def export_relations(self, relations):
        """Export the specified relations.

        :param relations: names of the relations in a list.
        :return: a dict with string keys for the names of relations, and values containing all the rows.
        """
        if self.embedded:
            return self.embedded.export_relations(relations)
        else:
            import requests
            import urllib.parse

            rels = ','.join(map(lambda s: urllib.parse.quote_plus(s), relations))
            url = f'{self.host}/export/{rels}'

            r = requests.get(url, headers=self._headers())
            res = r.json()
            if res['ok']:
                return res['data']
            else:
                raise RuntimeError(res['message'])

    def import_relations(self, data):
        """Import data into a database

        Note that triggers are _not_ run for the relations, if any exists.
        If you need to activate triggers, use queries with parameters.

        :param data: should be given as a dict with string keys, in the same format as returned by `export_relations`.
                     The relations to import into must exist.
        """
        if self.embedded:
            self.embedded.import_relations(data)
        else:
            import requests
            url = f'{self.host}/import'

            r = requests.put(url, headers=self._headers(), json=data)
            res = r.json()
            if not res['ok']:
                raise RuntimeError(res['message'])

    def backup(self, path):
        """Backup a database to the specified path.

        :param path: the path to write the backup into. For a remote database, this is a path on the remote machine.
        """
        if self.embedded:
            self.embedded.backup(path)
        else:
            import requests

            r = requests.post(f'{self.host}/backup', headers=self._headers(), json={'path': path})
            res = r.json()
            if not res['ok']:
                raise RuntimeError(res['message'])

    def register_callback(self, relation, callback):
        if self.embedded:
            return self.embedded.register_callback(relation, callback)
        else:
            import threading

            tid = self._remote_cb_id
            self._remote_cb_id += 1
            url = f'{self.host}/changes/{relation}'
            thread = threading.Thread(target=self._start_sse, args=(tid, url, callback), daemon=True)
            thread.start()
            self._remote_sse[tid] = {'thread': thread}

            return tid

    def _start_sse(self, tid, url, callback, min_delay=1, max_delay=60):
        import requests
        logger.info('Starting SSE thread')
        headers = {'Accept': 'text/event-stream', 'Accept-Encoding': ''}

        consecutive_failures = 0

        while True:
            try:
                with requests.get(url, stream=True, headers=headers) as response:
                    response.raise_for_status()

                    consecutive_failures = 0

                    buffer = b""
                    for chunk in response.iter_content(chunk_size=1):
                        if tid not in self._remote_sse:
                            logger.info('Stopping SSE thread')
                            return
                        buffer += chunk
                        if buffer.endswith(b'\n\n'):
                            event_text = buffer.decode('utf-8').strip()
                            if event_text.startswith('data:'):
                                payload = json.loads(event_text[5:].strip())
                                callback(payload['op'], payload['new_rows']['rows'], payload['old_rows']['rows'])
                            buffer = b""
            except Exception as e:
                import time

                logger.error(f'Error in SSE thread: {e}')
                consecutive_failures += 1

                # Exponential backoff with a cap at max_delay
                backoff_delay = min(min_delay * (2 ** (consecutive_failures - 1)), max_delay)

                logger.info(f'Sleeping for {backoff_delay} seconds before retrying...')
                time.sleep(backoff_delay)

    def unregister_callback(self, cb_id):
        if self.embedded:
            self.embedded.unregister_callback(cb_id)
        else:
            del self._remote_sse[cb_id]

    def register_fixed_rule(self, name, arity, impl):
        if self.embedded:
            return self.embedded.register_fixed_rule(name, arity, impl)
        else:
            raise RuntimeError('Only supported on embedded DBs')

    def unregister_fixed_rule(self, name):
        if self.embedded:
            return self.embedded.unregister_fixed_rule(name)
        else:
            raise RuntimeError('Only supported on embedded DBs')

    def restore(self, path):
        """Restore database from a backup. Must be called on an empty database.

        :param path: the path to the backup.
                     For remote databases, you cannot restore them this way: use the executable directly.
        """
        if self.embedded:
            self.embedded.restore(path)
        else:
            raise RuntimeError('Remote databases cannot be restored remotely')

    def import_from_backup(self, path, relations):
        """Import stored relations from a backup.

        Note that triggers are _not_ run for the relations, if any exists.
        If you need to activate triggers, use queries with parameters.

        :param path: path to the backup file. For remote databases, this is a path on the remote machine.
        :param relations: a list containing the names of the relations to import. The relations must exist
                          in the database.
        """
        if self.embedded:
            self.embedded.import_from_backup(path, relations)
        else:
            import requests

            r = requests.post(f'{self.host}/import-from-backup', headers=self._headers(),
                              json={'path': path, 'relations': relations})
            res = r.json()
            if not res['ok']:
                raise RuntimeError(res['message'])

    def multi_transact(self, write=False):
        if self.embedded:
            return MultiTransact(self.embedded.multi_transact(write))
        else:
            raise RuntimeError('Multi-transaction not yet supported for remote')

    def _process_mutate_data_dict(self, data):
        cols = []
        row = []
        for k, v in data.items():
            cols.append(k)
            row.append(v)
        return cols, row

    def _process_mutate_data(self, data):
        if isinstance(data, dict):
            cols, row = self._process_mutate_data_dict(data)
            return ','.join(cols), [row]
        elif isinstance(data, list):
            cols, row = self._process_mutate_data_dict(data[0])
            rows = [row]
            for el in data[1:]:
                nxt_row = []
                for col in cols:
                    nxt_row.append(el[col])
                rows.append(nxt_row)
            return ','.join(cols), rows
        else:
            import pandas as pd
            if isinstance(data, pd.DataFrame):
                cols = data.columns.tolist()
                rows = data.values.tolist()
                return ','.join(cols), rows
            else:
                raise RuntimeError('Invalid data type for mutation')

    def _mutate(self, relation, data, op):
        cols_str, processed_data = self._process_mutate_data(data)
        q = f'?[{cols_str}] <- $data :{op} {relation} {{ {cols_str} }}'
        return self.run(q, {'data': processed_data})

    def insert(self, relation, data):
        return self._mutate(relation, data, 'insert')

    def put(self, relation, data):
        return self._mutate(relation, data, 'put')

    def update(self, relation, data):
        return self._mutate(relation, data, 'update')

    def rm(self, relation, data):
        return self._mutate(relation, data, 'rm')


class MultiTransact:
    def __init__(self, multi_tx):
        self.multi_tx = multi_tx

    def commit(self):
        return self.multi_tx.commit()

    def abort(self):
        return self.multi_tx.abort()

    def run(self, script, params=None):
        return self.multi_tx.run_script(script, params or {})


class QueryException(Exception):
    """The exception class for queries. `repr(e)` will pretty format the exceptions into ANSI-coloured messages.
    """

    def __init__(self, resp):
        super().__init__()
        self.resp = resp

    def __repr__(self):
        if hasattr(self.resp, 'get'):
            return self.resp.get('display') or self.resp.get('message') or str(self.resp)
        else:
            return str(self.resp)

    def __str__(self):
        return self.resp.get('message') or str(self.resp)

    def _repr_pretty_(self, p, cycle):
        p.text(repr(self))

    @property
    def code(self):
        return self.resp.get('code')

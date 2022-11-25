import json


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
            self.host = options.host
            self.auth = options.auth
        else:
            from cozo_embedded import CozoDbPy
            self.embedded = CozoDbPy(engine, path, json.dumps(options or {}))

        if dataframe:
            try:
                import pandas
                self.pandas = pandas
            except ImportError as _:
                print('`pandas` feature was requested, but pandas is not installed')
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

    def _client_request(self, script, params=None):
        import requests

        r = requests.post(f'{self.host}/text-query', headers=self._headers(), json={
            'script': script,
            'params': params or {}
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

    def _embedded_request(self, script, params=None):
        import json

        params_str = json.dumps(params or {}, ensure_ascii=False)
        r = self.embedded.run_query(script, params_str)
        res = json.loads(r)
        return self._format_return(res)

    def run(self, script, params=None):
        """Run a given CozoScript query.

        :param script: the query in CozoScript
        :param params: the named parameters for the query. If specified, must be a dict with string keys.
        :return: the query result as a dict, or a pandas dataframe if the `dataframe` option was true.
        """
        if self.embedded is None:
            return self._client_request(script, params)
        else:
            return self._embedded_request(script, params)

    def export_relations(self, relations, *, as_objects=False):
        """Export the specified relations.

        :param relations: names of the relations in a list.
        :param as_objects: if `true`, each row of a relation will be given as a dict of key-value pairs, otherwise
                           each row will be given as an array of values, with keys given separately for all rows.
        :return: a dict with string keys for the names of relations, and values containing all the rows.
        """
        if self.embedded:
            payload = json.dumps({'relations': relations, 'as_objects': as_objects})
            res = json.loads(self.embedded.export_relations(payload))
            if res['ok']:
                return res['data']
            else:
                raise RuntimeError(res['message'])
        else:
            import requests
            import urllib.parse

            rels = ','.join(map(lambda s: urllib.parse.quote_plus(s), relations))
            url = f'{self.host}/export/{rels}'
            if as_objects:
                url = url + '?as_objects=1'

            r = requests.get(url, headers=self._headers())
            res = r.json()
            if res['ok']:
                return res['data']
            else:
                raise RuntimeError(res['message'])

    def import_relations(self, data):
        """Import data into a database

        :param data: should be given as a dict with string keys, in the same format as returned by `export_relations`.
                     The relations to import into must exist.
        """
        if self.embedded:
            payload = json.dumps(data, ensure_ascii=False)
            res = json.loads(self.embedded.import_relations(payload))
            if not res['ok']:
                raise RuntimeError(res['message'])
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
            res = json.loads(self.embedded.backup(path))
            if not res['ok']:
                raise RuntimeError(res['message'])
        else:
            import requests

            r = requests.post(f'{self.host}/backup/', headers=self._headers(), json={'path': path})
            res = r.json()
            if not res['ok']:
                raise RuntimeError(res['message'])

    def restore(self, path):
        """Restore database from a backup. Must be called on an empty database.

        :param path: the path to the backup.
                     For remote databases, you cannot restore them this way: use the executable directly.
        """
        if self.embedded:
            res = json.loads(self.embedded.restore(path))
            if not res['ok']:
                raise RuntimeError(res['message'])
        else:
            raise RuntimeError('Remote databases cannot be restored remotely')

    def import_from_backup(self, path, relations):
        """Import named relations from a backup

        :param path: path to the backup file. For remote databases, this is a path on the remote machine.
        :param relations: a list containing the names of the relations to import. The relations must exist
                          in the database.
        """
        if self.embedded:
            payload = json.dumps({'path': path, 'relations': relations}, ensure_ascii=False)
            res = json.loads(self.embedded.import_from_backup(payload))
            if not res['ok']:
                raise RuntimeError(res['message'])
        else:
            import requests

            r = requests.post(f'{self.host}/import-from-backup', headers=self._headers(),
                              json={'path': path, 'relations': relations})
            res = r.json()
            if not res['ok']:
                raise RuntimeError(res['message'])


class QueryException(Exception):
    """The exception class for queries. `repr(e)` will pretty format the exceptions into ANSI-coloured messages.
    """

    def __init__(self, resp):
        super().__init__()
        self.resp = resp

    def __repr__(self):
        return self.resp.get('display') or self.resp.get('message') or str(self.resp)

    def __str__(self):
        return self.resp.get('message') or str(self.resp)

    def _repr_pretty_(self, p, cycle):
        p.text(repr(self))

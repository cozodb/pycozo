class Client:
    def __init__(self, *, path=None, host=None, auth=None, dataframe=True):
        self.pandas = None
        if path is not None:
            from cozo_embedded import CozoDbPy
            self.embedded = CozoDbPy(path)
        elif host is not None:
            self.host = host
            self.auth = auth or ''
        else:
            raise Exception('you must specify either `path` for embedded mode, or `host` for client/server mode')

        if dataframe:
            try:
                import pandas
                self.pandas = pandas
            except ImportError as _:
                print('`pandas` feature was requested, but pandas is not installed')
                pass

    def url(self):
        return f'{self.host}/text-query'

    def headers(self):
        return {
            'x-cozo-auth': self.auth
        }

    def client_request(self, script, params=None):
        import requests

        r = requests.post(self.url(), headers=self.headers(), json={
            'script': script,
            'params': params or {}
        })
        res = r.json()
        return self.format_return(res)

    def format_return(self, res):
        if not res['ok']:
            raise QueryException(res)

        if self.pandas:
            return self.pandas.DataFrame(columns=res['headers'], data=res['rows']).style.applymap(
                colour_code_type)
        else:
            return res

    def embedded_request(self, script, params=None):
        import json

        params_str = json.dumps(params or {}, ensure_ascii=False)
        res = self.embedded.run_query(script, params_str)
        res = json.loads(res)
        return self.format_return(res)

    def run(self, script, params=None):
        if self.embedded is None:
            return self.client_request(script, params)
        else:
            return self.embedded_request(script, params)


def colour_code_type(val):
    if isinstance(val, int) or isinstance(val, float):
        colour = '#307fc1'
    elif isinstance(val, str):
        colour = 'black'
    else:
        colour = '#bf5b3d'
    return f'color: {colour}'


class QueryException(Exception):
    def __init__(self, resp):
        super().__init__()
        self.resp = resp

    def __repr__(self):
        return self.resp.get('display') or self.resp.get('message') or str(self.resp)

    def __str__(self):
        return self.resp.get('message') or str(self.resp)

    def _repr_pretty_(self, p, cycle):
        p.text(repr(self))

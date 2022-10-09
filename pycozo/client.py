import requests


class Client:
    def __init__(self, *, host='http://127.0.0.1:9070', auth=None, dataframe=True):
        self.host = host
        self.auth = auth or ''
        self.pandas = None
        if dataframe:
            try:
                import pandas
                self.pandas = pandas
            except ImportError as _:
                pass

    def url(self):
        return f'{self.host}/text-query'

    def headers(self):
        return {
            'x-cozo-auth': self.auth
        }

    def run(self, script, params=None):
        r = requests.post(self.url(), headers=self.headers(), json={
            'script': script,
            'params': params or {}
        })
        if r.ok:
            res = r.json()
            if self.pandas:
                return self.pandas.DataFrame(columns=res['headers'], data=res['rows']).style.applymap(
                    colour_code_type), res.get('time_taken')
            else:
                return res
        else:
            raise QueryException(r.text)


def colour_code_type(val):
    if isinstance(val, int) or isinstance(val, float):
        colour = '#307fc1'
    elif isinstance(val, str):
        colour = 'black'
    else:
        colour = '#bf5b3d'
    return f'color: {colour}'


class QueryException(Exception):
    def __init__(self, text):
        super().__init__()
        self.text = text

    def _repr_pretty_(self, p, cycle):
        p.text(self.text)

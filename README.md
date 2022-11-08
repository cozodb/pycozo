# PyCozo

[![pypi](https://img.shields.io/pypi/v/pycozo)](https://pypi.org/project/pycozo/)

Python client and Jupyter helper for [CozoDB](https://github.com/cozodb/cozo):

```bash
pip install "pycozo[embedded,requests,pandas]"
```

To be useful, you must specify either the `embedded` option, which enables
using CozoDB in the embedded mode, or the `requests` option, which enables
using CozoDB through the HTTP API. The `pandas` option installs `pandas`
as a dependency and allows optional auto-conversion of output relations to
Pandas dataframes. You should specify `pandas` if you use the Jupyter helper.

## Python client

First you need to import the client to use it:

```python
from pycozo.client import Client
```

Opening a local database directory with the embedded option:
```python
client = Client(path='<PATH_TO_DB_DIR>')
```
Connecting to a standalone server:
```python
client = Client(host='http://127.0.0.1:9070')
```
If the address is not a loopback address, you also need to provide the auth string:
```python
client = Client(host='http://<DOMAIN>:<PORT>', auth='<AUTH_STRING>')
```
For how to determine the `<AUTH_STRING>`, see [here](https://github.com/cozodb/cozo/blob/main/standalone.md).

After you are done with a client, you need to explicitly close it:
```python
client.close()
```
If you don't do this, the database resources may linger for an undetermined length of time
inside your process, even if you `del` the `client` variable.
It is OK to close a client multiple times.

To run query:
```python
res = client.run('::relations')
```

If you need to bind variables:
To run query:
```python
res = client.run('?[] <- [[$name]]', {'name': 'Python'})
```

If `pandas` is available, a dataframe containing the results is returned.
If you want to disable this behaviour even when you have `pandas` installed,
pass `dataframe=False` in the constructor of `Client`,
in which case a python dict containing the relation data in `res['rows']`
and the relation header in `res['header']` is returned.

When a query is unsuccessful, an exception is raised containing the details.
If you want a nicely formatted message:
```python
try:
    res = client.run('BAD!')
except Exception as e:
    print(repr(e))
```

`Client` is thread-safe, but you cannot spawn multiple processes opening the same embedded database
(connecting to the same standalone server is of course OK).

In the embedded mode, `Client` will release the [GIL](https://wiki.python.org/moin/GlobalInterpreterLock)
when executing queries so that multiple queries in different threads can proceed concurrently.

## Jupyter helper

There are two versions of the helper loaded through [magic commands](https://ipython.readthedocs.io/en/stable/interactive/magics.html)
that allows you to query CozoDB directly.
The first version is activated by
```
%load_ext pycozo.ipyext_direct
```
and allows all subsequent cells to be interpreted as CozoScript,
unless the first line of the cell starts with `%`.
If A cell has the first line `%%py`, then all following lines
are interpreted as python.

The second is activated by
```
%load_ext pycozo.ipyext
```
This version is less intrusive in that you need to prefix a cell by the line
`%%cozo` in order for subsequent content to be interpreted as CozoScript.

To execute queries, you also need to connect to a database.
If you have the embedded option enabled, you can open a database directory
by
```
%cozo_path <PATH>
```
where `<PATH>` is not quoted.

To connect to a standalone server, use
```
%cozo_host http://<ADDRESS>:<PORT>
%cozo_auth <AUTH_STRING>
```
where `<AUTH_STRING>` is optional if `<ADDRESS>` is a loopback address.
For how to determine the `<AUTH_STRING>`, see [here](https://github.com/cozodb/cozo/blob/main/standalone.md).

There are other magic commands you can use:

* `%cozo_run_file <PATH_TO_FILE>` runs a local file as CozoScript.
* `%cozo_run_string <VARIABLE>` runs variable containing string as CozoScript.
* `%cozo_set <KEY> <VALUE>` sets a parameter with the name <KEY> to the expression <VALUE>. The updated parameters will be used by subsequent queries.
* `%cozo_set_params <PARAM_MAP>` replace all parameters by the given expression, which must evaluate to a dictionary with string keys.
* `%cozo_clear` clears all set parameters.
* `%cozo_params` returns the parameters currently set.

## Building

This library is pure Python, but the `embedded` option depends on 
[cozo-lib-python](https://github.com/cozodb/cozo-lib-python),
which provides the `cozo_embedded` native extension package. See its documentation for how to build the native extension.

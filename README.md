# PyCozo

[![pypi](https://img.shields.io/pypi/v/pycozo)](https://pypi.org/project/pycozo/)

Python client and Jupyter helper for [CozoDB](https://www.cozodb.org).

This document describes how to set up CozoDB in Python.
To learn how to use CozoDB (CozoScript), read the [docs](https://docs.cozodb.org/en/latest/index.html).

## Install

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

### Opening a database

In-memory database:

```python
client = Client()
```

SQLite-backed (lightweight persistent storage):

```python
client = Client('sqlite', 'file.db')
```

RocksDB-backed (highly concurrent persistent storage):

```python
client = Client('rocksdb', 'file.db')
```

Connecting to a standalone server:

```python
client = Client('http', options={'host': 'http://127.0.0.1:9070'})
```

If the address is not a loopback address, you also need to provide the auth string:

```python
client = Client('http', options={'host': ..., 'auth': ...})
```

The `auth` string is in the file created when you run the standalone server.

After you are done with a client, you need to explicitly close it:

```python
client.close()
```

If you don't do this, the database resources may linger for an undetermined length of time
inside your process, even if you `del` the `client` variable.
It is OK to close a client multiple times.

### Query

```python
res = client.run(SCRIPT)
```

If you need to bind variables:

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

The embedded database exchanges data with the Python runtime directly, without going through JSON.
Hence you can pass Python bytes directly in named parameters, and bytes returned by the
database does not need any decoding.

#### Convenience methods

`Client` has convenience methods for common operations:

```python
client.put('test_rel', {'a': 1, 'b': 2, 'c': 3})
client.put('test_rel', [{'a': 3, 'b': 4, 'c': 2}, {'a': 5, 'b': 6, 'c': 7}])
client.put('test_rel', pandas.DataFrame({'a': [7, 8, 9], 'b': [9, 10, 11], 'c': [12, 13, 14]}))
# for update, only specify the keys and the values you want to update
client.update('test_rel', {'a': 7, 'b': 8})
# for rm, only the keys are needed
client.rm('test_rel', [{'a': 9}, {'a': 11}])
```

### Other operations

`Client` has other methods on it: `export_relations`, `import_relations`, `backup`,
`restore` and `import_from_backup`. See the [doc](https://docs.cozodb.org/en/latest/nonscript.html) for more details.

### Multi-statement transaction

You can intersperse CozoDB statements within a single transaction with
Python computations by using a multi-statement transaction.

```python
tx = client.multi_transact(True)  # Pass False or nothing for read-only transaction

tx.run(':create a {a}')
tx.run('?[a] <- [[1]] :put a {a}')
try:
    tx.run(':create a {a}')
except:
    pass

tx.run('?[a] <- [[2]] :put a {a}')
tx.run('?[a] <- [[3]] :put a {a}')
tx.commit()  # `tx.abort()` abandons the changes so far 
# and deletes resources associated with the transaction.

r = client.run('?[a] := *a[a]')
assert r['rows'] == [[1], [2], [3]]
```

You **must** run either `tx.commit()` or `tx.abort()` at the end, otherwise
you will have a resource leak.

### Mutation callbacks

You can register functions to run whenever mutations are made against stored relations. As an example:

```python
# callbacks must be callable and accept three arguments
def cb(op_name, new_rows, old_rows):
    # op_name is 'Put' or 'Rm'
    # new_rows is a list of lists containing the new rows (i.e., requested puts or deletes)
    # old_rows is a list of lists containing the changed rows (i.e., the old rows in the case of puts, 
    # or the rows actually deleted in the case of deletes)
    pass


# this registers the callback to run when the stored relation `test_rel` changes
cb_id = client.register_callback('test_rel', cb)

# your application logic here

# use the returned id for unregistration
# client.unregister_callback(cb_id)
```

### User-defined fixed rules

You can define your own fixed rules in Python to be used inside CozoDB queries. As an example:

```python
# custom rule implementation, must accept two arguments
def rule_impl(inputs, options):
    # inputs is a list of lists of lists, representing the input relations to the rule
    # option is a dict with string keys, representing the options passed in when the rule is called

    # You should return a list of tuples (or lists) to represent the return relation of the rule.
    # Here the returned relation has arity one.
    # If you cannot perform the computation due to any reason (wrong parameters, etc.),
    # simply raise an exception.
    return [('Nicely',), ('Done!',)]


# Actually registering the rule, the second argument is the arity, must match the actual arity
# of the relation returned by the implementation.
client.register_fixed_rule('Custom', 1, rule_impl)

r = client.run("""
    rel[u, v, w] <- [[1,2,3],[4,5,6]]
    ?[] <~ Custom(rel[], x: 1, y: null)
""")
assert r['rows'] == [['Done!'], ['Nicely']]

# Custom rules can be unregistered
client.unregister_fixed_rule('Custom')
```

## Jupyter helper

There are two versions of the helper loaded
through [magic commands](https://ipython.readthedocs.io/en/stable/interactive/magics.html)
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
If you have the embedded option enabled and you do nothing, you connect to a default
in-memory database. To override:

```
%cozo_open <ENGINE>, <PATH>
```

where `<ENGINE>` can now be `'sqlite'`, `'rocksdb'` or `'mem'`.

To connect to a standalone server, use

```
%cozo_host http://<ADDRESS>:<PORT>
%cozo_auth <AUTH_STRING>
```

where `<AUTH_STRING>` is optional if `<ADDRESS>` is a loopback address.
For how to determine the `<AUTH_STRING>`, see [here](https://github.com/cozodb/cozo/tree/main/cozoserver).

There are other magic commands you can use:

* `%cozo_run_file <PATH_TO_FILE>` runs a local file as CozoScript.
* `%cozo_run_string <VARIABLE>` runs variable containing string as CozoScript.
* `%cozo_set <KEY> <VALUE>` sets a parameter with the name `<KEY>` to the expression `<VALUE>`. The updated parameters will
  be used by subsequent queries.
* `%cozo_set_params <PARAM_MAP>` replace all parameters by the given expression, which must evaluate to a dictionary
  with string keys.
* `%cozo_clear` clears all set parameters.
* `%cozo_params` returns the parameters currently set.

## Programmatically constructing queries

You can use builders in `pycozo.builder` to construct queries programmatically.
This is both safer and more convenient than concatenating strings.
See [here](./pycozo/test_builder.py) for how to use it.

## Building

This library is pure Python, but the `embedded` option depends on
`cozo-embedded` native package described [here](https://github.com/cozodb/cozo/tree/main/cozo-lib-python).

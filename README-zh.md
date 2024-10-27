# PyCozo

[![pypi](https://img.shields.io/pypi/v/pycozo)](https://pypi.org/project/pycozo/)

[Cozo](https://www.cozodb.org) 数据库的 Python 库，支持在 Jupyter 笔记本中使用。

本文叙述的是如何安装设置库本身。有关如何使用 CozoDB（CozoScript）的信息，见 [文档](https://docs.cozodb.org/zh_CN/latest/index.html) 。

## 安装

```bash
pip install "pycozo[embedded,requests,pandas]"
```

如果想通过嵌入模式使用 CozoDB，则必须指定 `embedded` 选项；如果想通过 HTTP 请求模式连接 CozoDB 服务器，则必须指定 `requests` 选项。`pandas` 选项会安装 `pandas` 包，并在查询返回结果时将其转换为 Pandas 数据帧。在使用 Jupyter 中使用 pycozo 时建议打开 `pandas` 选项。

## Python 客户端

首先引入模块：

```python
from pycozo.client import Client
```

### 构建数据库

基于纯内存非值久化的存储引擎的数据库：

```python
client = Client()
```

基于 SQLite 引擎的数据库（占用资源小）：

```python
client = Client('sqlite', 'file.db')
```

基于 RocksDB 引擎的数据库（性能强劲，支持高并发）：

通过 HTTP 连接独立的 CozoDB 服务：

```python
client = Client('http', options={'host': 'http://127.0.0.1:9070'})
```

如果服务器地址不是本地回环地址，则需要传入验证令牌：

```python
client = Client('http', options={'host': ..., 'auth': ...})
```

验证令牌 `auth` 的内容在运行服务器时会有提示告诉如何获得。

数据库使用完后需要手动关闭：

```python
client.close()
```

如果不关闭而仅仅是将 `client` 变量 `del`，则相关的原生资源不会被释放。多次关闭同一个数据库不会报错。

### 查询

```python
res = await client.run(SCRIPT)
```

需要绑定变量时：

```python
res = await client.run('?[] <- [[$name]]', {'name': 'Python'})
```

如果 `pandas` 模块可用，则结果通过数据帧的形式返回。如果你安装了 `pandas` 但是不希望返回数据帧，则可以在创建数据库时使用 `dataframe=False` 选项，在此情况下返回的是一个字典，字典里的 `'rows'` 字段包含返回行，而 `'header'` 包含行的标头。

当查询出错时，会抛出异常，可以通过以下方式显示更加友好的异常信息：

```python
try:
    res = await client.run('BAD!')
except Exception as e:
    print(repr(e))
```

`Client` 是线程安全的，但是多个不同的进程不可以同时访问同一个嵌入式数据库（接入同一个独立服务是可以的）。

在嵌入模式下，`Client` 执行查询时会释放 [GIL](https://wiki.python.org/moin/GlobalInterpreterLock) ，因此与原生的 Python 程序不同，多线程查询确实会并行查询。

嵌入式的数据库与 Python 运行时直接交换数据（不会经过转化为 JSON 的过程）。因此你可以直接传入字节数组为参数，且查询返回的字节数组也不需要解码。


### 其它操作

`Client` 类有有以下方法：`export_relations`、`import_relations`、`backup`、`restore`、 `import_from_backup`，其作用见 [此文档](https://docs.cozodb.org/zh_CN/latest/nonscript.html) 。

### 多语句事务

你可以将同一个事务中的多个查询语句与 Python 代码交叉执行，如下例：

```python
tx = client.multi_transact(True) # False 或不传参数代表只读事务

tx.run(':create a {a}')
tx.run('?[a] <- [[1]] :put a {a}')
try:
    tx.run(':create a {a}')
except:
    pass

tx.run('?[a] <- [[2]] :put a {a}')
tx.run('?[a] <- [[3]] :put a {a}')
tx.commit() # `tx.abort()` 会舍弃所有更改并删除事务相关联的系统资源

r = client.run('?[a] := *a[a]')
assert r['rows'] == [[1], [2], [3]]
```

事务结束时，你 **必须** 调用 `tx.commit()` 或 `tx.abort()` ，否则系统资源会泄露。

### 更改回调

你可以设置在存储表被更改时会被调用的回调函数。例子：

```python
# 回调函数必须接受三个参数
def cb(op_name, new_rows, old_rows):
    # op_name 是 'Put' 或 'Rm'
    # new_rows 是一个包含列表的列表，包含新的行（要求插入或删除的行）
    # old_rows 是一个包含列表的列表，包含旧的行（被更改的行的旧值，或被删除的行）
    pass

# 回调函数在存储表 test_rel 被更改时会被调用
cb_id = await client.register_callback('test_rel', cb)

# 程序的其它逻辑

# 注册回调函数时返回的值可以用来删除注册
# client.unregister_callback(cb_id)
```

### 自定义固定规则

你可以使用 Python 来自定义固定规则。例子：

```python
# 固定规则的实现，必须接受两个参数
def rule_impl(inputs, options):
    # inputs 是一个列表的列表的列表，含有固定规则被调用时传入的表
    # option 是一个字符串键的字典，包含被调用时传入的参数
    
    # 必须返回列表（或元组）的列表作为固定规则的返回表。如果无法返回（比如参数错误等），直接抛出异常即可。
    return [('Nicely',), ('Done!',)]

# 注册固定规则。第二个参数是返回列表的列数，必须与实现中返回的列数相同。
client.register_fixed_rule('Custom', 1, rule_impl)

r = await client.run("""
    rel[u, v, w] <- [[1,2,3],[4,5,6]]
    ?[] <~ Custom(rel[], x: 1, y: null)
""")
assert r['rows'] == [['Done!'], ['Nicely']]

# 取消注册的固定规则
client.unregister_fixed_rule('Custom')
```

## Jupyter 工具

通过 [魔法命令](https://ipython.readthedocs.io/en/stable/interactive/magics.html) 可激活两种不同的 Jupyter 工具，两种工具都可以让你直接查询数据库。第一种是：

```
%load_ext pycozo.ipyext_direct
```

在这种模式下，所有单元格都默认会被作为 CozoScript 执行，除非整个单元格以 `%` 开头。如果单元格的第一行的内容是 `%%py`，则余下的行作为 Python 代码执行。

第二种是：

```
%load_ext pycozo.ipyext
```

在这种模式下，只有在单元格第一行的内容为 `%%cozo` 时，余下的内容才会被作为 CozoScript 执行，因此这种模式适用于 Python 代码比 CozoScript 多的情况。

执行查询之前，先要打开数据库。如果你安装了嵌入模式而没做额外的事情，则默认会打开纯内存非持久化的数据库。你可以执行

```
%cozo_open <ENGINE>, <PATH>
```

来选择打开哪种数据库以及数据文件的路径。这里 `<ENGINE>` 可以是 `'sqlite'`、`'rocksdb'` 或 `'mem'`。

如果需要连接到独立的服务，则执行

```
%cozo_host http://<ADDRESS>:<PORT>
%cozo_auth <AUTH_STRING>
```

若 `<ADDRESS>` 指向本地回传地址，则 `<AUTH_STRING>` 可省略。在其它情况下，如何获取其需要的值请参见 [这里](https://github.com/cozodb/cozo/blob/main/cozoserver/README-zh.md)（或 [国内镜像](这里](https://gitee.com/cozodb/cozo/tree/main/cozoserver)）.

还有一些其它的魔法命令可以使用：

* `%cozo_run_file <PATH_TO_FILE>` 运行一个包含 CozoScript 内容的本地文件。
* `%cozo_run_string <VARIABLE>` 运行一个变量或常量中包含的 CozoScript 文本内容。
* `%cozo_set <KEY> <VALUE>` 将查询参数 `<KEY>` 设为 `<VALUE>`，设置的参数可以在接下来的查询中使用。
* `%cozo_set_params <PARAM_MAP>` 以给出的字典替换当前所有的参数。
* `%cozo_clear` 清空当前设置的所有参数。
* `%cozo_params` 返回当前设置的所有参数。

## 编译

这个库本身是纯 Python 写成的，但是其 `embedded` 选项依赖于 `cozo-embedded` 库，[在此](https://github.com/cozodb/cozo/blob/main/cozo-lib-python/README-zh.md)（[国内镜像](https://gitee.com/cozodb/cozo/tree/main/cozo-lib-python)）有叙述。

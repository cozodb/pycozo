#  Copyright 2022, The Cozo Project Authors.
#
#  This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0.
#  If a copy of the MPL was not distributed with this file,
#  You can obtain one at https://mozilla.org/MPL/2.0/.
from pycozo import Client
from pycozo.client import QueryException


def test_client():
    client = Client(dataframe=False)

    collected = []

    def cb(a, b, c):
        collected.append((a, b, c))

    inputs = None
    options = None

    def rule_impl(i, o):
        nonlocal inputs, options
        inputs = i
        options = o
        return [('Nicely',), ('Done!',)]

    cb_id = client.register_callback('test', cb)
    client.register_fixed_rule('Holy', 1, rule_impl)
    client.run("?[a, b, c] <- [[1,2,3]] :create test {a => b, c}")
    r = client.run("""
        rel[u, v, w] <- [[1,2,3],[4,5,6]]
        ?[] <~ Holy(rel[], x: 1, y: null)
    """)
    assert r['rows'] == [['Done!'], ['Nicely']]
    client.unregister_callback(cb_id)
    client.unregister_fixed_rule('Holy')
    assert collected == [('Put', [[1, 2, 3]], [])]
    assert inputs == [[[1, 2, 3], [4, 5, 6]]]
    assert options == {'x': 1, 'y': None}
    exported = client.export_relations(['test'])
    assert exported['test']['rows'] == [[1, 2, 3]]
    raised = False
    try:
        client.run("""
                rel[u, v, x] <- [[1,2,3],[4,5,6]]
                
                
                ?[] <~ Holy(rel[], x: 1, y: null)
            """)
    except QueryException:
        raised = True
    assert raised

    data = b'abcxyz'
    r = client.run("?[z] <- [[$z]]", {'z': data})
    assert r['rows'][0][0] == data

    tx = client.multi_transact(True)
    tx.run(':create a {a}')
    tx.run('?[a] <- [[1]] :put a {a}')
    try:
        tx.run(':create a {a}')
    except:
        pass
    tx.run('?[a] <- [[2]] :put a {a}')
    tx.run('?[a] <- [[3]] :put a {a}')
    tx.commit()
    r = client.run('?[a] := *a[a]')
    assert r['rows'] == [[1], [2], [3]]


if __name__ == '__main__':
    test_client()

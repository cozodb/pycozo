#  Copyright 2022, The Cozo Project Authors.
#
#  This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0.
#  If a copy of the MPL was not distributed with this file,
#  You can obtain one at https://mozilla.org/MPL/2.0/.
from pycozo import Client

if __name__ == '__main__':
    client = Client()


    def cb(a, b, c):
        print("python callback called!")
        print(a, b, c)
        print("python callback finished!")


    def xxx(inputs, zzz):
        print(inputs)
        print(zzz)
        return [('Nicely',), ('Done!',)]


    cb_id = client.register_callback('test', cb)
    client.register_fixed_rule('Holy', 1, xxx)
    print(client.run("?[a, b, c] <- [[1,2,3]] :create test {a => b, c}"))
    print(client.run("""
        rel[u, v, w] <- [[1,2,3],[4,5,6]]
        ?[] <~ Holy(rel[], x: 1, y: null)
    """))
    print(cb_id)
    client.unregister_callback(cb_id)
    client.unregister_fixed_rule('Holy')

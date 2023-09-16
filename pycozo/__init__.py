#  Copyright 2022, The Cozo Project Authors.
#
#  This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0.
#  If a copy of the MPL was not distributed with this file,
#  You can obtain one at https://mozilla.org/MPL/2.0/.

"""
>>> from pycozo.client import Client
>>> db = Client()
>>> db.relations()
Empty DataFrame
Columns: [name, arity, access_level, n_keys, n_non_keys, n_put_triggers, n_rm_triggers, n_replace_triggers, description]
Index: []
>>> db.create('users_table', 'username', 'email', 'is_active')
  status
0     OK
>>> db.relations()
          name  arity access_level  n_keys  n_non_keys  n_put_triggers  n_rm_triggers  n_replace_triggers description
0  users_table      3       normal       3           0               0              0                   0            
"""

from pycozo.client_patch import Client

# pycozo.py
from pycozo import *  # noqa
from pycozo import client

""" Thin wrapper for pycozo.client.Client adding create(), relations(), 
>>> db = Client()
>>> db.relations()
Empty DataFrame
Columns: [name, arity, access_level, n_keys, n_non_keys, n_put_triggers, n_rm_triggers, n_replace_triggers, description]
Index: []
>>> db.create('ABCs', *list('ABCDEFG'))
  status
0     OK
>>> db.create('table123', *('col1 col2 col3'.split()))
  status
0     OK
>>> db.relations()
       name  arity access_level  n_keys  n_non_keys  n_put_triggers  n_rm_triggers  n_replace_triggers description
0      ABCs      7       normal       7           0               0              0                   0            
1  table123      3       normal       3           0               0              0                   0            
>>> db.columns().keys()
dict_keys(['ABCs', 'table123'])
>>> db.columns('table123')
  column  is_key  index  type  has_default
0   col1    True      0  Any?        False
1   col2    True      1  Any?        False
2   col3    True      2  Any?        False
>>> db.columns()['ABCs']
  column  is_key  index  type  has_default
0      A    True      0  Any?        False
1      B    True      1  Any?        False
2      C    True      2  Any?        False
3      D    True      3  Any?        False
4      E    True      4  Any?        False
5      F    True      5  Any?        False
6      G    True      6  Any?        False
>>> db.create('table123', *'col1 col2 col3'.split())
>>> db.create('users_table', *'username email is_active'.split())
  status
0     OK
>>> df.relations
>>> db.relations
<bound method Client.relations of <nlpia2.pycozo_enhanced_client.Client object at 0x7f43f2823cd0>>
>>> db.relations()
          name  arity access_level  n_keys  n_non_keys  n_put_triggers  n_rm_triggers  n_replace_triggers description
0         ABCs      7       normal       7           0               0              0                   0            
1     table123      3       normal       3           0               0              0                   0            
2  users_table      3       normal       3           0               0              0                   0            
"""


class Client(client.Client):
    """ PyCozo Client wrapper with .create(), .relations(), .columns() methods

    create(name, *column_names): create a stored (persistent) relation (table)
    relations(name): DataFrame describing relation (table) schemas 
    columns(name): DataFrame describing the columns of the named relation (tables) with their names, arity, etc 

    TODO:
      remove(name): delete a stored (persistent) relation (relational DB table)
      query(name): run arbitrary cozo "select * where " query strings
    """

    def create(self, name, *args, **kwargs):
        """ Create a new empty table with the table name and column labels indicated (positional args) 

        >>> db = Client()
        >>> db.create('ABCs', *list('ABCDEFG'))
          status
        0     OK
        >>> db.relations()
               name  arity access_level  n_keys  n_non_keys  n_put_triggers  ... description
        0      ABCs      7       normal       7           0               0
        """
        # pk_name = kwargs.get('pk', kwargs.get('index', kwargs.get('id', None)))
        # if pk_name is not None:
        #     self.run(f':create {name} {{{pk_name} => {", ".join([c for c in args])}}}')
        return self.run(f':create {name} {{{", ".join([c for c in args])}}}')

    def relations(self, name=None):
        """ Return DataFrame listing all the relations (tables) with their names, arity, etc

        >>> db = Client()
        >>> db.relations()
        Empty DataFrame
        Columns: [name, arity, access_level, n_keys, n_non_keys ...description]
        Index: []
        >>> db.create('ABCs', *list('ABCDEFG'))
          status
        0     OK
        >>> db.create('table123', *('col1 col2 col3'.split()))
          status
        0     OK
        >>> db.relations()
               name  arity access_level  n_keys  n_non_keys  n_put_triggers  n_rm_triggers  n_replace_triggers description
        0      ABCs      7       normal       7           0               0              0                   0            
        1  table123      3       normal       3           0               0              0                   0            
        """
        if name is None:
            return self.run('::relations')
        df = self.relations(name=None)
        if isinstance(name, str):
            return df.loc[df['name'] == name].copy()
        return df.loc[df['name'].isin(name)].copy()

    def columns(self, name=None):
        """ DataFrame of columns for the named relation (tables) with their names, arity, etc 

        If name is None (default) return a dict of DataFrames, one DataFrame per relation (table)
        """
        if name is None:
            return {n: self.columns(name=str(n)) for n in self.relations()['name']}
        return self.run(f'::columns {name}')

    def query(self, query_str):
        """ Execute a raw cozodb query string """
        return self.run(f'?[] {query_str}')

    def remove(self, name):
        """ Delete the named relation (table) """
        return self.run(f'::remove {name}')


client.Client = Client






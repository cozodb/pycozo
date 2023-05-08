#  Copyright 2023, The Cozo Project Authors.
#
#  This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0.
#  If a copy of the MPL was not distributed with this file,
#  You can obtain one at https://mozilla.org/MPL/2.0/.

from .builder import *


def test_build():
    rules = [
        ConstantRule(RuleHead('parent', []),
                     Const([['abraham', 'isaac'],
                            ['isaac', 'jakob'],
                            ['jakob', 'joseph']])),
        InlineRule(RuleHead('grandparent', ['A', 'C']),
                   [RuleApply('parent', ['A', 'B']), RuleApply('parent', ['B', 'C'])], ),
        InlineRule(RuleHead('great_grandparent', ['A', 'D']),
                   [RuleApply('parent', ['A', 'B']), RuleApply('parent', ['B', 'C']), RuleApply('parent', ['C', 'D'])]),
        InlineRule(RuleHead('?', ['who']),
                   [RuleApply('great_grandparent', [Const('abraham'), 'who'])])
    ]
    program = InputProgram(rules, limit=10)
    print(program)
    print('---')

    rules = [
        ConstantRule(RuleHead('r1', []), Const([[1, 'a'], [2, 'b']])),
        ConstantRule(RuleHead('r2', []), Const([[2, 'B'], [3, 'C']])),
        InlineRule(RuleHead('?', ['l1', 'l2']), [
            RuleApply('r1', ['a', 'l1']),
            RuleApply('r2', ['a', 'l2'])
        ])
    ]
    program = InputProgram(rules, store_relation=(StoreOp.CREATE, InputRelation('stored', ['l1', 'l2'])))
    print(program)
    print('---')

    rules = [
        InlineRule(RuleHead('?', ['a', 'b']), [
            StoredRuleNamedApply('stored', {'l2': 'b', 'l1': 'a'}),
        ])
    ]
    program = InputProgram(rules)
    print(program)
    print('---')

    rules = [
        ConstantRule(RuleHead('?', []), InputList([
            InputList([
                OpApply('add', [Const(1), Const(2)]),
                OpApply('div', [Const(3), Const(4)]),
                OpApply('eq', [Const(5), Const(6)]),
                OpApply('gt', [Const(7), Const(8)]),
                OpApply('or', [Const(True), Const(False)]),
                OpApply('lowercase', [Const('HELLO')]),
                OpApply('rand_float'),
                OpApply('union', [Const([1, 2, 3]), Const([3, 4, 5]), Const([5, 6, 7])]),
            ]),
        ])),
    ]
    program = InputProgram(rules)
    print(program)
    print('---')

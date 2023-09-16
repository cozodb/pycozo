#  Copyright 2023, The Cozo Project Authors.
#
#  This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0.
#  If a copy of the MPL was not distributed with this file,
#  You can obtain one at https://mozilla.org/MPL/2.0/.
import json
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Union


@dataclass
class Var:
    name: str

    def __str__(self):
        return self.name


@dataclass
class Const:
    value: Any

    def __str__(self):
        return json.dumps(self.value)


@dataclass
class InputParam:
    name: str

    def __str__(self):
        return '$' + self.name


Expr = Union[str | Var, Const, InputParam, 'InputObject', 'InputList', 'OpApply']


@dataclass
class InputObject:
    kvs: dict[str, Expr]

    def __str__(self):
        return '{' + ', '.join(f'{k}: {v}' for k, v in self.kvs) + '}'


@dataclass
class InputList:
    items: list[Expr]

    def __str__(self):
        return '[' + ', '.join(map(str, self.items)) + ']'


@dataclass
class OpApply:
    op: str
    args: list[Expr] = field(default_factory=list)

    def __str__(self):
        return f'{self.op}({", ".join(map(str, self.args))})'


class StoreOp(Enum):
    CREATE = 'create'
    REPLACE = 'replace'
    PUT = 'put'
    UPDATE = 'update'
    RM = 'rm'
    ENSURE = 'ensure'
    ENSURE_NOT = 'ensure_not'

    def __str__(self):
        return ':' + self.value


@dataclass
class Sorter:
    column: str
    aggr: str | None = None
    reverse: bool = False

    def __str__(self):
        ret = ""
        if self.reverse:
            ret += "-"
        if self.aggr:
            ret += f"{self.aggr}("
        ret += self.column
        if self.aggr:
            ret += ")"
        return ret


@dataclass
class RuleHead:
    name: str
    args: list[str | tuple[str, str]]

    def __str__(self):
        ret = self.name + "["
        for arg in self.args:
            if isinstance(arg, tuple):
                ret += f"{arg[0]}({arg[1]}), "
            else:
                ret += f"{arg}, "
        if len(self.args) > 0:
            ret = ret[:-2]
        ret += "]"
        return ret


@dataclass
class InputRelation:
    name: str
    keys: list[str]
    values: list[str] = field(default_factory=list)

    def __str__(self):
        ret = self.name + ' {'
        for k in self.keys:
            ret += f'{k}, '

        if len(self.values) > 0:
            ret += ' => '
            for v in self.values:
                ret += f'{v}, '
        if ret.endswith(', '):
            ret = ret[:-2]
        ret += ' }'
        return ret


@dataclass
class RuleApply:
    name: str
    args: list[Expr] = field(default_factory=list)

    def __str__(self):
        return f'{self.name}[{", ".join(map(str, self.args))}]'


@dataclass
class StoredRuleApply:
    name: str
    args: list[Expr] = field(default_factory=list)
    validity: Expr | None = None

    def __str__(self):
        return f'*{self.name}[{", ".join(map(str, self.args))} {"| @" + str(self.validity) if self.validity else ""}]'


@dataclass
class StoredRuleNamedApply:
    name: str
    args: dict[str, Expr]
    validity: Expr | None = None

    def __str__(self):
        ret = '*' + self.name + '{'
        for k, v in self.args.items():
            ret += f'{k}: {v}, '
        if self.validity:
            ret += f'| @{self.validity}'
        if ret.endswith(', '):
            ret = ret[:-2]
        ret += '}'
        return ret


@dataclass
class ProximityApply:
    name: str
    args: dict[str, Expr]
    params: dict[str, Expr]

    def __str__(self):
        ret = '~' + self.name + '{'
        for k, v in self.args.items():
            ret += f'{k}: {v}, '
        ret += '| '
        for k, v in self.params.items():
            ret += f'{k}: {v}, '
        ret += '}'
        return ret


@dataclass
class Conjunction:
    atoms: list['Atom']

    def __str__(self):
        ret = ''
        for part in self.atoms:
            if ret != '':
                ret += ', (' + str(part) + ')'
            else:
                ret += '(' + str(part) + ')'


@dataclass
class Disjunction:
    atoms: list['Atom']

    def __str__(self):
        ret = ''
        for part in self.atoms:
            if ret != '':
                ret += ' or (' + str(part) + ')'
            else:
                ret += '(' + str(part) + ')'


@dataclass
class Negation:
    atom: 'Atom'

    def __str__(self):
        return 'not (' + str(self.atom) + ')'


@dataclass
class Bind:
    name: str
    expr: Expr
    multi_bind: bool = False

    def __str__(self):
        return f'{self.name} {"in" if self.multi_bind else "="} {self.expr}'


@dataclass
class Cond:
    clauses: list[(Expr, Expr)]

    def __str__(self):
        return 'cond ' + ', '.join(f'{k}, {v}, ' for k, v in self.clauses)


@dataclass
class RawAtom:
    script: str

    def __str__(self):
        return f'({self.script})'


Atom = Expr | Cond | Bind | RuleApply | StoredRuleApply | StoredRuleNamedApply | Conjunction | Disjunction | Negation | RawAtom


@dataclass
class FixedRule:
    head: RuleHead
    rule_name: str
    inputs: list[RuleApply | StoredRuleApply | StoredRuleNamedApply] = field(default_factory=list)
    parameters: dict[str, Expr] = field(default_factory=dict)

    def __str__(self):
        ret = f'{self.head} <~\n    {self.rule_name}('
        for rule in self.inputs:
            ret += str(rule) + ', '
        for k, v in self.parameters.items():
            ret += f'{k}: {v}, '
        ret += ')\n'
        return ret


@dataclass
class InlineRule:
    head: RuleHead
    atoms: list[Atom]

    def __str__(self):
        ret = f'{self.head} :=\n'
        for atom in self.atoms[:-1]:
            ret += '    ' + str(atom) + ',\n'
        ret += '    ' + str(self.atoms[-1]) + '\n'
        return ret


@dataclass
class ConstantRule:
    head: RuleHead
    body: Expr

    def __str__(self):
        return f'{self.head} <-\n    {self.body}\n'


@dataclass
class InputProgram:
    rules: list[ConstantRule | InlineRule | FixedRule]
    limit: int | None = None
    offset: int | None = None
    sorters: list[Sorter] = field(default_factory=list)
    store_relation: tuple[StoreOp, InputRelation] | None = None

    def __str__(self):
        ret = ''
        for rule in self.rules:
            ret += str(rule)
        ret += '\n'
        if self.limit:
            ret += f':limit {self.limit}\n'
        if self.offset:
            ret += f':offset {self.offset}\n'
        if len(self.sorters) > 0:
            ret += ':sort ' + ', '.join(map(str, self.sorters)) + '\n'
        if self.store_relation:
            ret += f'{self.store_relation[0]} {self.store_relation[1]}' + '\n'
        return ret.strip()

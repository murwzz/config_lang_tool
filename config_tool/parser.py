import json
from dataclasses import dataclass
from typing import Any, Dict, Set

from lark import Lark, Transformer, v_args
from lark.exceptions import LarkError, UnexpectedInput

from .errors import ConfigSyntaxError, ConfigSemanticError


_GRAMMAR = r"""
start: (_NL | stmt)*

stmt: var_decl _NL*

var_decl: "var" NAME value

?value: const_ref
      | array
      | STRING
      | NUMBER

const_ref: "^[" NAME "]"
array: "(" [value ("," value)*] ")"

NAME: /[_a-z]+/

// Разрешаем:
// 10, 10., 10.5, .5, 1e3, .5E+3, -2.0e-2
NUMBER: /[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?/

%import common.ESCAPED_STRING -> STRING
%import common.NEWLINE -> _NL
%import common.WS_INLINE

// Многострочный комментарий: #| ... |#
COMMENT_ML: /#\|(.|\n)*?\|#/
// На всякий случай добавим однострочный комментарий: # ...
COMMENT_SL: /#[^\n]*/

%ignore WS_INLINE
%ignore COMMENT_ML
%ignore COMMENT_SL
"""


@dataclass
class Ref:
    name: str


@v_args(inline=True)
class _BuildTree(Transformer):
    def _NL(self, tok):
        return None

    def start(self, *items):
        return [i for i in items if i is not None]

    def NAME(self, tok):
        return str(tok)

    def NUMBER(self, tok):
        # Все числа переводим во float, чтобы не усложнять.
        return float(str(tok))

    def STRING(self, tok):
        # Lark даёт строку как "...." с экранированием, делаем real value через json.loads
        return json.loads(str(tok))

    def const_ref(self, name):
        return Ref(name=name)

    def array(self, *items):
        return list(items)

    def var_decl(self, name, value):
        return ("var", name, value)

    def stmt(self, item):
        return item


_parser = Lark(
    _GRAMMAR,
    parser="lalr",
    maybe_placeholders=False,
)


def _resolve_value(value: Any, env: Dict[str, Any], stack: Set[str]) -> Any:
    """Рекурсивно вычисляет значение с подстановкой ссылок ^[name]."""
    if isinstance(value, Ref):
        n = value.name
        if n not in env:
            raise ConfigSemanticError(f"Неизвестная константа: {n}")
        if n in stack:
            cycle = " -> ".join(list(stack) + [n])
            raise ConfigSemanticError(f"Циклическая зависимость: {cycle}")
        stack.add(n)
        resolved = _resolve_value(env[n], env, stack)
        env[n] = resolved  # мемоизация
        stack.remove(n)
        return resolved

    if isinstance(value, list):
        return [_resolve_value(v, env, stack) for v in value]

    return value


def parse_config(text: str) -> Dict[str, Any]:
    """Парсит текст учебного языка и возвращает dict для JSON."""
    try:
        tree = _parser.parse(text)
    except UnexpectedInput as e:
        raise ConfigSyntaxError(f"Синтаксическая ошибка: строка {e.line}, столбец {e.column}") from e
    except LarkError as e:
        raise ConfigSyntaxError("Синтаксическая ошибка") from e

    items = _BuildTree().transform(tree)

    env: Dict[str, Any] = {}
    for it in items:
        if not it:
            continue
        kind, name, value = it
        if kind == "var":
            env[name] = value

    # Вычисляем ссылки
    for k in list(env.keys()):
        env[k] = _resolve_value(env[k], env, set())

    return env

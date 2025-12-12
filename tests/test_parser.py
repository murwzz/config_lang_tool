import pytest

from config_tool.parser import parse_config
from config_tool.errors import ConfigSemanticError, ConfigSyntaxError


def test_numbers_and_strings():
    cfg = '''
    var a 10
    var b 10.5
    var c .5E+3
    var s "hello"
    '''
    out = parse_config(cfg)
    assert out["a"] == 10.0
    assert out["b"] == 10.5
    assert out["c"] == 500.0
    assert out["s"] == "hello"


def test_arrays_nested():
    cfg = '''
    var arr ( 1, 2, ( 3, 4 ), "x" )
    '''
    out = parse_config(cfg)
    assert out["arr"] == [1.0, 2.0, [3.0, 4.0], "x"]


def test_const_refs():
    cfg = '''
    var x 2
    var y ( ^[x], 3 )
    var z ^[y]
    '''
    out = parse_config(cfg)
    assert out["y"] == [2.0, 3.0]
    assert out["z"] == [2.0, 3.0]


def test_unknown_const():
    cfg = '''
    var y ^[nope]
    '''
    with pytest.raises(ConfigSemanticError):
        parse_config(cfg)


def test_cycle():
    cfg = '''
    var a ^[b]
    var b ^[a]
    '''
    with pytest.raises(ConfigSemanticError):
        parse_config(cfg)


def test_comments_ignored():
    cfg = '''
    #| multi
    line
    |#
    var a 1
    # one-line comment
    var b ( 2, 3 )
    '''
    out = parse_config(cfg)
    assert out["a"] == 1.0
    assert out["b"] == [2.0, 3.0]


def test_syntax_error():
    cfg = '''
    var a ( 1, 2
    '''
    with pytest.raises(ConfigSyntaxError):
        parse_config(cfg)

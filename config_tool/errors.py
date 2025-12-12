class ConfigToolError(Exception):
    """Базовая ошибка инструмента."""


class ConfigSyntaxError(ConfigToolError):
    """Ошибка синтаксиса входного файла."""


class ConfigSemanticError(ConfigToolError):
    """Ошибка семантики (необъявленная константа, циклы и т.п.)."""

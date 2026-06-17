# app/__init__.py
# Monkey-patch SQLAlchemy typing for Python 3.14 compatibility
# Must run BEFORE any SQLAlchemy/SQLModel import
import sqlalchemy.util.typing as _sqla_typing
import typing as _typing

_orig_make_union = _sqla_typing.make_union_type

def _patched_make_union_type(*types):
    if len(types) == 1 and isinstance(types[0], tuple):
        types = types[0]
    return _typing.Union[types]

_sqla_typing.make_union_type = _patched_make_union_type

from typing import (
    Any,
    Union,
    TypeVar,
    Optional,
    Callable,
    Iterable,
    Coroutine,
    TYPE_CHECKING
)
from copy import copy
import inspect

T = TypeVar('T')
Func_T = TypeVar('Func_T', bound=Callable)

class _MissingSentinel:

    __slots__ = ()

    def __bool__(self):
        return False

    def __eq__(self, other):
        return False

    def __repr__(self):
        return '...'


MISSING: Any = _MissingSentinel()


def find(predicate: Callable[[T], bool], iterable: Iterable[T]) -> Optional[T]:
    for i in iterable:
        if predicate(i):
            return i
    return None


def get(iterable: Iterable[T], conditions: dict[str, Any]) -> Optional[T]:

    for item in iterable:
        flags: list[bool] = []

        for k, v in conditions.items():
            var = copy(item)

            for attr in k.split('.'):
                var = getattr(var, attr)

            flags.append(var==v)

        if all(flags):
            return item

    return None


async def maybe_coroutine(
    func: Callable[[T], Union[T, Coroutine[Any, Any, T]]],
    *args,
    **kwargs
) -> Coroutine[Any, Any, T]:

    if inspect.iscoroutinefunction(func):
        return await func(*args, **kwargs)
    else:
        return func(*args, **kwargs)


class Content:

    __slots__ = (
        '__description',
        'extra'
    )


    if TYPE_CHECKING:
        __description: str
        extra: Any

    def __init__(self, **kwargs):
        self.__description = kwargs.get('description')
        self.extra = kwargs.get('extra')

    def to_dict(self) -> dict[str, Any]:
        return {
            "description": self.description,
            "extra": self.extra,
        }

    @property
    def description(self) -> Optional[str]:
        return self.__description



class Docs:

    __slots__ = (
        '__data'
    )

    if TYPE_CHECKING:
        __data: dict[str, Content]

    def __init__(self) -> None:
        self.__data = {}

    @property
    def data(self) -> dict[str, Content]:
        return self.__data

    def to_dict(self) -> dict[str, dict[str, Any]]:
        return {k: v.to_dict() for k, v in self.__data.items()}

    def __str__(self) -> str:
        return str(self.to_dict())


    def register_doc(self, extra: Optional[Any] = None) -> Func_T:

        def decorator(func: Func_T):
            self.__data[func.__qualname__] = Content(
                description=func.__doc__,
                extra=extra
            )
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper

        return decorator

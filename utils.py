from typing import (
    Any,
    Union,
    TypeVar,
    NoReturn,
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
CoroutineFunc = Callable[..., Coroutine[Any, Any, T]]
MaybeCoroutineFunc = Callable[[T], Union[T, Coroutine[Any, Any, T]]]


class _MissingSentinel:
    """A sentinel object to represent a missing value."""

    __slots__ = ()

    def __bool__(self):
        return False

    def __eq__(self, other):
        return False

    def __repr__(self):
        return '...'


MISSING: Any = _MissingSentinel()


def find(predicate: Callable[[T], bool], iterable: Iterable[T]) -> Optional[T]:
    """A helper to return the first element found in the sequence
    that meets the predicate.

    Parameters
    ----------
    predicate : Callable[[T], bool]
        The predicate to check against.
    iterable : Iterable[T]
        The iterable to search through.
    """

    for i in iterable:
        if predicate(i):
            return i
    return None


def get(iterable: Iterable[T], conditions: dict[str, Any]) -> Optional[T]:
    """A helper to return the first element found in the iterable

    Parameters
    ----------
    iterable : Iterable[T]
        The iterable to search through.
    conditions : dict[str, Any]
        The conditions to check against.

    Returns
    -------
    Optional[T]
        The first element found in the iterable that meets the conditions.

    To have a nested attribute search (i.e. search by ``x.y``) then
    pass in ``x.y`` as the conditions' dict key.


    Sample
    ------
    >>> class A:
    >>>     def __init__(self, a, b):
    >>>         self.a = a
    >>>         self.b = b
    >>>
    >>> class B:
    >>>
    >>>     def __init__(self, c, d):
    >>>         self.c = c
    >>>         self.d = d
    >>>
    >>> var = get([A(B(1, 2), 3), A(B(4, 5), 6)], {'a.c': 1, 'b': 3})    # returns A(B(1, 2), 3)
    >>> var_2 = get([A(B(1, 2), 3), A(B(4, 5), 6)], {'a.c': 4, 'b': 6})  # returns A(B(4, 5), 6)
    """

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
    """A helper to return the result of a function or coroutine.

    Parameters
    ----------
    func : Callable[[T], Union[T, Coroutine[Any, Any, T]]]
        The function or coroutine to run.

    Returns
    -------
    Coroutine[Any, Any, T]
        The result of the function or coroutine.
    """

    if inspect.iscoroutinefunction(func):
        return await func(*args, **kwargs)
    else:
        return func(*args, **kwargs)


class Content:
    """This class represents the content of a documentation."""

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
    """This class represents the documentation of functions."""

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
        '''A decorator to register the documentation of a function.

        Parameters
        ----------
        extra : Optional[Any], optional
            extra information to register, by default None

        Returns
        -------
        Func_T
            The decorated function.

        Sample
        ------
        >>> docs = Docs()
        >>>
        >>> @docs.register_doc()
        >>> def func():
        >>>     """This is a function."""
        >>>     pass
        >>>
        >>> print(docs) # {'func': {'description': 'This is a function.', 'extra': None}}
        '''

        def decorator(func: Func_T):
            self.__data[func.__qualname__] = Content(
                description=func.__doc__,
                extra=extra
            )
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper

        return decorator


class ErrorHandler:
    """This class represents the error handler

    Sample
    ------
    >>> class MyErrorHandler(ErrorHandler):
    >>>
    >>>     def on_error(self, error: Exception, func: Callable, *args, **kwargs) -> None:
    >>>         '''your code here'''
    >>>
    >>> @MyErrorHandler.error_handling(ignore_exception=False)
    >>> def test(a, b, c):
    >>>    ...
    """

    def on_error(error: Exception, func: Callable, *args, **kwargs) -> NoReturn:
        """This function is called when an error is raised.

        Parameters
        ----------
        error : Exception
            The error that was raised.
        func : Callable
            The function that was called.
        args : Any
            The arguments passed to the function.
        kwargs : Any
        """
        raise error


    @classmethod
    def error_handling(cls, ignore_exception: bool = False) -> Func_T:
        """A decorator to handle errors.

        Parameters
        ----------
        ignore_exception : bool, optional
            Whether or not to ignore exceptions, by default False

        Returns
        -------
        Func_T
            The decorated function.
        """

        def decorator(func: Func_T):

            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if ignore_exception:
                        return
                    else:
                        cls.on_error(e, func, *args, **kwargs)

            return wrapper

        return decorator

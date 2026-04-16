import functools
import json
import time
from datetime import UTC, datetime
from typing import Any, NoReturn, ParamSpec, Protocol, TypeVar
from urllib.request import urlopen

INVALID_CRITICAL_COUNT = "Breaker count must be positive integer!"
INVALID_RECOVERY_TIME = "Breaker recovery time must be positive integer!"
VALIDATIONS_FAILED = "Invalid decorator args."
TOO_MUCH = "Too much requests, just wait."


P = ParamSpec("P")
R_co = TypeVar("R_co", covariant=True)


class CallableWithMeta(Protocol[P, R_co]):
    __name__: str
    __module__: str

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R_co: ...


class BreakerError(Exception):
    def __init__(self, message: str, func_name: str, block_time: datetime):
        super().__init__(message)
        self.func_name = func_name
        self.block_time = block_time


class CircuitBreaker:
    def __init__(
        self,
        critical_count: int = 5,
        time_to_recover: int = 30,
        triggers_on: type[Exception] = Exception,
    ):
        errors = []
        if not isinstance(critical_count, int) or critical_count <= 0:
            errors.append(ValueError(INVALID_CRITICAL_COUNT))

        if not isinstance(time_to_recover, int) or time_to_recover <= 0:
            errors.append(ValueError(INVALID_RECOVERY_TIME))

        if errors:
            raise ExceptionGroup(VALIDATIONS_FAILED, errors)

        self.critical_count = critical_count
        self.time_to_recover = time_to_recover
        self.triggers_on = triggers_on

        self._fail_count = 0
        self._last_fail_time: float | None = None

    def __call__(self, func: CallableWithMeta[P, R_co]) -> CallableWithMeta[P, R_co]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R_co:
            self._check_state(func)
            try:
                result = func(*args, **kwargs)
            except self.triggers_on as e:
                self._handle_failure(func, e)
            else:
                self._fail_count = 0
                return result

        return wrapper

    def _check_state(self, func: CallableWithMeta[Any, Any]) -> None:
        if self._last_fail_time is not None:
            if time.time() - self._last_fail_time < self.time_to_recover:
                block_date_time = datetime.fromtimestamp(self._last_fail_time, tz=UTC)
                raise BreakerError(TOO_MUCH, f"{func.__module__}.{func.__name__}", block_date_time)
            self._last_fail_time = None

    def _handle_failure(self, func: CallableWithMeta, error: Exception) -> NoReturn:
        self._fail_count += 1
        if self._fail_count >= self.critical_count:
            self._last_fail_time = time.time()
            block_date_time = datetime.fromtimestamp(self._last_fail_time, tz=UTC)
            raise BreakerError(TOO_MUCH, f"{func.__module__}.{func.__name__}", block_date_time) from error
        raise error


circuit_breaker = CircuitBreaker(5, 30, Exception)


# @circuit_breaker
def get_comments(post_id: int) -> Any:
    """
    Получает комментарии к посту

    Args:
        post_id (int): Идентификатор поста

    Returns:
        list[dict[int | str]]: Список комментариев
    """
    response = urlopen(f"https://jsonplaceholder.typicode.com/comments?postId={post_id}")
    return json.loads(response.read())


if __name__ == "__main__":
    comments = get_comments(1)

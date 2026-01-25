from rich.pretty import pprint
from functools import wraps

def trace(fn):

    @wraps(fn)
    def wrapper(self, *a, **kw):
        # Print entry with method name and rich repr
        print(f"entering method: {fn.__name__}(args)")
        pprint(self)

        try:
            result = fn(self, *a, **kw)
            # Print exit with method name and rich repr
            print(f"exiting method: {fn.__name__}(args)")
            pprint(self)
            return result
        except Exception as e:
            # Print exit with error
            print(f"{fn.__name__}: exit (error: {e})")
            pprint(self)
            raise e

    return wrapper


def trace_task_state(fn):
    @wraps(fn)
    def wrapper(self, *a, **kw):
        # Print entry with method name and rich repr
        print(f"Task({self.__class__.__name__}): '{fn.__name__}({self.request_id})': {self._internal_status.name:<15} -> {a[0].name if a else 'N/A':>15}")

        try:
            result = fn(self, *a, **kw)
            return result
        except Exception as e:
            # Print exit with error
            print(f"{fn.__name__}: exit (error: {e})")
            pprint(self)
            raise e

    return wrapper

def trace_with_pyinspect(fn):
    import inspect as pyinspect
    from rich.pretty import pprint

    @wraps(fn)
    def wrapper(self, *a, **kw):
        # Get caller information
        try:
            caller_frame = pyinspect.stack()[1]
            caller_file = caller_frame.filename
            caller_line = caller_frame.lineno
            caller_func = caller_frame.function
        except Exception:
            caller_file = "unknown"
            caller_line = -1
            caller_func = "unknown"

        # Print entry with method name and rich repr
        print(f"entering method: {fn.__name__}(args) called from {caller_func} in {caller_file}:{caller_line}")
        pprint(self)

        try:
            result = fn(self, *a, **kw)
            # Print exit with method name and rich repr
            print(f"exiting method: {fn.__name__}(args) called from {caller_func} in {caller_file}:{caller_line}")
            pprint(self)
            return result
        except Exception as e:
            # Print exit with error
            print(f"{fn.__name__}: exit (error: {e}) called from {caller_func} in {caller_file}:{caller_line}")
            pprint(self)
            raise e

    return wrapper

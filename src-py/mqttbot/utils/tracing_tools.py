from rich.pretty import pprint


def trace(fn):
    def wrapper(self, *a, **kw):
        # Print entry with method name and rich repr
        print(f"{fn.__name__}: enter")
        pprint(self)

        try:
            result = fn(self, *a, **kw)
            # Print exit with method name and rich repr
            print(f"{fn.__name__}: exit")
            pprint(self)
            return result
        except Exception as e:
            # Print exit with error
            print(f"{fn.__name__}: exit (error: {e})")
            pprint(self)
            raise e

    return wrapper

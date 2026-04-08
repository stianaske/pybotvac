from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("pybotvac")
except PackageNotFoundError:  # pragma: no cover - environment dependent
    __version__ = "unknown"

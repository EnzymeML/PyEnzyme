from .base import BaseThinLayer

def _get_pysces():
    global ThinLayerPysces
    try:
        from .psyces import ThinLayerPysces as _ThinLayerPysces
    except ImportError as e:
        raise ImportError(
            f"ThinLayerPysces is not available because of missing dependencies: {e}"
        )
    return _ThinLayerPysces


def _get_copasi():
    global ThinLayerCopasi
    try:
        from .basico import ThinLayerCopasi as _ThinLayerCopasi
    except ImportError as e:
        raise ImportError(
            f"ThinLayerCopasi is not available because of missing dependencies: {e}"
        )
    return _ThinLayerCopasi


def __getattr__(name):
    if name == "ThinLayerPysces":
        return _get_pysces()
    elif name == "ThinLayerCopasi":
        return _get_copasi()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = ["BaseThinLayer", "ThinLayerPysces", "ThinLayerCopasi"]

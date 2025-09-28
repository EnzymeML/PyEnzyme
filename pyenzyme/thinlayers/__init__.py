from .base import BaseThinLayer

# Only import and show warnings if the modules are explicitly requested
ThinLayerPysces = None
ThinLayerCopasi = None


def _get_pysces():
    global ThinLayerPysces
    if ThinLayerPysces is None:
        try:
            from .psyces import ThinLayerPysces as _ThinLayerPysces

            ThinLayerPysces = _ThinLayerPysces
        except ImportError as e:
            raise ImportError(
                f"ThinLayerPysces is not available because of missing dependencies: {e}"
            )
    return ThinLayerPysces


def _get_copasi():
    global ThinLayerCopasi
    if ThinLayerCopasi is None:
        try:
            from .basico import ThinLayerCopasi as _ThinLayerCopasi

            ThinLayerCopasi = _ThinLayerCopasi
        except ImportError as e:
            raise ImportError(
                f"ThinLayerCopasi is not available because of missing dependencies: {e}"
            )
    return ThinLayerCopasi


def __getattr__(name):
    if name == "ThinLayerPysces":
        return _get_pysces()
    elif name == "ThinLayerCopasi":
        return _get_copasi()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = ["BaseThinLayer", "ThinLayerPysces", "ThinLayerCopasi"]

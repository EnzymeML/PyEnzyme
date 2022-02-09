from .TL_Base import BaseThinLayer

try:
    from .TL_Pysces import ThinLayerPysces
except ModuleNotFoundError:
    ThinLayerPysces = None

try:
    from .TL_Copasi import ThinLayerCopasi
except ModuleNotFoundError:
    ThinLayerCopasi = None

try:
    from .TL_Strenda import ThinLayerStrendaML
except ModuleNotFoundError:
    ThinLayerStrendaML = None

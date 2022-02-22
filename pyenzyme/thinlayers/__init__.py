import warnings

from .TL_Base import BaseThinLayer
from .TL_Strenda import ThinLayerStrendaML

try:
    from .TL_Pysces import ThinLayerPysces
except ModuleNotFoundError as e:
    print(
        "%s - ThinLayerCopasi now returns 'None', please provide the dependencies to use this module." % str(e)
    )
    ThinLayerPysces = None

try:
    from .TL_Copasi import ThinLayerCopasi
except ModuleNotFoundError as e:
    print(
        "%s - ThinLayerCopasi now returns 'None', please provide the dependencies to use this module." % str(e)
    )
    ThinLayerCopasi = None


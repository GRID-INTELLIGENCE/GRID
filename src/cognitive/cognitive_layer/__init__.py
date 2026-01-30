# Package marker for cognitive_layer

from __future__ import annotations

import os
from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)

_nested = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "light_of_the_seven", "cognitive_layer"))
if os.path.isdir(_nested) and _nested not in __path__:
    __path__.append(_nested)

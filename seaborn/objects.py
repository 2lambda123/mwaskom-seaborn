"""
A declarative, object-oriented interface for creating statistical graphics.

The seaborn.objects namespace contains a number of classes that can be composed
together to build a customized visualization.

The main object is :class:`Plot`, which is the starting point for all figures.
Pass :class:`Plot` a dataset and specify assignments from its variables to
roles in the plot. Build up the visualization by calling its methods.

There are four other general types of objects in this interface:

- :class:`Mark` subclasses, which create matplotlib artists for visualization
- :class:`Stat` subclasses, which apply statistical transforms before plotting
- :class:`Move` subclasses, which make further adjustments to reduce overplotting

These classes are passed to :meth:`Plot.add` to define a layer in the plot.
Each layer has a :class:`Mark` and optional :class:`Stat` and/or :class:`Move`.
Plots can have multiple layers.

The other general type of object is a :class:`Scale` subclass, which provide an
interface for controlling the mappings between data values and visual properties.
Pass :class:`Scale` objects to :meth:`Plot.scale`.

See the documentation for other :class:`Plot` methods to learn about the many
ways that a plot can be enhanced and customized.

"""
from seaborn._core.plot import Plot  # noqa: F401

from seaborn._marks.base import Mark  # noqa: F401
from seaborn._marks.area import Area, Ribbon  # noqa: F401
from seaborn._marks.bar import Bar, Bars  # noqa: F401
from seaborn._marks.line import Line, Lines, Path, Paths, Interval  # noqa: F401
from seaborn._marks.scatter import Dot, Dots  # noqa: F401

from seaborn._stats.base import Stat  # noqa: F401
from seaborn._stats.aggregation import Agg, Est  # noqa: F401
from seaborn._stats.regression import OLSFit, PolyFit  # noqa: F401
from seaborn._stats.histogram import Hist  # noqa: F401

from seaborn._core.moves import Dodge, Jitter, Norm, Shift, Stack  # noqa: F401

from seaborn._core.scales import Nominal, Continuous, Temporal  # noqa: F401

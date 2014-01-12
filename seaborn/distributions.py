"""Plottng functions for visualizing distributions."""
from __future__ import division
import colorsys
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.transforms as transforms
from six.moves import range
import moss

from seaborn.utils import (color_palette, husl_palette, blend_palette,
                           desaturate, _kde_support)


def _box_reshape(vals, groupby, names, order):
    """Reshape the box/violinplot input options and find plot labels."""

    # Set up default label outputs
    xlabel, ylabel = None, None

    # If order is provided, make sure it was used correctly
    if order is not None:
        # Assure that order is the same length as names, if provided
        if names is not None:
            if len(order) != len(names):
                raise ValueError("`order` must have same length as `names`")
        # Assure that order is only used with the right inputs
        is_pd = isinstance(vals, pd.Series) or isinstance(vals, pd.DataFrame)
        if not is_pd:
            raise ValueError("`vals` must be a Pandas object to use `order`.")

    # Handle case where data is a wide DataFrame
    if isinstance(vals, pd.DataFrame):
        if order is not None:
            vals = vals[order]
        if names is None:
            names = vals.columns.tolist()
        if vals.columns.name is not None:
            xlabel = vals.columns.name
        vals = vals.values.T

    # Handle case where data is a long Series and there is a grouping object
    elif isinstance(vals, pd.Series) and groupby is not None:
        groups = pd.groupby(vals, groupby).groups
        order = sorted(groups) if order is None else order
        if hasattr(groupby, "name"):
            if groupby.name is not None:
                xlabel = groupby.name
        if vals.name is not None:
            ylabel = vals.name
        vals = [vals.reindex(groups[name]) for name in order]
        if names is None:
            names = order

    else:

        # Handle case where the input data is an array or there was no groupby
        if hasattr(vals, 'shape'):
            if len(vals.shape) == 1:
                if np.isscalar(vals[0]):
                    vals = [vals]
                else:
                    vals = list(vals)
            elif len(vals.shape) == 2:
                nr, nc = vals.shape
                if nr == 1:
                    vals = [vals]
                elif nc == 1:
                    vals = [vals.ravel()]
                else:
                    vals = [vals[:, i] for i in range(nc)]
            else:
                error = "Input `vals` can have no more than 2 dimensions"
                raise ValueError(error)

        # This should catch things like flat lists
        elif np.isscalar(vals[0]):
            vals = [vals]

        # By default, just use the plot positions as names
        if names is None:
            names = list(range(1, len(vals) + 1))
        elif hasattr(names, "name"):
            if names.name is not None:
                xlabel = names.name

    # Now convert vals to a common representation
    # The plotting functions will work with a list of arrays
    # The list allows each array to possibly be of a different length
    vals = [np.asarray(a, np.float) for a in vals]

    return vals, xlabel, ylabel, names


def _box_colors(vals, color):
    """Find colors to use for boxplots or violinplots."""
    if color is None:
        colors = husl_palette(len(vals), l=.7)
    else:
        try:
            color = mpl.colors.colorConverter.to_rgb(color)
            colors = [color for _ in vals]
        except ValueError:
                colors = color_palette(color, len(vals))

    # Desaturate a bit because these are patches
    colors = [mpl.colors.colorConverter.to_rgb(c) for c in colors]
    colors = [desaturate(c, .7) for c in colors]

    # Determine the gray color for the lines
    light_vals = [colorsys.rgb_to_hls(*c)[1] for c in colors]
    l = min(light_vals) * .6
    gray = (l, l, l)

    return colors, gray

def boxplot(vals, groupby=None, names=None, join_rm=False, order=None,
            color=None, alpha=None, fliersize=3, linewidth=1.5, widths=.8,
            ax=None, **kwargs):
    """Wrapper for matplotlib boxplot with better aesthetics and functionality.

    Parameters
    ----------
    vals : DataFrame, Series, 2D array, list of vectors, or vector.
        Data for plot. DataFrames and 2D arrays are assuemd to be "wide" with
        each column mapping to a box. Lists of data are assumed to have one
        element per box.  Can also provide one long Series in conjunction with
        a grouping element as the `groupy` parameter to reshape the data into
        several boxes. Otherwise 1D data will produce a single box.
    groupby : grouping object
        If `vals` is a Series, this is used to group into boxes by calling
        pd.groupby(vals, groupby).
    names : list of strings, optional
        Names to plot on x axis; otherwise plots numbers. This will override
        names inferred from Pandas inputs.
    order : list of strings, optional
        If vals is a Pandas object with name information, you can control the
        order of the boxes by providing the box names in your preferred order.
    join_rm : boolean, optional
        If True, positions in the input arrays are treated as repeated
        measures and are joined with a line plot.
    color : mpl color, sequence of colors, or seaborn palette name
        Inner box color.
    alpha : float
        Transparancy of the inner box color.
    fliersize : float, optional
        Markersize for the fliers.
    linewidth : float, optional
        Width for the box outlines and whiskers.
    ax : matplotlib axis, optional
        Existing axis to plot into, otherwise grab current axis.
    kwargs : additional keyword arguments to boxplot

    Returns
    -------
    ax : matplotlib axis
        Axis where boxplot is plotted.

    """
    if ax is None:
        ax = plt.gca()

    # Reshape and find labels for the plot
    vals, xlabel, ylabel, names = _box_reshape(vals, groupby, names, order)

    # Draw the boxplot using matplotlib
    boxes = ax.boxplot(vals, patch_artist=True, widths=widths, **kwargs)

    # Find plot colors
    colors, gray = _box_colors(vals, color)

    # Set the new aesthetics
    for i, box in enumerate(boxes["boxes"]):
        box.set_color(colors[i])
        if alpha is not None:
            box.set_alpha(alpha)
        box.set_edgecolor(gray)
        box.set_linewidth(linewidth)
    for i, whisk in enumerate(boxes["whiskers"]):
        whisk.set_color(gray)
        whisk.set_linewidth(linewidth)
        whisk.set_linestyle("-")
    for i, cap in enumerate(boxes["caps"]):
        cap.set_color(gray)
        cap.set_linewidth(linewidth)
    for i, med in enumerate(boxes["medians"]):
        med.set_color(gray)
        med.set_linewidth(linewidth)
    for i, fly in enumerate(boxes["fliers"]):
        fly.set_color(gray)
        fly.set_marker("d")
        fly.set_markeredgecolor(gray)
        fly.set_markersize(fliersize)

    # Is this a vertical plot?
    vertical = kwargs.get("vert", True)

    # Draw the joined repeated measures
    if join_rm:
        x, y = np.arange(1, len(np.transpose(vals)) + 1), np.transpose(vals)
        if not vertical:
            x, y = y, x
        ax.plot(x, y, color=gray, alpha=2. / 3)

    # Label the axes and ticks
    if vertical:
        ax.set_xticklabels(names)
    else:
        ax.set_yticklabels(names)
        xlabel, ylabel = ylabel, xlabel
    if xlabel is not None:
        ax.set_xlabel(xlabel)
    if ylabel is not None:
        ax.set_ylabel(ylabel)

    # Turn off the grid parallel to the boxes
    if vertical:
        ax.xaxis.grid(False)
    else:
        ax.yaxis.grid(False)

    return ax


def violin(*args, **kwargs):
    """Deprecated old name for violinplot. Please update your code."""
    import warnings
    warnings.warn("violin() is deprecated; please use violinplot()",
                  UserWarning)
    return violinplot(*args, **kwargs)


def violinplot(vals, groupby=None, inner="box", color=None, positions=None,
               names=None, order=None, kernel="gau", bw="scott", widths=.8,
               alpha=None, join_rm=False, gridsize=100, cut=3, inner_kws=None,
               ax=None, **kwargs):

    """Create a violin plot (a combination of boxplot and kernel density plot).

    Parameters
    ----------
    vals : DataFrame, Series, 2D array, or list of vectors.
        Data for plot. DataFrames and 2D arrays are assuemd to be "wide" with
        each column mapping to a box. Lists of data are assumed to have one
        element per box.  Can also provide one long Series in conjunction with
        a grouping element as the `groupy` parameter to reshape the data into
        several violins. Otherwise 1D data will produce a single violins.
    groupby : grouping object
        If `vals` is a Series, this is used to group into boxes by calling
        pd.groupby(vals, groupby).
    inner : box | sticks | points
        Plot quartiles or individual sample values inside violin.
    color : mpl color, sequence of colors, or seaborn palette name
        Inner violin colors
    positions : number or sequence of numbers
        Position of first violin or positions of each violin.
    names : list of strings, optional
        Names to plot on x axis; otherwise plots numbers. This will override
        names inferred from Pandas inputs.
    order : list of strings, optional
        If vals is a Pandas object with name information, you can control the
        order of the plot by providing the violin names in your preferred
        order.
    kernel : {'gau' | 'cos' | 'biw' | 'epa' | 'tri' | 'triw' }
        Code for shape of kernel to fit with.
    bw : {'scott' | 'silverman' | scalar}
        Name of reference method to determine kernel size, or size as a
        scalar.
    widths : float
        Width of each violin at maximum density.
    alpha : float, optional
        Transparancy of violin fill.
    join_rm : boolean, optional
        If True, positions in the input arrays are treated as repeated
        measures and are joined with a line plot.
    gridsize : int
        Number of discrete gridpoints to evaluate the density on.
    cut : scalar
        Draw the estimate to cut * bw from the extreme data points.
    inner_kws : dict, optional
        Keyword arugments for inner plot.
    ax : matplotlib axis, optional
        Axis to plot on, otherwise grab current axis.
    kwargs : additional parameters to fill_betweenx

    Returns
    -------
    ax : matplotlib axis
        Axis with violin plot.

    """
    if ax is None:
        ax = plt.gca()

    # Reshape and find labels for the plot
    vals, xlabel, ylabel, names = _box_reshape(vals, groupby, names, order)

    # Sort out the plot colors
    colors, gray = _box_colors(vals, color)

    # Initialize the kwarg dict for the inner plot
    if inner_kws is None:
        inner_kws = {}
    in_alpha = inner_kws.pop("alpha", .6 if inner == "points" else 1)
    in_alpha *= 1 if alpha is None else alpha
    in_color = inner_kws.pop("color", gray)
    in_marker = inner_kws.pop("marker", ".")
    in_lw = inner_kws.pop("lw", 1.5 if inner == "box" else .8)

    # Find where the violins are going
    if positions is None:
        positions = np.arange(1, len(vals) + 1)
    elif not hasattr(positions, "__iter__"):
        positions = np.arange(positions, len(vals) + positions)

    # Set the default linewidth if not provided in kwargs
    try:
        lw = kwargs[({"lw", "linewidth"} & set(kwargs)).pop()]
    except KeyError:
        lw = 1.5

    # Iterate over the variables
    for i, a in enumerate(vals):

        # Fit the KDE
        x = positions[i]
        kde = sm.nonparametric.KDEUnivariate(a)
        fft = kernel == "gau"
        kde.fit(bw=bw, kernel=kernel, gridsize=gridsize, cut=cut, fft=fft)
        y, dens = kde.support, kde.density
        scl = 1 / (dens.max() / (widths / 2))
        dens *= scl

        # Draw the violin
        ax.fill_betweenx(y, x - dens, x + dens, alpha=alpha, color=colors[i])
        if inner == "box":
            for quant in moss.percentiles(a, [25, 75]):
                q_x = kde.evaluate(quant) * scl
                q_x = [x - q_x, x + q_x]
                ax.plot(q_x, [quant, quant], color=in_color,
                        linestyle=":", linewidth=in_lw, **inner_kws)
            med = np.median(a)
            m_x = kde.evaluate(med) * scl
            m_x = [x - m_x, x + m_x]
            ax.plot(m_x, [med, med], color=in_color,
                    linestyle="--", linewidth=in_lw, **inner_kws)
        elif inner == "stick":
            x_vals = kde.evaluate(a) * scl
            x_vals = [x - x_vals, x + x_vals]
            ax.plot(x_vals, [a, a], color=in_color,
                    linewidth=in_lw, alpha=in_alpha, **inner_kws)
        elif inner == "points":
            x_vals = [x for _ in a]
            ax.plot(x_vals, a, in_marker, color=in_color,
                    alpha=in_alpha, mew=0, **inner_kws)
        for side in [-1, 1]:
            ax.plot((side * dens) + x, y, c=gray, lw=lw)

    # Draw the repeated measure bridges
    if join_rm:
        ax.plot(range(1, len(vals) + 1), vals,
                color=in_color, alpha=2. / 3)

    # Add in semantic labels
    ax.set_xticks(positions)
    if names is not None:
        if len(vals) != len(names):
            raise ValueError("Length of names list must match nuber of bins")
        ax.set_xticklabels(names)
    ax.set_xlim(positions[0] - .5, positions[-1] + .5)

    if xlabel is not None:
        ax.set_xlabel(xlabel)
    if ylabel is not None:
        ax.set_ylabel(ylabel)

    ax.xaxis.grid(False)
    return ax


def distplot(a, bins=None, hist=True, kde=True, rug=False, fit=None,
             hist_kws=None, kde_kws=None, rug_kws=None, fit_kws=None,
             color=None, vertical=False, axlabel=None, ax=None):
    """Flexibly plot a distribution of observations.

    Parameter
    a : (squeezable to) 1d array
        Observed data.
    bins : argument for matplotlib hist(), or None
        Specification of hist bins, or None to use Freedman-Diaconis rule.
    hist : bool, default True
        Whether to plot a (normed) histogram.
    kde : bool, default True
        Whether to plot a gaussian kernel density estimate.
    rug : bool, default False
        Whether to draw a rugplot on the support axis.
    fit : random variable object
        An object with `fit` method, returning a tuple that can be passed to a
        `pdf` method a positional arguments following an grid of values to
        evaluate the pdf on.
    {hist, kde, rug, fit}_kws : dictionaries
        Keyword arguments for underlying plotting functions.
    color : matplotlib color, optional
        Color to plot everything but the fitted curve in.
    vertical : bool, default False
        If True, oberved values are on y-axis.
    axlabel : string, False, or None
        Name for the support axis label. If None, will try to get it
        from a.namel if False, do not set a label.
    ax : matplotlib axis, optional
        if provided, plot on this axis

    Returns
    -------
    ax : matplotlib axis

    """
    if ax is None:
        ax = plt.gca()

    # Intelligently label the support axis
    label_ax = bool(axlabel)
    if axlabel is None and hasattr(a, "name"):
        axlabel = a.name
        if axlabel is not None:
            label_ax = True

    # Make a a 1-d array
    a = np.asarray(a).squeeze()

    # Handle dictionary defaults
    if hist_kws is None:
        hist_kws = dict()
    if kde_kws is None:
        kde_kws = dict()
    if rug_kws is None:
        rug_kws = dict()
    if fit_kws is None:
        fit_kws = dict()

    # Get the color from the current color cycle
    if color is None:
        if vertical:
            line, = ax.plot(0, a.mean())
        else:
            line, = ax.plot(a.mean(), 0)
        color = line.get_color()
        line.remove()

    if hist:
        if bins is None:
            # From http://stats.stackexchange.com/questions/798/
            h = 2 * moss.iqr(a) * len(a) ** -(1 / 3)
            bins = (a.max() - a.min()) / h
        hist_alpha = hist_kws.pop("alpha", 0.4)
        orientation = "horizontal" if vertical else "vertical"
        hist_color = hist_kws.pop("color", color)
        ax.hist(a, bins, normed=True, color=hist_color, alpha=hist_alpha,
                orientation=orientation, **hist_kws)

    if kde:
        kde_color = kde_kws.pop("color", color)
        kdeplot(a, vertical=vertical, color=kde_color, ax=ax, **kde_kws)

    if rug:
        rug_color = rug_kws.pop("color", color)
        axis = "y" if vertical else "x"
        rugplot(a, axis=axis, color=rug_color, ax=ax, **rug_kws)

    if fit is not None:
        fit_color = fit_kws.pop("color", "#282828")
        gridsize = fit_kws.pop("gridsize", 500)
        cut = fit_kws.pop("cut", 3)
        clip = fit_kws.pop("clip", (-np.inf, np.inf))
        bw = sm.nonparametric.bandwidths.bw_scott(a)
        x = _kde_support(a, bw, gridsize, cut, clip)
        params = fit.fit(a)
        pdf = lambda x: fit.pdf(x, *params)
        y = pdf(x)
        if vertical:
            x, y = y, x
        ax.plot(x, y, color=fit_color, **fit_kws)

    if label_ax:
        if vertical:
            ax.set_ylabel(axlabel)
        else:
            ax.set_xlabel(axlabel)

    return ax


def _univariate_kde(data, shade, vertical, kernel, bw, gridsize, cut,
                    clip, legend, ax, **kwargs):
    """Plot a univariate kernel density estimate on one of the axes."""

    # Sort out the clipping
    if clip is None:
        clip = (-np.inf, np.inf)

    # Calculate the KDE
    fft = kernel == "gau"
    kde = sm.nonparametric.KDEUnivariate(data)
    kde.fit(kernel, bw, fft, gridsize=gridsize, cut=cut, clip=clip)
    x, y = kde.support, kde.density
    if vertical:
        x, y = y, x

    # Check if a label was specified in the call
    label = kwargs.pop("label", None)

    # Otherwise check if the data object has a name
    if label is None and hasattr(data, "name"):
        label = data.name

    # Decide if we're going to add a legend
    legend = not label is None and legend
    label = "_nolegend_" if label is None else label

    # Use the active color cycle to find the plot color
    line, = ax.plot(x, y, **kwargs)
    color = line.get_color()
    line.remove()
    kwargs.pop("color", None)

    # Draw the KDE plot and, optionally, shade
    ax.plot(x, y, color=color, label=label, **kwargs)
    alpha = kwargs.pop("alpha", 0.25)
    if shade:
        ax.fill_between(x, 1e-12, y, color=color, alpha=alpha)

    # Draw the legend here
    if legend:
        ax.legend(loc="best")

    return ax


def _bivariate_kde(x, y, filled, kernel, bw, gridsize, cut, clip, axlabel, ax,
                   **kwargs):
    """Plot a joint KDE estimate as a bivariate contour plot."""

    # Determine the clipping
    if clip is None:
        clip = [(-np.inf, np.inf), (-np.inf, np.inf)]
    elif np.ndim(clip) == 1:
        clip = [clip, clip]

    # Calculate the KDE
    if isinstance(bw, str):
        bw_func = getattr(sm.nonparametric.bandwidths, "bw_" + bw)
        x_bw = bw_func(x)
        y_bw = bw_func(y)
        bw = [x_bw, y_bw]
    elif np.isscalar(bw):
        bw = [bw, bw]
    kde = sm.nonparametric.KDEMultivariate([x, y], "cc", bw)
    x_support = _kde_support(x, kde.bw[0], gridsize, cut, clip[0])
    y_support = _kde_support(y, kde.bw[1], gridsize, cut, clip[1])
    xx, yy = np.meshgrid(x_support, y_support)
    z = kde.pdf([xx.ravel(), yy.ravel()]).reshape(xx.shape)

    # Plot the contours
    n_levels = kwargs.pop("n_levels", 10)
    cmap = kwargs.pop("cmap", "BuGn" if filled else "BuGn_d")
    if isinstance(cmap, str):
        if cmap.endswith("_d"):
            pal = ["#333333"]
            pal.extend(color_palette(cmap.replace("_d", "_r"), 2))
            cmap = blend_palette(pal, as_cmap=True)
    contour_func = ax.contourf if filled else ax.contour
    contour_func(xx, yy, z, n_levels, cmap=cmap, **kwargs)

    # Label the axes
    if hasattr(x, "name") and axlabel:
        ax.set_xlabel(x.name)
    if hasattr(y, "name") and axlabel:
        ax.set_ylabel(y.name)

    return ax


def kdeplot(data, data2=None, shade=False, vertical=False, kernel="gau",
            bw="scott", gridsize=100, cut=3, clip=None, legend=True, ax=None,
            **kwargs):
    """Fit and plot a univariate or bivarate kernel density estimate.

    Parameters
    ----------
    data : 1d or 2d array-like
        Input data. If two-dimensional, assumed to be shaped (n_unit x n_var),
        and a bivariate contour plot will be drawn.
    data2: 1d array-like
        Second input data. If provided `data` must be one-dimensional, and
        a bivariate plot is produced.
    shade : bool, optional
        If true, shade in the area under the KDE curve (or draw with filled
        contours when data is bivariate).
    vertical : bool
        If True, density is on x-axis.
    kernel : {'gau' | 'cos' | 'biw' | 'epa' | 'tri' | 'triw' }, optional
        Code for shape of kernel to fit with. Bivariate KDE can only use
        gaussian kernel.
    bw : {'scott' | 'silverman' | scalar | pair of scalars }, optional
        Name of reference method to determine kernel size, scalar factor,
        or scalar for each dimension of the bivariate plot.
    gridsize : int, optional
        Number of discrete points in the evaluation grid.
    cut : scalar, optional
        Draw the estimate to cut * bw from the extreme data points.
    clip : pair of scalars, or pair of pair of scalars, optional
        Lower and upper bounds for datapoints used to fit KDE. Can provide
        a pair of (low, high) bounds for bivariate plots.
    legend : bool, optoinal
        If True, add a legend or label the axes when possible.
    ax : matplotlib axis, optional
        Axis to plot on, otherwise uses current axis.
    kwargs : other keyword arguments for plot()

    Returns
    -------
    ax : matplotlib axis
        Axis with plot.

    """
    if ax is None:
        ax = plt.gca()

    bivariate = False
    if isinstance(data, np.ndarray) and np.ndim(data) > 1:
        bivariate = True
        x, y = data.T
    elif isinstance(data, pd.DataFrame) and np.ndim(data) > 1:
        bivariate = True
        x = data.iloc[:, 0]
        y = data.iloc[:, 1]
    elif data2 is not None:
        bivariate = True
        x = data
        y = data2

    if bivariate:
        ax = _bivariate_kde(x, y, shade, kernel, bw, gridsize,
                            cut, clip, legend, ax, **kwargs)
    else:
        ax = _univariate_kde(data, shade, vertical, kernel, bw,
                             gridsize, cut, clip, legend, ax, **kwargs)

    return ax


def rugplot(a, height=None, axis="x", ax=None, **kwargs):
    """Plot datapoints in an array as sticks on an axis.

    Parameters
    ----------
    a : vector
        1D array of datapoints.
    height : scalar, optional
        Height of ticks, if None draw at 5% of axis range.
    axis : {'x' | 'y'}, optional
        Axis to draw rugplot on.
    ax : matplotlib axis
        Axis to draw plot into; otherwise grabs current axis.
    kwargs : other keyword arguments for plt.plot()

    Returns
    -------
    ax : matplotlib axis
        Axis with rugplot.

    """
    if ax is None:
        ax = plt.gca()
    other_axis = dict(x="y", y="x")[axis]
    min, max = getattr(ax, "get_%slim" % other_axis)()
    if height is None:
        range = max - min
        height = range * .05
    if axis == "x":
        ax.plot([a, a], [min, min + height], **kwargs)
    else:
        ax.plot([min, min + height], [a, a], **kwargs)
    return ax




def dotplot(vals, points, intervals=None, lines=None,
            styles=None, sections=None, split_names=None,
            marker_props=None, line_props=None, striped=False,
            stacked=False, gridlines=False, section_order=None,
            line_order=None, horizontal=True, ax=None):
    """
    Produce a dotplot similar in style to those in Cleveland's
    "Visualizing Data" book (also known as a "forest plot").  Several
    extensions to the basic dotplot are also implemented: intervals
    can be plotted along with the dots, and multiple points and
    intervals can be drawn on each line of the dotplot.

    Parameters
    ----------
    vals : DataFrame
        Data for dotplot.

    points : string
        The name of the variable in the DataFrame defining the
        coordinates of the plotted points.

    intervals : string or sequence of two strings
        If `interval` is a single string, this is the name of the
        variable that defines one-half of the length of the symmetric
        interval that is plotted around the point.  If `interval` is
        a sequence of two strings, the two strings are variable names
        that define the lengths of the left and right sides of the
        interval that is plotted around the point.

    lines : string
        This is a variable name that determines which points are drawn
        on the same line of the dotplot.

    styles : string
        This is a variable name that is used to determine the point
        style (symbol and color).

    sections : string
        This is a variable name that is used to define groups of
        lines that are placed in the same section

    split_names : string
        If not None, this is used to split the values of groupby into
        substrings that are drawn in the left and right margins,
        respectively.

    marker_props : dict
        A dictionary mapping styles for the points (coded as in column
        `style` of `vals` to keyword arguments to the plot function.

    line_props : dict
        A dictionary mapping styles for the interval lines (coded as
        in column `style` of `vals`) to keyword arguments to the plot
        function.

    striped : bool
        If True, draw a shaded box around every other line of the
        dotplot.

    stacked : bool
        If true, when multiple points are present on a line, offset
        them from each other.

    gridlines : bool
        If true, draw the gridlines as grey lines.

    section_order : list of strings
        If provided, order the sections in the given order.

    line_order : list of strings
        If provided, order the lines of the dotplot in the given
        order.

    horizontal : bool
        If True, the axis lines are horizontal, otherwise the axis
        lines are vertical.

    ax : matplotlib.axes
        The axes on which the dotplot is drawn.

    Returns
    -------
    ax : matplotlib axis
        Axis object with plot.

    References
    ----------
      * Cleveland, William S. (1993). "Visualizing Data". Hobart
        Press.
      * Jacoby, William G. (2006) "The Dot Plot: A Graphical Display
        for Labeled Quantitative Values." The Political Methodologist
        14(1): 6-14.
    """

    if ax is None:
        ax = plt.gca()

    # Total number of points
    npoint = vals.shape[0]

    # We will be modifying the data frame.
    vals = vals.copy()

    # Set default line values if needed
    if lines is None:
        lines = "_lines"
        vals[lines] = np.arange(npoint)

    # Set default section values if needed
    if sections is None:
        sections = "_sections"
        vals[sections] = np.zeros(npoint)

    # Set default style values if needed
    if styles is None:
        styles = "_styles"
        vals[styles] = np.zeros(npoint)

    # The vertical space (in inches) for a section title
    section_title_space = 0.5

    # The number of sections
    nsect = len(set(vals[sections]))

    # The number of section titles
    nsect_title = nsect if nsect > 1 else 0

    # The total vertical space devoted to section titles.
    section_space_total = section_title_space * nsect_title

    # Add a bit of room so that points that fall at the axis limits
    # are not cut in half.
    ax.set_xmargin(0.02)
    ax.set_ymargin(0.02)

    if section_order is None:
        lines0 = list(set(vals[sections]))
        lines0.sort()
    else:
        lines0 = section_order

    if line_order is None:
        lines1 = list(set(vals[lines]))
        lines1.sort()
    else:
        lines1 = line_order

    # A map from (section,line) codes to index positions.
    lines_map = {}
    for i in range(npoint):
        ky = (vals[sections][i], vals[lines][i])
        if ky not in lines_map:
            lines_map[ky] = []
        lines_map[ky].append(i)

    # Get the size of the axes on the parent figure in inches
    fig = ax.figure
    bbox = ax.get_window_extent().transformed(
        fig.dpi_scale_trans.inverted())
    awidth, aheight = bbox.width, bbox.height

    # The number of lines in the plot.
    nrows = len(lines_map)

    # The positions of the lowest and highest guideline in axes
    # coordinates (for horizontal dotplots), or the leftmost and
    # rightmost guidelines (for vertical dotplots).
    bottom,top = 0,1

    if horizontal:
        # x coordinate is data, y coordinate is axes
        trans = transforms.blended_transform_factory(ax.transData,
                                                     ax.transAxes)
    else:
        # x coordinate is axes, y coordinate is data
        trans = transforms.blended_transform_factory(ax.transAxes,
                                                     ax.transData)

    # Space used for a section title, in axes coordinates
    title_space_axes = section_title_space / aheight

    # Space between lines
    if horizontal:
        dpos = (top - bottom - nsect_title*title_space_axes) /\
            float(nrows)
    else:
        dpos = (top - bottom) / float(nrows)

    # Determine the spacing for stacked points
    # The maximum number of points on one line.
    style_codes = list(set(vals[styles]))
    style_codes.sort()
    nval = len(style_codes)
    if nval > 1:
        stackd = dpos / (2.5*(float(nval)-1))
    else:
        stackd = 0.

    if nval == 1 and stacked == True:
        warnings.warn("dotplot: stacked is True but there is only one style group")

    # Map from style code to its integer position
    style_codes_map = {x: style_codes.index(x) for x in style_codes}

    # Setup default marker styles
    colors = husl_palette(nval)
    if marker_props is None:
        marker_props = {x: {} for x in style_codes}
    for j in range(nval):
        sc = style_codes[j]
        if "color" not in marker_props[sc]:
            marker_props[sc]["color"] = colors[j % len(colors)]
        if "marker" not in marker_props[sc]:
            marker_props[sc]["marker"] = "o"
        if "ms" not in marker_props[sc]:
            marker_props[sc]["ms"] = 10 if stackd == 0 else 6

    # Setup default line styles
    if line_props is None:
        line_props = {x: {} for x in style_codes}
    for j in range(nval):
        sc = style_codes[j]
        if "color" not in line_props[sc]:
            line_props[sc]["color"] = "grey"
        if "linewidth" not in line_props[sc]:
            line_props[sc]["linewidth"] = 2 if stackd > 0 else 8

    if horizontal:
        # The vertical position of the first line.
        pos = top - dpos/2 if nsect == 1 else top
    else:
        # The horizontal position of the first line.
        pos = bottom + dpos/2

    # Points that have already been labeled
    labeled = set()

    # Positions of the axis grid lines
    tickpos = []

    # Loop through the sections
    for k0 in lines0:

        # Draw a section title
        if nsect_title > 0:

            # Title for a horizontal dotplot
            if horizontal:

                y0 = pos + dpos/2 if k0 == lines0[0] else pos

                ax.fill_between((0, 1), (y0,y0),
                                (pos-0.7*title_space_axes,
                                 pos-0.7*title_space_axes),
                                color='darkgrey',
                                transform=ax.transAxes,
                                zorder=1)

                txt = ax.text(0.5, pos - 0.35*title_space_axes, k0,
                              horizontalalignment='center',
                              verticalalignment='center',
                              transform=ax.transAxes)
                txt.set_fontweight("bold")
                pos -= title_space_axes

            # Title for a vertical dotplot
            else:

                m = len([k for k in lines_map if k[0] == k0])

                ax.fill_between((pos-dpos/2+0.01,
                                 pos+(m-1)*dpos+dpos/2-0.01),
                                (1.01,1.01), (1.06,1.06),
                                color='darkgrey',
                                transform=ax.transAxes,
                                zorder=1, clip_on=False)

                txt = ax.text(pos + (m-1)*dpos/2, 1.02, k0,
                              horizontalalignment='center',
                              verticalalignment='bottom',
                              transform=ax.transAxes)
                txt.set_fontweight("bold")

        jrow = 0
        for k1 in lines1:

            # No data to plot
            if (k0, k1) not in lines_map:
                continue

            # Set up the labels
            if split_names is not None:
                us = k1.split(split_names)
                if len(us) >= 2:
                    left_label, right_label = us[0], us[1]
                else:
                    left_label, right_label = k1, None
            else:
                left_label, right_label = k1, None

            # Draw the stripe
            if striped and jrow % 2 == 0:
                if horizontal:
                    ax.fill_between((0, 1), (pos-dpos/2, pos-dpos/2),
                                    (pos+dpos/2, pos+dpos/2),
                                    color='lightgrey',
                                    transform=ax.transAxes,
                                    zorder=0)
                else:
                    ax.fill_between((pos-dpos/2, pos+dpos/2),
                                    (0, 0), (1, 1),
                                    color='lightgrey',
                                    transform=ax.transAxes,
                                    zorder=0)

            # Draw the guideline
            if gridlines:
                if horizontal:
                    ax.axhline(y=pos, color='grey')
                else:
                    # axvline seems not to work as expected
                    #ax.axvline(x=pos, color='green')
                    plt.plot([pos, pos], [0, 1], color='grey',
                             transform=ax.transAxes)

            jrow += 1

            # Draw the left margin label
            if horizontal:
                ax.text(-0.1/awidth, pos, left_label,
                           horizontalalignment="right",
                           verticalalignment='center',
                           transform=ax.transAxes, family='monospace')
            else:
                ax.text(pos, -0.1/aheight, left_label,
                           horizontalalignment="center",
                           verticalalignment='top',
                           transform=ax.transAxes, family='monospace')

            # Draw the right margin label
            if right_label is not None:
                if horizontal:
                    ax.text(1 + 0.1/awidth, pos, right_label,
                            horizontalalignment="left",
                            verticalalignment='center',
                            transform=ax.transAxes,
                            family='monospace')
                else:
                    ax.text(pos, 1 + 0.1/aheight, right_label,
                            horizontalalignment="center",
                            verticalalignment='bottom',
                            transform=ax.transAxes,
                            family='monospace')

            # Save the position so that we can place the tick marks
            tickpos.append(pos)

            # Loop over the points in one line
            for ji,jp in enumerate(lines_map[(k0,k1)]):

                # Calculate the vertical offset
                yo = 0
                if stacked:
                    style = vals[styles][jp]
                    yo = -dpos/5 + style_codes_map[style]*stackd

                pt = vals[points][jp]

                # Plot the interval
                if intervals is not None:

                    # Symmetric interval
                    if np.isscalar(intervals):
                        lcb, ucb = pt - vals[intervals][jp],\
                            pt + vals[intervals][jp]

                    # Nonsymmetric interval
                    else:
                        lcb, ucb = pt - vals[intervals[0]][jp],\
                            pt + vals[intervals[1]][jp]

                    # Draw the interval
                    if horizontal:
                        ax.plot([lcb, ucb], [pos+yo, pos+yo], '-',
                                transform=trans,
                                **line_props[vals[styles][jp]])
                    else:
                        ax.plot([pos+yo, pos+yo], [lcb, ucb], '-',
                                transform=trans,
                                **line_props[vals[styles][jp]])


                # Plot the point
                sl = vals[styles][jp]
                sll = sl if sl not in labeled else None
                labeled.add(sl)
                if horizontal:
                    ax.plot([pt,], [pos+yo,], ls='None',
                            transform=trans, label=sll,
                            **marker_props[sl])
                else:
                    ax.plot([pos+yo,], [pt,], ls='None',
                            transform=trans, label=sll,
                            **marker_props[sl])

            if horizontal:
                pos -= dpos
            else:
                pos += dpos

    # Set up the axis
    if horizontal:
        ax.xaxis.set_ticks_position("bottom")
        ax.yaxis.set_ticks_position("none")
        ax.set_yticklabels([])
        ax.spines['bottom'].set_position(('axes', -0.1/aheight))
        ax.set_ylim(0, 1)
        ax.yaxis.set_ticks(tickpos)
        ax.autoscale_view(scaley=False, tight=True)
    else:
        ax.yaxis.set_ticks_position("left")
        ax.xaxis.set_ticks_position("none")
        ax.set_xticklabels([])
        ax.spines['left'].set_position(('axes', -0.1/awidth))
        ax.set_xlim(0, 1)
        ax.xaxis.set_ticks(tickpos)
        ax.autoscale_view(scalex=False, tight=True)

    return ax

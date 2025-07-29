import math
from typing import List, Optional, Tuple, Union

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes

from pyenzyme.thinlayers.base import BaseThinLayer, SimResult, Time
from pyenzyme.versions import v2

# Default figure dimensions
DEFAULT_WIDTH = 6
DEFAULT_HEIGHT = 3


def plot(
    enzmldoc: v2.EnzymeMLDocument,
    columns: int = 2,
    show: bool = False,
    measurement_ids: Optional[list[str]] = None,
    marker_size: int = 6,
    marker_style: str = "o",
    thinlayer: Optional[BaseThinLayer] = None,
    out: Optional[str] = None,
    img_format: str = "png",
    dpi: int = 300,
    **kwargs,
) -> Tuple[Figure, Union[Axes, List[Axes]]]:
    """
    Creates publication-quality plots of measurement data from an EnzymeML document.

    This function generates plots for experimental measurements and optionally includes
    model fits provided by a thinlayer. Each measurement is displayed in a separate
    subplot, with species data and their corresponding model fits if available.

    Parameters
    ----------
    enzmldoc : v2.EnzymeMLDocument
        The EnzymeML document containing measurement data to plot.
    columns : int, optional
        Number of columns in the plot grid, by default 2.
    measurement_ids : Optional[list[str]], optional
        List of specific measurement IDs to plot. If None, all measurements are plotted.
    marker_size : int, optional
        Size of markers for experimental data points, by default 6.
    marker_style : str, optional
        Style of markers for experimental data points, by default "o".
    thinlayer : Optional[BaseThinLayer], optional
        A thinlayer object providing model fits for the data. If provided,
        fitting curves will be displayed alongside experimental data.
    **kwargs
        Additional keyword arguments passed to matplotlib plotting functions.

    Returns
    -------
    tuple
        Figure and axes objects from matplotlib.

    Examples
    --------
    Basic usage with all measurements:

    >>> import pyenzyme as pe
    >>> doc = pe.read_enzymeml("path/to/enzmldoc.json")
    >>> fig, axes = pe.plot(enzmldoc=doc)
    >>> fig.savefig("output.png", dpi=300)

    Using a thinlayer for model fitting:

    >>> import pyenzyme as pe
    >>> import pyenzyme.thinlayers as tls
    >>> doc = pe.read_enzymeml("path/to/enzmldoc.json")
    >>> tl = tls.ThinLayerPysces(doc)
    >>> tl.optimize()
    >>> fig, _ = pe.plot(
    ...     enzmldoc=doc,
    ...     thinlayer=tl,
    ...     measurement_ids=["measurement0", "measurement1"],
    ... )
    >>> fig.savefig("with_fits.png", dpi=300)
    """

    # Check if we're in a Jupyter environment and set up matplotlib backend
    try:
        from IPython.core.getipython import get_ipython

        ipython = get_ipython()
        if ipython is not None:
            # We're in IPython/Jupyter
            ipython.run_line_magic("matplotlib", "inline")
    except ImportError:
        # IPython not available, continue normally
        pass

    # Filter measurements based on provided IDs
    if measurement_ids is None:
        measurements = enzmldoc.measurements
    else:
        measurements = [m for m in enzmldoc.measurements if m.id in measurement_ids]

    # Configure subplot layout
    n_measurements = len(measurements)
    rows = math.ceil(n_measurements / columns)

    # Single measurement case: use single column
    if n_measurements == 1:
        columns = 1

    # Create figure and axes
    fig, axs = plt.subplots(
        nrows=rows,
        ncols=columns,
        figsize=(DEFAULT_WIDTH * columns, DEFAULT_HEIGHT * rows),
    )

    # Ensure axs is always a flat list for consistent handling
    if isinstance(axs, np.ndarray):
        axs = axs.flatten()
    else:
        axs = [axs]

    # Plot each measurement
    for ax, measurement in zip(axs, measurements):
        _plot_measurement(
            ax, enzmldoc, measurement, thinlayer, marker_size, marker_style, **kwargs
        )

    # Hide unused axes
    for idx in range(len(measurements), len(axs)):
        axs[idx].set_visible(False)

    # Adjust layout with minimal space for legends
    plt.tight_layout(rect=(0, 0, 0.98, 1))

    if out:
        fig.savefig(out, dpi=dpi, format=img_format)

    if show:
        plt.show()

    return fig, axs  # type: ignore


def _plot_measurement(
    ax: Axes,
    enzmldoc: v2.EnzymeMLDocument,
    measurement: v2.Measurement,
    thinlayer: Optional[BaseThinLayer],
    marker_size: int,
    marker_style: str,
    **kwargs,
) -> None:
    """
    Plot a single measurement on the given axes.

    Parameters
    ----------
    ax : Axes
        The matplotlib axes to plot on.
    enzmldoc : v2.EnzymeMLDocument
        The EnzymeML document containing the data.
    measurement : v2.Measurement
        The specific measurement to plot.
    thinlayer : Optional[BaseThinLayer]
        A thinlayer object providing model predictions, if available.
    marker_size : int
        Size of markers for experimental data points.
    marker_style : str
        Style of markers for experimental data points.
    **kwargs
        Additional keyword arguments passed to matplotlib plotting functions.
    """
    # Sort species data by ID for consistent order
    species_data = sorted(
        [s for s in measurement.species_data], key=lambda x: x.species_id
    )

    # Get data types for y-axis label
    dataytypes = _collect_dataytypes(species_data)

    # Get model predictions if available
    if thinlayer:
        pred, time = _get_fit(enzmldoc, measurement, thinlayer)
    else:
        pred, time = {}, []

    # Plot each species
    for species in species_data:
        _plot_species(
            ax,
            species,
            pred,
            time,
            marker_size,
            marker_style,
            **kwargs,
        )

    # Configure plot appearance
    _configure_plot(ax, measurement, dataytypes)


def _plot_species(
    ax: Axes,
    species: v2.MeasurementData,
    pred: SimResult,
    time: List[float],
    marker_size: int,
    marker_style: str,
    **kwargs,
) -> None:
    """
    Plot experimental data and model fit for a single species.

    Parameters
    ----------
    ax : Axes
        The matplotlib axes to plot on.
    species : v2.MeasurementData
        The measurement data for a specific species.
    pred : Dict[str, List[float]]
        Model predictions, if available.
    time : List[float]
        Time points for model predictions.
    marker_size : int
        Size of markers for experimental data points.
    marker_style : str
        Style of markers for experimental data points.
    **kwargs
        Additional keyword arguments passed to matplotlib plotting functions.
    """
    # Plot experimental data if available
    if len(species.data) > 0:
        line = ax.plot(
            species.time,
            species.data,
            marker_style,
            markersize=marker_size,
            label=species.species_id,
            **kwargs,
        )
        line_color = line[0].get_color()

        # Add model fit if available for this species
        if species.species_id in pred:
            ax.plot(
                time,
                pred[species.species_id],
                "--",
                color=line_color,
                label=f"{species.species_id} Fit",
                **kwargs,
            )
    # If no experimental data but model fit is available
    elif species.species_id in pred:
        ax.plot(
            time,
            pred[species.species_id],
            "--",
            label=f"{species.species_id} Fit",
            **kwargs,
        )


def _configure_plot(
    ax: Axes, measurement: v2.Measurement, dataytypes: List[str]
) -> None:
    """
    Configure plot appearance with titles, labels, and styling.

    Parameters
    ----------
    ax : Axes
        The matplotlib axes to configure.
    measurement : v2.Measurement
        The measurement being plotted.
    dataytypes : List[str]
        List of data types for the y-axis label.
    """
    # Add legend outside the plot at the top right
    ax.legend(
        loc="upper left",
        bbox_to_anchor=(1.01, 1),
        frameon=True,
        framealpha=0.9,
        fancybox=True,
        shadow=True,
        fontsize="small",
        labelspacing=0.5,  # Make entries more compact vertically
    )

    # Set title and axis labels
    ax.set_title(measurement.name, fontweight="bold")
    ax.set_xlabel("Time")
    ax.set_ylabel(", ".join(dataytypes))

    # Configure grid and spines
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def _get_fit(
    enzmldoc: v2.EnzymeMLDocument,
    measurement: v2.Measurement,
    thinlayer: BaseThinLayer,
) -> Tuple[SimResult, Time]:
    """
    Get model predictions for a measurement using a thinlayer.

    Parameters
    ----------
    enzmldoc : v2.EnzymeMLDocument
        The EnzymeML document containing the data.
    measurement : v2.Measurement
        The measurement to generate predictions for.
    thinlayer : BaseThinLayer
        The thinlayer object providing integration capabilities.

    Returns
    -------
    Tuple[Dict[str, List[float]], List[float]]
        A tuple containing predictions for each species and the time points.

    Raises
    ------
    ValueError
        If time data is missing for all species in the measurement.
    """
    # Get the initial conditions from the measurement
    initial_conditions = {
        s.species_id: s.initial for s in measurement.species_data if s.initial
    }

    # Get the time points from the measurement
    time = next((s.time for s in measurement.species_data if s.time), None)

    if time is None:
        raise ValueError("Time is not set for any species in the measurement")

    t0, t1 = min(time), max(time)

    # Use thinlayer to integrate the model
    return thinlayer.integrate(
        model=enzmldoc,
        initial_conditions=initial_conditions,
        t0=t0,
        t1=t1,
    )


def _collect_dataytypes(measurement_data: List[v2.MeasurementData]) -> List[str]:
    """
    Extract and format unique measurement data types.

    Parameters
    ----------
    measurement_data : List[v2.MeasurementData]
        List of measurement data objects.

    Returns
    -------
    List[str]
        Unique, capitalized data types from measurements.
    """
    return list(
        set(
            [
                s.data_type.value.capitalize()
                for s in measurement_data
                if s.data_type is not None
            ]
        )
    )

from typing import List, Optional, Tuple, Dict

from bokeh.models import TabPanel, Tabs, HoverTool, ColumnDataSource
from bokeh.plotting import figure, show as show_bokeh
from bokeh.io import output_file, output_notebook
from bokeh.palettes import Category10, Category20
import rich

from pyenzyme.thinlayers.base import BaseThinLayer, SimResult, Time
from pyenzyme.versions import v2

# Default figure dimensions
DEFAULT_WIDTH = 800
DEFAULT_HEIGHT = 400


def plot_interactive(
    enzmldoc: v2.EnzymeMLDocument,
    measurement_ids: Optional[list[str]] = None,
    thinlayer: Optional[BaseThinLayer] = None,
    out: Optional[str] = None,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    show: bool = True,
    output_nb: bool = True,
    **kwargs,
) -> Tabs:
    """
    Creates interactive plots of measurement data from an EnzymeML document using Bokeh.

    This function generates plots for experimental measurements and optionally includes
    model fits provided by a thinlayer. Each measurement is displayed in a separate
    tab, with species data and their corresponding model fits if available.

    Parameters
    ----------
    enzmldoc : v2.EnzymeMLDocument
        The EnzymeML document containing measurement data to plot.
    measurement_ids : Optional[list[str]], optional
        List of specific measurement IDs to plot. If None, all measurements are plotted.
    thinlayer : Optional[BaseThinLayer], optional
        A thinlayer object providing model fits for the data. If provided,
        fitting curves will be displayed alongside experimental data.
    out : Optional[str], optional
        File path to save the plot if desired. If provided, the plot is saved
        as an HTML file.
    width : int, optional
        Width of the plot in pixels, by default 600.
    height : int, optional
        Height of the plot in pixels, by default 400.
    render : bool, optional
        Whether to immediately display the plot, by default True.
    **kwargs
        Additional keyword arguments passed to Bokeh plotting functions.

    Returns
    -------
    Tabs
        A Bokeh Tabs object containing all measurement plots.

    Examples
    --------
    Basic usage with all measurements:

    >>> import pyenzyme as pe
    >>> doc = pe.read_enzymeml("path/to/enzmldoc.json")
    >>> tabs = pe.plot_interactive(enzmldoc=doc)
    >>> show(tabs)  # Display in a notebook or browser

    Using a thinlayer for model fitting:

    >>> import pyenzyme as pe
    >>> import pyenzyme.thinlayers as tls
    >>> doc = pe.read_enzymeml("path/to/enzmldoc.json")
    >>> tl = tls.ThinLayerPysces(doc)
    >>> tl.optimize()
    >>> tabs = pe.plot_interactive(
    ...     enzmldoc=doc,
    ...     thinlayer=tl,
    ...     measurement_ids=["measurement0", "measurement1"],
    ...     out="interactive_plots.html"
    ... )
    >>> show(tabs)  # Display in a notebook or browser
    """

    is_nb = _is_notebook()
    if output_nb and is_nb:
        output_notebook()

    # Filter measurements based on provided IDs
    if measurement_ids is None:
        measurements = enzmldoc.measurements
    else:
        measurements = [m for m in enzmldoc.measurements if m.id in measurement_ids]

    # If an output file is specified, set it up
    if out:
        output_file(out)

    # Create a color map for consistent species colors across tabs
    species_ids = set()
    for measurement in measurements:
        for species_data in measurement.species_data:
            species_ids.add(species_data.species_id)

    # Choose a palette based on the number of species
    num_species = len(species_ids)
    if num_species <= 10:
        palette = Category10[10]
    else:
        palette = Category20[20]

    # Make sure we have enough colors by cycling if needed
    color_map = {}
    for i, species_id in enumerate(sorted(species_ids)):
        color_map[species_id] = palette[i % len(palette)]

    # Create tabs for each measurement
    tabs = []
    for measurement in measurements:
        # Create a tab for this measurement
        tab = _create_measurement_tab(
            enzmldoc, measurement, thinlayer, width, height, color_map, **kwargs
        )
        tabs.append(tab)

    # Return the tabbed layout
    tabs = Tabs(tabs=tabs)

    if show:
        show_bokeh(tabs, notebook_handle=is_nb)

    if out:
        rich.print(f"Saving plot to [bold green]{out}[/bold green]")
        output_file(out)

    return tabs


def _is_notebook() -> bool:
    """
    Check if the current environment is a Jupyter notebook.

    Returns
    -------
    bool
        True if running in a Jupyter notebook, False otherwise.
    """
    try:
        from IPython.core.getipython import get_ipython

        return get_ipython() is not None
    except ModuleNotFoundError:
        return False


def _create_measurement_tab(
    enzmldoc: v2.EnzymeMLDocument,
    measurement: v2.Measurement,
    thinlayer: Optional[BaseThinLayer],
    width: int,
    height: int,
    color_map: Dict[str, str],
    **kwargs,
) -> TabPanel:
    """
    Create a tab panel for a single measurement.

    Parameters
    ----------
    enzmldoc : v2.EnzymeMLDocument
        The EnzymeML document containing the data.
    measurement : v2.Measurement
        The specific measurement to plot.
    thinlayer : Optional[BaseThinLayer]
        A thinlayer object providing model predictions, if available.
    width : int
        Width of the plot in pixels.
    height : int
        Height of the plot in pixels.
    color_map : Dict[str, str]
        Mapping from species ID to color for consistent coloring across tabs.
    **kwargs
        Additional keyword arguments passed to Bokeh plotting functions.

    Returns
    -------
    TabPanel
        A Bokeh TabPanel containing the plot for this measurement.
    """
    # Sort species data by ID for consistent order
    species_data = sorted(
        [s for s in measurement.species_data], key=lambda x: x.species_id
    )

    # Get data types for y-axis label
    dataytypes = _collect_dataytypes(species_data)

    # Create a figure for this measurement
    p = figure(
        width=width,
        height=height,
        title=measurement.name,
        tools="pan,box_zoom,wheel_zoom,reset,save",
        x_axis_label="Time",
        y_axis_label=", ".join(dataytypes),
        **kwargs,
    )

    # Style the plot
    p.grid.grid_line_alpha = 0.3
    p.grid.grid_line_dash = [6, 4]

    # Add hover tool for interactive data inspection
    hover = HoverTool(
        tooltips=[
            ("Species", "@species"),
            ("Time", "@time"),
            ("Value", "@value"),
            ("Type", "@data_type"),
        ]
    )
    p.add_tools(hover)

    # Get model predictions if available
    if thinlayer:
        pred, time = _get_fit(enzmldoc, measurement, thinlayer)
    else:
        pred, time = {}, []

    # Plot each species
    for species in species_data:
        _plot_species_bokeh(p, species, pred, time, color_map, **kwargs)

    # Configure the legend
    p.legend.location = "top_right"
    p.legend.click_policy = "hide"  # Allow toggling visibility by clicking

    # Return the tab panel
    return TabPanel(child=p, title=measurement.name)


def _plot_species_bokeh(
    p: figure,
    species: v2.MeasurementData,
    pred: SimResult,
    time: List[float],
    color_map: Dict[str, str],
    **kwargs,
) -> None:
    """
    Plot experimental data and model fit for a single species using Bokeh.

    Parameters
    ----------
    p : figure
        The Bokeh figure to plot on.
    species : v2.MeasurementData
        The measurement data for a specific species.
    pred : Dict[str, List[float]]
        Model predictions, if available.
    time : List[float]
        Time points for model predictions.
    color_map : Dict[str, str]
        Mapping from species ID to color for consistent coloring across tabs.
    **kwargs
        Additional keyword arguments passed to Bokeh plotting functions.
    """
    # Get color for this species from the color map
    color = color_map[species.species_id]

    # Plot experimental data if available
    if len(species.data) > 0:
        # Create a ColumnDataSource for hover tooltips
        source = ColumnDataSource(
            data={
                "time": species.time,
                "value": species.data,
                "species": [species.species_id] * len(species.time),
                "data_type": [
                    species.data_type.value if species.data_type else "Unknown"
                ]
                * len(species.time),
            }
        )

        p.circle(
            x="time",
            y="value",
            source=source,
            radius=7,
            color=color,
            alpha=1.0,
            legend_label=species.species_id,
            **kwargs,
        )

        # Add model fit if available for this species
        if species.species_id in pred:
            # Create a ColumnDataSource for fit data with hover tooltips
            fit_source = ColumnDataSource(
                data={
                    "time": time,
                    "value": pred[species.species_id],
                    "species": [f"{species.species_id} (fit)"] * len(time),
                    "data_type": ["Model prediction"] * len(time),
                }
            )

            p.line(
                x="time",
                y="value",
                source=fit_source,
                line_width=1.5,
                color=color,
                alpha=1.0,
                legend_label=f"{species.species_id} Fit",
                **kwargs,
            )

    # If no experimental data but model fit is available
    elif species.species_id in pred:
        # Create a ColumnDataSource for fit data with hover tooltips
        fit_source = ColumnDataSource(
            data={
                "time": time,
                "value": pred[species.species_id],
                "species": [f"{species.species_id} (fit)"] * len(time),
                "data_type": ["Model prediction"] * len(time),
            }
        )

        p.line(
            x="time",
            y="value",
            source=fit_source,
            line_width=1.5,
            color=color,
            alpha=0.8,
            legend_label=f"{species.species_id} Fit",
            **kwargs,
        )


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

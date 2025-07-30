from typing import TYPE_CHECKING, Any, get_origin, get_args

if TYPE_CHECKING:
    from pyenzyme.versions.v2 import EnzymeMLDocument


def _is_notebook() -> bool:
    """Check if the current environment is a Jupyter notebook."""
    try:
        from IPython.core.getipython import get_ipython

        ipython = get_ipython()
        return (
            ipython is not None and ipython.__class__.__name__ == "ZMQInteractiveShell"
        )
    except (ModuleNotFoundError, AttributeError):
        return False


def create_interactive_summary(doc: "EnzymeMLDocument") -> None:
    """Create interactive Jupyter notebook summary using ipywidgets."""
    try:
        import ipywidgets as widgets
        from IPython.display import display
    except ImportError:
        raise ImportError("ipywidgets and IPython are required for interactive summary")

    # Display document overview directly (not in accordion)
    overview_content = _create_overview_widget(doc)
    display(overview_content)

    # Create accordion for different categories
    accordion_children = []
    accordion_titles = []

    # Dynamically create sections based on available data
    categories = [
        ("proteins", "🧬 Proteins"),
        ("small_molecules", "⚗️ Small Molecules"),
        ("complexes", "🔗 Complexes"),
        ("vessels", "🧪 Vessels"),
        ("reactions", "⚡ Reactions"),
        ("measurements", "📈 Measurements"),
        ("parameters", "🔢 Parameters"),
        ("equations", "📐 Equations"),
    ]

    for attr_name, title in categories:
        items = getattr(doc, attr_name, [])
        if items:
            if attr_name == "reactions":
                widget = _create_reactions_widget(items)
            elif attr_name == "measurements":
                widget = _create_measurements_widget(items)
            elif attr_name == "parameters":
                widget = _create_parameters_widget(items)
            elif attr_name == "equations":
                widget = _create_equations_widget(items)
            else:
                widget = _create_generic_category_widget(items, attr_name)

            accordion_children.append(widget)
            accordion_titles.append(title)

    # Create accordion only if there are categories with data
    if accordion_children:
        accordion = widgets.Accordion(children=accordion_children)
        for i, title in enumerate(accordion_titles):
            accordion.set_title(i, title)

        # Set first tab open by default
        accordion.selected_index = 0

        display(accordion)


def _create_overview_widget(doc: "EnzymeMLDocument"):
    """Create overview widget for document metadata."""
    import ipywidgets as widgets

    # Add heading
    info_lines = [
        "<h3>📄 Document Overview</h3>",
        f"<b>Name:</b> {doc.name}",
        f"<b>Version:</b> {doc.version}",
    ]

    if doc.description:
        info_lines.append(f"<b>Description:</b> {doc.description}")
    if doc.created:
        info_lines.append(f"<b>Created:</b> {doc.created}")
    if doc.modified:
        info_lines.append(f"<b>Modified:</b> {doc.modified}")

    if doc.creators:
        creators_text = ", ".join(
            [f"{c.given_name} {c.family_name}" for c in doc.creators[:3]]
        )
        if len(doc.creators) > 3:
            creators_text += f" ... (+{len(doc.creators) - 3} more)"
        info_lines.append(f"<b>Creators:</b> {creators_text}")

    return widgets.HTML(value="<br>".join(info_lines))


def _clip_string(text: str, max_length: int) -> str:
    """Clip string to maximum length with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def _get_simple_attributes(obj: Any) -> dict[str, Any]:
    """Dynamically get non-object/array attributes from a model object."""
    simple_attrs = {}

    if hasattr(obj, "model_fields"):
        # Pydantic model - use model_fields
        for field_name, field_info in obj.model_fields.items():
            # Skip JSON-LD fields and complex types
            if field_name.startswith("ld_"):
                continue

            value = getattr(obj, field_name, None)
            if value is None:
                continue

            # Get the field type
            field_type = (
                field_info.annotation if hasattr(field_info, "annotation") else None
            )

            # Check if it's a simple type (not list, not custom object)
            if _is_simple_type(field_type, value):
                # Clip long string values
                if isinstance(value, str):
                    value = _clip_string(value, 50)
                simple_attrs[field_name] = value
    else:
        # Fallback for other objects
        for attr_name in dir(obj):
            if attr_name.startswith("_"):
                continue
            try:
                value = getattr(obj, attr_name)
                if callable(value):
                    continue
                if _is_simple_type(type(value), value):
                    # Clip long string values
                    if isinstance(value, str):
                        value = _clip_string(value, 50)
                    simple_attrs[attr_name] = value
            except (AttributeError, TypeError, ValueError):
                continue

    return simple_attrs


def _is_simple_type(field_type: Any, value: Any) -> bool:
    """Check if a field type is a simple displayable type."""
    if value is None:
        return False

    # Check for basic types
    if isinstance(value, (str, int, float, bool)):
        return True

    # Check for Optional types
    if hasattr(field_type, "__origin__"):
        origin = get_origin(field_type)
        if origin is type(None):  # Optional/Union with None
            return True
        args = get_args(field_type)
        if origin in (type(None), type) and len(args) >= 1:
            # Handle Optional[Type] = Union[Type, None]
            non_none_args = [arg for arg in args if arg is not type(None)]
            if len(non_none_args) == 1:
                return _is_simple_type(non_none_args[0], value)

    # Exclude lists, dicts, custom objects
    if isinstance(value, (list, dict)):
        return False

    # Exclude objects with model_fields (Pydantic models)
    if hasattr(value, "model_fields"):
        return False

    return True


def _create_generic_category_widget(items: list, category_name: str):
    """Create a simple table widget for generic categories."""
    import ipywidgets as widgets
    import pandas as pd

    if not items:
        return widgets.HTML(value=f"<i>No {category_name} found</i>")

    # Create table data for all items
    rows = []
    for item in items:
        attrs = _get_simple_attributes(item)
        if attrs:
            rows.append(attrs)

    if rows:
        df = pd.DataFrame(rows)
        return widgets.HTML(value=df.to_html(index=False, escape=False))
    else:
        return widgets.HTML(value=f"<i>No data to display for {category_name}</i>")


def _format_species_list(species_list: list, separator: str = "<br>") -> str:
    """Format a list of species with stoichiometry."""
    if not species_list:
        return "∅"

    formatted_species = []
    for species in species_list:
        stoich = f"{species.stoichiometry}" if species.stoichiometry != 1 else ""
        formatted_species.append(f"{stoich}{species.species_id}".strip())

    # Use line breaks for few items, commas for many
    if len(formatted_species) <= 3:
        return separator.join(formatted_species)
    else:
        return ", ".join(formatted_species)


def _create_reactions_widget(reactions: list):
    """Create reactions widget with table display."""
    import ipywidgets as widgets
    import pandas as pd

    if not reactions:
        return widgets.HTML(value="<i>No reactions found</i>")

    # Create table data for all reactions
    rows = []
    for reaction in reactions:
        row = {
            "ID": reaction.id,
            "Name": _clip_string(reaction.name, 30),
            "Reactants": _format_species_list(reaction.reactants),
            "Products": _format_species_list(reaction.products),
            "Reversible": "Yes" if reaction.reversible else "No",
        }

        # Add kinetic law equation if available
        if (
            hasattr(reaction, "kinetic_law")
            and reaction.kinetic_law
            and hasattr(reaction.kinetic_law, "equation")
        ):
            equation = _clip_string(reaction.kinetic_law.equation, 60)
            row["Kinetic Law"] = equation
        else:
            row["Kinetic Law"] = "—"

        rows.append(row)

    df = pd.DataFrame(rows)
    return widgets.HTML(value=df.to_html(index=False, escape=False))


def _create_measurements_widget(measurements: list):
    """Create measurements widget with table display including initial conditions."""
    import ipywidgets as widgets
    import pandas as pd

    if not measurements:
        return widgets.HTML(value="<i>No measurements found</i>")

    # Find all species that have initial values in any measurement
    species_with_initials = set()
    for measurement in measurements:
        if measurement.species_data:
            for species in measurement.species_data:
                if hasattr(species, "initial") and species.initial is not None:
                    species_with_initials.add(species.species_id)

    # Sort species IDs for consistent column order
    sorted_species = sorted(species_with_initials)

    # Create table data for all measurements
    rows = []
    for measurement in measurements:
        row = {
            "ID": measurement.id,
            "Name": measurement.name,
        }

        # Add initial condition columns for each species
        for species_id in sorted_species:
            initial_value = "-"
            if measurement.species_data:
                for species in measurement.species_data:
                    if (
                        species.species_id == species_id
                        and hasattr(species, "initial")
                        and species.initial is not None
                    ):
                        initial_value = species.initial
                        break
            row[species_id] = initial_value

        # Add conditions
        if hasattr(measurement, "ph") and measurement.ph:
            row["pH"] = measurement.ph
        if hasattr(measurement, "temperature") and measurement.temperature:
            temp_unit = (
                getattr(measurement.temperature_unit, "name", "")
                if hasattr(measurement, "temperature_unit")
                and measurement.temperature_unit
                else ""
            )
            row["Temperature"] = f"{measurement.temperature} {temp_unit}".strip()

        rows.append(row)

    df = pd.DataFrame(rows)
    return widgets.HTML(value=df.to_html(index=False, escape=False))


def _create_parameters_widget(parameters: list):
    """Create parameters widget with table display."""
    import ipywidgets as widgets
    import pandas as pd

    if not parameters:
        return widgets.HTML(value="<i>No parameters found</i>")

    # Create table of parameters
    rows = []
    for param in parameters:
        attrs = _get_simple_attributes(param)
        rows.append(attrs)

    df = pd.DataFrame(rows)
    return widgets.HTML(value=df.to_html(index=False, escape=False))


def _create_equations_widget(equations: list):
    """Create equations widget with table display."""
    import ipywidgets as widgets
    import pandas as pd

    if not equations:
        return widgets.HTML(value="<i>No equations found</i>")

    # Create table of equations
    rows = []
    for eq in equations:
        equation_str = getattr(eq, "equation", "")

        row = {
            "Species ID": getattr(eq, "species_id", "Unknown"),
            "Equation": _clip_string(equation_str, 60),
            "Type": str(getattr(eq, "equation_type", "unknown"))
            .replace("_", " ")
            .title(),
        }

        # Add variables info if available
        if hasattr(eq, "variables") and eq.variables:
            variables = [
                getattr(var, "symbol", getattr(var, "id", "")) for var in eq.variables
            ]
            row["Variables"] = ", ".join(variables[:5])  # Limit to first 5
            if len(eq.variables) > 5:
                row["Variables"] += f" ... (+{len(eq.variables) - 5} more)"
        else:
            row["Variables"] = "None"

        rows.append(row)

    df = pd.DataFrame(rows)
    return widgets.HTML(value=df.to_html(index=False, escape=False))

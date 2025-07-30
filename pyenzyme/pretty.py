from typing import TYPE_CHECKING
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns

if TYPE_CHECKING:
    from pyenzyme.versions.v2 import EnzymeMLDocument


def summary(
    doc: "EnzymeMLDocument",
    console: Console | None = None,
    interactive: bool = True,
) -> None:
    """
    Create a comprehensive visual summary of an EnzymeML document.

    In Jupyter notebooks, creates interactive widgets with dropdowns and selection.
    In terminal, creates rich formatted tables and panels.

    Args:
        doc: EnzymeMLDocument to summarize
        console: Rich console instance (creates new one if None) - only used for terminal
        interactive: Whether to create interactive widgets in Jupyter notebooks
    """
    try:
        from . import widgets

        if widgets._is_notebook() and interactive:
            widgets.create_interactive_summary(doc)
            return
    except ImportError:
        pass

    # Fall back to terminal summary
    _create_terminal_summary(doc, console)


def _create_terminal_summary(
    doc: "EnzymeMLDocument", console: Console | None = None
) -> None:
    """Create terminal summary using rich formatting."""
    if console is None:
        console = Console()

    # Collect all content in a list
    content_panels = []

    # Overview is always shown
    content_panels.append(_create_overview_panel(doc))

    # Counts and species
    counts_species = _create_counts_and_species_content(doc)
    if counts_species:
        content_panels.append(counts_species)

    # Only add sections that have content
    if doc.vessels:
        content_panels.append(_create_vessels_content(doc))

    if doc.reactions:
        content_panels.append(_create_reactions_content(doc))

    if doc.measurements:
        content_panels.append(_create_measurements_content(doc))

    if doc.parameters:
        content_panels.append(_create_parameters_content(doc))

    if doc.references:
        content_panels.append(_create_references_content(doc))

    # Create a group of all content
    from rich.console import Group

    # Add spacing between sections
    spaced_content = []
    for i, content in enumerate(content_panels):
        spaced_content.append(content)
        if i < len(content_panels) - 1:
            spaced_content.append("")

    # Print title and content separately
    console.print("📋 [bold blue]EnzymeML Document Summary[/bold blue]")

    content_group = Group(*spaced_content)
    console.print(content_group)


def _create_overview_panel(doc: "EnzymeMLDocument") -> Panel:
    """Create the document overview panel with basic information."""
    overview_content = []
    overview_content.append(f"[bold]Name:[/bold] {doc.name}")
    overview_content.append(f"[bold]Version:[/bold] {doc.version}")

    if doc.description:
        overview_content.append(f"[bold]Description:[/bold] {doc.description}")
    if doc.created:
        overview_content.append(f"[bold]Created:[/bold] {doc.created}")
    if doc.modified:
        overview_content.append(f"[bold]Modified:[/bold] {doc.modified}")

    # Add creators info
    if doc.creators:
        creators_text = _format_creators_list(doc.creators)
        overview_content.append(f"[bold]Creators:[/bold] {creators_text}")

    return Panel(
        "\n".join(overview_content),
        title="📄 Document Overview",
        title_align="left",
        border_style="blue",
    )


def _format_creators_list(creators) -> str:
    """Format the creators list with truncation for display."""
    creators_text = ", ".join([f"{c.given_name} {c.family_name}" for c in creators[:3]])
    if len(creators) > 3:
        creators_text += f" ... (+{len(creators) - 3} more)"
    return creators_text


def _create_counts_table(doc: "EnzymeMLDocument") -> Table:
    """Create a table summarizing component counts."""
    counts_table = Table(
        title="📊 Component Counts", show_header=True, header_style="bold magenta"
    )
    counts_table.add_column("Component", no_wrap=True)
    counts_table.add_column("Count", justify="right")

    # Add all component counts
    component_counts = [
        ("Vessels", len(doc.vessels)),
        ("Proteins", len(doc.proteins)),
        ("Complexes", len(doc.complexes)),
        ("Small Molecules", len(doc.small_molecules)),
        ("Reactions", len(doc.reactions)),
        ("Measurements", len(doc.measurements)),
        ("Equations", len(doc.equations)),
        ("Parameters", len(doc.parameters)),
    ]

    for component_name, count in component_counts:
        counts_table.add_row(component_name, str(count))

    return counts_table


def _create_species_table(doc: "EnzymeMLDocument") -> Table:
    """Create a table summarizing species (proteins, molecules, complexes)."""
    species_table = Table(
        title="🧬 Species Details", show_header=True, header_style="bold green"
    )
    species_table.add_column("Type", min_width=12)
    species_table.add_column("ID", style="magenta", min_width=15)
    species_table.add_column("Name", min_width=20)
    species_table.add_column("Details")

    _add_proteins_to_species_table(doc, species_table)
    _add_molecules_to_species_table(doc, species_table)
    _add_complexes_to_species_table(doc, species_table)

    return species_table


def _add_proteins_to_species_table(doc: "EnzymeMLDocument", table: Table) -> None:
    """Add protein entries to the species table."""
    for protein in doc.proteins[:5]:  # Limit to first 5
        details = []
        if protein.organism:
            details.append(f"Organism: {protein.organism}")
        if protein.ecnumber:
            details.append(f"EC: {protein.ecnumber}")
        if protein.vessel_id:
            details.append(f"Vessel: {protein.vessel_id}")

        table.add_row(
            "Protein",
            f"[magenta]{protein.id}[/magenta]",
            protein.name,
            " | ".join(details) if details else "—",
        )

    if len(doc.proteins) > 5:
        table.add_row("", f"... +{len(doc.proteins) - 5} more proteins", "", "")


def _add_molecules_to_species_table(doc: "EnzymeMLDocument", table: Table) -> None:
    """Add small molecule entries to the species table."""
    for molecule in doc.small_molecules[:5]:  # Limit to first 5
        details = []
        if molecule.canonical_smiles:
            details.append(f"SMILES: {molecule.canonical_smiles[:20]}...")
        if molecule.vessel_id:
            details.append(f"Vessel: {molecule.vessel_id}")

        table.add_row(
            "Small Molecule",
            f"[magenta]{molecule.id}[/magenta]",
            molecule.name,
            " | ".join(details) if details else "—",
        )

    if len(doc.small_molecules) > 5:
        table.add_row("", f"... +{len(doc.small_molecules) - 5} more molecules", "", "")


def _add_complexes_to_species_table(doc: "EnzymeMLDocument", table: Table) -> None:
    """Add complex entries to the species table."""
    for complex_obj in doc.complexes[:3]:  # Limit to first 3
        details = []
        if complex_obj.participants:
            details.append(f"Participants: {len(complex_obj.participants)}")
        if complex_obj.vessel_id:
            details.append(f"Vessel: {complex_obj.vessel_id}")

        table.add_row(
            "Complex",
            f"[magenta]{complex_obj.id}[/magenta]",
            complex_obj.name,
            " | ".join(details) if details else "—",
        )

    if len(doc.complexes) > 3:
        table.add_row("", f"... +{len(doc.complexes) - 3} more complexes", "", "")


def _create_counts_and_species_content(doc: "EnzymeMLDocument"):
    """Create the counts and species content."""
    counts_table = _create_counts_table(doc)

    if doc.proteins or doc.small_molecules or doc.complexes:
        species_table = _create_species_table(doc)
        return Columns([counts_table, species_table], equal=True)
    else:
        return counts_table


def _create_vessels_content(doc: "EnzymeMLDocument"):
    """Create vessels content."""
    vessels_table = Table(
        title="🧪 Vessels", show_header=True, header_style="bold yellow"
    )
    vessels_table.add_column("ID", style="magenta")
    vessels_table.add_column("Name")
    vessels_table.add_column("Volume")
    vessels_table.add_column("Constant", justify="center")

    for vessel in doc.vessels:
        unit_str = vessel.unit.name if vessel.unit else "L"
        vessels_table.add_row(
            vessel.id,
            vessel.name,
            f"{vessel.volume} {unit_str}",
            "✓" if vessel.constant else "✗",
        )

    return vessels_table


def _create_reactions_content(doc: "EnzymeMLDocument"):
    """Create reactions content."""
    reactions_table = Table(
        title="⚡ Reactions", show_header=True, header_style="bold red"
    )
    reactions_table.add_column("ID", style="magenta", min_width=12)
    reactions_table.add_column("Name", min_width=20)
    reactions_table.add_column("Reversible", justify="center")
    reactions_table.add_column("Reaction Schema", min_width=30)

    for reaction in doc.reactions[:5]:  # Limit to first 5
        schema = _format_reaction_schema(reaction)

        reactions_table.add_row(
            reaction.id,
            reaction.name,
            "✓" if reaction.reversible else "✗",
            schema,
        )

    if len(doc.reactions) > 5:
        reactions_table.add_row(
            f"... +{len(doc.reactions) - 5} more reactions", "", "", ""
        )

    return reactions_table


def _format_reaction_schema(reaction) -> str:
    """Format reaction schema showing reactants, products and modifiers with IDs."""
    # Format reactants
    reactants = []
    for reactant in reaction.reactants:
        stoich = f"{reactant.stoichiometry}" if reactant.stoichiometry != 1 else ""
        reactants.append(f"{stoich}{reactant.species_id}".strip())

    # Format products
    products = []
    for product in reaction.products:
        stoich = f"{product.stoichiometry}" if product.stoichiometry != 1 else ""
        products.append(f"{stoich}{product.species_id}".strip())

    # Format modifiers
    modifiers = []
    for modifier in reaction.modifiers:
        modifiers.append(modifier.species_id)

    # Build reaction equation
    reactants_str = " + ".join(reactants) if reactants else "∅"
    products_str = " + ".join(products) if products else "∅"

    # Choose arrow based on reversibility
    arrow = "⇌" if reaction.reversible else "→"

    schema = f"{reactants_str} {arrow} {products_str}"

    # Add modifiers if present
    if modifiers:
        modifiers_str = ", ".join(modifiers)
        schema += f" [{modifiers_str}]"

    return schema


def _create_measurements_content(doc: "EnzymeMLDocument"):
    """Create measurements content."""
    measurements_table = Table(
        title="📈 Measurements", show_header=True, header_style="bold cyan"
    )
    measurements_table.add_column("ID", style="magenta", min_width=12)
    measurements_table.add_column("Name", min_width=20)
    measurements_table.add_column("Species Data", justify="center")
    measurements_table.add_column("Conditions")

    for measurement in doc.measurements[:5]:  # Limit to first 5
        conditions = _format_measurement_conditions(measurement)
        measurements_table.add_row(
            measurement.id,
            measurement.name,
            str(len(measurement.species_data)),
            conditions,
        )

    if len(doc.measurements) > 5:
        measurements_table.add_row(
            f"... +{len(doc.measurements) - 5} more measurements", "", "", ""
        )

    return measurements_table


def _format_measurement_conditions(measurement) -> str:
    """Format measurement conditions for display."""
    conditions = []
    if measurement.ph:
        conditions.append(f"pH: {measurement.ph}")
    if measurement.temperature:
        temp_unit = (
            measurement.temperature_unit.name if measurement.temperature_unit else ""
        )
        conditions.append(f"T: {measurement.temperature} {temp_unit}")
    return " | ".join(conditions) if conditions else "—"


def _create_parameters_content(doc: "EnzymeMLDocument"):
    """Create parameters content."""
    parameters_table = Table(
        title="🔢 Parameters", show_header=True, header_style="bold purple"
    )
    parameters_table.add_column("Symbol", style="magenta")
    parameters_table.add_column("Name")
    parameters_table.add_column("Value")
    parameters_table.add_column("Initial Value")
    parameters_table.add_column("Bounds")
    parameters_table.add_column("Unit")
    parameters_table.add_column("Constant", justify="center")

    for param in doc.parameters[:8]:  # Limit to first 8
        # Pre-populate all data for the parameter
        symbol = param.symbol or "—"
        name = param.name or "—"
        value_str = str(param.value) if param.value is not None else "—"
        initial_value_str = (
            str(param.initial_value) if param.initial_value is not None else "—"
        )

        # Format bounds as [lower, upper]
        if param.lower_bound is not None and param.upper_bound is not None:
            bounds_str = f"[{param.lower_bound}, {param.upper_bound}]"
        elif param.lower_bound is not None:
            bounds_str = f"[{param.lower_bound}, ∞]"
        elif param.upper_bound is not None:
            bounds_str = f"[-∞, {param.upper_bound}]"
        else:
            bounds_str = "—"

        unit_str = param.unit.name if param.unit else "—"
        constant_str = "✓" if param.constant else "✗"

        parameters_table.add_row(
            symbol,
            name,
            value_str,
            initial_value_str,
            bounds_str,
            unit_str,
            constant_str,
        )

    return parameters_table


def _create_references_content(doc: "EnzymeMLDocument"):
    """Create references content."""
    refs_text = f"📚 [bold]References:[/bold] {len(doc.references)} items"
    if len(doc.references) <= 3:
        refs_text += "\n" + "\n".join([f"  • {ref}" for ref in doc.references])
    else:
        refs_text += "\n" + "\n".join([f"  • {ref}" for ref in doc.references[:3]])
        refs_text += f"\n  • ... +{len(doc.references) - 3} more"

    return Panel(refs_text, border_style="dim")

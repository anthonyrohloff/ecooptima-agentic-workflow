import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing_extensions import TypedDict, Literal
from agents import Agent, FunctionTool, RunContextWrapper, function_tool
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


# TypedDict for structured bar chart data (label-value pairs)
# They are separated because pie charts and bar charts may be configured differently in the future
class BarChartPoint(TypedDict):
    label: str
    value: float | int | str


class PieChartPoint(TypedDict):
    label: str
    value: float | int | str


# Regex helper to extract numeric values from agent response strings
def _coerce_numeric(raw_value: float | int | str) -> float:
    # If the value is already numeric, return it as float
    if isinstance(raw_value, (int, float)):
        return float(raw_value)

    # Otherwise, use regex to find a numeric pattern in the string
    match = re.search(r"-?\d+(?:\.\d+)?", raw_value)

    # If no match is found, raise an error
    if not match:
        raise ValueError(f"Could not extract a numeric value from '{raw_value}'.")
    return float(match.group())


def _generate_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


# Helper to create a filesystem-safe slug from a title, like "Tree Height Comparison" -> "tree-height-comparison"
def _slugify_title(title: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", title).strip("-").lower()
    return slug or "tree-chart"


# Bar chart plotting function
@function_tool(name_override="plot_bar_chart")
def plot_bar_chart(
    series: list[BarChartPoint],  # list of (label, value) pairs to chart
    metric_name: str,  # the name of the metric being charted (e.g., "Height", "Canopy Spread")
    title: str
    | None = None,  # optional chart title (from the agent, else default generated below)
    top_n: int | None = None,  # number of top entries to include (top 10, top 5, etc.)
    orientation: Literal[
        "horizontal", "vertical"
    ] = "horizontal",  # chart orientation with default "horizontal" and option for "vertical" - no other options allowed
    output_directory: str = "response_log",  # directory to save the chart image files
) -> str:  # should return a string path to the saved chart image file
    """Generate a bar chart from structured tree metrics."""
    # No data provided error
    if not series:
        raise ValueError("Provide at least one (label, value) pair to chart.")

    cleaned: list[
        tuple[str, float]
    ] = []  # type hint: list of (label, numeric value) pairs, starts empty. Same as cleaned = [], except with type hint
    for entry in series:
        label = (
            entry.get("label") or entry.get("name") or entry.get("tree")
        )  # setting label to the string the agent provides - could be 'label', 'name', or 'tree'. If none, raise error below

        # Error if no label found
        if not label:
            raise ValueError("Each entry must include a label or tree name.")
        cleaned.append(
            (label, _coerce_numeric(entry["value"]))
        )  # append (label, numeric value) tuple to cleaned list - this is the data we will plot

    # Sort key value pairs and limit to top_n if specified
    cleaned.sort(key=lambda row: row[1], reverse=True)
    if top_n:
        cleaned = cleaned[: max(1, top_n)]

    # Chart saving setup
    chart_dir = Path(os.environ.get("ECOOPTIMA_LOG_DIR", output_directory))
    chart_dir.mkdir(parents=True, exist_ok=True)
    safe_title = title or f"{metric_name} for selected trees"
    filename = (
        f"{_slugify_title(safe_title)}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.png"
    )
    chart_path = chart_dir / filename

    # Plotting
    labels = [label for label, _ in cleaned]  # extract labels from cleaned data
    values = [value for _, value in cleaned]  # extract values from cleaned data
    fig_height = max(
        3.5, len(labels) * 0.6
    )  # dynamic figure height based on number of labels
    fig, ax = plt.subplots(
        figsize=(9, fig_height)
    )  # create figure and axis with specified size

    # Plot based on orientation
    if orientation == "horizontal":
        ax.barh(labels, values, color="#2f855a")
        ax.invert_yaxis()
        ax.set_xlabel(metric_name)
    else:
        ax.bar(labels, values, color="#2f855a")
        ax.set_ylabel(metric_name)
        ax.set_xticklabels(labels, rotation=35, ha="right")

    # Set title
    ax.set_title(safe_title)

    # Add value labels
    for index, value in enumerate(values):
        # Format value to 2 decimal places, removing trailing zeros
        formatted = f"{value:.2f}".rstrip("0").rstrip(".")

        # Position label based on orientation
        if orientation == "horizontal":
            ax.text(value, index, f" {formatted}", va="center", fontsize=9)
        else:
            ax.text(index, value, formatted, ha="center", va="bottom", fontsize=9)

    # Finalize and save chart
    fig.tight_layout()
    fig.savefig(chart_path)
    plt.close(fig)
    return f"Bar chart saved to {chart_path.resolve().as_posix()}"


# Pie chart plotting function
@function_tool(name_override="plot_pie_chart")
def plot_pie_chart(
    series: list[PieChartPoint],  # list of (label, value) pairs to chart
    metric_name: str,  # the name of the metric being charted (e.g., "Height", "Canopy Spread")
    title: str
    | None = None,  # optional chart title (from the agent, else default generated below)
    top_n: int | None = None,  # number of top entries to include (top 10, top 5, etc.)
    output_directory: str = "response_log",  # directory to save the chart image files
) -> str:  # should return a string path to the saved chart image file
    """Generate a pie chart from structured tree metrics."""
    # No data provided error
    if not series:
        raise ValueError("Provide at least one (label, value) pair to chart.")

    cleaned: list[
        tuple[str, float]
    ] = []  # type hint: list of (label, numeric value) pairs, starts empty. Same as cleaned = [], except with type hint
    for entry in series:
        label = (
            entry.get("label") or entry.get("name") or entry.get("tree")
        )  # setting label to the string the agent provides - could be 'label', 'name', or 'tree'. If none, raise error below

        # Error if no label found
        if not label:
            raise ValueError("Each entry must include a label or tree name.")
        cleaned.append(
            (label, _coerce_numeric(entry["value"]))
        )  # append (label, numeric value) tuple to cleaned list - this is the data we will plot

    # Sort key value pairs and limit to top_n if specified, giving "Other" category for remaining values
    cleaned = sorted(cleaned, key=lambda r: r[1], reverse=True)
    if top_n and len(cleaned) > top_n:
        kept = cleaned[: top_n - 1]
        other_value = sum(value for _, value in cleaned[top_n - 1 :])
        cleaned = kept + [("Other", other_value)]

    # Chart saving setup
    chart_dir = Path(os.environ.get("ECOOPTIMA_LOG_DIR", output_directory))
    chart_dir.mkdir(parents=True, exist_ok=True)
    safe_title = (
        title or f"{metric_name} for selected trees"
    )  # default title if none provided
    filename = (
        f"{_slugify_title(safe_title)}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.png"
    )
    chart_path = chart_dir / filename

    # Plotting
    labels = [label for label, _ in cleaned]  # extract labels from cleaned data
    values = [value for _, value in cleaned]  # extract values from cleaned data
    fig_height = max(
        3.5, len(labels) * 0.6
    )  # dynamic figure height based on number of labels
    fig, ax = plt.subplots(
        figsize=(9, fig_height)
    )  # create figure and axis with specified size
    ax.pie(values, labels=labels)  # create pie chart

    # Set title
    ax.set_title(safe_title)

    # Finalize and save chart
    fig.tight_layout()
    fig.savefig(chart_path)
    plt.close(fig)
    return f"Pie chart saved to {chart_path.resolve().as_posix()}"

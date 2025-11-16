import json
import re
from datetime import datetime
from pathlib import Path
from typing import Iterable

from typing_extensions import TypedDict, Literal, Any

from agents import Agent, FunctionTool, RunContextWrapper, function_tool
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


class Location(TypedDict):
    lat: float
    long: float


class BarChartPoint(TypedDict):
    label: str
    value: float | int | str


class PieChartPoint(TypedDict):
    label: str
    value: float | int | str

# Regex helper to extract numeric values from agent response strings
def _coerce_numeric(raw_value: float | int | str) -> float:
    if isinstance(raw_value, (int, float)):
        return float(raw_value)
    match = re.search(r"-?\d+(?:\.\d+)?", raw_value)
    if not match:
        raise ValueError(f"Could not extract a numeric value from '{raw_value}'.")
    return float(match.group())


# Helper to create a filesystem-safe slug from a title
def _slugify_title(title: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", title).strip("-").lower()
    return slug or "tree-chart"


@function_tool(name_override="plot_tree_metric_bar_chart")
def plot_tree_metric_bar_chart(
    series: list[BarChartPoint],
    metric_name: str,
    title: str | None = None,
    top_n: int | None = None, # number of top entries to include (top 10, top 5, etc.)
    orientation: Literal["horizontal", "vertical"] = "horizontal",
    output_directory: str = "charts",
) -> str:
    """Generate a bar chart from structured tree metrics."""
    if not series:
        raise ValueError("Provide at least one (label, value) pair to chart.")

    cleaned: list[tuple[str, float]] = [] # type hint: list of (label, numeric value) pairs, starts empty. Same as cleaned = [], except with type hint.
    for entry in series:
        label = entry.get("label") or entry.get("name") or entry.get("tree") # setting label to the string the agent provides - could be 'label', 'name', or 'tree'. If none, raise error below.
        if not label:
            raise ValueError("Each entry must include a label or tree name.")
        cleaned.append((label, _coerce_numeric(entry["value"])))

    # Sort kv pairs and limit to top_n if specified
    cleaned.sort(key=lambda row: row[1], reverse=True)
    if top_n:
        cleaned = cleaned[: max(1, top_n)]

    chart_dir = Path(output_directory)
    chart_dir.mkdir(parents=True, exist_ok=True)
    safe_title = title or f"{metric_name} for selected trees"
    filename = f"{_slugify_title(safe_title)}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.png"
    chart_path = chart_dir / filename

    labels = [label for label, _ in cleaned]
    values = [value for _, value in cleaned]
    fig_height = max(3.5, len(labels) * 0.6)
    fig, ax = plt.subplots(figsize=(9, fig_height))

    if orientation == "horizontal":
        ax.barh(labels, values, color="#2f855a")
        ax.invert_yaxis()
        ax.set_xlabel(metric_name)
    else:
        ax.bar(labels, values, color="#2f855a")
        ax.set_ylabel(metric_name)
        ax.set_xticklabels(labels, rotation=35, ha="right")

    ax.set_title(safe_title)
    for index, value in enumerate(values):
        formatted = f"{value:.2f}".rstrip("0").rstrip(".")
        if orientation == "horizontal":
            ax.text(value, index, f" {formatted}", va="center", fontsize=9)
        else:
            ax.text(index, value, formatted, ha="center", va="bottom", fontsize=9)

    fig.tight_layout()
    fig.savefig(chart_path)
    plt.close(fig)
    return f"Bar chart saved to {chart_path.resolve().as_posix()}"


@function_tool(name_override="plot_tree_metric_pie_chart")
def plot_tree_metric_pie_chart(
    series: list[PieChartPoint],
    metric_name: str,
    title: str | None = None,
    top_n: int | None = None, # number of top entries to include (top 10, top 5, etc.)
    output_directory: str = "charts",
) -> str:
    
    """Generate a pie chart from structured tree metrics."""
    if not series:
        raise ValueError("Provide at least one (label, value) pair to chart.")

    cleaned: list[tuple[str, float]] = [] # type hint: list of (label, numeric value) pairs, starts empty. Same as cleaned = [], except with type hint.
    for entry in series:
        label = entry.get("label") or entry.get("name") or entry.get("tree") # setting label to the string the agent provides - could be 'label', 'name', or 'tree'. If none, raise error below.
        if not label:
            raise ValueError("Each entry must include a label or tree name.")
        cleaned.append((label, _coerce_numeric(entry["value"]))) # append (label, numeric value) tuple to cleaned list

    # Sort kv pairs and limit to top_n if specified, giving "Other" category for remaining values
    cleaned = sorted(cleaned, key=lambda r: r[1], reverse=True)
    if top_n and len(cleaned) > top_n:
        kept = cleaned[: top_n - 1]
        other_value = sum(value for _, value in cleaned[top_n - 1 :])
        cleaned = kept + [("Other", other_value)]

    # Chart saving setup
    chart_dir = Path(output_directory)
    chart_dir.mkdir(parents=True, exist_ok=True)
    safe_title = title or f"{metric_name} for selected trees" # default title if none provided
    filename = f"{_slugify_title(safe_title)}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.png"
    chart_path = chart_dir / filename

    # Plotting
    labels = [label for label, _ in cleaned]
    values = [value for _, value in cleaned]
    fig_height = max(3.5, len(labels) * 0.6)
    fig, ax = plt.subplots(figsize=(9, fig_height))
    ax.pie(values, labels=labels)

    fig.tight_layout()
    fig.savefig(chart_path)
    plt.close(fig)
    return f"Pie chart saved to {chart_path.resolve().as_posix()}"


@function_tool(name_override="fetch_data")
def read_file(ctx: RunContextWrapper[Any], path: str, directory: str | None = None) -> str:
    return "<file contents>"


agent = Agent(
    name="Assistant",
    tools=[read_file, plot_tree_metric_bar_chart],
)

for tool in agent.tools:
    if isinstance(tool, FunctionTool):
        print(tool.name)
        print(tool.description)
        print(json.dumps(tool.params_json_schema, indent=2))
        print()

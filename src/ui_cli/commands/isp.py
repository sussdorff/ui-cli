"""ISP metrics commands."""

import asyncio
from enum import Enum
from typing import Annotated

import typer

from ui_cli.client import APIError, UniFiClient
from ui_cli.output import OutputFormat, print_error, render_output

app = typer.Typer(help="View ISP performance metrics")

# Column definitions for ISP metrics table
ISP_COLUMNS = [
    ("siteId", "Site ID"),
    ("hostId", "Host ID"),
    ("ispName", "ISP Name"),
    ("avgLatency", "Avg Latency (ms)"),
    ("maxLatency", "Max Latency (ms)"),
    ("downloadKbps", "Download (kbps)"),
    ("uploadKbps", "Upload (kbps)"),
    ("packetLoss", "Packet Loss (%)"),
    ("uptime", "Uptime"),
    ("timestamp", "Timestamp"),
]


class MetricInterval(str, Enum):
    """ISP metric interval options."""

    FIVE_MIN = "5m"
    HOURLY = "1h"


@app.command("metrics")
def get_metrics(
    interval: Annotated[
        MetricInterval,
        typer.Option(
            "--interval",
            "-i",
            help="Metric interval: 5m (24h retention) or 1h (30d retention)",
        ),
    ] = MetricInterval.HOURLY,
    hours: Annotated[
        int | None,
        typer.Option(
            "--hours",
            "-H",
            help="Hours of data to retrieve (default: 24 for 5m, 168 for 1h)",
        ),
    ] = None,
    output: Annotated[
        OutputFormat,
        typer.Option(
            "--output",
            "-o",
            help="Output format: table, json, or csv",
        ),
    ] = OutputFormat.TABLE,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Show detailed request/response information",
        ),
    ] = False,
) -> None:
    """Get ISP performance metrics for all sites.

    Metrics include latency (avg/max), download/upload speeds, uptime/downtime,
    packet loss, and ISP information.

    Data retention:
    - 5m interval: 24 hours
    - 1h interval: 30 days
    """

    async def _get() -> list:
        client = UniFiClient()
        return await client.get_isp_metrics(metric_type=interval.value, duration_hours=hours)

    try:
        metrics = asyncio.run(_get())

        if verbose:
            typer.echo(f"Found {len(metrics)} metric record(s)")

        render_output(
            data=metrics,
            output_format=output,
            columns=ISP_COLUMNS,
            title=f"ISP Metrics ({interval.value})",
            verbose=verbose,
        )
    except APIError as e:
        print_error(e.message)
        raise typer.Exit(1)

import os
from typing import Optional, Any
import pandas as pd
import requests
import json
from shapely.geometry import shape, Point

import typer
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


def get_config() -> tuple[str, str]:
    """Get API tokens from environment variables (after loading .env)."""
    load_dotenv()
    one_map_api_token = os.getenv("ONE_MAP_API_TOKEN")
    data_sg_api = os.getenv("DATA_SG_API")
    if not one_map_api_token:
        console.print(
            "[bold red]ERROR:[/] ONE_MAP_API_TOKEN environment variable not set."
        )
        raise typer.Exit(code=1)
    if not data_sg_api:
        console.print("[bold red]ERROR:[/] DATA_SG_API environment variable not set.")
        raise typer.Exit(code=1)
    return one_map_api_token, data_sg_api


def fetch_planning_areas(one_map_api_token: str) -> pd.DataFrame:
    """Fetch planning area boundaries from OneMap API."""
    url = "https://www.onemap.gov.sg/api/public/popapi/getAllPlanningarea?year=2019"
    headers = {"Authorization": one_map_api_token}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        areas = pd.DataFrame.from_records(response.json()["SearchResults"])

        def extract_shape(geojson: str) -> Optional[Any]:
            try:
                return shape(json.loads(geojson))
            except Exception as e:
                console.print(f"[yellow]Warning:[/] Failed to parse geojson: {e}")
                return None

        areas["geojson"] = areas["geojson"].apply(lambda geojson: extract_shape(geojson))  # type: ignore
        return areas
    except Exception as e:
        console.print(f"[bold red]ERROR:[/] Error fetching planning areas: {e}")
        raise typer.Exit(code=1)


def fetch_taxi_availability(data_sg_api: str) -> pd.DataFrame:
    """Fetch current taxi locations from Data.gov.sg API."""
    url = "https://api.data.gov.sg/v1/transport/taxi-availability"
    headers = {"X-Api-Key": data_sg_api}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        coords = data["features"][0]["geometry"]["coordinates"]
        df = pd.DataFrame(coords, columns=["long", "lat"])
        return df
    except Exception as e:
        console.print(f"[bold red]ERROR:[/] Error fetching taxi availability: {e}")
        raise typer.Exit(code=1)


def get_planning_area(row: pd.Series, areas: pd.DataFrame) -> Optional[str]:
    """Return the planning area name for a given taxi location (row)."""
    point = Point(row["long"], row["lat"])
    for _, area in areas.iterrows():
        if area["geojson"] and area["geojson"].contains(point):
            return area["pln_area_n"]
    return None


def get_area_description(lat: float, long: float) -> str:
    """Reverse geocode coordinates to get a human-readable location description."""
    url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={long}&zoom=16&addressdetails=1"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code == 200:
            data = response.json()
            return data.get("display_name", "Unknown")
        else:
            console.print(
                f"[yellow]Warning:[/] Reverse geocoding failed for {lat},{long} with status {response.status_code}"
            )
            return "Unknown"
    except Exception as e:
        console.print(
            f"[yellow]Warning:[/] Reverse geocoding exception for {lat},{long}: {e}"
        )
        return "Unknown"


app = typer.Typer(help="Taxi Availability and Planning Area Analysis")


@app.command()
def main(top_k: int = 10):
    """Fetch, analyze, and display taxi availability by planning area."""
    try:
        one_map_api_token, data_sg_api = get_config()
        console.print("[bold blue]Fetching planning areas...[/]")
        areas = fetch_planning_areas(one_map_api_token)
        console.print(f"[green]Fetched {len(areas)} planning areas.[/]")

        console.print("[bold blue]Fetching taxi availability...[/]")
        df = fetch_taxi_availability(data_sg_api)
        console.print(f"[green]Fetched {len(df)} taxi locations.[/]")

        console.print(
            "[bold blue]Mapping taxis to planning areas (this may take a while)...[/]"
        )
        df["planning_area"] = df.apply(lambda row: get_planning_area(row, areas), axis=1)  # type: ignore

        top_ten = df["planning_area"].value_counts().head(top_k)
        table = Table(title=f"Total Available Taxis: {len(df)}", show_lines=True)
        table.add_column("#", style="cyan", justify="right")
        table.add_column("Area", style="magenta")
        table.add_column("Count", style="green", justify="right")
        table.add_column("Location", style="yellow")
        table.add_column("Google Maps Link", style="blue", overflow="fold")

        # Prepare data for threading
        area_info = []
        for idx, (area, count) in enumerate(top_ten.items(), 1):
            coords = df[df["planning_area"] == area][["lat", "long"]].mean()
            lat, long = coords["lat"], coords["long"]
            gmap_link = f"https://www.google.com/maps/search/?api=1&query={lat},{long}"
            area_info.append((idx, area, count, lat, long, gmap_link))

        # Fetch descriptions in parallel with a loader
        from typing import List

        descriptions: List[str] = [""] * len(area_info)
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
            console=console,
        ) as progress:
            task = progress.add_task(
                "Fetching area descriptions...", total=len(area_info)
            )
            with ThreadPoolExecutor(max_workers=2) as executor:
                future_to_idx = {
                    executor.submit(get_area_description, lat, long): i
                    for i, (_, _, _, lat, long, _) in enumerate(area_info)
                }
                for future in as_completed(future_to_idx):
                    idx = future_to_idx[future]
                    try:
                        descriptions[idx] = future.result()
                    except Exception as e:
                        descriptions[idx] = f"Error: {e}"
                    progress.advance(task)

        for (idx, area, count, lat, long, gmap_link), description in zip(
            area_info, descriptions
        ):
            table.add_row(
                str(idx), area or "Unknown", str(count), description, gmap_link
            )

        console.print(table)
    except Exception as e:
        console.print(f"[bold red]FATAL ERROR:[/] {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()

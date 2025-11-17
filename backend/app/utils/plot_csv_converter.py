"""
Plot CSV Converter - Convert plot.json to/from CSV for user editing.

Supports both General Mode and Story Mode plot formats.
"""
import logging
import json
import csv
from pathlib import Path
from typing import Dict, List
from io import StringIO

logger = logging.getLogger(__name__)


def plot_to_csv(plot_data: Dict, mode: str = "general") -> str:
    """
    Convert plot.json to CSV string for user editing.

    Args:
        plot_data: Plot JSON data
        mode: "general" or "story"

    Returns:
        CSV string representation of plot
    """
    output = StringIO()

    if mode == "general":
        # General Mode: scene_id, image_prompt, text, speaker, duration_ms
        fieldnames = ["scene_id", "image_prompt", "text", "speaker", "duration_ms"]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for scene in plot_data.get("scenes", []):
            writer.writerow({
                "scene_id": scene.get("scene_id", ""),
                "image_prompt": scene.get("image_prompt", ""),
                "text": scene.get("text", ""),
                "speaker": scene.get("speaker", ""),
                "duration_ms": scene.get("duration_ms", 5000)
            })

    elif mode == "story":
        # Story Mode: more complex with characters
        fieldnames = [
            "scene_id", "char1_id", "char1_expression", "char1_pose", "char1_pos",
            "speaker", "text", "background_img", "duration_ms"
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for scene in plot_data.get("scenes", []):
            writer.writerow({
                "scene_id": scene.get("scene_id", ""),
                "char1_id": scene.get("char1_id", ""),
                "char1_expression": scene.get("char1_expression", ""),
                "char1_pose": scene.get("char1_pose", ""),
                "char1_pos": scene.get("char1_pos", ""),
                "speaker": scene.get("speaker", ""),
                "text": scene.get("text", ""),
                "background_img": scene.get("background_img", ""),
                "duration_ms": scene.get("duration_ms", 5000)
            })

    csv_content = output.getvalue()
    output.close()

    logger.info(f"Converted plot to CSV ({len(plot_data.get('scenes', []))} scenes)")
    return csv_content


def csv_to_plot(csv_content: str, mode: str = "general", original_plot: Dict = None) -> Dict:
    """
    Convert CSV string back to plot.json format.

    Args:
        csv_content: CSV string from user
        mode: "general" or "story"
        original_plot: Original plot data (to preserve bgm_prompt, etc.)

    Returns:
        Updated plot JSON data
    """
    input_stream = StringIO(csv_content)
    reader = csv.DictReader(input_stream)

    scenes = []
    for row in reader:
        if mode == "general":
            scene = {
                "scene_id": row.get("scene_id", ""),
                "image_prompt": row.get("image_prompt", ""),
                "text": row.get("text", ""),
                "speaker": row.get("speaker", "char_1"),
                "duration_ms": int(row.get("duration_ms", 5000))
            }
        elif mode == "story":
            scene = {
                "scene_id": row.get("scene_id", ""),
                "char1_id": row.get("char1_id", ""),
                "char1_expression": row.get("char1_expression", "neutral"),
                "char1_pose": row.get("char1_pose", "standing"),
                "char1_pos": row.get("char1_pos", "center"),
                "speaker": row.get("speaker", ""),
                "text": row.get("text", ""),
                "background_img": row.get("background_img", ""),
                "duration_ms": int(row.get("duration_ms", 5000))
            }

        scenes.append(scene)

    input_stream.close()

    # Build final plot data
    plot_data = {"scenes": scenes}

    # Preserve bgm_prompt from original plot if available
    if original_plot and "bgm_prompt" in original_plot:
        plot_data["bgm_prompt"] = original_plot["bgm_prompt"]

    logger.info(f"Converted CSV to plot ({len(scenes)} scenes)")
    return plot_data


def save_plot_csv(run_id: str, plot_data: Dict, mode: str = "general") -> Path:
    """
    Save plot as CSV file for user download/editing.

    Args:
        run_id: Run identifier
        plot_data: Plot JSON data
        mode: "general" or "story"

    Returns:
        Path to saved CSV file
    """
    output_dir = Path(f"app/data/outputs/{run_id}").resolve()  # Use absolute path
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_path = output_dir / "plot.csv"
    csv_content = plot_to_csv(plot_data, mode)

    csv_path.write_text(csv_content, encoding="utf-8")
    logger.info(f"Saved plot CSV to {csv_path}")

    return csv_path


def load_and_update_plot(run_id: str, csv_content: str, mode: str = "general") -> Path:
    """
    Load CSV content and update plot.json file.

    Args:
        run_id: Run identifier
        csv_content: CSV string from user
        mode: "general" or "story"

    Returns:
        Path to updated plot.json
    """
    output_dir = Path(f"app/data/outputs/{run_id}")
    plot_path = output_dir / "plot.json"

    # Load original plot to preserve metadata
    original_plot = None
    if plot_path.exists():
        with open(plot_path, 'r', encoding='utf-8') as f:
            original_plot = json.load(f)

    # Convert CSV to plot
    updated_plot = csv_to_plot(csv_content, mode, original_plot)

    # Save updated plot
    with open(plot_path, 'w', encoding='utf-8') as f:
        json.dump(updated_plot, f, ensure_ascii=False, indent=2)

    logger.info(f"Updated plot.json from CSV ({len(updated_plot['scenes'])} scenes)")
    return plot_path

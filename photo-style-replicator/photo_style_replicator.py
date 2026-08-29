#!/usr/bin/env python3
"""Analyze a reference photo and reproduce its broad tone in Photoshop.

The analysis is intentionally explainable: it estimates global color and tonal
statistics, then emits a JSX script using Photoshop's documented adjustment APIs.
It cannot recover the original artist's exact layer history from a flattened image.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


def load_image(path: Path) -> np.ndarray:
    try:
        with Image.open(path) as image:
            return np.asarray(image.convert("RGB"), dtype=np.float32) / 255.0
    except (OSError, ValueError) as exc:
        raise SystemExit(f"cannot read image {path}: {exc}")


def percentile_channel(values: np.ndarray, percentile: float) -> float:
    return float(np.percentile(values, percentile))


def analyze(path: Path) -> dict[str, Any]:
    source_image = load_image(path)
    pixels = source_image.reshape(-1, 3)
    luminance = pixels @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    maximum = pixels.max(axis=1)
    minimum = pixels.min(axis=1)
    saturation = np.divide(maximum - minimum, maximum, out=np.zeros_like(maximum), where=maximum > 1e-6)
    mean_rgb = pixels.mean(axis=0)
    warm_cast = float(mean_rgb[0] - mean_rgb[2])
    contrast = float(luminance.std())
    mean_saturation = float(saturation.mean())
    palette = Image.fromarray(np.uint8(np.clip(source_image * 255, 0, 255)), "RGB").quantize(colors=6)
    colors = palette.getpalette()[:18]
    counts = sorted(palette.getcolors() or [], reverse=True)
    dominant = []
    for count, index in counts[:6]:
        offset = index * 3
        dominant.append({"rgb": [int(v) for v in colors[offset:offset + 3]], "share": round(count / len(pixels), 4)})

    if warm_cast > 0.035:
        temperature = "warm"
    elif warm_cast < -0.035:
        temperature = "cool"
    else:
        temperature = "neutral"
    if contrast > 0.23:
        contrast_style = "high contrast"
    elif contrast < 0.12:
        contrast_style = "soft contrast"
    else:
        contrast_style = "moderate contrast"
    if mean_saturation > 0.48:
        color_style = "high saturation"
    elif mean_saturation < 0.2:
        color_style = "muted color"
    else:
        color_style = "balanced saturation"

    techniques = ["global tonal balancing"]
    if contrast > 0.18:
        techniques.append("curves-like contrast shaping")
    if abs(warm_cast) > 0.025:
        techniques.append(f"{temperature} color balance")
    if mean_saturation > 0.35:
        techniques.append("hue/saturation enhancement")
    if percentile_channel(luminance, 10) < 0.12 and percentile_channel(luminance, 90) > 0.78:
        techniques.append("shadow/highlight separation")

    return {
        "source": str(path),
        "image": {"width": int(source_image.shape[1]), "height": int(source_image.shape[0])},
        "tone": {
            "mean_luminance": round(float(luminance.mean()), 5),
            "luminance_std": round(contrast, 5),
            "p10": round(percentile_channel(luminance, 10), 5),
            "p50": round(percentile_channel(luminance, 50), 5),
            "p90": round(percentile_channel(luminance, 90), 5),
            "contrast_style": contrast_style,
        },
        "color": {
            "mean_rgb": [round(float(v), 5) for v in mean_rgb],
            "mean_saturation": round(mean_saturation, 5),
            "temperature": temperature,
            "warm_cast": round(warm_cast, 5),
            "style": color_style,
            "dominant_palette": dominant,
        },
        "techniques": techniques,
        "limitations": [
            "A flattened photo cannot reveal the original Photoshop layer stack or exact tools.",
            "The generated adjustments approximate global appearance and should be reviewed by a human.",
        ],
    }


def js_number(value: float) -> str:
    return f"{value:.3f}"


def jsx_for(report: dict[str, Any], target: Path, output: Path) -> str:
    tone = report["tone"]
    color = report["color"]
    contrast = max(-50.0, min(50.0, (tone["luminance_std"] - 0.18) * 180.0))
    saturation = max(-35.0, min(35.0, (color["mean_saturation"] - 0.3) * 70.0))
    warmth = max(-25.0, min(25.0, color["warm_cast"] * 220.0))
    target_js = target.resolve().as_posix().replace("'", "\\'")
    output_js = output.resolve().as_posix().replace("'", "\\'")
    return f"""#target photoshop
var inputFile = new File('{target_js}');
var outputFile = new File('{output_js}');
var doc = app.open(inputFile);
var layer = doc.activeLayer;
layer.adjustBrightnessContrast(0, {js_number(contrast)});
layer.adjustColorBalance([{js_number(warmth)}, 0, {js_number(-warmth)}], [0, 0, 0], [{js_number(warmth / 2)}, 0, {js_number(-warmth / 2)}], true);
var options = new JPEGSaveOptions();
options.quality = 12;
doc.saveAs(outputFile, options, true);
doc.close(SaveOptions.DONOTSAVECHANGES);
"""


def run_photoshop(jsx_path: Path) -> None:
    escaped = str(jsx_path.resolve()).replace("'", "''")
    command = ["powershell", "-NoProfile", "-Command", f"$app = New-Object -ComObject Photoshop.Application; $app.DoJavaScriptFile('{escaped}')"]
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
    if result.returncode != 0:
        details = (result.stderr or result.stdout or "unknown error").strip()
        raise SystemExit(f"Photoshop automation failed: {details}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("target", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--no-photoshop", action="store_true", help="only write analysis and JSX")
    args = parser.parse_args()
    report = analyze(args.reference)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    jsx_path = args.output.with_suffix(".jsx")
    jsx_path.write_text(jsx_for(report, args.target, args.output), encoding="utf-8")
    if not args.no_photoshop:
        run_photoshop(jsx_path)
    print(json.dumps({"report": str(args.report), "jsx": str(jsx_path), "output": str(args.output), "photoshop": not args.no_photoshop}, indent=2))


if __name__ == "__main__":
    main()

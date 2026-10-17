"""Render the recorded browser-capture sequence with an explicitly supplied FFmpeg."""

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs" / "assets" / "demo"


def timestamp(seconds: int) -> str:
    return f"{seconds // 3600:02}:{seconds // 60 % 60:02}:{seconds % 60:02}.000"


def render(ffmpeg: Path, font: Path) -> None:
    manifest = json.loads((ASSETS / "walkthrough.json").read_text(encoding="utf-8"))
    steps = manifest["steps"]
    if sum(step["duration_s"] for step in steps) != manifest["duration_s"]:
        raise ValueError("walkthrough duration does not match its steps")
    for step in steps:
        raw = (ASSETS / step["file"]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != step["sha256"]:
            raise ValueError(f"source capture changed: {step['file']}")
    artifacts = ROOT / "artifacts"
    artifacts.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="demo-render-", dir=artifacts) as directory:
        work = Path(directory)
        shutil.copyfile(font, work / "font.ttf")

        def run(*args: str) -> None:
            subprocess.run([str(ffmpeg), "-hide_banner", "-loglevel", "error", "-y", *args],
                           cwd=work, check=True, timeout=180)

        for index, step in enumerate(steps, 1):
            heading = f"AeroTest Copilot | {index}/{len(steps)}  {step['title']}"
            (work / "heading.txt").write_text(heading, encoding="utf-8", newline="\n")
            label = ("Edited browser captures | Scripted mode | Educational simulation | "
                     "AI-assisted development")
            (work / "label.txt").write_text(label, encoding="utf-8", newline="\n")
            (work / "caption.txt").write_text(step["caption"], encoding="utf-8", newline="\n")
            filters = (
                "scale=1800:880:force_original_aspect_ratio=decrease:force_divisible_by=2:out_range=tv:out_color_matrix=bt709,"
                "pad=1920:1080:(ow-iw)/2:90+(880-ih)/2:color=0x10232b,setsar=1,"
                "drawtext=fontfile=font.ttf:textfile=heading.txt:expansion=none:"
                "fontsize=32:fontcolor=white:x=40:y=17,"
                "drawtext=fontfile=font.ttf:textfile=label.txt:expansion=none:"
                "fontsize=21:fontcolor=0xc2d6cd:x=40:y=57,"
                "drawtext=fontfile=font.ttf:textfile=caption.txt:expansion=none:"
                "fontsize=26:line_spacing=9:fontcolor=white:x=(w-text_w)/2:y=991"
            )
            run("-loop", "1", "-framerate", "24", "-i", str(ASSETS / step["file"]),
                "-t", str(step["duration_s"]), "-vf", filters, "-c:v", "libx264",
                "-preset", "veryfast", "-crf", "20", "-profile:v", "high", "-level", "4.0",
                "-pix_fmt", "yuv420p", "-color_range", "tv", "-colorspace", "bt709",
                "-color_trc", "bt709", "-color_primaries", "bt709",
                "-r", "24", "-an", f"part-{index:02}.mp4")
        (work / "parts.txt").write_text(
            "".join(f"file 'part-{i:02}.mp4'\n" for i in range(1, len(steps) + 1)),
            encoding="utf-8")
        output = ASSETS / "aerotest-walkthrough.mp4"
        run("-f", "concat", "-safe", "0", "-i", "parts.txt", "-c", "copy",
            "-map_metadata", "-1", "-movflags", "+faststart", str(output))
        # Decode the complete video; a successful encode alone is insufficient.
        run("-v", "error", "-xerror", "-i", str(output), "-f", "null", "-")
        run("-ss", "30", "-i", str(output), "-frames:v", "1", "-q:v", "2",
            str(ASSETS / "poster.jpg"))
        captions = ["WEBVTT\n"]
        transcript = ["# Recorded walkthrough transcript\n",
                      "Edited browser-capture sequence; scripted mode; no audio.\n"]
        cursor = 0
        for step in steps:
            end = cursor + step["duration_s"]
            captions.append(f"{timestamp(cursor)} --> {timestamp(end)}\n{step['caption']}\n")
            transcript.append(f"## {timestamp(cursor)} - {step['title']}\n\n"
                              f"{step['caption']}\n")
            cursor = end
        (ASSETS / "captions.vtt").write_text("\n".join(captions), encoding="utf-8", newline="\n")
        (ASSETS / "transcript.md").write_text("\n".join(transcript), encoding="utf-8", newline="\n")
        version = subprocess.run([str(ffmpeg), "-version"], capture_output=True,
                                 text=True, check=True).stdout.splitlines()[0]
        result = {
            "rendered_at_utc": datetime.now(UTC).isoformat(), "ffmpeg": version,
            "duration_s": cursor, "width_px": 1920, "height_px": 1080, "fps": 24,
            "codec": "H.264 high / yuv420p", "audio": "none",
            "full_decode": "passed", "video_bytes": output.stat().st_size,
            "video_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
            "manifest_sha256": hashlib.sha256(
                (ASSETS / "walkthrough.json").read_bytes()).hexdigest(),
        }
        (ASSETS / "render-report.json").write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ffmpeg", required=True, type=Path)
    parser.add_argument("--font", required=True, type=Path, help="Local TrueType font; not bundled")
    arguments = parser.parse_args()
    render(arguments.ffmpeg.resolve(strict=True), arguments.font.resolve(strict=True))

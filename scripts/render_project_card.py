"""Build/check the standalone portfolio card from canonical copy and verified assets."""

import argparse
import hashlib
import json
from html import escape
from pathlib import Path
from string import Template

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def render() -> str:
    data = json.loads((DOCS / "project-card.json").read_text(encoding="utf-8"))
    image = data["image"]
    image_path = (DOCS / image["src"]).resolve()
    if not image_path.is_relative_to(DOCS.resolve()):
        raise ValueError("image must stay inside docs")
    if hashlib.sha256(image_path.read_bytes()).hexdigest() != image["sha256"]:
        raise ValueError("source screenshot hash changed")
    provenance = json.loads((DOCS / image["provenance"]).read_text(encoding="utf-8"))
    if not any(item["file"] == image_path.name and item["sha256"] == image["sha256"]
               for item in provenance["assets"]):
        raise ValueError("image does not match its capture provenance")
    repository = data["repository_url"]
    if repository != "https://github.com/JohnZargaryan/aerotest-copilot":
        raise ValueError("unexpected repository URL")
    links = []
    for link in data["links"]:
        target = link["repo_path"]
        if target:
            local = (ROOT / target).resolve()
            if not local.is_relative_to(ROOT) or not local.is_file():
                raise ValueError(f"missing repository link: {target}")
        url = f"{repository}/blob/main/{target}" if target else repository
        links.append(f'<a href="{escape(url, quote=True)}">{escape(link["label"])}</a>')
    fields = {key: escape(data[key], quote=True) for key in (
        "title", "category", "status", "description", "mode", "limitation", "assistance")}
    fields.update(
        image_src=escape(image["src"], quote=True),
        image_alt=escape(image["alt"], quote=True),
        image_caption=escape(image["caption"], quote=True),
        highlights="".join(f"<li>{escape(item)}</li>" for item in data["highlights"]),
        technologies="".join(f"<li>{escape(item)}</li>" for item in data["technologies"]),
        links="".join(links),
    )
    template = (ROOT / "scripts" / "project-card-template.html").read_text(encoding="utf-8")
    return Template(template).substitute(fields)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify without writing files")
    args = parser.parse_args()
    html = render()
    output = DOCS / "project-card.html"
    if args.check:
        if not output.is_file() or output.read_text(encoding="utf-8") != html:
            raise SystemExit("project card is stale; run scripts/render_project_card.py")
        print("Project card is current; source image and repository links verified.")
    else:
        output.write_text(html, encoding="utf-8", newline="\n")
        print("Rendered docs/project-card.html from verified copy and screenshot.")


if __name__ == "__main__":
    main()

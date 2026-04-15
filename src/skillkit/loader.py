import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

_NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def _validate_name(name: str, skill_dir: Path):
    assert 1 <= len(name) <= 64, f"name must be 1-64 chars, got {len(name)}"
    assert _NAME_RE.match(
        name
    ), f"name must be lowercase alphanumeric+hyphens, no leading/trailing/consecutive hyphens: {name!r}"
    assert (
        name == skill_dir.name
    ), f"name {name!r} must match directory name {skill_dir.name!r}"


def _validate_description(description: str):
    assert (
        1 <= len(description) <= 1024
    ), f"description must be 1-1024 chars, got {len(description)}"


@dataclass
class Skill:
    name: str
    description: str
    instructions: str
    license: str | None = None
    compatibility: str | None = None
    metadata: dict = field(default_factory=dict)
    allowed_tools: list[str] = field(default_factory=list)
    resources: dict[str, str] = field(default_factory=dict)


def load_skill_from_dir(skill_dir: Path, validate: bool = True) -> Skill:
    skill_md = (skill_dir / "SKILL.md").read_text()
    parts = skill_md.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"SKILL.md in {skill_dir} is missing frontmatter")

    fm = yaml.safe_load(parts[1])
    instructions = parts[2].strip()

    name = fm.get("name", "")
    description = fm.get("description", "")

    if validate:
        _validate_name(name, skill_dir)
        _validate_description(description)

    allowed_tools_raw = fm.get("allowed-tools", "")
    if isinstance(allowed_tools_raw, list):
        allowed_tools = allowed_tools_raw
    else:
        allowed_tools = allowed_tools_raw.split() if allowed_tools_raw else []

    resources = {}
    for subdir in ("references", "assets", "scripts"):
        d = skill_dir / subdir
        if d.exists():
            for f in d.rglob("*"):
                if f.is_file():
                    rel = str(f.relative_to(skill_dir))
                    try:
                        resources[rel] = f.read_text()
                    except UnicodeDecodeError:
                        resources[rel] = f"<binary file: {rel}>"

    return Skill(
        name=name,
        description=description,
        instructions=instructions,
        license=fm.get("license"),
        compatibility=fm.get("compatibility"),
        metadata=fm.get("metadata") or {},
        allowed_tools=allowed_tools,
        resources=resources,
    )


def load_skills_from_dir(skills_dir: Path, validate: bool = True) -> dict[str, Skill]:
    skills = {}
    for d in skills_dir.iterdir():
        if d.is_dir() and (d / "SKILL.md").exists():
            skill = load_skill_from_dir(d, validate=validate)
            skills[skill.name] = skill
    return skills

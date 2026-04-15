from .loader import Skill


def build_skill_catalog(skills: dict[str, Skill]) -> str:
    lines = [
        "## Available Skills\n",
        "When a task matches a skill's domain, call `load_skill` with its name "
        "to get detailed instructions before proceeding. "
        "Call `load_skill_resource` to fetch files referenced in the instructions.\n",
    ]
    for skill in skills.values():
        entry = f"- **{skill.name}**: {skill.description}"
        if skill.compatibility:
            entry += f" *(requires: {skill.compatibility})*"
        lines.append(entry)
    return "\n".join(lines)

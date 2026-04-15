import shlex
import subprocess
from pathlib import Path

from langchain_core.tools import tool

from .loader import Skill


def make_skill_tools(skills: dict[str, Skill], skill_base_dir: Path):
    @tool
    def load_skill(name: str) -> str:
        """Load the full instructions for a skill by name.
        Call this when a task matches a skill's domain, before proceeding."""
        skill = skills.get(name)
        if not skill:
            return f"Skill '{name}' not found. Available: {list(skills.keys())}"
        return skill.instructions

    @tool
    def load_skill_resource(skill_name: str, resource_path: str) -> str:
        """Load a file from a skill by its relative path from the skill root.
        Examples: 'references/model-limits.md', 'assets/template.md', 'scripts/count_tokens.py'
        Use this when skill instructions reference a specific file."""
        skill = skills.get(skill_name)
        if not skill:
            return f"Skill '{skill_name}' not found."
        content = skill.resources.get(resource_path)
        if content is None:
            return (
                f"Resource '{resource_path}' not found in skill '{skill_name}'. "
                f"Available: {sorted(skill.resources.keys())}"
            )
        return content

    @tool
    def run_skill_script(skill_name: str, script_path: str, script_args: str = "") -> str:
        """Execute a script bundled with a skill.

        Args:
            skill_name:  Name of the skill (e.g. 'token-counter')
            script_path: Relative path to the script from skill root (e.g. 'scripts/count_tokens.py')
            script_args: Command-line arguments to pass to the script (e.g. '--text "hello" --format json')

        The script runs with the skill directory as cwd, so relative paths in
        script arguments resolve correctly.

        Returns combined stdout. Stderr is included on failure.
        Timeout: 60 seconds.
        """
        skill = skills.get(skill_name)
        if not skill:
            return f"Skill '{skill_name}' not found."

        if not script_path.startswith("scripts/"):
            return (
                f"Error: script_path must be under scripts/ "
                f"(got '{script_path}'). "
                f"Available scripts: {[k for k in skill.resources if k.startswith('scripts/')]}"
            )

        if script_path not in skill.resources:
            available = [k for k in skill.resources if k.startswith("scripts/")]
            return f"Script '{script_path}' not found. Available: {available}"

        skill_dir = skill_base_dir / skill_name
        script_file = skill_dir / script_path

        suffix = Path(script_path).suffix
        extra_args = shlex.split(script_args) if script_args else []
        if suffix == ".py":
            import shutil

            if shutil.which("uv"):
                cmd = ["uv", "run", str(script_file), *extra_args]
            else:
                cmd = ["python3", str(script_file), *extra_args]
        elif suffix == ".sh":
            cmd = ["bash", str(script_file), *extra_args]
        elif suffix == ".ts":
            cmd = ["deno", "run", str(script_file), *extra_args]
        else:
            return (
                f"Error: unsupported script type '{suffix}'. "
                f"Supported: .py, .sh, .ts"
            )

        try:
            result = subprocess.run(
                cmd,
                shell=False,
                cwd=skill_dir,
                capture_output=True,
                text=True,
                timeout=60,
            )
        except subprocess.TimeoutExpired:
            return "Error: script timed out after 60 seconds."

        if result.returncode == 0:
            output = result.stdout
            if result.stderr:
                output += f"\n[stderr]\n{result.stderr}"
            return output or "(script produced no output)"
        else:
            return (
                f"Error: script exited with code {result.returncode}\n"
                f"[stdout]\n{result.stdout}\n"
                f"[stderr]\n{result.stderr}"
            )

    return [load_skill, load_skill_resource, run_skill_script]

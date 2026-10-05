"""Shared frontmatter utilities; PyYAML is a declared repository dependency."""

from pathlib import Path
import re
import yaml


def split_skill_content(content: str) -> tuple[dict, str]:
    match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", content, re.DOTALL)
    if not match:
        raise ValueError("SKILL.md requires delimited YAML frontmatter")
    data = yaml.safe_load(match.group(1))
    if not isinstance(data, dict):
        raise ValueError("Frontmatter must be a mapping")
    return data, content[match.end():]


def parse_skill_md(skill_path: Path) -> tuple[str, str, str]:
    content = (skill_path / "SKILL.md").read_text(encoding="utf-8")
    data, _ = split_skill_content(content)
    if not isinstance(data.get("name"), str) or not isinstance(data.get("description"), str):
        raise ValueError("Skill name and description must be strings")
    return data["name"], data["description"].strip(), content


def update_skill_description(content: str, new_description: str) -> str:
    if not isinstance(new_description, str) or not new_description.strip() or len(new_description) > 1024:
        raise ValueError("Candidate description must be a nonempty string of at most 1024 characters")
    if "<" in new_description or ">" in new_description:
        raise ValueError("Candidate frontmatter cannot contain angle brackets")
    data, body = split_skill_content(content)
    data["description"] = new_description
    return "---\n" + yaml.safe_dump(data, sort_keys=False, allow_unicode=True) + "---\n" + body

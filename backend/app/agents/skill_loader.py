import re
from dataclasses import dataclass
from pathlib import Path

SKILLS_DIR = Path(__file__).parent / "skills"

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)


@dataclass
class Skill:
    """A packet of specialized instructions, kept out of the main system prompt
    until explicitly loaded. name/description form the lightweight "index";
    body is only read into context on demand (progressive disclosure)."""

    name: str
    description: str
    body: str


def _parse_skill_file(path: Path) -> Skill:
    text = path.read_text(encoding="utf-8")
    match = _FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError(f"Skill file {path} is missing YAML frontmatter (---...---)")

    frontmatter, body = match.groups()
    meta = dict(line.split(":", 1) for line in frontmatter.strip().splitlines())
    meta = {key.strip(): value.strip() for key, value in meta.items()}

    return Skill(name=meta["name"], description=meta["description"], body=body.strip())


def list_skills() -> list[Skill]:
    return [_parse_skill_file(path) for path in sorted(SKILLS_DIR.glob("*.md"))]


def get_skill(name: str) -> Skill:
    for skill in list_skills():
        if skill.name == name:
            return skill
    raise KeyError(f"Compétence inconnue : {name}")

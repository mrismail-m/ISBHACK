"""Load prompt files from app/ai/prompts/.

A prompt file starts with `version: <id>`. An optional `---USER---` line splits the system
part from the user part. Placeholders look like {name}. Rendering is single pass, so text that
is inserted (like student work) is never searched for placeholders again.
"""

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent / "prompts"
USER_MARKER = "---USER---"
_PLACEHOLDER = re.compile(r"\{(\w+)\}")


@dataclass(frozen=True)
class Prompt:
    name: str
    version: str
    system: str
    user_template: str


@lru_cache
def load_prompt(name: str) -> Prompt:
    raw = (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")
    first, _, body = raw.partition("\n")
    if not first.startswith("version:"):
        raise ValueError(f"prompt {name} must start with a 'version:' line")
    version = first.split(":", 1)[1].strip()
    system, _, user = body.partition(USER_MARKER)
    return Prompt(name=name, version=version, system=system.strip(), user_template=user.strip())


def render(template: str, **values: str) -> str:
    """Replace {name} placeholders that appear in `values`. Others are left untouched."""
    return _PLACEHOLDER.sub(lambda m: values.get(m.group(1), m.group(0)), template)

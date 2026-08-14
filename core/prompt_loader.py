"""
Prompt loader — single place that knows how to render a prompt.

Prompts live in `prompts/<group>/<name>.j2`.
Optional few-shot examples live in `prompt_examples/<name>.yaml`.

To change a prompt: edit the .j2 file. To change examples: edit the .yaml file.
No code changes needed.

Example yaml format:
    examples:
      - query: "What are the fees for an ISP license?"
        queries:
          - "ISP license annual fee"
          - "ISP license acquisition fee"

The `examples` list is exposed in the template as the `examples` variable.
The template decides how to render them (so different prompts can use different
example shapes).
"""

import logging
from pathlib import Path
from typing import Optional

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined, TemplateNotFound

logger = logging.getLogger("PromptLoader")


# Resolve directories relative to the project root (this file is in core/)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_PROMPTS_DIR = _PROJECT_ROOT / "prompts"
_EXAMPLES_DIR = _PROJECT_ROOT / "prompt_examples"


class PromptLoader:
    """
    Renders Jinja prompts with optional YAML-loaded few-shot examples.

    Construct once per process (Jinja env caches templates). Thread-safe for reads.
    """

    def __init__(
        self,
        prompts_dir: Optional[Path] = None,
        examples_dir: Optional[Path] = None,
    ):
        self.prompts_dir = Path(prompts_dir) if prompts_dir else _PROMPTS_DIR
        self.examples_dir = Path(examples_dir) if examples_dir else _EXAMPLES_DIR

        if not self.prompts_dir.exists():
            raise FileNotFoundError(f"Prompts directory not found: {self.prompts_dir}")

        # StrictUndefined: a typo in template variable names raises immediately
        # instead of silently rendering an empty string.
        self.env = Environment(
            loader=FileSystemLoader(str(self.prompts_dir)),
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    # ---------- public API ----------

    def render(
        self,
        template_name: str,
        examples_file: Optional[str] = None,
        **context,
    ) -> str:
        """
        Render `prompts/<template_name>` with the given context.

        Args:
            template_name: path relative to prompts_dir, e.g. "query/decompose.j2"
            examples_file: name (no extension) of YAML in prompt_examples/, e.g. "decompose"
            **context: variables to expose to the template

        Examples are exposed as the `examples` variable. If no examples file is
        given (or the file doesn't exist), `examples` is an empty list — templates
        should handle this case with an `{% if examples %}` block.
        """
        try:
            template = self.env.get_template(template_name)
        except TemplateNotFound:
            raise FileNotFoundError(
                f"Prompt template not found: {self.prompts_dir / template_name}"
            )

        # Inject examples (always defined, possibly empty)
        if "examples" not in context:
            context["examples"] = self._load_examples(examples_file) if examples_file else []

        return template.render(**context)

    # ---------- internals ----------

    def _load_examples(self, name: str) -> list:
        """
        Load few-shot examples from `prompt_examples/<name>.yaml`. Returns [] if missing.
        """
        path = self.examples_dir / f"{name}.yaml"
        if not path.exists():
            logger.debug(f"No examples file at {path} — rendering without examples")
            return []

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            examples = data.get("examples", [])
            if not isinstance(examples, list):
                logger.warning(f"{path}: 'examples' should be a list, got {type(examples)}")
                return []
            return examples
        except yaml.YAMLError as e:
            logger.error(f"Could not parse {path}: {e}")
            return []


# A singleton is convenient — most callers don't need to customize paths
_default_loader: Optional[PromptLoader] = None


def get_loader() -> PromptLoader:
    """Get the process-wide default loader. Construct on first call."""
    global _default_loader
    if _default_loader is None:
        _default_loader = PromptLoader()
    return _default_loader

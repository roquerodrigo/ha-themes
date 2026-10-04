import importlib.metadata
import importlib.util
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

VAR_REFERENCE = re.compile(r"var\(\s*--([A-Za-z0-9_-]+)\s*(,)?")
SCRIPT_READ = re.compile(r"getPropertyValue\(\s*[\"'`]--([A-Za-z0-9_-]+)[\"'`]\s*\)")
DYNAMIC_NAME = re.compile(r"`--([a-z0-9-]+-)\$\{")
MAX_FALLBACK_LENGTH = 120


@dataclass
class TokenUsage:
    chunks: set[str] = field(default_factory=set)
    fallbacks: set[str] = field(default_factory=set)


@dataclass
class BundleScan:
    usage: dict[str, TokenUsage]
    dynamic_families: dict[str, int]
    """Name prefixes the frontend completes at runtime, such as `--state-${domain}-…`."""


def installed_frontend_directory() -> Path:
    spec = importlib.util.find_spec("hass_frontend")
    if spec is None or spec.origin is None:
        raise RuntimeError("hass_frontend is not installed; run `uv sync` first")
    return Path(spec.origin).parent / "frontend_latest"


def installed_frontend_version() -> str:
    return importlib.metadata.version("home-assistant-frontend")


def _read_fallback(source: str, start: int) -> str:
    depth = 0
    for index in range(start, len(source)):
        character = source[index]
        if character == "(":
            depth += 1
        elif character == ")":
            if depth == 0:
                return source[start:index].strip()
            depth -= 1
        elif character in "`;{}" and depth == 0:
            break
    return ""


def scan_bundle(directory: Path | None = None) -> BundleScan:
    directory = directory or installed_frontend_directory()
    usage: dict[str, TokenUsage] = defaultdict(TokenUsage)
    dynamic_chunks: dict[str, set[str]] = defaultdict(set)
    for chunk in sorted(directory.glob("*.js")):
        source = chunk.read_text(errors="ignore")
        for match in SCRIPT_READ.finditer(source):
            usage[f"--{match.group(1)}"].chunks.add(chunk.name)
        for match in DYNAMIC_NAME.finditer(source):
            dynamic_chunks[f"--{match.group(1)}"].add(chunk.name)
        for match in VAR_REFERENCE.finditer(source):
            token_usage = usage[f"--{match.group(1)}"]
            token_usage.chunks.add(chunk.name)
            if match.group(2):
                fallback = _read_fallback(source, match.end())
                if fallback and len(fallback) <= MAX_FALLBACK_LENGTH and "${" not in fallback:
                    token_usage.fallbacks.add(fallback)
    return BundleScan(
        dict(usage), {prefix: len(chunks) for prefix, chunks in sorted(dynamic_chunks.items())}
    )

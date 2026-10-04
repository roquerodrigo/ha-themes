import re
from dataclasses import dataclass

CORE_PALETTE = re.compile(r"^--ha-color-(black|white|(?P<family>[a-z]+)-\d+)$")
NAMED_COLOR = re.compile(r"^--([a-z]+-)*[a-z]+-color$")


@dataclass(frozen=True)
class Classification:
    layer: str
    group: str


LAYERS = {
    "core-palette": "Core palette — raw tonal scales every semantic color is derived from",
    "semantic-color": "Semantic colors — role-based colors built on the core palette",
    "foundation": "Foundation — spacing, borders, radii, elevation and motion",
    "typography": "Typography — font families, sizes, weights and line heights",
    "application": "Application colors — the classic theme variables used across the app",
    "state-color": "State colors — per-domain and per-state entity colors",
    "data-visualization": "Data visualization — chart, energy and history colors",
    "code-editor": "Code editor — CodeMirror syntax colors",
    "webawesome": "Web Awesome bridge — maps HA tokens onto the Web Awesome components",
    "material-bridge": "Material bridge — maps HA tokens onto legacy Material components",
    "layout": "Layout — safe areas, direction and structural values",
    "component": "Component hooks — consumed by components but not declared globally",
}

_FOUNDATION_PREFIXES = {
    "--ha-space-": "spacing",
    "--ha-border-width-": "border-width",
    "--ha-border-radius-": "border-radius",
    "--ha-box-shadow-": "elevation",
    "--ha-animation-": "motion",
}
_TYPOGRAPHY_PREFIXES = (
    "--ha-font-",
    "--ha-line-height-",
    "--ha-moz-osx-font-smoothing",
    "--md-list-item-",
)
_LAYOUT_PREFIXES = ("--safe-", "--header-height", "--direction", "--float-", "--margin-title-")


def classify_global_token(name: str) -> Classification:
    if match := CORE_PALETTE.match(name):
        return Classification("core-palette", match.group("family") or "pure")
    if name.startswith("--ha-color-"):
        return Classification("semantic-color", name.removeprefix("--ha-color-").split("-")[0])
    for prefix, group in _FOUNDATION_PREFIXES.items():
        if name.startswith(prefix):
            return Classification("foundation", group)
    if name.startswith(_TYPOGRAPHY_PREFIXES):
        return Classification("typography", _typography_group(name))
    if name.startswith("--wa-"):
        return Classification("webawesome", name.removeprefix("--wa-").split("-")[0])
    if name.startswith(("--mdc-", "--md-")):
        return Classification("material-bridge", name.removeprefix("--").split("-")[1])
    if name.startswith("--state-"):
        return Classification("state-color", name.removeprefix("--state-").split("-")[0])
    if re.match(r"^--color-\d+$", name):
        return Classification("data-visualization", "categorical")
    if name.startswith(("--energy-", "--history-")):
        return Classification("data-visualization", name.removeprefix("--").split("-")[0])
    if name.startswith("--codemirror-"):
        return Classification("code-editor", "syntax")
    if name.startswith(_LAYOUT_PREFIXES) or name.endswith("-opacity"):
        return Classification("layout", name.removeprefix("--").split("-")[0])
    return Classification("application", _application_group(name))


def _typography_group(name: str) -> str:
    if name.startswith("--ha-line-height-"):
        return "line-height"
    if name.startswith("--md-list-item-"):
        return "family"
    if "smoothing" in name:
        return "smoothing"
    return name.removeprefix("--ha-font-").split("-")[0]


def _application_group(name: str) -> str:
    bare = name.removeprefix("--")
    if bare.startswith("rgb-"):
        return "rgb-channels"
    for prefix in ("sidebar", "input", "label-badge", "app-header", "table", "slider", "chip"):
        if bare.startswith(prefix):
            return prefix
    if "background" in bare:
        return "background"
    if "text" in bare:
        return "text"
    if NAMED_COLOR.match(name):
        return "named-colors"
    return "misc"


def classify_component_token(name: str) -> Classification:
    segments = name.removeprefix("--").split("-")
    if segments[0] in {"ha", "md", "mdc", "wa"} and len(segments) > 2:
        return Classification("component", "-".join(segments[:2]))
    return Classification("component", segments[0])


def is_private_token(name: str) -> bool:
    return name.startswith("--_")

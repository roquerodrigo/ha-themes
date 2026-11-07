from dataclasses import dataclass
from pathlib import Path

from ha_theme_kit.inventory.dev_instance import DevInstance, chrome_session, open_with_theme

CAPTURE_SCRIPT = (Path(__file__).parent / "capture_tokens.js").read_text()


@dataclass(frozen=True)
class ModeSnapshot:
    declared: dict[str, str]
    conditional: dict[str, dict[str, str]]
    inline: dict[str, str]
    computed: dict[str, str]


@dataclass(frozen=True)
class RuntimeCapture:
    light: ModeSnapshot
    dark: ModeSnapshot


def capture_runtime_tokens(instance: DevInstance) -> RuntimeCapture:
    snapshots = {}
    with chrome_session(instance) as page:
        for mode, dark in (("light", False), ("dark", True)):
            open_with_theme(page, f"{instance.url}/lovelace/0", "default", dark)
            snapshots[mode] = ModeSnapshot(**page.evaluate(CAPTURE_SCRIPT))
    return RuntimeCapture(**snapshots)

from dataclasses import dataclass
from pathlib import Path

from playwright.sync_api import Page

from ha_theme_kit.inventory.dev_instance import DevInstance, chrome_session, open_with_theme

PREVIEWS_DIRECTORY = Path(__file__).resolve().parents[3] / "previews"


@dataclass(frozen=True)
class PreviewShot:
    path: str
    scroll: int = 0
    more_info_entity: str | None = None


PREVIEW_SHOTS = {
    "overview": PreviewShot("/lovelace/0"),
    "dashboard": PreviewShot("/theme-lab/components", scroll=260),
    "dialog": PreviewShot("/theme-lab/components", more_info_entity="light.bed_light"),
    "settings": PreviewShot("/config/dashboard"),
    "entities": PreviewShot("/config/entities"),
    "history": PreviewShot(
        "/history?entity_id="
        + ",".join(
            (
                "sensor.outside_temperature",
                "light.bed_light",
                "light.ceiling_lights",
                "lock.front_door",
                "lock.kitchen_door",
                "climate.ecobee",
                "cover.kitchen_window",
                "media_player.living_room",
                "binary_sensor.basement_floor_wet",
            )
        )
    ),
}


def _stage(page: Page, shot: PreviewShot) -> None:
    if shot.scroll:
        page.evaluate("offset => document.scrollingElement.scrollTo(0, offset)", shot.scroll)
    if shot.more_info_entity:
        page.evaluate(
            """entityId => document.querySelector("home-assistant").dispatchEvent(
                new CustomEvent("hass-more-info", {
                    detail: { entityId }, bubbles: true, composed: true,
                })
            )""",
            shot.more_info_entity,
        )
    page.wait_for_timeout(1500)


def capture_previews(
    instance: DevInstance, theme_name: str, slug: str, directory: Path = PREVIEWS_DIRECTORY
) -> list[Path]:
    output_directory = directory / slug
    output_directory.mkdir(parents=True, exist_ok=True)
    written = []
    with chrome_session(instance) as page:
        for mode, dark in (("light", False), ("dark", True)):
            for shot_name, shot in PREVIEW_SHOTS.items():
                open_with_theme(page, instance.url + shot.path, theme_name, dark)
                _stage(page, shot)
                target = output_directory / f"{shot_name}-{mode}.png"
                page.screenshot(path=target)
                written.append(target)
    return written

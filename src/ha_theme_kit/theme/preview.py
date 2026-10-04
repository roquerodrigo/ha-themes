from pathlib import Path

from ha_theme_kit.inventory.dev_instance import DevInstance, chrome_session, open_with_theme

PREVIEWS_DIRECTORY = Path(__file__).resolve().parents[3] / "previews"
PREVIEW_PAGES = {
    "overview": "/lovelace/0",
    "settings": "/config/dashboard",
    "entities": "/config/entities",
    "history": "/history",
}


def capture_previews(
    instance: DevInstance, theme_name: str, slug: str, directory: Path = PREVIEWS_DIRECTORY
) -> list[Path]:
    output_directory = directory / slug
    output_directory.mkdir(parents=True, exist_ok=True)
    written = []
    with chrome_session(instance) as page:
        for mode, dark in (("light", False), ("dark", True)):
            for page_name, path in PREVIEW_PAGES.items():
                open_with_theme(page, instance.url + path, theme_name, dark)
                target = output_directory / f"{page_name}-{mode}.png"
                page.screenshot(path=target)
                written.append(target)
    return written

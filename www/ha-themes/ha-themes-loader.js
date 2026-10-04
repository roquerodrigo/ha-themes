// Two caches sit in front of /local: Home Assistant serves it with a 31-day Cache-Control,
// and the frontend's service worker answers it stale-while-revalidate. This stable entry
// point never changes; it reads the current content hash through a URL no cache has seen
// and imports that exact build.
const base = new URL(".", import.meta.url);

try {
  const versionUrl = new URL(`ha-themes.version.json?t=${Date.now()}`, base);
  const { hash } = await (await fetch(versionUrl, { cache: "no-store" })).json();
  await import(new URL(`ha-themes.js?v=${hash}`, base).href);
} catch (_error) {
  await import(new URL("ha-themes.js", base).href);
}

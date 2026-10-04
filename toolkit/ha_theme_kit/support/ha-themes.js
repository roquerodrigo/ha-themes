const PROJECT_VARIABLE_PREFIX = "--ha-themes-";
const FONT_STYLESHEET_VARIABLE = "--ha-themes-font-stylesheet";
const BRAND_PATH = "/api/brands/";
const BRAND_ICON_COLOR_VARIABLE = "--ha-themes-brand-icon-color";
const BRAND_ICON_COLOR_DECLARATION = new RegExp(`${BRAND_ICON_COLOR_VARIABLE}\\s*:\\s*([^;]*)`);
// Generic integration icons on the brands CDN are a single flat color; real logos are not.
const GENERIC_ICON_RGB = [0, 171, 248];
const CHANNEL_TOLERANCE = 3;
const DASHBOARD_HEADER_BACKGROUND =
  "var(--ha-themes-dashboard-header-background, var(--app-header-background-color))";

// Only the dashboard header pairs its background with a backdrop filter, so the translucent
// background is painted there alone; the frontend's edit-mode rules are more specific and win.
const dashboardHeaderStyles = new CSSStyleSheet();
dashboardHeaderStyles.replaceSync(`
  .header { background-color: ${DASHBOARD_HEADER_BACKGROUND}; }
  ha-tab-group::part(scroll-button) {
    background: linear-gradient(90deg, ${DASHBOARD_HEADER_BACKGROUND}, transparent);
  }
  ha-tab-group::part(scroll-button-end) {
    background: linear-gradient(270deg, ${DASHBOARD_HEADER_BACKGROUND}, transparent);
  }
`);

// The dropdown derives its menu surface from the page-toned card background on its own host,
// which outranks anything a theme sets, so only a rule inside its shadow root can raise it.
const dropdownMenuStyles = new CSSStyleSheet();
dropdownMenuStyles.replaceSync(`
  :host {
    --wa-color-surface-raised: var(
      --ha-themes-menu-background,
      var(--card-background-color, var(--ha-dialog-surface-background, var(--mdc-theme-surface, #fff)))
    );
  }
`);

// The toast reuses the loud neutral and normal primary on-colors, which a theme tunes for other
// backdrops, so its message and actions take colors set for the toast itself. The slotted action
// buttons inherit from .actions; the toast keeps the page's brand text under another name, since
// a custom property cannot fall back to its own inherited value.
const toastStyles = new CSSStyleSheet();
toastStyles.replaceSync(`
  .toast {
    box-shadow: var(--ha-themes-toast-box-shadow, var(--wa-shadow-l));
    --ha-themes-page-brand-on-normal: var(--wa-color-brand-on-normal);
  }
  .toast,
  .actions { color: var(--ha-themes-toast-text-color, var(--ha-color-on-neutral-loud)); }
  .actions {
    --wa-color-brand-on-normal: var(
      --ha-themes-toast-action-color, var(--ha-themes-page-brand-on-normal)
    );
  }
`);

// The energy totals table paints the page-toned card background inside its own card, so
// letting the card show through keeps the card one tone.
const energySourcesTableStyles = new CSSStyleSheet();
energySourcesTableStyles.replaceSync(`
  .mdc-data-table,
  .mdc-data-table__header-cell { background-color: transparent; }
`);

// The integration page's entry lists take their surface from the page-toned card background,
// so they are raised to the card tone they would have on the default theme.
const configEntryListStyles = new CSSStyleSheet();
configEntryListStyles.replaceSync(`
  ha-md-list { --md-sys-color-surface: var(--ha-card-background, var(--card-background-color)); }
`);

// Settings, System, About and the search dialog draw their icon tiles with literal inline colors,
// so each known literal is matched by value and moved toward the entity color of the same hue.
// A literal missing here keeps its stock color; without the theme's share and lightness cap the
// rules reproduce the literal, so other themes are unaffected.
const ICON_TILE_ENTITY_COLORS = {
  "#0082FC": "blue",
  "#00838F": "teal",
  "#0D47A1": "indigo",
  "#153163": "indigo",
  "#2458B3": "indigo",
  "#24A5CB": "cyan",
  "#2D338F": "indigo",
  "#301A8E": "indigo",
  "#301ABE": "indigo",
  "#3263C3": "indigo",
  "#3B808E": "teal",
  "#4084CD": "blue",
  "#4A5963": "blue-grey",
  "#4D2EA4": "deep-purple",
  "#4EAA66": "green",
  "#518C43": "green",
  "#5A87FA": "blue",
  "#5C995C": "green",
  "#607D8B": "blue-grey",
  "#616161": "grey",
  "#653249": "pink",
  "#660066": "purple",
  "#7A5AA6": "purple",
  "#8B69E3": "purple",
  "#8E24AA": "purple",
  "#9C27B0": "purple",
  "#9E4DD1": "purple",
  "#B1345C": "pink",
  "#B1B134": "lime",
  "#C65326": "deep-orange",
  "#E4002C": "red",
  "#E48629": "orange",
  "#E74011": "deep-orange",
  "#ED7744": "deep-orange",
  "#F1C447": "amber",
};

// A property binding serializes the literal as rgb(), an attribute binding keeps it as written.
const serializedRgb = (hex) =>
  `rgb(${[1, 3, 5].map((start) => parseInt(hex.slice(start, start + 2), 16)).join(", ")})`;

const iconTileRule = ([hex, entityColor]) => `
  [style*="${hex}" i], [style*="${serializedRgb(hex)}"] {
    background-color: oklch(
      from color-mix(
        in oklab, ${hex}, var(--${entityColor}-color) var(--ha-themes-icon-tile-palette-share, 0%)
      )
      min(l, var(--ha-themes-icon-tile-max-lightness, 1)) c h
    ) !important;
  }`;

const iconTileStyles = new CSSStyleSheet();
iconTileStyles.replaceSync(`
  @supports (color: oklch(from red l c h)) {
    ${Object.entries(ICON_TILE_ENTITY_COLORS).map(iconTileRule).join("")}
  }
`);

// Filled form fields mark their edge, focus and errors with a bottom line drawn by an ::after
// rule. A theme that sets --ha-themes-field-outline to 1 outlines the whole field instead, and
// the outline takes over the focus and error colors; at the default 0 every rule resolves to
// the stock look.
const FIELD_OUTLINE = "var(--ha-themes-field-outline, 0)";
const FIELD_BORDER = `calc(${FIELD_OUTLINE} * 1px) solid var(--ha-themes-field-border-color, transparent)`;
const FIELD_UNDERLINE_OPACITY = `calc(1 - ${FIELD_OUTLINE})`;
const FIELD_FOCUS_BORDER_COLOR = "var(--primary-color)";
const FIELD_INVALID_BORDER_COLOR = "var(--ha-color-border-danger-normal)";
const FIELD_DISABLED_BORDER_COLOR =
  "color-mix(in srgb, var(--ha-themes-field-border-color, transparent) 50%, transparent)";
const fieldBorderRadius = (stockTop, stockBottom = "var(--ha-border-radius-square)") =>
  `var(--ha-themes-field-border-radius, ${stockTop} ${stockTop} ${stockBottom} ${stockBottom})`;
const STOCK_FIELD_RADIUS = fieldBorderRadius("var(--ha-border-radius-sm)");

const inputFieldStyles = new CSSStyleSheet();
inputFieldStyles.replaceSync(`
  :host([appearance="material"]) wa-input::part(base) {
    border: ${FIELD_BORDER};
    border-radius: ${STOCK_FIELD_RADIUS};
  }
  :host([appearance="material"]) wa-input::part(base)::after {
    opacity: ${FIELD_UNDERLINE_OPACITY};
  }
  :host([appearance="material"]:focus-within) wa-input::part(base) {
    border-color: ${FIELD_FOCUS_BORDER_COLOR};
  }
  :host([appearance="material"]:focus-within) wa-input.invalid::part(base),
  :host([appearance="material"]) wa-input.invalid:not([disabled])::part(base) {
    border-color: ${FIELD_INVALID_BORDER_COLOR};
  }
  :host([appearance="material"]) wa-input:disabled::part(base) {
    border-color: ${FIELD_DISABLED_BORDER_COLOR};
  }
`);

const textareaFieldStyles = new CSSStyleSheet();
textareaFieldStyles.replaceSync(`
  :host wa-textarea::part(base) {
    border: ${FIELD_BORDER};
    border-radius: ${STOCK_FIELD_RADIUS};
  }
  wa-textarea::part(base)::after { opacity: ${FIELD_UNDERLINE_OPACITY}; }
  :host(:focus-within) wa-textarea::part(base),
  :host([focused]) wa-textarea::part(base) {
    border-color: ${FIELD_FOCUS_BORDER_COLOR};
  }
  :host(:focus-within) wa-textarea.invalid::part(base),
  wa-textarea.invalid:not([disabled])::part(base) {
    border-color: ${FIELD_INVALID_BORDER_COLOR};
  }
  wa-textarea[disabled]::part(base) { border-color: ${FIELD_DISABLED_BORDER_COLOR}; }
`);

// Selects and pickers render their field as a list item, which dims itself when disabled.
const pickerFieldStyles = new CSSStyleSheet();
pickerFieldStyles.replaceSync(`
  ha-combo-box-item {
    border: ${FIELD_BORDER};
    border-radius: ${fieldBorderRadius("var(--ha-border-radius-sm)", "0")};
  }
  ha-combo-box-item::after { opacity: ${FIELD_UNDERLINE_OPACITY}; }
  ha-combo-box-item:focus,
  :host(.opened) ha-combo-box-item {
    border-color: ${FIELD_FOCUS_BORDER_COLOR};
  }
  :host([invalid]) ha-combo-box-item { border-color: ${FIELD_INVALID_BORDER_COLOR}; }
`);

const labelsFieldStyles = new CSSStyleSheet();
labelsFieldStyles.replaceSync(`
  ha-chip-set {
    border: ${FIELD_BORDER};
    border-bottom: 1px solid var(
      --ha-themes-field-border-color, var(--ha-color-border-neutral-normal)
    );
    border-radius: ${fieldBorderRadius("var(--ha-border-radius-sm)", "0")};
  }
`);

// A time input joins one input per unit, the separators and the clear button into one strip,
// so the strip takes the outline and its inputs and separators drop their own edges.
const STOCK_TIME_RADIUS = "var(--mdc-shape-small, var(--ha-border-radius-sm))";
const FIELD_SEGMENT_RADIUS = `calc(var(--ha-border-radius-sm) * ${FIELD_UNDERLINE_OPACITY})`;
const timeFieldStyles = new CSSStyleSheet();
timeFieldStyles.replaceSync(`
  .time-input-wrap {
    border: ${FIELD_BORDER};
    border-radius: ${fieldBorderRadius(STOCK_TIME_RADIUS)};
  }
  .time-input-wrap:focus-within { border-color: ${FIELD_FOCUS_BORDER_COLOR}; }
  ha-input::part(wa-base) {
    border-width: 0;
    border-radius: ${FIELD_SEGMENT_RADIUS} ${FIELD_SEGMENT_RADIUS} var(--ha-border-radius-square)
      var(--ha-border-radius-square);
  }
  .time-separator,
  ha-icon-button {
    border-bottom-color: color-mix(
      in srgb,
      var(--ha-color-border-neutral-loud) calc(${FIELD_UNDERLINE_OPACITY} * 100%),
      transparent
    );
  }
`);

const hostStyles = new Map([
  ["ha-input", inputFieldStyles],
  ["ha-textarea", textareaFieldStyles],
  ["ha-picker-field", pickerFieldStyles],
  ["ha-labels-picker", labelsFieldStyles],
  ["ha-base-time-input", timeFieldStyles],
  ["ha-config-navigation-list", iconTileStyles],
  ["ha-config-info", iconTileStyles],
  ["ha-picker-combo-box", iconTileStyles],
  ["hui-root", dashboardHeaderStyles],
  ["ha-dropdown", dropdownMenuStyles],
  ["ha-toast", toastStyles],
  ["hui-energy-sources-table-card", energySourcesTableStyles],
  ["ha-config-entry-row", configEntryListStyles],
]);

const styleHost = (root) => {
  const styles = hostStyles.get(root.host?.localName);
  const sheets = root.adoptedStyleSheets;
  if (styles && !sheets.includes(styles)) {
    root.adoptedStyleSheets = [...sheets, styles];
  }
};

// Themes (global on <html>, or per view or card) are applied as inline custom properties.
const declaresProjectTheme = (element) =>
  element.getAttribute("style")?.includes(PROJECT_VARIABLE_PREFIX) ?? false;

const syncBodyFontBinding = () => {
  const binding = document.head.querySelector("style[data-ha-themes]");
  if (!declaresProjectTheme(document.documentElement)) {
    binding?.remove();
  } else if (!binding) {
    const style = document.createElement("style");
    style.dataset.haThemes = "";
    style.textContent =
      "body { font-family: var(--ha-font-family-body); " +
      "font-size-adjust: var(--ha-themes-font-size-adjust, none); }";
    document.head.append(style);
  }
};

const declaredFontStylesheet = (element) =>
  element.style
    ?.getPropertyValue(FONT_STYLESHEET_VARIABLE)
    .trim()
    .replace(/^(["'])(.*)\1$/, "$2");

// Elements whose theme (global on <html>, or per view or card) asks for a web font stylesheet.
const fontStylesheetDeclarers = new Set();
let fontStylesheetSyncPending = false;

const syncFontStylesheets = () => {
  fontStylesheetSyncPending = false;
  const needed = new Set();
  for (const element of fontStylesheetDeclarers) {
    const href = element.isConnected && declaredFontStylesheet(element);
    if (href) {
      needed.add(href);
    } else {
      fontStylesheetDeclarers.delete(element);
    }
  }
  for (const link of document.head.querySelectorAll("link[data-ha-themes-font-stylesheet]")) {
    if (!needed.delete(link.dataset.haThemesFontStylesheet)) {
      link.remove();
    }
  }
  for (const href of needed) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    link.dataset.haThemesFontStylesheet = href;
    document.head.append(link);
  }
};

const scheduleFontStylesheetSync = () => {
  if (!fontStylesheetSyncPending) {
    fontStylesheetSyncPending = true;
    queueMicrotask(syncFontStylesheets);
  }
};

const trackFontStylesheet = (element) => {
  if (!declaresProjectTheme(element) && !fontStylesheetDeclarers.has(element)) {
    return;
  }
  if (declaredFontStylesheet(element)) {
    fontStylesheetDeclarers.add(element);
    scheduleFontStylesheetSync();
  } else if (fontStylesheetDeclarers.has(element)) {
    scheduleFontStylesheetSync();
  }
};

const brandIconColor = (element) =>
  getComputedStyle(element).getPropertyValue(BRAND_ICON_COLOR_VARIABLE).trim();

const declaredBrandIconColor = (styleAttribute) =>
  styleAttribute?.includes(BRAND_ICON_COLOR_VARIABLE)
    ? styleAttribute.match(BRAND_ICON_COLOR_DECLARATION)?.[1].trim()
    : undefined;

const loadImage = (url) =>
  new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = reject;
    image.src = url;
  });

const isGenericIcon = (image) => {
  const canvas = document.createElement("canvas");
  canvas.width = image.naturalWidth;
  canvas.height = image.naturalHeight;
  const context = canvas.getContext("2d", { willReadFrequently: true });
  context.drawImage(image, 0, 0);
  const { data } = context.getImageData(0, 0, canvas.width, canvas.height);
  let opaquePixels = 0;
  for (let index = 0; index < data.length; index += 4) {
    if (data[index + 3] < 250) {
      continue;
    }
    opaquePixels++;
    for (let channel = 0; channel < 3; channel++) {
      if (Math.abs(data[index + channel] - GENERIC_ICON_RGB[channel]) > CHANNEL_TOLERANCE) {
        return false;
      }
    }
  }
  return opaquePixels > 0;
};

const recolor = (image, color) => {
  const canvas = document.createElement("canvas");
  canvas.width = image.naturalWidth;
  canvas.height = image.naturalHeight;
  const context = canvas.getContext("2d");
  context.drawImage(image, 0, 0);
  context.globalCompositeOperation = "source-in";
  context.fillStyle = color;
  context.fillRect(0, 0, canvas.width, canvas.height);
  return canvas.toDataURL("image/png");
};

const genericIconCache = new Map();
const recoloredCache = new Map();

const sameOriginUrl = (url) => {
  const resolved = new URL(url, location.href);
  return resolved.origin === location.origin ? resolved : null;
};

const recoloredUrl = async (url, color) => {
  const resolved = sameOriginUrl(url);
  if (!resolved) {
    return null;
  }
  const key = resolved.pathname;
  if (!genericIconCache.has(key)) {
    genericIconCache.set(
      key,
      loadImage(url)
        .then((image) => (isGenericIcon(image) ? image : null))
        .catch(() => null),
    );
  }
  const image = await genericIconCache.get(key);
  if (!image) {
    return null;
  }
  const cacheKey = `${key}|${color}`;
  if (!recoloredCache.has(cacheKey)) {
    recoloredCache.set(cacheKey, recolor(image, color));
  }
  return recoloredCache.get(cacheKey);
};

const backgroundBrandUrl = (element) =>
  element.style.backgroundImage.match(/url\(["']?([^"')]*\/api\/brands\/[^"')]*)["']?\)/)?.[1];

const forget = (element) => {
  delete element.dataset.haThemesSrc;
  delete element.dataset.haThemesSrcset;
  delete element.dataset.haThemesBackground;
  delete element.dataset.haThemesApplied;
};

const displayedValue = (element) =>
  element instanceof HTMLImageElement ? element.src : element.style.backgroundImage;

const storedSource = (element) =>
  element instanceof HTMLImageElement
    ? element.dataset.haThemesSrc
    : element.dataset.haThemesBackground;

const originalSource = (element) => {
  if (element instanceof HTMLImageElement) {
    if (element.src.includes(BRAND_PATH)) {
      element.dataset.haThemesSrc = element.src;
      element.dataset.haThemesSrcset = element.srcset;
      return element.src;
    }
  } else {
    const url = backgroundBrandUrl(element);
    if (url) {
      element.dataset.haThemesBackground = url;
      return url;
    }
  }
  // The frontend replaced or cleared the image: it no longer shows a brand icon.
  if (displayedValue(element) !== element.dataset.haThemesApplied) {
    forget(element);
    return undefined;
  }
  return storedSource(element);
};

const applyTo = async (element) => {
  const source = originalSource(element);
  if (!source) {
    return;
  }
  const color = brandIconColor(element);
  const replacement = color ? await recoloredUrl(source, color) : null;
  if (originalSource(element) !== source || (replacement && brandIconColor(element) !== color)) {
    return;
  }
  if (element instanceof HTMLImageElement) {
    const target = replacement || source;
    if (element.src !== target) {
      element.srcset = replacement ? "" : element.dataset.haThemesSrcset || "";
      element.src = target;
    }
  } else {
    const target = `url("${replacement || source}")`;
    if (element.style.backgroundImage !== target) {
      element.style.backgroundImage = target;
    }
  }
  element.dataset.haThemesApplied = displayedValue(element);
};

const isBrandElement = (element) =>
  (element instanceof HTMLImageElement &&
    (element.src.includes(BRAND_PATH) || element.dataset.haThemesSrc)) ||
  element.dataset?.haThemesBackground ||
  element.style?.backgroundImage.includes(BRAND_PATH);

const scan = (root) => {
  for (const element of root.querySelectorAll("*")) {
    trackDeclarer(element);
    if (isBrandElement(element)) {
      applyTo(element);
    }
    if (element.shadowRoot) {
      if (watchedRoots.has(element.shadowRoot)) {
        scan(element.shadowRoot);
      } else {
        watch(element.shadowRoot);
      }
    }
  }
};

const rescan = (element) => {
  scan(element);
  if (element.shadowRoot) {
    scan(element.shadowRoot);
  }
};

const changesBrandIconColor = (mutation) =>
  mutation.attributeName === "style" &&
  declaredBrandIconColor(mutation.oldValue) !==
    declaredBrandIconColor(mutation.target.getAttribute("style"));

const handleMutations = (mutations) => {
  for (const mutation of mutations) {
    if (mutation.type === "attributes") {
      if (mutation.attributeName === "style") {
        trackDeclarer(mutation.target);
        if (mutation.oldValue?.includes(PROJECT_VARIABLE_PREFIX)) {
          scheduleActivitySync();
        }
      }
      if (changesBrandIconColor(mutation)) {
        rescan(mutation.target);
      }
      if (isBrandElement(mutation.target)) {
        applyTo(mutation.target);
      }
      continue;
    }
    if (mutation.removedNodes.length) {
      scheduleActivitySync();
      if (fontStylesheetDeclarers.size) {
        scheduleFontStylesheetSync();
      }
    }
    for (const node of mutation.addedNodes) {
      if (node.nodeType !== Node.ELEMENT_NODE) {
        continue;
      }
      trackDeclarer(node);
      if (isBrandElement(node)) {
        applyTo(node);
      }
      scan(node);
    }
  }
};

const observers = new Set();
let watchedRoots = new WeakSet();
const watch = (root) => {
  if (watchedRoots.has(root)) {
    return;
  }
  watchedRoots.add(root);
  styleHost(root);
  const observer = new MutationObserver(handleMutations);
  observer.observe(root, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ["src", "style"],
    attributeOldValue: true,
  });
  observers.add(observer);
  scan(root);
};

// The module stays dormant, without patching attachShadow or observing any root, until a
// project theme declares one of its variables somewhere on the page.
let active = false;
// A project variable was set on an element no scan has found yet (for example one not yet
// connected), so the module must not fall dormant before that element shows up.
let unlocatedDeclaration = false;
// Weak references keep declarers that the frontend detaches and reattaches (cached views)
// without keeping them alive.
const declarerReferences = new Set();
const trackedDeclarers = new WeakSet();

const trackDeclarer = (element) => {
  if (declaresProjectTheme(element)) {
    unlocatedDeclaration = false;
    if (!trackedDeclarers.has(element)) {
      trackedDeclarers.add(element);
      declarerReferences.add(new WeakRef(element));
    }
  }
  trackFontStylesheet(element);
};

const projectThemeInUse = () => {
  if (unlocatedDeclaration || declaresProjectTheme(document.documentElement)) {
    return true;
  }
  for (const reference of declarerReferences) {
    const element = reference.deref();
    if (element && declaresProjectTheme(element)) {
      return true;
    }
    declarerReferences.delete(reference);
    if (element) {
      trackedDeclarers.delete(element);
    }
  }
  return false;
};

let attachShadowPatched = false;
const patchAttachShadow = () => {
  if (attachShadowPatched) {
    return;
  }
  attachShadowPatched = true;
  // Never restored: another module may have wrapped it since, so it only idles while dormant.
  const nativeAttachShadow = Element.prototype.attachShadow;
  Element.prototype.attachShadow = function attachShadow(...options) {
    const root = nativeAttachShadow.apply(this, options);
    if (active) {
      queueMicrotask(() => active && watch(root));
    }
    return root;
  };
};

const activate = () => {
  active = true;
  patchAttachShadow();
  watch(document);
};

const deactivate = () => {
  for (const observer of observers) {
    handleMutations(observer.takeRecords());
    observer.disconnect();
  }
  observers.clear();
  watchedRoots = new WeakSet();
  active = false;
  syncFontStylesheets();
};

let activitySyncPending = false;
const syncActivity = () => {
  activitySyncPending = false;
  syncBodyFontBinding();
  const inUse = projectThemeInUse();
  if (inUse && !active) {
    activate();
  } else if (!inUse && active) {
    deactivate();
  }
};

const scheduleActivitySync = () => {
  if (!activitySyncPending) {
    activitySyncPending = true;
    queueMicrotask(syncActivity);
  }
};

// The frontend applies every theme through style.setProperty, which is the only signal
// cheap enough to watch while dormant.
const nativeSetProperty = CSSStyleDeclaration.prototype.setProperty;
CSSStyleDeclaration.prototype.setProperty = function setProperty(name, value, ...rest) {
  const result = nativeSetProperty.call(this, name, value, ...rest);
  if (typeof name === "string" && name.startsWith(PROJECT_VARIABLE_PREFIX)) {
    if (!active && value) {
      unlocatedDeclaration = true;
    }
    scheduleActivitySync();
  }
  return result;
};

syncActivity();

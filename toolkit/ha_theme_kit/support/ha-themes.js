const PROJECT_VARIABLE_PREFIX = "--ha-themes-";
const FONT_STYLESHEET_VARIABLE = "--ha-themes-font-stylesheet";
const BRAND_PATH = "/api/brands/";
const BRAND_ICON_COLOR_VARIABLE = "--ha-themes-brand-icon-color";
const BRAND_ICON_COLOR_DECLARATION = new RegExp(`${BRAND_ICON_COLOR_VARIABLE}\\s*:\\s*([^;]*)`);
// Generic integration icons on the brands CDN are a single flat color; real logos are not.
const GENERIC_ICON_RGB = [0, 171, 248];
const CHANNEL_TOLERANCE = 3;

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
    style.textContent = "body { font-family: var(--ha-font-family-body); }";
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

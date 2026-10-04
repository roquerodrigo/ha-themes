const fontStylesheets = [
  "https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400..700;1,400..700&family=Poppins:wght@300;400;500;600;700&display=swap"
];

const BRAND_PATH = "/api/brands/";
const BRAND_ICON_COLOR_VARIABLE = "--ha-themes-brand-icon-color";
// Generic integration icons on the brands CDN are a single flat color; real logos are not.
const GENERIC_ICON_RGB = [0, 171, 248];
const CHANNEL_TOLERANCE = 3;

const appendOnce = (selector, create) => {
  if (!document.head.querySelector(selector)) {
    document.head.append(create());
  }
};

appendOnce("style[data-ha-themes]", () => {
  const style = document.createElement("style");
  style.dataset.haThemes = "";
  style.textContent = "body { font-family: var(--ha-font-family-body); }";
  return style;
});

for (const href of fontStylesheets) {
  appendOnce(`link[href="${href}"]`, () => {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    return link;
  });
}

const brandIconColor = () =>
  getComputedStyle(document.documentElement).getPropertyValue(BRAND_ICON_COLOR_VARIABLE).trim();

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

const recoloredUrl = async (url, color) => {
  const key = new URL(url, location.href).pathname;
  if (!genericIconCache.has(key)) {
    genericIconCache.set(
      key,
      loadImage(url).then((image) => (isGenericIcon(image) ? image : null), () => null),
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

const originalSource = (element) => {
  if (element instanceof HTMLImageElement) {
    if (element.src.includes(BRAND_PATH)) {
      element.dataset.haThemesSrc = element.src;
      element.dataset.haThemesSrcset = element.srcset;
    }
    return element.dataset.haThemesSrc;
  }
  const url = backgroundBrandUrl(element);
  if (url) {
    element.dataset.haThemesBackground = url;
  }
  return element.dataset.haThemesBackground;
};

const applyTo = async (element) => {
  const source = originalSource(element);
  if (!source) {
    return;
  }
  const color = brandIconColor();
  const replacement = color ? await recoloredUrl(source, color) : null;
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
};

const isBrandElement = (element) =>
  (element instanceof HTMLImageElement &&
    (element.src.includes(BRAND_PATH) || element.dataset.haThemesSrc)) ||
  element.dataset?.haThemesBackground ||
  element.style?.backgroundImage.includes(BRAND_PATH);

const scan = (root) => {
  for (const element of root.querySelectorAll("*")) {
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

const watchedRoots = new WeakSet();
const watch = (root) => {
  if (watchedRoots.has(root)) {
    return;
  }
  watchedRoots.add(root);
  new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      if (mutation.type === "attributes") {
        if (isBrandElement(mutation.target)) {
          applyTo(mutation.target);
        }
        continue;
      }
      for (const node of mutation.addedNodes) {
        if (node.nodeType !== Node.ELEMENT_NODE) {
          continue;
        }
        if (isBrandElement(node)) {
          applyTo(node);
        }
        scan(node);
      }
    }
  }).observe(root, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ["src", "style"],
  });
  scan(root);
};

const nativeAttachShadow = Element.prototype.attachShadow;
Element.prototype.attachShadow = function attachShadow(...options) {
  const root = nativeAttachShadow.apply(this, options);
  queueMicrotask(() => watch(root));
  return root;
};

let lastColor = brandIconColor();
new MutationObserver(() => {
  const color = brandIconColor();
  if (color !== lastColor) {
    lastColor = color;
    scan(document);
  }
}).observe(document.documentElement, { attributes: true, attributeFilter: ["style"] });

watch(document);

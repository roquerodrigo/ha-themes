const fontStylesheets = [
  "https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400..700;1,400..700&family=Poppins:wght@300;400;500;600;700&display=swap"
];

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

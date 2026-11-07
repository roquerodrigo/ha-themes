() => {
  const root = document.documentElement;
  const declared = {};
  const conditional = {};

  const collectStyleRule = (rule, condition) => {
    if (rule.selectorText !== "html") {
      return;
    }
    for (let index = 0; index < rule.style.length; index++) {
      const name = rule.style[index];
      if (!name.startsWith("--")) {
        continue;
      }
      const value = rule.style.getPropertyValue(name).trim();
      if (condition) {
        conditional[name] = { condition, value };
      } else {
        declared[name] = value;
      }
    }
  };

  const walkRules = (rules, condition) => {
    for (const rule of rules) {
      if (rule instanceof CSSStyleRule) {
        collectStyleRule(rule, condition);
      } else if (rule instanceof CSSMediaRule) {
        walkRules(rule.cssRules, rule.conditionText);
      }
    }
  };

  for (const sheet of [...document.styleSheets, ...document.adoptedStyleSheets]) {
    try {
      walkRules(sheet.cssRules, null);
    } catch (_error) {
      continue;
    }
  }

  const inline = {};
  for (let index = 0; index < root.style.length; index++) {
    const name = root.style[index];
    if (name.startsWith("--")) {
      inline[name] = root.style.getPropertyValue(name).trim();
    }
  }

  const computedStyle = getComputedStyle(root);
  const computed = {};
  for (const name of new Set([...Object.keys(declared), ...Object.keys(inline)])) {
    computed[name] = computedStyle.getPropertyValue(name).trim();
  }

  return { declared, conditional, inline, computed };
};

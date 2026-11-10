/* SPDX-License-Identifier: MIT */
(function (scope) {
  'use strict';
  function resolveLocale(catalog, saved, preferences = []) {
    const locales = catalog.locales;
    function match(input) {
      if (typeof input !== 'string' || !input.trim()) return null;
      const raw = input.trim();
      const garmin = locales.find(item => item.garmin === raw.toLowerCase());
      if (garmin) return garmin.id;
      let tag;
      try { tag = new Intl.Locale(raw.replace(/_/g, '-')); }
      catch { return null; }
      const exact = locales.find(item => item.id.toLowerCase() === tag.toString().toLowerCase());
      if (exact) return exact.id;
      if (tag.language === 'zh') {
        const script = tag.script || tag.maximize().script;
        return script === 'Hant' ? 'zh-Hant' : script === 'Hans' ? 'zh-Hans' : null;
      }
      const language = tag.language === 'no' ? 'nb' : tag.language;
      return locales.find(item => item.id === language)?.id || null;
    }
    const candidates = [saved, ...(Array.isArray(preferences) ? preferences : [])];
    for (const candidate of candidates) {
      const found = match(candidate);
      if (found) return found;
    }
    return catalog.defaultLocale;
  }
  const api = {resolveLocale};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else scope.SpaceFoxI18n = api;
})(globalThis);

/* SPDX-License-Identifier: MIT. Export the accepted marker owner without browser layout. */
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm');
class Element {
  constructor(tag) { this.tag = tag; this.attributes = {}; this.style = {}; this.dataset = {}; this.children = []; }
  setAttribute(name, value) { this.attributes[name] = String(value); }
  append(child) { this.children.push(child); }
}
const context = { document: { createElementNS(_ns, tag) { return new Element(tag); } } };
context.window = context;
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(__dirname, '../prototype/marker/renderer.js'), 'utf8'), context);
const escape = value => String(value).replaceAll('&', '&amp;').replaceAll('"', '&quot;').replaceAll('<', '&lt;');
const serialize = node => {
  const styles = Object.entries(node.style).map(([key, value]) => key.replace(/[A-Z]/g, c => '-' + c.toLowerCase()) + ':' + value).join(';');
  const attrs = { ...node.attributes, style: styles };
  return '<' + node.tag + Object.entries(attrs).map(([key, value]) => ' ' + key + '="' + escape(value) + '"').join('') + '>' + node.children.map(serialize).join('') + '</' + node.tag + '>';
};
// Two transparent pixels around the radius12 disk avoid clipping its antialiasing.
process.stdout.write('<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 28 28">' + serialize(context.SpaceFoxMR.markerGlyph('ring24', 14, 14)) + '</svg>');

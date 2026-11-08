import fs from 'node:fs';

// Exact brand swatches only: status colors, photos and layout are untouched.
const {colors} = JSON.parse(fs.readFileSync(new URL('../content/ocean-palette.json', import.meta.url), 'utf8'));
const rgb = hex => [1, 3, 5].map(i => parseInt(hex.slice(i, i + 2), 16));
const channels = new Map(Object.entries(colors).map(([from, to]) => [rgb(from).join(','), rgb(to)]));

export function oceanColors(source) {
  return source
    .replace(/#[\da-f]{6}(?:[\da-f]{2})?\b/gi, hex => {
      const replacement = colors[hex.slice(0, 7).toUpperCase()];
      return replacement ? replacement + hex.slice(7) : hex;
    })
    .replace(/\b(rgba?\()\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)(?=\s*[,\)])/gi, (match, prefix, r, g, b) => {
      const replacement = channels.get([r, g, b].join(','));
      return replacement ? prefix + replacement.join(', ') : match;
    })
    .replace(/(--mui-palette-[\w-]+Channel:\s*)(\d+) (\d+) (\d+)/g, (match, prefix, r, g, b) => {
      const replacement = channels.get([r, g, b].join(','));
      return replacement ? prefix + replacement.join(' ') : match;
    });
}

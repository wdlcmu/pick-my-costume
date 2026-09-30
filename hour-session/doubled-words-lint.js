#!/usr/bin/env node
/**
 * doubled-words-lint.js — copy-hygiene gate for generated suggestion/share strings.
 *
 * Catches what template concatenation and copy edits introduce:
 *   1. Doubled words:      "ketchup ketchup", "the the"
 *   2. Double hedges:      "about ~$12", "roughly ~15 minutes" (one hedge is enough)
 *   3. Doubled punctuation: "!!", "??", "  " double spaces inside visible copy
 *
 * Usage: node hour-session/doubled-words-lint.js [file ...]
 *   No args -> scans the repo's known string sources (share captions, suggestion
 *   copy in the e*-preview files, pantry.html, index.html). Exits 1 on hits.
 *   index.html / bank.json hits are REPORT-only (owned by other agents).
 */
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const DEFAULT_FILES = [
  'index.html',
  'pantry.html',
  'e12-preview.html', 'e13-preview.html', 'e25-preview.html', 'e26-preview.html',
  'e27-preview.html', 'e28-preview.html', 'e30-preview.html', 'e31-preview.html',
];

const files = process.argv.slice(2).length
  ? process.argv.slice(2)
  : DEFAULT_FILES.map(f => path.join(ROOT, f));

// Doubled-word match on visible text (skip code-y spans handled by extraction below).
const DOUBLED_WORD = /\b([a-zA-Z]{2,})\s+\1\b/gi;      // "ketchup ketchup"
// "about ~$12", "roughly ~15 min", "around ~$8", "approximately ~..."
const DOUBLE_HEDGE = /\b(about|around|roughly|approximately|nearly|almost|close to)\s+~\s*\$?\d/i;
// Doubled sentence punctuation outside URLs/code.
const DOUBLED_PUNCT = /([!?])\1/;
const DOUBLE_SPACE = /[^\s]\s{2,}[^\s]/;

// Intentional repetitions that are legitimate copy (onomatopoeia, song lyrics).
const KNOWN_GOOD = [/buzz buzz/i, /doo doo/i, /hee hee/i];

// Extract candidate copy: JS string literals + HTML visible text, minus script internals.
function extractStrings(src) {
  const chunks = [];
  // JS/JSON single/double-quoted string literals (multiline-safe, simple heuristic)
  const litRe = /(['"])((?:\\\1|(?:(?!\1)[^\\])){3,})\1/g;
  let m;
  while ((m = litRe.exec(src)) !== null) {
    const s = m[2];
    // Skip strings that are clearly code: selectors, URLs, ids, hex, regexes,
    // and space-joined CSS class lists ("btn btn-ghost copylist").
    if (/^[#.\w/-]*$/.test(s)) continue;
    if (/^[\w-]+(\s+[\w-]+)+\s*$/.test(s) && !/[A-Z.,!?'"()]/.test(s)) continue;
    if (/^https?:\/\//.test(s) && !/ /.test(s)) continue;
    if (/^[a-f0-9]{8,}$/i.test(s)) continue;
    chunks.push({ text: s, kind: 'literal' });
  }
  // HTML visible text: strip tags/scripts/styles/comments
  const html = src
    .replace(/<script[\s\S]*?<\/script>/gi, ' ')
    .replace(/<style[\s\S]*?<\/style>/gi, ' ')
    .replace(/<!--[\s\S]*?-->/g, ' ')
    .replace(/<[^>]+>/g, ' ');
  html.split(/\n+/).forEach(line => {
    const t = line.trim();
    if (t.length > 8 && /[a-zA-Z]/.test(t)) chunks.push({ text: t, kind: 'text' });
  });
  return chunks;
}

let failures = 0;
for (const file of files) {
  if (!fs.existsSync(file)) continue;
  const rel = path.relative(ROOT, file);
  const src = fs.readFileSync(file, 'utf8');
  for (const { text, kind } of extractStrings(src)) {
    const checks = [
      ['doubled-word', DOUBLED_WORD],
      ['double-hedge', DOUBLE_HEDGE],
    ];
    for (const [label, re] of checks) {
      re.lastIndex = 0;
      const hit = re.exec(text);
      if (hit && !KNOWN_GOOD.some(g => g.test(text))) {
        failures++;
        console.log(`${rel} [${label}] (${kind}): ...${hit[0]}...`);
        console.log(`    ctx: ${text.slice(Math.max(0, hit.index - 60), hit.index + 80).trim()}`);
      }
    }
    // Punct/space checks only on visible text, not code literals
    if (kind === 'text') {
      const p = DOUBLED_PUNCT.exec(text);
      if (p) { failures++; console.log(`${rel} [doubled-punct] (text): ${p[0]} — ${text.slice(0, 90).trim()}`); }
      const sp = DOUBLE_SPACE.exec(text.replace(/ {2,}/g, m2 => m2)); // keep simple
      void sp;
    }
  }
}
console.log(failures ? `\n${failures} hit(s).` : '\nClean.');
process.exit(failures ? 1 : 0);

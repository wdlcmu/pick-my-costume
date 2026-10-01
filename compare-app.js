/* compare-app.js — client logic for the dynamic /compare page.
 *
 * Two halves:
 *  PURE renderers (no DOM): cmpCard, cmpCards, cmpH2, cmpBluf, cmpTradeoffs.
 *    The generator (gen_compare.js) loads these in Node to server-render the
 *    default matchup into compare.html, so crawlers see a real comparison.
 *  BROWSER boot (guarded by `typeof window !== 'undefined'`): search-first
 *    picker, chips, ?vs= shareable URLs (replaceState), swap, and UnitTrack
 *    instrumentation. Never executed by the generator.
 *
 * Globals the page provides before this script: CMP_DATA, CMP_DEFAULT.
 * Visible copy rule: no em/en dashes anywhere, same as the rest of the site.
 */
'use strict';

/* ============================ PURE ============================ */

function cmpEsc(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function cmpJoinNames(names) {
  if (names.length < 3) return names.join(' and ');
  return names.slice(0, -1).join(', ') + ', and ' + names[names.length - 1];
}

function cmpTimeMin(t) {
  var m = String(t).match(/(\d+)/);
  return m ? +m[1] : 999;
}

function cmpSpookCell(n) {
  if (!n) return 'Not spooky';
  var p = '';
  for (var i = 0; i < n; i++) p += '&#127875;';
  return p + ' <span class="fine">(' + n + ' of 3)</span>';
}

function cmpRow(label, valueHtml) {
  return '<div class="cr"><dt>' + cmpEsc(label) + '</dt><dd>' + valueHtml + '</dd></div>';
}

function cmpCard(d) {
  var tonightCell = d.tonight ? 'Yes - nothing to buy'
    : 'Not yet - ' + d.buyN + ' to buy';
  var buyCell = d.buy.length ? cmpEsc(d.buy.join('; ')) : 'Nothing';
  var homeCell = d.home.length ? cmpEsc(d.home.join('; ')) : 'None';
  if (d.note.length) {
    homeCell += ' <span class="fine">Plus ' + cmpEsc(d.note.join('; ')) +
      ' (unmarked in the bank; likely at home)</span>';
  }
  var rows = [
    cmpRow('Make tonight', cmpEsc(tonightCell)),
    cmpRow('Supplies to buy', buyCell),
    cmpRow('Use from home', homeCell),
    cmpRow('Build time', cmpEsc(d.time)),
    cmpRow('Effort', cmpEsc(d.effort)),
    cmpRow('Best for', cmpEsc(d.aud)),
    cmpRow('Vibe', cmpEsc(d.vibe)),
    cmpRow('Spookiness', cmpSpookCell(d.spook)),
    cmpRow('Why it wins', cmpEsc(d.w))
  ].join('');
  return '<article class="cmp-card">' +
    '<a class="cmp-photo" href="/c/' + d.id + '" data-item-id="' + d.id + '"' +
    ' aria-label="' + cmpEsc(d.t) + ' build guide">' +
    '<img src="/photos/' + d.id + '.webp" alt="' + cmpEsc(d.t) +
    ' costume" loading="lazy"></a>' +
    '<h3 class="cmp-title"><a href="/c/' + d.id + '" data-item-id="' + d.id + '">' +
    cmpEsc(d.t) + '</a></h3>' +
    '<p class="cmp-blurb">' + cmpEsc(d.b) + '</p>' +
    '<dl class="cmp-rows">' + rows + '</dl>' +
    '<a class="cmp-guide" href="/c/' + d.id + '" data-item-id="' + d.id + '">' +
    'Step-by-step for the ' + cmpEsc(d.t.toLowerCase()) + ' &rarr;</a>' +
    '</article>';
}

function cmpCards(ids, DB) {
  return ids.map(function (id) { return cmpCard(DB[id]); }).join('\n');
}

function cmpH2(ids, DB) {
  return ids.map(function (id) { return DB[id].t; }).join(' vs ') + ': head to head';
}

function cmpBluf(ids, DB) {
  var rows = ids.map(function (id) { return DB[id]; });
  var nWord = ids.length === 2 ? 'Two' : 'Three';
  var byTime = rows.slice().sort(function (a, b) { return cmpTimeMin(a.time) - cmpTimeMin(b.time); });
  var fastMin = cmpTimeMin(byTime[0].time);
  var fastTie = byTime.filter(function (r) { return cmpTimeMin(r.time) === fastMin; });
  var fastLine = fastTie.length === 1
    ? fastTie[0].t + ' is the fastest (' + fastTie[0].time + ')'
    : cmpJoinNames(fastTie.map(function (r) { return r.t; })) + ' tie for fastest (' + fastTie[0].time + ')';
  var kidRows = rows.filter(function (r) { return r.kid; });
  var kidLine = '';
  if (kidRows.length && kidRows.length < rows.length) {
    kidLine = ' Only the ' + cmpJoinNames(kidRows.map(function (r) { return r.t; })) +
      (kidRows.length > 1 ? ' work' : ' works') + ' for young kids.';
  }
  var efforts = {};
  rows.forEach(function (r) { efforts[r.effort] = 1; });
  var effortLine = Object.keys(efforts).length === 1
    ? ' Every one is rated ' + rows[0].effort + ' in our build guides and links to a full step-by-step below.'
    : ' Each links to a full step-by-step build guide below.';
  return nWord + ' easy DIY costumes, head to head. ' +
    fastLine + '.' + kidLine + effortLine +
    ' Numbers come straight from our costume bank, which is what powers the Pick My Costume quiz.';
}

function cmpTradeoffs(ids, DB) {
  return ids.map(function (id) {
    var d = DB[id];
    var line = d.tonight ? 'nothing to buy beyond the assumed basics'
      : 'needs ' + d.buyN + ' store item' + (d.buyN > 1 ? 's' : '');
    return '<li><strong>' + cmpEsc(d.t) + ':</strong> ' + cmpEsc(d.time) + ', ' +
      cmpEsc(line) + '. ' + cmpEsc(d.w) + '</li>';
  }).join('\n');
}

/* ====================== BROWSER ONLY ====================== */
if (typeof window !== 'undefined') (function () {
  var DB = window.CMP_DATA || {};
  var DEF = window.CMP_DEFAULT || [];
  var MAXPICK = 3;
  var selected = [];

  function $(id) { return document.getElementById(id); }

  /* ---------- analytics: same anonymous beacon pattern as pantry ---------- */
  var _phq = [];
  function cmpTrack(name, props) {
    try {
      if (window.posthog && posthog.capture) posthog.capture(name, props || {});
      else _phq.push([name, props || {}]);
    } catch (e) {}
  }
  (function () {
    var s = document.createElement('script');
    s.async = true;
    s.src = 'https://us.i.posthog.com/static/array.js';
    s.onload = function () {
      try {
        if (window.posthog && posthog.init) {
          posthog.init('phc_t9dkHXAZR5VEjPFm3K5JDzGKFsNNxKcwSxxcEBEeLbS7', {
            api_host: 'https://us.i.posthog.com', autocapture: false,
            capture_pageview: true, disable_session_recording: true
          });
          _phq.splice(0).forEach(function (e) { try { posthog.capture(e[0], e[1]); } catch (x) {} });
        }
      } catch (e) {}
    };
    try { document.head.appendChild(s); } catch (e) {}
  })();

  /* ---------- UnitTrack (standing rule: every content unit instrumented) -- */
  var CMP_UNITS = {
    'compare-picker': { type: 'picker', container: 'cmp-picker' },
    'compare-cards': { type: 'cards', container: 'cmp-cards' }
  };
  var seenUnit = {};
  function pageName() { try { return location.pathname || '/'; } catch (e) { return '/'; } }
  function unitAnchors(container) {
    var out = [], list = container.querySelectorAll('a,button[data-item-id]'), i;
    for (i = 0; i < list.length; i++) out.push(list[i]);
    return out;
  }
  function unitItemId(el) {
    if (el.getAttribute && el.getAttribute('data-item-id')) return el.getAttribute('data-item-id');
    var href = el.getAttribute('href') || '';
    var m = href.match(/\/c\/([^\/?#]+)/);
    return m ? m[1] : 'unknown';
  }
  function fireUnitImpression(unitId, def, container) {
    if (seenUnit[unitId]) return;
    seenUnit[unitId] = true;
    var ids = unitAnchors(container).map(unitItemId);
    cmpTrack('unit_impression', {
      unit_id: unitId, unit_type: def.type, page: pageName(),
      item_count: ids.length, item_ids: ids.slice(0, 40)
    });
  }
  function instrumentUnit(unitId) {
    var def = CMP_UNITS[unitId];
    if (!def) return;
    var container = $(def.container);
    if (!container || container.__cmpTracked) return;
    container.__cmpTracked = true;
    container.addEventListener('click', function (e) {
      var t = e.target;
      var a = (t && t.closest) ? t.closest('a,button[data-item-id]') : null;
      if (!a || !container.contains(a)) return;
      var pos = unitAnchors(container).indexOf(a);
      cmpTrack('unit_click', {
        unit_id: unitId, unit_type: def.type, page: pageName(),
        item_id: unitItemId(a), position: pos
      });
    });
    try {
      if ('IntersectionObserver' in window) {
        var io = new IntersectionObserver(function (entries) {
          for (var i = 0; i < entries.length; i++) {
            if (entries[i].isIntersecting) { fireUnitImpression(unitId, def, container); io.disconnect(); }
          }
        }, { threshold: 0.4 });
        io.observe(container);
      } else { fireUnitImpression(unitId, def, container); }
    } catch (e2) { fireUnitImpression(unitId, def, container); }
  }

  /* ---------- matchup state ---------- */
  function validIds(ids) {
    var out = [];
    (ids || []).forEach(function (raw) {
      var id = String(raw || '').trim().toLowerCase();
      if (id && DB[id] && out.indexOf(id) < 0) out.push(id);
    });
    return out.slice(0, MAXPICK);
  }
  function parseUrl() {
    try {
      var m = /[?&]vs=([^&#]*)/.exec(location.search);
      if (!m) return null;
      var ids = validIds(decodeURIComponent(m[1]).split(','));
      return ids.length >= 2 ? ids : null;
    } catch (e) { return null; }
  }
  /* replaceState, not pushState: in-page Back exits to where you came from
     (codebase convention, same as the quiz result URLs). */
  function setUrl(ids) {
    try {
      history.replaceState(null, '', location.pathname + '?vs=' + ids.join(','));
    } catch (e) {}
  }

  /* ---------- picker ---------- */
  function norm(s) { return String(s || '').toLowerCase().replace(/[^a-z0-9]/g, ''); }
  function search(q) {
    q = norm(q);
    if (!q) return [];
    var out = [];
    Object.keys(DB).forEach(function (id) {
      if (selected.indexOf(id) > -1) return;
      var d = DB[id], score = 0, t = norm(d.t);
      if (t.indexOf(q) === 0) score = 100;
      else if (t.indexOf(q) > -1) score = 60;
      else {
        for (var i = 0; i < d.al.length; i++) {
          var na = norm(d.al[i]);
          if (na.indexOf(q) === 0) { score = 80; break; }
          if (na.indexOf(q) > -1) { score = 40; break; }
        }
      }
      if (score) out.push({ id: id, score: score });
    });
    out.sort(function (a, b) {
      return b.score - a.score || DB[a.id].t.localeCompare(DB[b.id].t);
    });
    return out.slice(0, 8);
  }

  function renderChips() {
    var box = $('cmp-chips');
    box.innerHTML = selected.map(function (id) {
      var d = DB[id];
      var locked = selected.length <= 2 ? ' disabled aria-disabled="true" title="Keep at least 2 to compare"' : '';
      return '<button type="button" class="chip" data-item-id="' + id + '" data-chip="' + id + '"' + locked +
        ' aria-label="Remove ' + cmpEsc(d.t) + '">' + cmpEsc(d.t) +
        ' <span aria-hidden="true">&times;</span></button>';
    }).join('');
  }

  function renderHint() {
    var h = $('cmp-hint');
    if (selected.length >= MAXPICK) h.textContent = '3 is the max - remove one to add another.';
    else h.textContent = 'Pick 2 or 3 costumes to compare - 3 is the max.';
  }

  function renderResults(q) {
    var box = $('cmp-results');
    var hits = search(q);
    if (!hits.length) { box.hidden = true; box.innerHTML = ''; return; }
    var capped = selected.length >= MAXPICK;
    box.innerHTML = hits.map(function (h, i) {
      return '<button type="button" role="option" class="cmp-hit" data-item-id="' + h.id + '"' +
        (capped ? ' disabled' : '') + '>' + cmpEsc(DB[h.id].t) + '</button>';
    }).join('');
    box.hidden = false;
  }

  function renderBrowse() {
    var box = $('cmp-browse');
    if (!box || box.__built) return;
    box.__built = true;
    var ids = Object.keys(DB).sort(function (a, b) { return DB[a].t.localeCompare(DB[b].t); });
    box.innerHTML = ids.map(function (id) {
      return '<button type="button" class="browse-btn" data-item-id="' + id + '">' + cmpEsc(DB[id].t) + '</button>';
    }).join('');
    var sum = $('cmp-browse-sum');
    if (sum) sum.innerHTML = 'Browse all ' + ids.length + ' costumes';
  }

  function render(ids) {
    selected = validIds(ids);
    if (selected.length < 2) selected = DEF.slice();
    $('cmp-h2').textContent = cmpH2(selected, DB);
    $('cmp-bluf').textContent = cmpBluf(selected, DB);
    $('cmp-cards').innerHTML = cmpCards(selected, DB);
    $('cmp-tradeoffs').innerHTML = cmpTradeoffs(selected, DB);
    var swap = $('cmp-swap');
    swap.hidden = selected.length !== 2;
    renderChips();
    renderHint();
    renderBrowse();
    setUrl(selected);
  }

  function add(id) {
    if (!DB[id] || selected.indexOf(id) > -1 || selected.length >= MAXPICK) return;
    selected.push(id);
    render(selected);
    cmpTrack('compare_matchup_viewed', { ids: selected.join(','), via: 'picker' });
  }

  function remove(id) {
    if (selected.length <= 2) return;
    selected = selected.filter(function (x) { return x !== id; });
    render(selected);
    cmpTrack('compare_matchup_viewed', { ids: selected.join(','), via: 'picker' });
  }

  function boot() {
    var picker = $('cmp-picker');
    if (!picker) return;
    var input = $('cmp-search');

    picker.addEventListener('click', function (e) {
      var chip = e.target.closest ? e.target.closest('[data-chip]') : null;
      if (chip && !chip.disabled) { remove(chip.getAttribute('data-chip')); return; }
      var hit = e.target.closest ? e.target.closest('.cmp-hit,.browse-btn') : null;
      if (hit && !hit.disabled) {
        add(hit.getAttribute('data-item-id'));
        input.value = '';
        renderResults('');
        input.focus();
      }
    });
    input.addEventListener('input', function () { renderResults(input.value); });
    input.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') {
        var first = $('cmp-results').querySelector('.cmp-hit:not([disabled])');
        if (first) {
          add(first.getAttribute('data-item-id'));
          input.value = '';
          renderResults('');
        }
        e.preventDefault();
      }
      if (e.key === 'Escape') { renderResults(''); input.blur(); }
    });
    document.addEventListener('click', function (e) {
      if (!picker.contains(e.target)) renderResults('');
    });

    var swap = $('cmp-swap');
    if (swap) swap.addEventListener('click', function () {
      if (selected.length !== 2) return;
      selected = [selected[1], selected[0]];
      render(selected);
      cmpTrack('compare_matchup_viewed', { ids: selected.join(','), via: 'swap' });
    });

    var cta = document.querySelector('.cta');
    if (cta) cta.addEventListener('click', function () {
      cmpTrack('compare_quiz_cta', { page: 'compare' });
    });

    var fromUrl = parseUrl();
    render(fromUrl || DEF);
    if (fromUrl) cmpTrack('compare_matchup_viewed', { ids: fromUrl.join(','), via: 'url' });
    instrumentUnit('compare-picker');
    instrumentUnit('compare-cards');
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();

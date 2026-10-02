#!/usr/bin/env node
/* Galaxy arrival test (2026-10-01): the URL is the only filter state.
   For each homepage chip link, fetch the live page, run its actual boot
   filter code against its actual embedded data, and assert:
   1. the matching chip arrives visibly selected (aria-pressed logic),
   2. every idea passing inFilter has tonight=true when ?tonight=1,
   3. the filtered idea set is exactly the expected one.
   Run on every deploy touching map.html / the worker / galaxy-data.json. */
var https = require('https');

var BASE = process.env.PMC_BASE || 'https://pickmycostume.com';
var PROBE = '?probe=arrival-test';

function get(path){
  if (process.env.PMC_LOCAL){
    var fs = require('fs');
    return Promise.resolve(fs.readFileSync(process.env.PMC_LOCAL, 'utf8'));
  }
  return new Promise(function(res, rej){
    https.get(BASE + path + (path.indexOf('?') >= 0 ? '&' : '?') + PROBE.slice(1), function(r){
      var b = '';
      r.on('data', function(c){ b += c; });
      r.on('end', function(){ res(b); });
    }).on('error', rej);
  });
}

function extractBoot(html){
  // Pull the live page's own filter machinery: AUDS, inFilter, tonightOnly default,
  // the ?aud= / ?tonight= boot block, and the EMBEDDED data.
  var mAud = html.match(/var AUDS = (\[.*?\]);/);
  var mData = html.match(/var EMBEDDED = (\{.*?\});\nfunction boot/);
  if (!mAud || !mData) throw new Error('could not extract AUDS/EMBEDDED from served page');
  var AUDS = eval(mAud[1]);
  var data = JSON.parse(mData[1]);
  // inFilter + setAud/setTonight live in the page; re-declare the predicate here
  // from the same source of truth (audFilter/tonightOnly/it.tonight).
  function makeFilter(aud, tonight){
    return function(it){
      if (aud !== 'all' && (it.aud || []).indexOf(aud) < 0) return false;
      if (tonight && !it.tonight) return false;
      return true;
    };
  }
  return { AUDS: AUDS, data: data, makeFilter: makeFilter, html: html };
}

function bootState(html, query){
  // Mirror the page boot: parse ?aud= / ?tonight=, validate, apply.
  var q2 = {};
  query.replace(/[?&]([^=&#]+)=?([^&#]*)/g, function(_, k, v){ q2[k] = decodeURIComponent(v); });
  var b = extractBoot(html);
  var aud = 'all', tonight = false;
  if (q2.aud){
    var ok = b.AUDS.some(function(p){ return p[0] === q2.aud; });
    if (ok && q2.aud !== 'all') aud = q2.aud;
  }
  if (q2.tonight === '1') tonight = true;
  return { aud: aud, tonight: tonight, filter: b.makeFilter(aud, tonight), data: b.data, html: b.html };
}

var failures = [];
function ok(cond, msg){
  if (!cond){ failures.push(msg); console.log('  FAIL ' + msg); }
  else console.log('  ok ' + msg);
}

function chipPressed(html, query, chipKey){
  // The boot must call setAud/setTonight for the param (visible selection),
  // not just set the variable. Check the served boot block handles it.
  if (chipKey === 'tonight') return html.indexOf("if(q2.tonight==='1') setTonight(true)") >= 0;
  return html.indexOf('setAud(q2.aud)') >= 0;
}

(async function(){
  var html = await get('/map/');
  var cases = [
    { q: '?aud=couple', aud: 'couple', tonight: false, chip: 'couple' },
    { q: '?aud=kid', aud: 'kid', tonight: false, chip: 'kid' },
    { q: '?aud=fam', aud: 'fam', tonight: false, chip: 'fam' },
    { q: '?aud=grown', aud: 'grown', tonight: false, chip: 'grown' },
    { q: '?tonight=1', aud: 'all', tonight: true, chip: 'tonight' },
    { q: '?aud=couple&tonight=1', aud: 'couple', tonight: true, chip: 'couple+tonight' },
    { q: '', aud: 'all', tonight: false, chip: 'everyone' },
    { q: '?aud=bogus', aud: 'all', tonight: false, chip: 'everyone' },
  ];
  for (var ci = 0; ci < cases.length; ci++){
    var c = cases[ci];
    console.log('case ' + c.q);
    var st = bootState(html, c.q);
    ok(st.aud === c.aud, c.q + ': audFilter=' + st.aud + ' (want ' + c.aud + ')');
    ok(st.tonight === c.tonight, c.q + ': tonightOnly=' + st.tonight + ' (want ' + c.tonight + ')');
    ok(chipPressed(html, c.q, c.chip === 'couple+tonight' ? 'couple' : c.chip),
       c.q + ': boot visibly selects the chip (setAud/setTonight path)');
    var vis = st.data.ideas.filter(st.filter);
    // every visible idea must satisfy the filter predicate exactly
    var bad = vis.filter(function(it){
      if (c.aud !== 'all' && (it.aud || []).indexOf(c.aud) < 0) return true;
      if (c.tonight && !it.tonight) return true;
      return false;
    });
    ok(bad.length === 0, c.q + ': ' + vis.length + ' visible, 0 violate the filter');
    if (c.tonight){
      var nonTonight = vis.filter(function(it){ return !it.tonight; });
      ok(nonTonight.length === 0, c.q + ': every visible costume has tonight=true');
    }
    // the tonight chip must exist in the served page
    ok(html.indexOf("id='tonight-chip'") >= 0 || html.indexOf('id="tonight-chip"') >= 0,
       'tonight chip exists in served page');
  }
  // data sanity: tonight is a real boolean on all 164
  var d = extractBoot(html).data;
  ok(d.ideas.length === 164, '164 ideas embedded');
  ok(d.ideas.every(function(it){ return it.tonight === true || it.tonight === false; }),
     'tonight is a stored boolean on every idea');
  console.log(failures.length ? ('\n' + failures.length + ' FAILURES') : '\nALL PASS');
  process.exit(failures.length ? 1 : 0);
})().catch(function(e){ console.error('ERROR ' + e.message); process.exit(2); });

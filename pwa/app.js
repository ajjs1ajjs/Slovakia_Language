/* Slovenčina 0→B2 PWA: каталог лекцій + TTS (Web Speech sk-SK) + MP3 + друк у PDF */
const LEVELS = [
  {id:'A0', dir:'00_A0-Zaklady-vymova', name:'A0 · Вимова'},
  {id:'A1', dir:'01_A1-Prezitie', name:'A1 · Виживання'},
  {id:'A2', dir:'02_A2-Kazdodenny-zivot', name:'A2 · Щоденне життя'},
  {id:'B1', dir:'03_B1-Nezavislost', name:'B1 · Незалежність'},
  {id:'B2', dir:'04_B2-Sloboda', name:'B2 · Свобода'},
];
let SLOW = true, LESSONS = [], CUR = null, SK_VOICE = null, AUDIO_IDX = null;

const $ = s => document.querySelector(s);
const esc = s => s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');

// --- мінімальний markdown → html (заголовки, таблиці, списки, bold, code, hr) ---
function md(src){
  const lines = src.split('\n'); let h='', table=[], inList=false;
  const flushT = ()=>{ if(table.length){
    const rows = table.map(r=>r.trim().replace(/^\||\|$/g,'').split('|').map(c=>c.trim()));
    const head = rows[0], body = rows.slice(1).filter(r=>!r.every(c=>/^:?-{2,}:?$/.test(c)));
    h += '<table><tr>'+head.map(c=>'<th>'+inline(c)+'</th>').join('')+'</tr>'
       + body.map(r=>'<tr>'+r.map((c,i)=>'<td>'+(i===0&&c?`<button class="speak" data-say="${esc(c)}">🔊</button>`:'')+inline(c)+'</td>').join('')+'</tr>').join('')+'</table>';
    table=[]; }};
  const flushL = ()=>{ if(inList){ h+='</ul>'; inList=false; }};
  for(const ln of lines){
    if(/^\|.*\|$/.test(ln.trim())){ flushL(); table.push(ln); continue; } flushT();
    if(/^#{1,4}\s/.test(ln)){ flushL(); const l=ln.match(/^(#+)/)[1].length; h+=`<h${l}>${inline(ln.replace(/^#+\s/,''))}</h${l}>`; continue; }
    if(/^---+$/.test(ln.trim())){ flushL(); h+='<hr>'; continue; }
    if(/^[-*]\s/.test(ln.trim())){ if(!inList){h+='<ul>';inList=true;} let t=ln.trim().slice(2);
      t=t.replace(/^—\s*(.+)$/,'<button class="speak" data-say="$1">🔊</button>$1'); h+='<li>'+inline(t)+'</li>'; continue; }
    if(/^\d+\.\s/.test(ln.trim())){ flushL(); let t=ln.trim().replace(/^\d+\.\s/,'');
      const dm2 = t.match(/^[—–-]\s*(.+)$/);
      if(dm2){ const say = dm2[1].split(' — ')[0].split(' [')[0].trim();
        h+='<p><button class="speak" data-say="'+esc(say)+'">🔊</button>'+inline(t)+'</p>'; continue; }
      h+='<p>'+inline(t)+'</p>'; continue; }
    if(!ln.trim()){ flushL(); continue; }
    flushL(); let t=ln;
    const dm = t.match(/^[—–-]\s*(.+)$/);
    if(dm){ const say = dm[1].split(' — ')[0].split(' [')[0].trim();
      h+='<p><button class="speak" data-say="'+esc(say)+'">🔊</button>'+inline(t)+'</p>'; continue; }
    h+='<p>'+inline(t)+'</p>';
  }
  flushT(); flushL(); return h;
}
function inline(s){ return esc(s).replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>').replace(/`(.+?)`/g,'<code>$1</code>'); }

// --- TTS: Web Speech, голос sk-SK, повільно/нормально ---
function pickVoice(){
  const vs = speechSynthesis.getVoices().filter(v=>v.lang.toLowerCase().startsWith('sk'));
  SK_VOICE = vs.find(v=>v.name.includes('Laura')) || vs[0] || null;
}
if('speechSynthesis' in window){ pickVoice(); speechSynthesis.onvoiceschanged = pickVoice; }
function speak(text){
  // якщо є готовий MP3 з тим самим текстом — граємо його, інакше Web Speech
  const norm = s => s.toLowerCase().replace(/[.\s]+$/,'').trim();
  const f = AUDIO_IDX && [...AUDIO_IDX.slow, ...AUDIO_IDX.normal].find(e=>norm(e.text)===norm(text)||norm(e.text).includes(norm(text)));
  if(f){ playFile(`../assets/audio/${CUR.id}/${f.file}`, text); return; }
  if(!('speechSynthesis' in window)){ alert('Нема TTS у цьому браузері'); return; }
  speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.lang='sk-SK'; if(SK_VOICE) u.voice=SK_VOICE; u.rate = SLOW?0.7:1;
  speechSynthesis.speak(u);
}
document.addEventListener('click', e=>{
  const b = e.target.closest('.speak'); if(!b) return;
  speak(b.dataset.say.replace(/\[.*?\]/g,'').trim());
});

// --- каталог ---
async function load(){
  LESSONS = await (await fetch('lessons.json')).json();
  const nav = $('#levels');
  LEVELS.forEach((l,i)=>{
    const b=document.createElement('button'); b.textContent=l.name;
    b.onclick=()=>{ [...nav.children].forEach(x=>x.classList.remove('on')); b.classList.add('on'); renderList(l.id); };
    nav.appendChild(b); if(i===0){ b.classList.add('on'); }
  });
  renderList('A0');
  $('#q').oninput = e=>renderList(null, e.target.value.toLowerCase());
}
function renderList(level, q=''){
  const box=$('#list'); box.innerHTML='';
  LESSONS.filter(l=>(!level||l.level===level)&&(!q||l.title.toLowerCase().includes(q))).forEach(l=>{
    const a=document.createElement('a'); a.href='#';
    a.innerHTML=`<strong>${l.id}</strong> · ${esc(l.title)}<br><small>${l.level}</small>`;
    if(CUR&&CUR.id===l.id) a.classList.add('on');
    a.onclick=ev=>{ev.preventDefault(); open(l);}; box.appendChild(a);
  });
}
async function open(l){
  CUR=l; document.querySelectorAll('#list a').forEach(a=>a.classList.toggle('on',a.textContent.includes(l.id)));
  const [raw, idx] = await Promise.all([
    (await fetch('../'+l.path)).text(),
    fetch(`../assets/audio/${l.id}/index.json`).then(r=>r.ok?r.json():null).catch(()=>null)
  ]);
  AUDIO_IDX = idx;
  $('#lesson').innerHTML = md(raw) + qrBlock(l);
  $('#lesson').scrollIntoView({behavior:'smooth',block:'start'});
  if('serviceWorker' in navigator){ /* lesson закешується SW при повторному візиті */ }
}
function qrBlock(l){
  if(!AUDIO_IDX) return '<p><small>🎧 MP3 ще генеруються через <code>tools/generate_audio.py</code>.</small></p>';
  const q = AUDIO_IDX.slow[0]||AUDIO_IDX.normal[0]; if(!q) return '';
  return `<p>🎧 Аудіо: ${AUDIO_IDX.slow.length+AUDIO_IDX.normal.length} файлів · перший: <button class="speak" data-say="${esc(q.text)}">🔊</button>
    <img class="qr" loading="lazy" src="../assets/qr/${l.id}/${q.file.replace('.mp3','.png')}" alt="QR до MP3" title="QR → MP3"></p>`;
}

// --- плеєр MP3 ---
function playFile(url, title){
  $('#player').classList.remove('hidden'); $('#p-title').textContent=title;
  const a=$('#audio'); a.src=url; a.play();
}
$('#p-play').onclick=()=>{ const a=$('#audio'); a.paused?a.play():a.pause(); };

// --- темп, друк, install, SW ---
$('#btn-slow').onclick=e=>{ SLOW=!SLOW; e.target.classList.toggle('on',SLOW); e.target.textContent=SLOW?'🐢 0.75×':'🐇 1×'; };
$('#btn-print').onclick=()=>window.print();
let deferred=null;
window.addEventListener('beforeinstallprompt',e=>{ e.preventDefault(); deferred=e; $('#btn-install').classList.remove('hidden'); });
$('#btn-install').onclick=async()=>{ if(deferred){ deferred.prompt(); deferred=null; $('#btn-install').classList.add('hidden'); } };
if('serviceWorker' in navigator) navigator.serviceWorker.register('sw.js');
load();

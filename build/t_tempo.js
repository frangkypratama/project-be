const { chromium } = require('playwright'); const fs=require('fs'); const http=require('http'); const path=require('path');
const which=process.env.SITE||'site'; const root=path.join(__dirname,'..',which);
const srv=http.createServer((q,r)=>{let f=path.join(root,decodeURIComponent(q.url.split('?')[0]));if(f.endsWith('/'))f+='index.html';
  fs.readFile(f,(e,d)=>{if(e){r.writeHead(404);r.end();return;}const html=f.endsWith('.html');
    r.writeHead(200,{'content-type':html?'text/html':f.endsWith('.json')?'application/json':'application/octet-stream'});
    r.end(html?'<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>'+d+'</body></html>':d);});}).listen(8772);
(async()=>{const b=await chromium.launch({args:['--autoplay-policy=no-user-gesture-required']});const p=await b.newPage({viewport:{width:1200,height:900}});const errs=[];
 p.on('pageerror',e=>errs.push(e.message));
 await p.route('**/*',r=>{const u=r.request().url();if(u.includes('abcjs'))return r.fulfill({body:fs.readFileSync(path.join(__dirname,'node_modules/abcjs/dist/abcjs-basic-min.js')),contentType:'application/javascript'});
   if(u.startsWith('http://localhost:8772'))return r.continue();return r.abort();});
 await p.goto('http://localhost:8772/#be-1');await p.waitForTimeout(1200);
 const setT=v=>p.evaluate(v=>{const i=document.getElementById('bpm');i.value=v;i.dispatchEvent(new Event('input',{bubbles:true}));},v);
 await setT(60);
 await p.evaluate(()=>{window.__ev=[];const els=[...document.querySelectorAll('#angka .el')];new MutationObserver(ms=>{ms.forEach(m=>{if(m.target.classList.contains('playing')&&!(m.oldValue||'').includes('playing'))window.__ev.push([performance.now(),els.indexOf(m.target)]);});}).observe(document.getElementById('angka'),{subtree:true,attributes:true,attributeFilter:['class'],attributeOldValue:true});});
 await p.click('#playBtn');await p.waitForTimeout(6000);
 const tChange=await p.evaluate(()=>performance.now()); await setT(120);
 await p.waitForTimeout(5000);
 const r=await p.evaluate(()=>({ev:window.__ev,playing:audio.playing,label:document.getElementById('playBtn').textContent}));
 // ms per ketukan: interval / durasi not sebelumnya (dur * unit)
 const durs=await p.evaluate(()=>{const h=current();const out=[];buildSecs(h).forEach(s=>{const u=unitOf(h,s.meter);noteEls(s.lines).forEach(e=>out.push(e.dur*u));});return out;});
 const per=[];for(let k=1;k<r.ev.length;k++){const dt=r.ev[k][0]-r.ev[k-1][0];const d=durs[r.ev[k-1][1]];if(d)per.push([Math.round(r.ev[k-1][0]-tChange),Math.round(dt/d)]);}
 const before=per.filter(x=>x[0]<-300).map(x=>x[1]), after=per.filter(x=>x[0]>400).map(x=>x[1]);
 const med=a=>a.length?a.slice().sort((x,y)=>x-y)[a.length>>1]:null;
 console.log(which,'ms/ketuk sebelum (60 bpm):',med(before),'n=',before.length,'| sesudah (120 bpm):',med(after),'n=',after.length,'| masih diputar:',r.playing,r.label.trim());
 await p.click('#playBtn');await p.waitForTimeout(300);
 console.log('berhenti:',await p.evaluate(()=>({playing:audio.playing,iv:!!audio.iv,hl:document.querySelectorAll('#staff .hl,.el.playing').length})));
 // akhir lagu alami pada tempo cepat
 await setT(130);await p.click('#playBtn');
 await p.waitForFunction(()=>!audio.playing,null,{timeout:60000}).then(()=>console.log('selesai sendiri: ya')).catch(()=>console.log('selesai sendiri: TIDAK'));
 console.log('errors',errs);await b.close();srv.close();})();

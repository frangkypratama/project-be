const { chromium } = require('playwright'); const fs=require('fs'); const http=require('http'); const path=require('path');
const root=path.join(__dirname,'..',process.env.SITE||'site');
const srv=http.createServer((q,r)=>{let f=path.join(root,decodeURIComponent(q.url.split('?')[0]));if(f.endsWith('/'))f+='index.html';
  fs.readFile(f,(e,d)=>{if(e){r.writeHead(404);r.end();return;}const html=f.endsWith('.html');
    r.writeHead(200,{'content-type':html?'text/html':f.endsWith('.json')?'application/json':'application/octet-stream'});
    r.end(html?'<!doctype html><html><head><meta charset="utf-8"></head><body>'+d+'</body></html>':d);});}).listen(8773);
(async()=>{const b=await chromium.launch({args:['--autoplay-policy=no-user-gesture-required']});const p=await b.newPage();
 await p.route('**/*',r=>{const u=r.request().url();if(u.includes('abcjs'))return r.fulfill({body:fs.readFileSync(path.join(__dirname,'node_modules/abcjs/dist/abcjs-basic-min.js')),contentType:'application/javascript'});
   if(u.startsWith('http://localhost:8773'))return r.continue();return r.abort();});
 for(const id of ['1','843']){
  await p.goto('http://localhost:8773/#be-'+id);await p.waitForTimeout(1000);
  const sec=await p.evaluate(()=>{const h=current();let beats=0;buildSecs(h).forEach(s=>{const u=unitOf(h,s.meter),reps=/:\|/.test(s.src)?2:1;noteEls(s.lines).forEach(e=>beats+=e.dur*u*reps);});return beats*60/130;});
  await p.evaluate(()=>{const i=document.getElementById('bpm');i.value=130;i.dispatchEvent(new Event('input',{bubbles:true}));});
  const t0=Date.now();await p.click('#playBtn');
  await p.waitForFunction(()=>!audio.playing,null,{timeout:120000});
  console.log('BE',id,'panjang hitungan',sec.toFixed(1),'dtk | berhenti sendiri setelah',((Date.now()-t0)/1000).toFixed(1),'dtk | label:',(await p.textContent('#playBtn')).trim(),'| sisa sorotan:',await p.evaluate(()=>document.querySelectorAll('#staff .hl,.el.playing').length));
 }
 await b.close();srv.close();})();

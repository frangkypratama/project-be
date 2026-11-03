const { chromium } = require('playwright'); const fs=require('fs'); const http=require('http'); const path=require('path');
const root=path.join(__dirname,'..',process.env.SITE||'site'); const PORT=8780+(process.env.SITE?1:0);
const srv=http.createServer((q,r)=>{let f=path.join(root,decodeURIComponent(q.url.split('?')[0]));if(f.endsWith('/'))f+='index.html';
  fs.readFile(f,(e,d)=>{if(e){r.writeHead(404);r.end();return;}const h=f.endsWith('.html');r.writeHead(200,{'content-type':h?'text/html':'application/json'});
    r.end(h?'<!doctype html><html><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"></head><body>'+d+'</body></html>':d);});}).listen(PORT);
(async()=>{const b=await chromium.launch();
 const c=await b.newContext({viewport:{width:1100,height:1000}});const p=await c.newPage();
 const errs=[];p.on('pageerror',e=>errs.push(e.message));
 await p.route('**/*',r=>{const u=r.request().url();if(u.includes('abcjs'))return r.fulfill({body:fs.readFileSync(path.join(__dirname,'node_modules/abcjs/dist/abcjs-basic-min.js')),contentType:'application/javascript'});
   if(u.startsWith('http://localhost:'+PORT))return r.continue();return r.abort();});
 await p.goto(`http://localhost:${PORT}/#be-550`);await p.waitForTimeout(1500);
 const syl=()=>p.evaluate(()=>Array.from(document.querySelectorAll('#angka .syl')).map(x=>x.textContent).filter(Boolean).slice(0,8).join('|'));
 const staffLyr=()=>p.evaluate(()=>Array.from(document.querySelectorAll('#staff .abcjs-lyric')).slice(0,6).map(x=>x.textContent).join('|'));
 console.log('chips',await p.evaluate(()=>document.querySelectorAll('.vchips button').length),'tag',await p.textContent('.vtag'));
 console.log('v1',await syl(),'//',await staffLyr());
 await p.click('.vchips button[data-k="1"]');await p.waitForTimeout(300);
 console.log('v2',await syl(),'//',await staffLyr(),'tag',await p.textContent('.vtag'),'cur',await p.evaluate(()=>document.querySelector('.verse.cur .vn').textContent));
 await p.screenshot({path:'v-550-a2.png',fullPage:false});
 // playback continues to next verse: set high tempo
 await p.click('.vchips button[data-k="2"]');
 await p.evaluate(()=>{const r=document.getElementById('bpm');r.value=130;r.dispatchEvent(new Event('input'));});
 await p.click('#playBtn');
 const t0=Date.now(); let seen=[];
 for(let i=0;i<60;i++){await p.waitForTimeout(500);const t=await p.textContent('.vtag');if(!seen.includes(t))seen.push(t);if(!(await p.evaluate(()=>audio.playing)))break;}
 console.log('tags seen during play',seen,'secs',(Date.now()-t0)/1000,'hl staff',await p.evaluate(()=>document.querySelectorAll('#staff .hl').length));
 // unmatched verse example
 const nm=await p.evaluate(async()=>{for(const e of INDEX){await loadBatch(e.batch);}return HYMNS.filter(h=>h.vl&&h.vl.some(v=>v&&v.x)).slice(0,1).map(h=>[h.id||h.be,h.vl.findIndex(v=>v&&v.x)])[0];});
 console.log('nomatch',nm);
 await p.goto(`http://localhost:${PORT}/#be-${nm[0]}`);await p.waitForTimeout(1200);
 await p.click(`.vchips button[data-k="${nm[1]}"]`);await p.waitForTimeout(300);
 console.log('vnote',await p.evaluate(()=>{const v=document.querySelector('.vnote');return [v.hidden,v.textContent.slice(0,120)];}),'syl',await syl());
 await p.screenshot({path:'v-nomatch.png'});
 // mobile
 await p.setViewportSize({width:390,height:844});await p.goto(`http://localhost:${PORT}/#be-550`);await p.waitForTimeout(1200);
 console.log('overflow',await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth));
 await p.screenshot({path:'v-550-m.png'});
 console.log('errs',errs);await b.close();srv.close();})();

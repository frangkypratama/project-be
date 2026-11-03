const { chromium } = require('playwright'); const fs=require('fs'); const http=require('http'); const path=require('path');
const root=path.join(__dirname,'..','site-prod');
const srv=http.createServer((q,r)=>{let f=path.join(root,decodeURIComponent(q.url.split('?')[0]));if(f.endsWith('/'))f+='index.html';
  fs.readFile(f,(e,d)=>{if(e){r.writeHead(404);r.end();return;}const html=f.endsWith('.html');
    r.writeHead(200,{'content-type':html?'text/html':f.endsWith('.json')?'application/json':'application/octet-stream'});
    r.end(html?'<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>'+d+'</body></html>':d);});}).listen(8771);
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:390,height:844},colorScheme:'dark'});const errs=[];
 p.on('pageerror',e=>errs.push(e.message));
 await p.route('**/*',r=>{const u=r.request().url();if(u.includes('abcjs'))return r.fulfill({body:fs.readFileSync(path.join(__dirname,'node_modules/abcjs/dist/abcjs-basic-min.js')),contentType:'application/javascript'});
   if(u.startsWith('http://localhost:8771'))return r.continue();return r.abort();});
 await p.goto('http://localhost:8771/');await p.waitForTimeout(1000);
 const ids=await p.evaluate(()=>INDEX.map(x=>String(x.id||x.be)));const bad=[];
 for(const id of ids){await p.evaluate(i=>{location.hash='#be-'+i;},id);
   try{await p.waitForFunction(i=>document.querySelector('.hymn-no')&&document.querySelector('.hymn-no').textContent===i&&document.querySelector('#staff svg')&&document.querySelector('.pager'),id,{timeout:5000});}catch(e){bad.push(id+':timeout');continue;}
   const r=await p.evaluate(()=>({ov:document.documentElement.scrollWidth>window.innerWidth,n:document.querySelectorAll('#staff .abcjs-note,#staff .abcjs-rest').length,e:document.querySelectorAll('.el:not(.hold)').length}));
   if(r.ov)bad.push(id+':overflow');}
 console.log('diuji',ids.length,'masalah',bad.length,bad.slice(0,20),'errors',errs.slice(0,5));
 await p.setViewportSize({width:1280,height:900});await p.goto('http://localhost:8771/#be-281');await p.waitForTimeout(1200);console.log('sisa:',await p.evaluate(()=>({footer:!!document.querySelector('footer'),pilot:!!document.querySelector('.pilot-note'),scan:!!document.getElementById('scanPanel'),refs:false,notes:false})));// '),refs:/pembanding/i.test(document.body.innerText),draf:/draf/i.test(document.body.innerText)})));await p.click('#playBtn');await p.waitForTimeout(1000);console.log('putar hl',await p.evaluate(()=>document.querySelectorAll('#staff .hl').length));await p.screenshot({path:'prod-v2.png',fullPage:true});
 await b.close();srv.close();})();

const { chromium } = require('playwright'); const fs=require('fs'); const http=require('http'); const path=require('path');
const root=path.join(__dirname,'..','site');
const srv=http.createServer((q,r)=>{let f=path.join(root,decodeURIComponent(q.url.split('?')[0]));if(f.endsWith('/'))f+='index.html';
  fs.readFile(f,(e,d)=>{if(e){r.writeHead(404);r.end();return;}const h=f.endsWith('.html');r.writeHead(200,{'content-type':h?'text/html':'application/json'});
    r.end(h?'<!doctype html><html><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"></head><body>'+d+'</body></html>':d);});}).listen(8778);
(async()=>{const b=await chromium.launch();
 const c=await b.newContext({viewport:{width:1100,height:900}});const p=await c.newPage();
 const errs=[];p.on('pageerror',e=>errs.push(e.message));
 await p.route('**/*',r=>{const u=r.request().url();if(u.includes('abcjs'))return r.fulfill({body:fs.readFileSync(path.join(__dirname,'node_modules/abcjs/dist/abcjs-basic-min.js')),contentType:'application/javascript'});
   if(u.startsWith('http://localhost:8778'))return r.continue();return r.abort();});
 for(const n of [550,12]){
  await p.goto('http://localhost:8778/#be-'+n);await p.waitForTimeout(1500);
  const st=await p.evaluate(()=>({sep:!!document.querySelector('.flow.sep'),hb:document.querySelectorAll('.el.hb').length,hb2:document.querySelectorAll('.el.hb2').length,holdWithHb:document.querySelectorAll('.el.hold.hb,.el.hold.hb2').length}));
  console.log(n,JSON.stringify(st));
  const el=await p.$('#angka');if(el)await el.screenshot({path:`ov-${n}.png`});
 }
 console.log('errs',errs);await b.close();srv.close();})();

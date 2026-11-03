const { chromium } = require('playwright'); const fs=require('fs'); const http=require('http'); const path=require('path');
const root=path.join(__dirname,'..','site'); const PORT=8795;
const srv=http.createServer((q,r)=>{let f=path.join(root,decodeURIComponent(q.url.split('?')[0]));if(f.endsWith('/'))f+='index.html';
  fs.readFile(f,(e,d)=>{if(e){r.writeHead(404);r.end();return;}const h=f.endsWith('.html');r.writeHead(200,{'content-type':h?'text/html':'application/json'});
    r.end(h?'<!doctype html><html><head><meta charset=utf-8></head><body>'+d+'</body></html>':d);});}).listen(PORT);
(async()=>{const b=await chromium.launch();const p=await (await b.newContext()).newPage();const errs=[];p.on('pageerror',e=>errs.push(e.message));
 await p.route('**/*',r=>{const u=r.request().url();if(u.includes('abcjs'))return r.fulfill({body:fs.readFileSync(path.join(__dirname,'node_modules/abcjs/dist/abcjs-basic-min.js')),contentType:'application/javascript'});
   if(u.startsWith('http://localhost:'+PORT))return r.continue();return r.abort();});
 for(const n of process.argv.slice(2)){await p.goto(`http://localhost:${PORT}/#be-${n}`);await p.waitForTimeout(1200);
  console.log(n,await p.evaluate(()=>({btn:[...document.querySelectorAll('.vchips button')].map(b=>b.textContent).join(','),bar:!!document.querySelector('.vbar'),tag:document.querySelector('.vtag').textContent,nomatch:document.querySelectorAll('.nomatch').length})));}
 console.log('errs',errs);await b.close();srv.close();})();

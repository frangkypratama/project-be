const { chromium } = require('playwright'); const fs=require('fs'); const http=require('http'); const path=require('path');
const root=path.join(__dirname,'..',process.env.SITE||'site-prod');
const srv=http.createServer((q,r)=>{let f=path.join(root,decodeURIComponent(q.url.split('?')[0]));if(f.endsWith('/'))f+='index.html';
  fs.readFile(f,(e,d)=>{if(e){r.writeHead(404);r.end();return;}const html=f.endsWith('.html');
    r.writeHead(200,{'content-type':html?'text/html':'application/json'});
    r.end(html?'<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>'+d+'</body></html>':d);});}).listen(8775);
(async()=>{const b=await chromium.launch();const errs=[];
 for(const [w,scheme] of [[1200,'light'],[390,'dark']]){
  const ctx=await b.newContext({viewport:{width:w,height:800},colorScheme:scheme});const p=await ctx.newPage();p.on('pageerror',e=>errs.push(e.message));
  await p.route('**/*',r=>{const u=r.request().url();if(u.includes('abcjs'))return r.fulfill({body:fs.readFileSync(path.join(__dirname,'node_modules/abcjs/dist/abcjs-basic-min.js')),contentType:'application/javascript'});if(u.startsWith('http://localhost:8775'))return r.continue();return r.abort();});
  await p.goto('http://localhost:8775/#be-1');await p.waitForTimeout(1200);
  const st=()=>p.evaluate(()=>({theme:document.documentElement.dataset.theme,bg:getComputedStyle(document.body).backgroundColor,stroke:document.querySelector('#staff svg path')?.getAttribute('fill')||document.querySelector('#staff .abcjs-staff path')?.getAttribute('stroke')||null,label:document.getElementById('themeBtn').getAttribute('aria-label'),over:document.documentElement.scrollWidth>innerWidth}));
  console.log(w,scheme,'awal',JSON.stringify(await st()));
  await p.click('#themeBtn');await p.waitForTimeout(500);console.log('  klik 1',JSON.stringify(await st()));
  await p.screenshot({path:`theme-${w}-1.png`,clip:{x:0,y:0,width:w,height:300}});
  await p.reload();await p.waitForTimeout(1000);console.log('  reload (tersimpan)',JSON.stringify(await st()));
  await p.click('#themeBtn');await p.waitForTimeout(400);console.log('  klik 2',JSON.stringify(await st()));
  await ctx.close();}
 console.log('errors',errs);await b.close();srv.close();})();

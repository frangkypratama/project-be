const { chromium } = require('playwright'); const fs=require('fs'); const http=require('http'); const path=require('path');
const root=path.join(__dirname,'..','site-prod');
const srv=http.createServer((q,r)=>{let f=path.join(root,decodeURIComponent(q.url.split('?')[0]));if(f.endsWith('/'))f+='index.html';
  fs.readFile(f,(e,d)=>{if(e){r.writeHead(404);r.end();return;}const html=f.endsWith('.html');
    r.writeHead(200,{'content-type':html?'text/html':f.endsWith('.json')?'application/json':'application/octet-stream'});
    r.end(html?'<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"></head><body>'+d+'</body></html>':d);});}).listen(8770);
(async()=>{const b=await chromium.launch({args:['--autoplay-policy=no-user-gesture-required']});
 const route=async p=>{await p.route('**/*',r=>{const u=r.request().url();if(u.includes('abcjs'))return r.fulfill({body:fs.readFileSync(path.join(__dirname,'node_modules/abcjs/dist/abcjs-basic-min.js')),contentType:'application/javascript'});
   if(u.startsWith('http://localhost:8770'))return r.continue();return r.abort();});};
 const errs=[];
 for(const [w,h,scheme,tag] of [[1280,900,'light','desk-light'],[390,844,'dark','mob-dark']]){
  const p=await b.newPage({viewport:{width:w,height:h},colorScheme:scheme});await route(p);
  p.on('pageerror',e=>errs.push(tag+': '+e.message));
  await p.goto('http://localhost:8770/#be-281');await p.waitForTimeout(1500);
  const info=await p.evaluate(()=>({title:document.title,h1:document.querySelector('h1').textContent,pager:[...document.querySelectorAll('.pager a')].map(a=>a.getAttribute('href')),
    count:document.getElementById('count').textContent,st:document.querySelector('#list .st')?.textContent,edit:getComputedStyle(document.querySelector('details.edit')).display,
    overflowX:document.documentElement.scrollWidth>window.innerWidth, notes:document.querySelector('details.notes summary').textContent}));
  console.log(tag,JSON.stringify(info));
  await p.screenshot({path:`prod-${tag}.png`});
  await p.click('#playBtn');await p.evaluate(()=>window.scrollTo(0,700));await p.waitForTimeout(1800);
  console.log(tag,'putar: hl balok=',await p.evaluate(()=>document.querySelectorAll('#staff .hl').length),'angka=',await p.evaluate(()=>document.querySelectorAll('.el.playing').length),
     'toolbar top=',await p.evaluate(()=>Math.round(document.querySelector('.toolbar').getBoundingClientRect().top)));
  await p.screenshot({path:`prod-${tag}-scroll.png`});
  await p.click('#playBtn');
  await p.keyboard.press('ArrowRight');await p.waitForTimeout(900);
  console.log(tag,'ArrowRight ->',await p.evaluate(()=>location.hash+' '+document.querySelector('h1').textContent));
  if(w<500){await p.click('#listToggle');await p.waitForTimeout(200);console.log('list open visible items:',await p.evaluate(()=>document.querySelectorAll('#list li').length),'ol shown:',await p.evaluate(()=>getComputedStyle(document.getElementById('list')).display));
    await p.screenshot({path:`prod-${tag}-list.png`});}
  await p.close();
 }
 console.log('errors',errs);await b.close();srv.close();})();

const { chromium } = require('playwright'); const fs=require('fs'); const path=require('path');
const B='http://localhost:8800';
(async()=>{const b=await chromium.launch();
 const route=async p=>p.route('**/*',r=>{const u=r.request().url();if(u.includes('abcjs'))return r.fulfill({body:fs.readFileSync(path.join(__dirname,'node_modules/abcjs/dist/abcjs-basic-min.js')),contentType:'application/javascript'});if(u.startsWith(B))return r.continue();return r.abort();});
 // 1) tanpa JS (yang dibaca crawler tanpa render)
 const c0=await b.newContext({javaScriptEnabled:false});const p0=await c0.newPage();await route(p0);
 await p0.goto(B+'/be/550/');
 console.log('noJS', await p0.evaluate(()=>({title:document.title,h1:document.querySelector('h1').textContent,desc:document.querySelector('meta[name=description]').content.slice(0,120),canon:document.querySelector('link[rel=canonical]').href,verses:document.querySelectorAll('.verse').length,ld:JSON.parse(document.querySelector('script[type="application/ld+json"]').textContent)['@type'],pager:[...document.querySelectorAll('.pager a')].map(a=>a.getAttribute('href'))})));
 await p0.goto(B+'/');console.log('noJS home links',await p0.evaluate(()=>document.querySelectorAll('#list a[href^="/be/"]').length));
 // 2) dengan JS
 const c=await b.newContext({viewport:{width:1100,height:900}});const p=await c.newPage();await route(p);const errs=[];p.on('pageerror',e=>errs.push(e.message));p.on('console',m=>{if(m.type()==='error')errs.push(m.text())});
 await p.goto(B+'/be/550/');await p.waitForTimeout(1500);
 console.log('JS 550',await p.evaluate(()=>({h1:document.querySelector('h1').textContent,angka:document.querySelectorAll('#angka .el').length,staff:document.querySelectorAll('#staff .abcjs-note').length,chips:document.querySelectorAll('.vchips button').length,cur:(document.querySelector('#list a[aria-current]')||{}).getAttribute?.('href'),listN:document.querySelectorAll('#list a').length})));
 await p.click('.pager a.next');await p.waitForLoadState();await p.waitForTimeout(1200);
 console.log('next ->',p.url(),await p.textContent('h1'));
 await p.keyboard.press('ArrowLeft');await p.waitForTimeout(1500);console.log('ArrowLeft ->',p.url());
 await p.click('#list a[href="/be/12/"]');await p.waitForTimeout(1500);console.log('list click ->',p.url(),await p.textContent('h1'));
 await p.goto(B+'/#be-281');await p.waitForTimeout(1500);console.log('hash lama ->',p.url(),await p.textContent('h1'));
 await p.goto(B+'/');await p.waitForTimeout(1000);console.log('home h1',await p.textContent('h1'),'list',await p.evaluate(()=>document.querySelectorAll('#list a').length));
 await p.fill('#q','568');await p.waitForTimeout(300);await p.press('#q','Enter');await p.waitForTimeout(1500);console.log('cari 568 Enter ->',p.url());
 await p.goto(B+'/be/568b/');await p.waitForTimeout(1200);console.log('varian',await p.textContent('h1'));
 await p.setViewportSize({width:390,height:844});await p.goto(B+'/be/550/');await p.waitForTimeout(1200);
 console.log('mobile overflow',await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth));await p.screenshot({path:'static-550-m.png'});
 console.log('errs',errs);await b.close();})();

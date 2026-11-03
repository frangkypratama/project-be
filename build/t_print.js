const { chromium } = require('playwright'); const fs=require('fs'); const path=require('path');
const B='http://localhost:8803';
(async()=>{const b=await chromium.launch();const errs=[];
 for(const [n,sch,view] of process.argv.slice(2).map(x=>x.split(':'))){
  const c=await b.newContext({viewport:{width:1100,height:900},colorScheme:sch});const p=await c.newPage();p.on('pageerror',e=>errs.push(n+': '+e.message));
  await p.addInitScript(v=>{try{localStorage.setItem('be-view',v)}catch(e){}},view||'both');
  await p.route('**/*',r=>{const u=r.request().url();if(u.includes('abcjs'))return r.fulfill({body:fs.readFileSync(path.join(__dirname,'node_modules/abcjs/dist/abcjs-basic-min.js')),contentType:'application/javascript'});if(u.startsWith(B))return r.continue();return r.abort();});
  await p.goto(B+'/be/'+n+'/');await p.waitForTimeout(1300);
  const btn=await p.evaluate(()=>!!document.getElementById('printBtn'));
  await p.evaluate(()=>window.dispatchEvent(new Event('beforeprint')));await p.waitForTimeout(400);
  const svgs=await p.evaluate(()=>document.querySelectorAll('#staff svg').length);
  await p.pdf({path:`print-${n}-${sch}.pdf`,preferCSSPageSize:true,printBackground:true});
  await p.evaluate(()=>window.dispatchEvent(new Event('afterprint')));await p.waitForTimeout(300);
  const after=await p.evaluate(()=>document.querySelectorAll('#staff svg').length);
  console.log(n,sch,view,'tombol',btn,'svg saat cetak',svgs,'setelah',after);
  await c.close();}
 console.log('errs',errs);await b.close();})();

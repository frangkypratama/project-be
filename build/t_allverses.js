const { chromium } = require('playwright'); const fs=require('fs'); const http=require('http'); const path=require('path');
const root=path.join(__dirname,'..',process.env.SITE||'site'); const PORT=8790;
const srv=http.createServer((q,r)=>{let f=path.join(root,decodeURIComponent(q.url.split('?')[0]));if(f.endsWith('/'))f+='index.html';
  fs.readFile(f,(e,d)=>{if(e){r.writeHead(404);r.end();return;}const h=f.endsWith('.html');r.writeHead(200,{'content-type':h?'text/html':'application/json'});
    r.end(h?'<!doctype html><html><head><meta charset=utf-8></head><body>'+d+'</body></html>':d);});}).listen(PORT);
(async()=>{const b=await chromium.launch();const p=await (await b.newContext({viewport:{width:1100,height:900}})).newPage();
 const errs=[];p.on('pageerror',e=>errs.push(e.message));
 await p.route('**/*',r=>{const u=r.request().url();if(u.includes('abcjs'))return r.fulfill({body:fs.readFileSync(path.join(__dirname,'node_modules/abcjs/dist/abcjs-basic-min.js')),contentType:'application/javascript'});
   if(u.startsWith('http://localhost:'+PORT))return r.continue();return r.abort();});
 await p.goto(`http://localhost:${PORT}/`);await p.waitForTimeout(1500);
 let all={n:0,nv:0,miss:0,nbad:0,bad:[]};
 for(let B=1;B<=44;B++){
 await p.goto(`http://localhost:${PORT}/?b=${B}`);await p.waitForTimeout(400);
 await p.evaluate(()=>{view="angka";});
 const res=await p.evaluate(async(B)=>{await loadBatch(B);
   let n=0,nv=0,bad=[],miss=0;
   for(const h of HYMNS.filter(x=>x.batch===B)){CUR=h;try{renderHymn();}catch(x){bad.push([h.id||h.be,'render',x.message]);continue;}
     for(let k=1;k<h.verses.length;k++){try{setVerse(k);nv++;
       const v=h.vl[k]; if(v&&v.r){ // every lyric slot filled? count empty syl among targets
         const empt=CURSECS.reduce((a,s)=>a+noteEls(s.lines).filter(e=>!e.rest&&!e.inSlurCont).filter(e=>(e.syl||[]).some(x=>!x)).length,0);
         if(empt) bad.push([h.id||h.be,k+1,'slot kosong '+empt]);
         const abc=toABC(h,CURSECS); if(/\*/.test(abc.split('\n').filter(l=>l.startsWith('w:')).join(''))) bad.push([h.id||h.be,k+1,'lirik balok kosong']);
         if(k===1){drawStaff(h,CURSECS); if(!document.querySelectorAll('#staff .abcjs-note').length) bad.push([h.id||h.be,k+1,'staff kosong']);}
       } else miss++;
     }catch(x){bad.push([h.id||h.be,k+1,x.message]);}}
     n++;}
   return {n,nv,miss,bad:bad.slice(0,15),nbad:bad.length};},B);
 all.n+=res.n;all.nv+=res.nv;all.miss+=res.miss;all.nbad+=res.nbad;all.bad.push(...res.bad);}
 console.log(JSON.stringify({...all,bad:all.bad.slice(0,25)},null,1));console.log('errs',errs.slice(0,5));await b.close();srv.close();})();

"use strict";
var BP="/project-be"; // awalan path situs

var SCANS = {}, INDEX = [], LOADED = {}, SCANLOADED = {}, CUR = null;
var TOTAL_BE = 864;

/* Format data notasi (meniru penulisan buku):
   - spasi memisah ketukan; | garis birama; :| ulang; |] akhir; baris baru = ganti baris
   - 1-7 nada, 0 diam, . tahan satu ketukan (atau setengah dalam kelompok +)
   - ' sesudah angka = oktaf atas, , = oktaf bawah, # / b di depan = naik/turun setengah
   - a+b = dua not setengah ketukan dalam satu ketukan (garis atas di buku)
   - ( ) = legato/slur, v = tanda napas
   Lirik: suku kata dipisah "-", kata dipisah spasi; satu suku kata per not (not lanjutan slur dilewati). */
var HYMNS = [];

/* ---------- music theory helpers ---------- */
var LETTERS=["C","D","E","F","G","A","B"], NAT=[0,2,4,5,7,9,11], MAJ=[0,2,4,5,7,9,11];
var KEYS={C:[0,0],G:[4,0],D:[1,0],A:[5,0],E:[2,0],B:[6,0],F:[3,0],Bb:[6,-1],Eb:[2,-1],Ab:[5,-1],Db:[1,-1],Gb:[4,-1],"F#":[3,1]};
var DO_NAME={C:"C",G:"G",D:"D",A:"A",E:"E",B:"B",F:"F",Bb:"Bes",Eb:"Es",Ab:"As",Db:"Des",Gb:"Ges","F#":"Fis"};
function keyInfo(key,shift){
  shift=shift||0;
  var k=KEYS[key]||KEYS.C, li=k[0], tonic=60+NAT[li]+k[1]+12*shift, alt={};
  for(var d=0;d<7;d++){var L=(li+d)%7, oc=Math.floor((li+d)/7); var m=tonic+MAJ[d]; alt[LETTERS[L]]=m-(60+12*(oc+shift)+NAT[L]);}
  for(var x in alt) alt[x]-=0;
  return {li:li,tonic:tonic,alt:alt,shift:shift};
}
function pitchOf(n,ki){ // n: {deg,oct,acc}
  var d=n.deg-1, L=(ki.li+d)%7, carry=Math.floor((ki.li+d)/7);
  var midi=ki.tonic+MAJ[d]+12*n.oct+n.acc;
  var octave=4+carry+n.oct+ki.shift; var natural=12*(octave+1)+NAT[L];
  var a=midi-natural, ks=ki.alt[LETTERS[L]], sym="";
  if(a!==ks){sym=a===0?"=":a===1?"^":a===-1?"_":a===2?"^^":"__";}
  var name=LETTERS[L];
  if(octave>=5){name=name.toLowerCase()+"'".repeat(octave-5);} else if(octave<4){name=name+",".repeat(4-octave);}
  return {midi:midi,abc:sym+name};
}

/* ---------- parser ---------- */
function parseNotes(src){
  var lines=[], cur=null, slurOpen=false, last=null;
  src.split("\n").forEach(function(lineSrc){
    var line={items:[]}; lines.push(line);
    var bar={beats:[],end:null}; line.items.push(bar);
    lineSrc.trim().split(/\s+/).forEach(function(tok){
      if(!tok) return;
      if(tok==="|"||tok===":|"||tok==="|]"){bar.end=tok;bar={beats:[],end:null};line.items.push(bar);return;}
      if(tok==="v"){var b=bar.beats.length?bar.beats:null; (b?b[b.length-1]:{}).breath=true; if(last) last.breath=true; return;}
      var parts=tok.split("+"), beat={els:[],breath:false}, unit=1/parts.length;
      parts.forEach(function(p){
        var m=p.match(/^(\()?([#b])?([0-7.])([',]*)(\))?$/);
        if(!m) throw new Error("Tidak dikenali: “"+p+"”");
        var el={raw:m[3],dur:unit,slurStart:!!m[1],slurEnd:!!m[5]};
        if(m[3]==="."){el.hold=true; if(last){last.dur+=unit;} el.owner=last;}
        else{
          el.deg=+m[3]; el.rest=el.deg===0;
          el.oct=(m[4].match(/'/g)||[]).length-(m[4].match(/,/g)||[]).length;
          el.acc=m[2]==="#"?1:m[2]==="b"?-1:0;
          if(el.slurStart) slurOpen=true;
          el.inSlurCont=slurOpen&&!el.slurStart&&!el.rest;
          last=el;
        }
        if(el.slurEnd){slurOpen=false; if(el.hold&&el.owner) el.owner.slurEndHere=true;}
        beat.els.push(el);
      });
      bar.beats.push(beat);
    });
    line.items=line.items.filter(function(b){return b.beats.length||b.end;});
  });
  return lines;
}
function noteEls(lines){var out=[];lines.forEach(function(l){l.items.forEach(function(b){b.beats.forEach(function(bt){bt.els.forEach(function(e){if(!e.hold)out.push(e);});});});});return out;}
function syllables(row){
  var out=[]; row.trim().split(/\s+/).forEach(function(w){if(w==="_"){out.push({t:"",cont:false,mel:true});return;}var s=w.split("-");s.forEach(function(x,i){out.push({t:x,cont:i<s.length-1});});});
  return out;
}
function assignLyrics(lines,rows){
  var targets=noteEls(lines).filter(function(e){return !e.rest&&!e.inSlurCont;});
  var report=[];
  rows.forEach(function(r,ri){
    var syl=syllables(r);
    report.push({row:ri,notes:targets.length,syl:syl.length});
    targets.forEach(function(e,i){(e.syl=e.syl||[])[ri]=syl[i]||null;});
  });
  return report;
}

/* ---------- not angka renderer ---------- */
function renderAngka(sec,container,rows){
  var sep=!!(current()&&current().overline==="sep"); // gaya buku: tiap not ½ ketuk punya garis atas sendiri
  var flow=document.createElement("div"); flow.className="flow"+(sep?" sep":"");
  var slurPairs=[], openStart=null;
  sec.lines.forEach(function(line){
    line.items.forEach(function(bar){
      var bd=document.createElement("div"); bd.className="bar";
      bar.beats.forEach(function(beat){
        var bt=document.createElement("div"); bt.className="beat"+(beat.els.length>1?" split":"")+(beat.els.length>2?" split2":"");
        beat.els.forEach(function(e){
          var el=document.createElement("div");
          el.className="el"+(e.hold?" hold":"")+(e.rest?" rest":"")+(e.acc>0?" sharp":e.acc<0?" flat":"")+(sep&&beat.els.length>1&&!e.hold?(e.dur<=.26?" hb2":" hb"):"");
          var up=document.createElement("span");up.className="up";up.textContent=e.oct>0?"•".repeat(e.oct):"";
          var dg=document.createElement("span");dg.className="dg";dg.textContent=e.hold?"·":String(e.deg);
          var dn=document.createElement("span");dn.className="dn";dn.textContent=e.oct<0?"•".repeat(-e.oct):"";
          el.appendChild(up);el.appendChild(dg);el.appendChild(dn);
          for(var r=0;r<rows;r++){var s=document.createElement("span");s.className="syl"+(r?" r2":"");var sy=e.syl&&e.syl[r];s.textContent=sy?(sy.t+(sy.cont?" -":"")):"";el.appendChild(s);}
          if(!e.hold) e.node=el;
          if(e.slurStart) openStart=el;
          if(e.slurEnd&&openStart){slurPairs.push([openStart,el]);openStart=null;}
          bt.appendChild(el);
          if(e.breath&&!e.hold){}
        });
        bd.appendChild(bt);
        if(beat.breath){var br=document.createElement("span");br.className="breath";br.textContent="’";bd.appendChild(br);}
      });
      if(bar.end){var bl=document.createElement("span");bl.className="barline"+(bar.end===":|"?" rep":bar.end==="|]"?" fin":"");bd.appendChild(bl);}
      flow.appendChild(bd);
    });
  });
  var svg=document.createElementNS("http://www.w3.org/2000/svg","svg");svg.setAttribute("class","slurs");flow.appendChild(svg);
  container.appendChild(flow);
  function draw(){
    while(svg.firstChild)svg.removeChild(svg.firstChild);
    var fr=flow.getBoundingClientRect();
    slurPairs.forEach(function(p){
      var a=p[0].querySelector(".dg").getBoundingClientRect(), b=p[1].querySelector(".dg").getBoundingClientRect();
      // arc sits above the beat box so it clears octave dots and half-beat overlines
      var ta=p[0].parentNode.getBoundingClientRect().top-fr.top-7, tb=p[1].parentNode.getBoundingClientRect().top-fr.top-7;
      var x1=a.left+a.width/2-fr.left, x2=b.left+b.width/2-fr.left, y=Math.min(ta,tb);
      if(Math.abs(a.top-b.top)>8){ // wrapped across rows: draw two open arcs
        seg(x1,ta,fr.width-x1>40?x1+40:fr.width);seg(Math.max(0,x2-40),tb,x2);return;}
      seg(x1,y,x2);
    });
    function seg(xa,yy,xb){var p=document.createElementNS("http://www.w3.org/2000/svg","path");var mid=(xa+xb)/2;p.setAttribute("d","M"+xa+" "+(yy+5)+" Q"+mid+" "+(yy-6)+" "+xb+" "+(yy+5));svg.appendChild(p);}
  }
  requestAnimationFrame(draw);
  if(window.ResizeObserver){new ResizeObserver(function(){draw();}).observe(flow);}
  if(document.fonts&&document.fonts.ready){document.fonts.ready.then(draw);}
  return draw;
}

/* ---------- ABC (not balok) ---------- */
function durStr(beats){var e=Math.round(beats*4);return e===1?"":String(e);}
function unitOf(h,m){var d=+String(m||h.meter||"4/4").split("/")[1]||4;return 4/d;}
function toABC(h,secs){
  var U=unitOf(h);
  var ki=keyInfo(h.key,h.oct), out=["X:1","M:"+(secs[0]&&secs[0].meter||h.meter),"L:1/16","K:"+h.key], curM=secs[0]&&secs[0].meter||h.meter, curK=h.key;
  secs.forEach(function(sec){
    var sm=sec.meter||h.meter; U=unitOf(h,sm); var pre=""; if(sm!==curM){pre="[M:"+sm+"] ";curM=sm;}
    var sk=sec.key||h.key; if(sk!==curK){pre+="[K:"+sk+"] ";curK=sk;ki=keyInfo(sk,h.oct);}
    var all={items:[]}; sec.lines.forEach(function(l){all.items=all.items.concat(l.items);});
    [all].forEach(function(line){
      var mus=[], lyr=sec.rows.map(function(){return [];});
      line.items.forEach(function(bar){
        bar.beats.forEach(function(beat){
          var chunk="", tri=beat.els.length===3&&beat.els.every(function(e){return Math.abs(e.dur*3-1)<1e-6;});
          if(tri) chunk="(3";
          beat.els.forEach(function(e){
            if(e.hold) return;
            var s="";
            if(e.breath) s+="!breath!";
            if(e.slurStart) s+="(";
            s+= e.rest?"z":pitchOf(e,ki).abc;
            s+=durStr(e.dur*U*(tri?1.5:1));
            if(e.slurEnd||e.slurEndHere) s+=")";
            chunk+=s;
            if(!e.rest){
              sec.rows.forEach(function(r,ri){
                if(e.inSlurCont){lyr[ri].push("_");return;}
                var sy=e.syl&&e.syl[ri]; lyr[ri].push(sy?(sy.mel?"_":sy.t.replace(/-/g,"")+(sy.cont?"-":"")):"*");
              });
            }
          });
          beat.els.forEach(function(e){if(e.hold&&e.slurEnd&&e.owner){}});
          if(chunk) mus.push(chunk);
        });
        if(bar.end) mus.push(bar.end==="|]"?"|]":bar.end);
      });
      out.push(pre+mus.join(" "));
      lyr.forEach(function(l){out.push("w: "+l.map(function(t){return /-$/.test(t)?t:t+" ";}).join("").replace(/\s+$/,""));});
    });
  });
  return out.join("\n");
}

/* ---------- audio ---------- */
var audio={ctx:null,timers:[],playing:false};
function stopAudio(keepTail){if(audio.iv){clearInterval(audio.iv);audio.iv=null;}audio.timers.forEach(clearTimeout);audio.timers=[];audio.playing=false;document.querySelectorAll(".el.playing").forEach(function(n){n.classList.remove("playing");});
  document.querySelectorAll("#staff .hl").forEach(function(n){n.classList.remove("hl");});
  if(audio.master&&!keepTail){try{audio.master.gain.setTargetAtTime(0,audio.ctx.currentTime,.04);}catch(e){}}
  var b=document.getElementById("playBtn"); if(b) b.innerHTML=PLAY_LABEL;}
/* Organ pipa: register Principal 8' + Octave 4' + Quint 2 2/3' + Superoctave 2', dengan ruang gema gereja */
function organWave(ctx){
  if(audio.wave) return audio.wave;
  var amp=[0,1,.62,.34,.42,.1,.16,.04,.2,.03,.05,0,.06]; // harmonik 1..12
  var re=new Float32Array(amp.length), im=new Float32Array(amp.length);
  for(var i=1;i<amp.length;i++) im[i]=amp[i];
  audio.wave=ctx.createPeriodicWave(re,im); return audio.wave;
}
function churchReverb(ctx){
  if(audio.ir) return audio.ir;
  var len=Math.floor(ctx.sampleRate*3.2), buf=ctx.createBuffer(2,len,ctx.sampleRate);
  for(var c=0;c<2;c++){var d=buf.getChannelData(c);for(var i=0;i<len;i++){var x=i/len;d[i]=(Math.random()*2-1)*Math.pow(1-x,3.2)*(i<ctx.sampleRate*.02?i/(ctx.sampleRate*.02):1);}}
  audio.ir=buf; return buf;
}
function curBpm(){return bpm;}
/* Penjadwal bertahap: not dijadwalkan ~0,2 detik ke depan memakai tempo saat itu,
   sehingga geser tempo langsung terdengar tanpa menghentikan pemutaran. */
function playHymn(h,secs){
  stopAudio();
  var AC=window.AudioContext||window.webkitAudioContext; if(!AC) return;
  audio.ctx=audio.ctx||new AC(); var ctx=audio.ctx; if(ctx.state==="suspended")ctx.resume();
  audio.master=ctx.createGain();audio.master.gain.value=.16;
  var tone=ctx.createBiquadFilter();tone.type="lowpass";tone.frequency.value=4200;tone.Q.value=.4;
  var dry=ctx.createGain();dry.gain.value=.75;
  var verb=ctx.createConvolver();verb.buffer=churchReverb(ctx);var wet=ctx.createGain();wet.gain.value=.5;
  tone.connect(dry);dry.connect(audio.master);tone.connect(verb);verb.connect(wet);wet.connect(audio.master);
  audio.master.connect(ctx.destination);
  var wave=organWave(ctx), ki=keyInfo(h.key,h.oct), seq=[];
  var gi=0, one=[]; // indeks not tanpa pengulangan = urutan not di not balok
  secs.forEach(function(sec){
    var notes=noteEls(sec.lines), reps=/:\|/.test(sec.src)?2:1;
    var uu=unitOf(h,sec.meter), kk=keyInfo(sec.key||h.key,h.oct); notes.forEach(function(e,i){e.u=uu;e.ki=kk;e.si=gi+i;}); gi+=notes.length;
    for(var r=0;r<reps;r++) notes.forEach(function(e){one.push(e);});
  });
  // satu putaran per ayat: mulai dari ayat yang dipilih, lanjut ke ayat berikut bila dicentang
  var ready=vReady(h), k0=VSEL.k||0, list=VALL?ready.filter(function(k){return k>=k0;}):[k0];
  if(list[0]!==k0) list.unshift(k0);
  list.forEach(function(vk,j){ if(j) seq.push({verse:vk,dur:0}); one.forEach(function(e){seq.push(e);}); });
  var idx=0, next=ctx.currentTime+.12;
  function sn(si){return document.querySelectorAll("#staff .abcjs-note, #staff .abcjs-rest")[si];}
  function step(){
    if(!audio.playing) return;
    var ahead=document.hidden?1.5:.2, spb=60/curBpm();
    while(idx<seq.length&&next<ctx.currentTime+ahead){
      var e=seq[idx], d=e.dur*spb*(e.u||unitOf(h));
      if(e.verse!==undefined){ // ganti lirik ke ayat berikut tepat saat not pertamanya berbunyi
        (function(vk,at){audio.timers.push(setTimeout(function(){if(audio.playing)setVerse(vk);},at));})(e.verse,Math.max(0,(next-ctx.currentTime)*1000-20));
        idx++; continue;
      }
      if(!e.rest){
        var f=440*Math.pow(2,(pitchOf(e,e.ki||ki).midi-69)/12), nx=seq[idx+1]; if(nx&&nx.verse!==undefined) nx=seq[idx+2];
        // organ dimainkan legato; jeda kecil hanya untuk napas, nada sama berulang, atau akhir lagu
        var gap=e.breath?Math.min(.18,d*.25):(!nx||nx.rest||(!nx.rest&&pitchOf(nx,nx.ki||ki).midi===pitchOf(e,e.ki||ki).midi))?.06:.012;
        var st=next, en=st+Math.max(.05,d-gap), g=ctx.createGain();
        g.gain.setValueAtTime(0,st);g.gain.linearRampToValueAtTime(1,st+.035);g.gain.setValueAtTime(1,en);g.gain.linearRampToValueAtTime(0,en+.07);
        [1,1.0016].forEach(function(det,k){ // dua pipa sedikit berbeda nada = suara organ yang hidup
          var o=ctx.createOscillator();o.setPeriodicWave(wave);o.frequency.value=f*det;
          var og=ctx.createGain();og.gain.value=k?.45:.7;
          o.connect(og);og.connect(g);o.start(st);o.stop(en+.1);
        });
        g.connect(tone);
      }
      (function(node,si,atMs,durMs){
        audio.timers.push(setTimeout(function(){if(node)node.classList.add("playing");
          var q=sn(si); if(q){q.classList.add("hl"); if(view==="balok"){try{q.scrollIntoView({block:"nearest",behavior:"smooth"});}catch(x){}}}},atMs));
        audio.timers.push(setTimeout(function(){if(node)node.classList.remove("playing");var q=sn(si);if(q)q.classList.remove("hl");},atMs+durMs-30));
      })(e.node,e.si,Math.max(0,(next-ctx.currentTime)*1000),d*1000);
      next+=d; idx++;
    }
    if(idx>=seq.length&&audio.iv){clearInterval(audio.iv);audio.iv=null;
      audio.timers.push(setTimeout(function(){stopAudio(true);},Math.max(0,(next-ctx.currentTime)*1000)+300));}
  }
  audio.playing=true; var b=document.getElementById("playBtn"); if(b) b.innerHTML=STOP_LABEL;
  audio.iv=setInterval(step,30); step();
}
var PLAY_LABEL='<svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true"><path d="M2 1l9 5-9 5z" fill="currentColor"/></svg>Putar';
var STOP_LABEL='<svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true"><rect x="2" y="2" width="8" height="8" fill="currentColor"/></svg>Berhenti';

/* ---------- state + views ---------- */
var view="both"; try{view=localStorage.getItem("be-view")||"both";}catch(e){}
var bpm=84;
var VSEL={id:null,k:0}, VALL=true, CURSECS=null, CURH=null; // ayat yang sedang tampil; putar semua ayat
function pad3(n){return ("00"+n).slice(-3);}
function buildSecs(h){
  return h.sections.map(function(s){var lines=parseNotes(s.notes);var rep=assignLyrics(lines,s.rows);return {lines:lines,rows:s.rows,src:s.notes,report:rep,meter:s.meter,key:s.key};});
}
function renderList(filter){
  var ol=document.getElementById("list"); ol.innerHTML="";
  var f=(filter||"").trim().toLowerCase().replace(/^be-?/,"");
  var shown=INDEX.filter(function(h){
    if(!f) return true;
    return String(h.be)===f.replace(/^0+/,"")||String(h.id||h.be)===f.replace(/^0+/,"")||!!h.bl&&String(h.bl)===f.replace(/^(bl|logu)\s*-?\s*/,"").replace(/^0+/,"")||h.title.toLowerCase().indexOf(f)>-1;
  });
  if(!shown.length){ol.innerHTML='<li class="empty">Tidak ada ende yang cocok. Coba nomor BE, nomor Logu, atau sebagian judul.</li>';return;}
  shown.forEach(function(h){
    var li=document.createElement("li"), a=document.createElement("a");
    a.href=BP+"/be/"+(h.id||h.be)+"/"; a.innerHTML='<span class="n">'+(h.id||h.be)+'</span><span class="t">'+h.title+'</span><span class="st">'+(h.variant?'lagu kedua':'')+'</span>';
    if(CUR&&(CUR.id||CUR.be)==(h.id||h.be)) a.setAttribute("aria-current","page");
    li.appendChild(a); ol.appendChild(li);
  });
}
function current(){return CUR;}
function pad2(n){return ("0"+n).slice(-2);}
function loadBatch(n){
  return fetch(BP+"/data/b"+pad2(n)+".json").then(function(r){if(!r.ok)throw new Error("HTTP "+r.status);return r.json();}).then(function(arr){
    arr.forEach(function(h){HYMNS.push(h);ORIG[h.id||h.be]=JSON.stringify(h.sections);});LOADED[n]=true;});
}
function loadScans(n){
  if(SCANLOADED[n]) return Promise.resolve();
  return fetch(BP+"/scans/b"+pad2(n)+".json").then(function(r){if(!r.ok)throw new Error("HTTP "+r.status);return r.json();}).then(function(o){for(var k in o)SCANS[k]=o[k];SCANLOADED[n]=true;});
}
function show(){
  if(!INDEX.length) return;
  var m=location.hash.match(/^#be-(\d+[a-z]?)$/);
  if(m){location.replace(BP+"/be/"+m[1].replace(/^0+/,"")+"/");return;} // alamat lama
  if(!window.BE_PAGE) return; // beranda: isi dari HTML statis
  var n=String(window.BE_PAGE);
  var e=INDEX.filter(function(x){return String(x.id||x.be)===n;})[0];
  var main=document.getElementById("main");
  if(!e){stopAudio();CUR=null;renderList(document.getElementById("q").value);
    main.innerHTML='<div class="hymn-head"><div class="hymn-no">'+n+'</div><h1>Belum ditranskrip</h1><div class="meta"><span>Ende nomor '+n+' sedang dikerjakan bertahap. Pilih nomor lain di daftar.</span></div></div>';return;}
  var p=LOADED[e.batch]?Promise.resolve():(main.innerHTML='<p class="loading">Memuat ende '+e.be+'\u2026</p>',loadBatch(e.batch));
  p.then(function(){CUR=HYMNS.filter(function(h){return String(h.id||h.be)===String(e.id||e.be);})[0];renderList(document.getElementById("q").value);renderHymn();})
   .catch(function(err){main.innerHTML='<p class="status">Gagal memuat data ende '+e.be+' ('+err.message+').</p>';});
}
function inkColor(){return getComputedStyle(document.documentElement).getPropertyValue("--ink").trim()||"#000";}

function renderHymn(){
  stopAudio();
  var h=current(), main=document.getElementById("main"), secs;
  try{secs=buildSecs(h);}catch(err){main.innerHTML='<p class="status">'+err.message+'</p>';return;}
  var mismatch=[];
  secs.forEach(function(s,si){s.report.forEach(function(r){if(r.notes!==r.syl) mismatch.push("Bagian "+(si+1)+", baris lirik "+(r.row+1)+": "+r.notes+" not, "+r.syl+" suku kata");});});
  main.innerHTML=
   '<header class="hymn-head"><div class="hymn-no">'+(h.id||h.be)+'</div><h1>'+h.title+'</h1>'+
   '<div class="meta"><span>BE <b>'+pad3(h.be)+(h.variant||'')+'</b></span>'+(h.bl?'<span>Logu <b>No. '+h.bl+'</b></span>':'<span>Logu <b>tidak dicantumkan</b></span>')+'<span><b>do = '+DO_NAME[h.key]+'</b></span><span>Birama <b>'+h.meter+'</b></span><span>Lagu: <b>'+h.credit+'</b></span></div></header>'+
   '<div class="toolbar"><div class="seg" role="group" aria-label="Tampilan notasi">'+
     '<button type="button" data-v="angka">Not angka</button><button type="button" data-v="balok">Not balok</button><button type="button" data-v="both">Keduanya</button></div>'+
     '<button type="button" class="btn primary" id="playBtn">'+PLAY_LABEL+'</button>'+
     (window.BE_STATIC?'<button type="button" class="btn" id="printBtn" title="Cetak atau simpan sebagai PDF (kertas F4)">Cetak Partitur</button>':'')+
     '<label class="tempo" for="bpm"><span class="tl">Tempo</span> <input id="bpm" type="range" min="50" max="130" value="'+bpm+'"><span id="bpmv">'+bpm+'</span></label></div>'+
   (vReady(h).length>1?'<div class="vbar"><span class="vl" id="vlab">Ayat</span><div class="vchips" role="group" aria-labelledby="vlab">'+vReady(h).map(function(i){return '<button type="button" data-k="'+i+'" title="Ayat '+(i+1)+'">'+(i+1)+'</button>';}).join("")+'</div>'+
     '<label class="vall"><input type="checkbox" id="vall"'+(VALL?' checked':'')+'> Putar sampai ayat terakhir</label></div>':'')+
   '<section class="block" id="angkaBlock"><h2>Not angka<span class="vtag"></span></h2><p class="vnote" hidden></p><div class="angka" id="angka"></div></section>'+
   '<section class="block" id="balokBlock"><h2>Not balok<span class="vtag"></span></h2><div class="staff" id="staff"></div></section>'+
   '<section class="block" id="endeBlock"><h2>Ende</h2><div class="verses">'+h.verses.map(function(v,i){return '<p class="verse" data-k="'+i+'"><span class="vn">'+(i+1)+'.</span><span>'+v.map(function(l){return '<span class="l">'+l+'</span>';}).join("")+'</span></p>';}).join("")+'</div><div class="credit">Lagu: '+h.credit+'</div></section>'+
   '<details class="panel edit" hidden><summary>Koreksi data notasi</summary><div class="panel-body">'+
     h.sections.map(function(s,i){return '<label for="n'+i+'">Bagian '+(i+1)+(s.rows.length>1?' (diulang)':'')+' — not</label><textarea id="n'+i+'" rows="4">'+s.notes+'</textarea>'+
       s.rows.map(function(r,j){return '<label for="r'+i+'_'+j+'">Bagian '+(i+1)+' — lirik baris '+(j+1)+'</label><textarea id="r'+i+'_'+j+'" rows="2">'+r+'</textarea>';}).join("");}).join("")+
     '<div class="row"><button type="button" class="btn primary" id="applyBtn">Terapkan</button><button type="button" class="btn" id="copyBtn">Salin data untuk dikirim</button><button type="button" class="btn" id="resetBtn">Kembalikan</button><span class="msg" id="msg" role="status"></span></div>'+
     '<p class="legend">Format: spasi = ketukan, <code>|</code> birama, <code>:|</code> ulang, <code>|]</code> akhir · <code>.</code> tahan · <code>1\'</code> oktaf atas, <code>5,</code> oktaf bawah, <code>#4</code> naik ½ · <code>5+6</code> dua not ½ ketukan · <code>( )</code> legato · <code>v</code> napas. Lirik: suku kata dipisah <code>-</code>, <code>_</code> = suku kata sebelumnya ditahan ke not berikut.</p>'+
   '</div></details>';

  var angka=document.getElementById("angka");
  secs.forEach(function(s,i){
    var lab=document.createElement("p");lab.className="sec-label";
    var ch=[];if(s.meter&&s.meter!==(i?(secs[i-1].meter||h.meter):h.meter))ch.push('birama '+s.meter);if((s.key||h.key)!==(i?(secs[i-1].key||h.key):h.key))ch.push('do = '+DO_NAME[s.key||h.key]);
    lab.innerHTML='<span class="tag">'+String.fromCharCode(65+i)+'</span>'+(ch.length?'<b>'+ch.join(' · ')+'</b> ':'')+(s.rows.length>1?'dinyanyikan dua kali — baris kedua lirik dicetak miring':'');
    if(secs.length>1) angka.appendChild(lab);
    renderAngka(s,angka,s.rows.length);
  });
  CURSECS=secs; CURH=h;
  if(VSEL.id!==(h.id||h.be)) VSEL={id:h.id||h.be,k:0};
  setVerse(VSEL.k,true);
  var pos=INDEX.map(function(x){return String(x.id||x.be);}).indexOf(String(h.id||h.be)), pv=INDEX[pos-1], nx=INDEX[pos+1];
  var pg=document.createElement("nav");pg.className="pager";pg.setAttribute("aria-label","Ende sebelum dan sesudahnya");
  pg.innerHTML=(pv?'<a class="prev" href="'+BP+'/be/'+(pv.id||pv.be)+'/" rel="prev"><span class="lbl">\u2190 Sebelumnya</span><span class="ttl"><b>'+(pv.id||pv.be)+'</b>'+pv.title+'</span></a>':'')+
    (nx?'<a class="next" href="'+BP+'/be/'+(nx.id||nx.be)+'/" rel="next"><span class="lbl">Berikutnya \u2192</span><span class="ttl"><b>'+(nx.id||nx.be)+'</b>'+nx.title+'</span></a>':'');
  main.appendChild(pg);
  applyView();

  document.querySelectorAll(".seg button").forEach(function(b){b.addEventListener("click",function(){view=b.dataset.v;try{localStorage.setItem("be-view",view);}catch(e){}applyView();});});
  document.getElementById("playBtn").addEventListener("click",function(){if(audio.playing)stopAudio();else playHymn(h,secs,bpm);});
  var pb=document.getElementById("printBtn"); if(pb) pb.addEventListener("click",function(){stopAudio();window.print();});
  document.querySelectorAll(".vchips button").forEach(function(b){b.addEventListener("click",function(){var was=audio.playing;if(was)stopAudio();setVerse(+b.dataset.k);if(was)playHymn(h,secs,bpm);});});
  var va=document.getElementById("vall"); if(va) va.addEventListener("change",function(){VALL=va.checked;});
  document.getElementById("bpm").addEventListener("input",function(e){bpm=+e.target.value;document.getElementById("bpmv").textContent=bpm;});
  document.getElementById("applyBtn").addEventListener("click",function(){
    var backup=JSON.stringify(h.sections), msg=document.getElementById("msg");
    h.sections.forEach(function(s,i){s.notes=document.getElementById("n"+i).value;s.rows=s.rows.map(function(r,j){return document.getElementById("r"+i+"_"+j).value;});});
    try{buildSecs(h);h.edited=true;renderHymn();var m=document.getElementById("msg");if(m){m.textContent="Diterapkan.";}document.querySelector("details.edit").open=true;}
    catch(err){h.sections=JSON.parse(backup);msg.className="msg bad";msg.textContent=err.message;}
  });
  document.getElementById("resetBtn").addEventListener("click",function(){h.sections=JSON.parse(ORIG[h.id||h.be]);renderHymn();});
  document.getElementById("copyBtn").addEventListener("click",function(){
    var txt=JSON.stringify({be:h.be,bl:h.bl,key:h.key,meter:h.meter,sections:h.sections},null,1), msg=document.getElementById("msg");
    var fallback=function(){var ta=document.getElementById("n0");ta.value=txt;ta.select();msg.textContent="Teks terpilih di kotak pertama — salin manual (Ctrl/Cmd+C).";};
    if(navigator.clipboard){navigator.clipboard.writeText(txt).then(function(){msg.className="msg";msg.textContent="Tersalin — tempel ke chat untuk saya perbarui.";},fallback);}else fallback();
  });
}
/* Ganti lirik di bawah not ke ayat k (lirik tidak ditumpuk; ayat 1 = baris asli). */
function vReady(h){ // ayat yang liriknya sudah terpasang ke not (ayat 1 selalu); ayat lain tidak diberi tombol
  var out=[0]; (h.vl||[]).forEach(function(v,i){if(i&&v&&v.r)out.push(i);}); return out;
}
function vlInfo(h){ // catatan dev: hasil pemasangan lirik ayat 2 dst
  if(!h.vl) return '';
  var ok=[],no=[],flex=[];
  h.vl.forEach(function(v,i){if(!i)return; if(v.r){ok.push(i+1); if(v.c>1)flex.push((i+1)+' (biaya '+v.c+')');} else no.push(i+1);});
  return '<li>Lirik ayat '+ (ok.length?ok.join(', ')+' dipasang otomatis ke not (pemecahan suku kata dari kamus ayat 1 semua lagu + aturan suku kata; belum dicek manual)':'2 dst belum dipasang')+
    (flex.length?'. Perlu dicek, banyak penyesuaian: ayat '+flex.join(', '):'')+(no.length&&ok.length?'. Belum bisa dipasang: ayat '+no.join(', '):'')+'.</li>';
}
function verseRows(h,k,si){
  if(!k) return h.sections[si].rows;
  var v=h.vl&&h.vl[k]; if(v&&v.r) return v.r[si];
  return h.sections[si].rows.map(function(){return "";});
}
function setVerse(k,quiet){
  var h=CURH, secs=CURSECS; if(!h||!secs) return;
  k=Math.max(0,Math.min(k,(h.verses.length||1)-1)); VSEL={id:h.id||h.be,k:k};
  var many=vReady(h).length>1, v=h.vl&&h.vl[k], miss=k>0&&!(v&&v.r);
  secs.forEach(function(sec,si){
    sec.rows=verseRows(h,k,si);
    noteEls(sec.lines).forEach(function(e){e.syl=null;});
    assignLyrics(sec.lines,sec.rows);
    noteEls(sec.lines).forEach(function(e){
      if(!e.node) return;
      e.node.querySelectorAll(".syl").forEach(function(sp,r){var sy=e.syl&&e.syl[r];sp.textContent=sy?(sy.t+(sy.cont?" -":"")):"";});
    });
  });
  document.querySelectorAll(".vtag").forEach(function(t){t.textContent=many?"Ayat "+(k+1):"";});
  document.querySelectorAll(".vchips button").forEach(function(b){b.setAttribute("aria-pressed",String(+b.dataset.k===k));});
  document.querySelectorAll(".verse[data-k]").forEach(function(p){p.classList.toggle("cur",many&&+p.dataset.k===k);});
  var vn=document.querySelector(".vnote");
  if(vn){vn.hidden=!miss; if(miss){vn.innerHTML='Lirik ayat '+(k+1)+' belum dipasang ke not. Teks ayatnya:<q></q>';vn.querySelector("q").textContent=h.verses[k].join(" ");}}
  if(view!=="angka") drawStaff(h,secs);
}
/* Cetak: dua versi, masing-masing mulai di halaman baru.
   1) not angka dengan lirik ayat 1 di bawah not, lalu ayat 2 dst sebagai teks
   2) not balok dengan lirik ayat 1 di bawah not, lalu ayat 2 dst sebagai teks */
function buildPrintView(){
  var h=current(), main=document.getElementById("main"); if(!h||!main) return;
  var old=document.getElementById("printView"); if(old) old.remove();
  var pv=document.createElement("div"); pv.id="printView"; main.appendChild(pv);
  var head=main.querySelector(".hymn-head"), c=document.querySelector('link[rel="canonical"]');
  var foot="Buku Ende "+(h.id||h.be)+" \u2013 "+h.title+" \u00b7 Buku Ende HKBP Digital"+(c?" \u00b7 "+c.href.replace(/^https?:\/\//,""):"");
  var rest=h.verses.slice(1), restH=rest.length?(rest.length>1?"Ayat 2\u2013"+h.verses.length:"Ayat 2"):"";
  function tail(part){
    if(rest.length){
      var keep=document.createElement("div");keep.className="pv-keep";part.appendChild(keep);
      var t=document.createElement("h2");t.textContent=restH;keep.appendChild(t);
      // ayat ditata per baris berisi dua ayat; tiap baris blok biasa sehingga bisa pindah halaman dengan rapi
      var row=null;
      rest.forEach(function(v,i){
        if(i%2===0){row=document.createElement("div");row.className="pv-verses";(i===0?keep:part).appendChild(row);}
        var p=document.createElement("p");p.className="verse";p.innerHTML='<span class="vn">'+(i+2)+'.</span><span>'+v.map(function(l){return '<span class="l">'+l+'</span>';}).join("")+'</span>';row.appendChild(p);
      });}
    var cr=document.createElement("div");cr.className="credit";cr.textContent="Lagu: "+h.credit;part.appendChild(cr);
    var f=document.createElement("p");f.className="print-foot";f.textContent=foot;part.appendChild(f);
  }
  function part(label){var d=document.createElement("section");d.className="pv-part";if(head)d.appendChild(head.cloneNode(true));
    var t=document.createElement("h2");t.textContent=label+(h.verses.length>1?" \u00b7 ayat 1":"");d.appendChild(t);pv.appendChild(d);return d;}
  var secs=buildSecs(h); // selalu lirik ayat 1
  var A=part("Not angka"), box=document.createElement("div"); box.className="pv-angka"; A.appendChild(box);
  var draws=[];
  secs.forEach(function(s,i){
    if(secs.length>1){var lab=document.createElement("p");lab.className="sec-label";lab.innerHTML='<span class="tag">'+String.fromCharCode(65+i)+'</span>'+(s.rows.length>1?'dinyanyikan dua kali \u2014 baris kedua lirik dicetak miring':'');box.appendChild(lab);}
    draws.push(renderAngka(s,box,s.rows.length));
  });
  tail(A);
  var B=part("Not balok"), st=document.createElement("div"); st.className="pv-staff"; B.appendChild(st);
  if(window.ABCJS) window.ABCJS.renderAbc(st,toABC(h,secs),{oneSvgPerLine:true,responsive:"resize",foregroundColor:"#000",staffwidth:740,paddingtop:4,paddingbottom:4,paddingleft:6,paddingright:6,wrap:{minSpacing:1.8,maxSpacing:2.6,preferredMeasuresPerLine:5}});
  tail(B);
  draws.forEach(function(d){try{d();}catch(e){}}); // busur legato diukur sekarang, sebelum dicetak
}
window.addEventListener("beforeprint",buildPrintView);
window.addEventListener("afterprint",function(){var pv=document.getElementById("printView"); if(pv) pv.remove();});
function drawStaff(h,secs){
  var el=document.getElementById("staff"); if(!el) return;
  if(!window.ABCJS){el.innerHTML='<p style="padding:10px;color:var(--ink-2)">Pustaka not balok gagal dimuat.</p>';return;}
  el.innerHTML="";
  window.ABCJS.renderAbc(el,toABC(h,secs),{add_classes:true,responsive:"resize",foregroundColor:inkColor(),staffwidth:740,paddingtop:4,paddingbottom:4,paddingleft:6,paddingright:6,wrap:{minSpacing:1.8,maxSpacing:2.6,preferredMeasuresPerLine:5}});
}
function applyView(){
  document.querySelectorAll(".seg button").forEach(function(b){b.setAttribute("aria-pressed",String(b.dataset.v===view));});
  var a=document.getElementById("angkaBlock"), b=document.getElementById("balokBlock");
  if(a) a.hidden=view==="balok"; if(b) b.hidden=view==="angka";
  if(view!=="angka"){var h=current();if(h)drawStaff(h,CURSECS&&CURH===h?CURSECS:buildSecs(h));}
}
var ORIG={};
/* ---------- mode gelap / terang ---------- */
(function(){
  var root=document.documentElement, btn=document.getElementById("themeBtn"), mq=window.matchMedia?window.matchMedia("(prefers-color-scheme: dark)"):null;
  function isDark(){var t=root.getAttribute("data-theme");return t?t==="dark":!!(mq&&mq.matches);}
  function label(){var d=isDark();btn.setAttribute("aria-label",d?"Ganti ke mode terang":"Ganti ke mode gelap");btn.title=d?"Mode terang":"Mode gelap";}
  var saved=null; try{saved=localStorage.getItem("be-theme");}catch(e){}
  if(saved==="dark"||saved==="light") root.setAttribute("data-theme",saved);
  else if(mq&&mq.matches) root.setAttribute("data-theme","dark");
  label();
  btn.addEventListener("click",function(){
    var next=isDark()?"light":"dark"; root.setAttribute("data-theme",next);
    try{localStorage.setItem("be-theme",next);}catch(e){}
    label();
  });
  if(mq&&mq.addEventListener) mq.addEventListener("change",function(){var sv=null;try{sv=localStorage.getItem("be-theme");}catch(e){} if(!sv){root.setAttribute("data-theme",mq.matches?"dark":"light");label();}});
})();
document.getElementById("q").addEventListener("input",function(e){renderList(e.target.value);});
document.getElementById("q").addEventListener("keydown",function(e){if(e.key==="Enter"){var a=document.querySelector("#list a");if(a)location.href=a.getAttribute("href");}});
window.addEventListener("hashchange",function(){var ix=document.querySelector(".index");ix.classList.remove("open");document.getElementById("listToggle").setAttribute("aria-expanded","false");show();window.scrollTo(0,0);});
document.getElementById("listToggle").addEventListener("click",function(){var ix=document.querySelector(".index"),o=ix.classList.toggle("open");this.setAttribute("aria-expanded",String(o));});
document.getElementById("q").addEventListener("input",function(e){var ix=document.querySelector(".index");if(e.target.value.trim()){ix.classList.add("open");document.getElementById("listToggle").setAttribute("aria-expanded","true");}});
function setTB(){var t=document.querySelector(".topbar");if(t)document.documentElement.style.setProperty("--tb",t.offsetHeight+"px");}
setTB();window.addEventListener("resize",setTB);try{document.fonts.ready.then(setTB);}catch(e){}
document.addEventListener("keydown",function(e){var tg=e.target&&e.target.tagName;if(tg==="INPUT"||tg==="TEXTAREA"||tg==="SELECT"||e.altKey||e.ctrlKey||e.metaKey)return;
  var sel=e.key==="ArrowLeft"?".pager a.prev":e.key==="ArrowRight"?".pager a.next":null;var a=sel&&document.querySelector(sel);if(a){location.href=a.getAttribute("href");}});
try{window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change",function(){applyView();});}catch(e){}
new MutationObserver(function(){applyView();}).observe(document.documentElement,{attributes:true,attributeFilter:["data-theme"]});
fetch(BP+"/data/index.json").then(function(r){return r.json();}).then(function(j){INDEX=j;
  var c=document.getElementById("count"); if(c) c.textContent=INDEX.filter(function(x){return !x.variant;}).length+" ende";
  renderList("");show();}).catch(function(){document.getElementById("main").innerHTML='<p class="status">Daftar ende gagal dimuat.</p>';});

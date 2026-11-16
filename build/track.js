(function(){
var dl=window.dataLayer=window.dataLayer||[];
function push(o){try{dl.push(o);}catch(e){}}
function buku(){return location.pathname.indexOf("/bn/")===0||/^#bn-/.test(location.hash)?"BN":"BE";}
function lagu(){
  var m=location.pathname.match(/^\/(be|bn)\/(\d+[a-z]?)-/)||location.hash.match(/^#(be|bn)-(\d+[a-z]?)$/);
  return m?{buku:m[1].toUpperCase(),nomor:m[2]}:null;}
function lihat(){var l=lagu(); if(l){push({event:"lihat_lagu",buku:l.buku,nomor:l.nomor,judul:document.title.split("|")[0].trim()});}}
function ctx(){var l=lagu()||{buku:buku(),nomor:""};return {buku:l.buku,nomor:l.nomor};}
// halaman lagu statis dan perpindahan lagu di halaman dasbor
if(/^\/(be|bn)\/\d/.test(location.pathname)||/^#b[ne]-/.test(location.hash)) lihat();
window.addEventListener("hashchange",lihat);
// klik (fase capture, supaya label tombol Putar dibaca sebelum berubah menjadi Berhenti)
document.addEventListener("click",function(e){
  var t=e.target.closest&&e.target.closest("button,a"); if(!t) return;
  if(t.id==="playBtn"){ if(!/berhenti|stop|henti/i.test(t.textContent)){var c=ctx();push({event:"putar_lagu",buku:c.buku,nomor:c.nomor});} }
  else if(t.id==="printBtn"){var c2=ctx();push({event:"cetak_partitur",buku:c2.buku,nomor:c2.nomor});}
  else if(t.id==="themeBtn"){push({event:"ganti_tema"});}
  else if(t.closest(".seg")&&t.getAttribute("data-v")){push({event:"ganti_tampilan",mode:t.getAttribute("data-v")});}
  else if(t.closest("nav.books")&&t.tagName==="A"){push({event:"pindah_buku",ke:t.textContent.trim()});}
},true);
// pencarian: kirim setelah berhenti mengetik 1 detik
var tm;
document.addEventListener("input",function(e){
  var q=e.target; if(!q||q.id!=="q") return;
  clearTimeout(tm);tm=setTimeout(function(){
    var k=q.value.trim().toLowerCase(); if(k.length<2) return;
    var n=document.querySelectorAll("#list li").length;
    push({event:"cari",kata_kunci:k.slice(0,60),jumlah_hasil:n,buku:buku()});},1000);
},true);
})();

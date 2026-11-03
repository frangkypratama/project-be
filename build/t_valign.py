import glob,re,collections,sys,copy
sys.path.insert(0,'.')
from build_site import parse_txt, validate
import verse_align as VA
H=[parse_txt(p) for p in sorted(glob.glob('work/be/*.txt')) if re.search(r'/\d+[a-z]?\.txt$',p)]
D=VA.build_dict(H)
# 1) uji ayat 1 (leave-one-out kamus)
ok=bad=fail=0; ex=[]
for h in H:
  if any('suku kata' in m for m in validate(h)) or not h['verses']: continue
  hd=VA.build_dict([h]); D2=copy.deepcopy(D)
  for k,c in hd.items():
    for l,n in c.items():
      D2[k][l]-=n
      if D2[k][l]<=0: del D2[k][l]
    if not D2[k]: del D2[k]
  r,_=VA.align_verse(h,h['verses'][0],D2)
  if not r: fail+=1; continue
  got=[x for sec in r['rows'] for x in sec]; want=[x for s in h['sections'] for x in s['rows']]
  norm=lambda rs:[re.sub(r'[^\w_]+',' ',x.lower()).split() for x in rs]
  def wmap(rs):
    out=[];pos=0
    for x in rs:
      for w in x.split():
        n=1 if w=='_' else len(w.split('-'))
        if w!='_': out.append((pos,n))
        pos+=n
    return out
  def lmap(rs):
    out=[];pos=0
    for x in rs:
      for w in x.split():
        if w=='_': out.append('H');continue
        for y in w.split('-'):
          out.append(pos); pos+=len(VA.norm(y))
    return out
  if lmap(got)==lmap(want): ok+=1
  else:
    bad+=1
    if len(ex)<8: ex.append((h['be'],r['cost'],got,want))
print('ayat1 leave-one-out: sama',ok,'beda',bad,'gagal',fail)
for e in ex[:0]:
  print(e[0],e[1]); 
  for g,w in zip(e[2],e[3]):
    if g!=w: print('  got ',g[:150]); print('  want',w[:150])
# 2) ayat 2+
st=collections.Counter(); costs=[]
for h in H:
  if any('suku kata' in m for m in validate(h)): st['lagu dgn ayat1 tak cocok']+=len(h['verses'])-1; continue
  for v in h['verses'][1:]:
    r,n=VA.align_verse(h,v,D)
    if not r: st['gagal']+=1
    elif r['cost']==0: st['pas (biaya 0)']+=1
    elif r['cost']<=1: st['biaya<=1']+=1
    else: st['biaya>1']+=1
print(st, sum(st.values()))

fails=collections.Counter(); exf=[]
for h in H:
  if any('suku kata' in m for m in validate(h)): continue
  T,ends=VA.template(h)
  for vi,v in enumerate(h['verses'][1:]):
    r,n=VA.align_verse(h,v,D)
    if r: continue
    words,ref,nn=VA.clean_verse(v)
    if words is None: fails['teks tak lengkap']+=1; continue
    lo=sum(min(len(p) for p,c in VA.options(w,D)) for w,_ in words); hi=sum(max(len(p) for p,c in VA.options(w,D)) for w,_ in words)
    k='ref' if ref else 'noref'
    if hi<len(T): fails[k+' kurang']+=1
    elif lo>len(T): fails[k+' lebih']+=1
    else: fails[k+' lain']+=1
    if len(exf)<400: exf.append((h['be'],vi+2,len(T),lo,hi,ref,' '.join(v)[:120]))
print(fails)
import random; random.seed(1)
for e in random.sample(exf,25): print(e)

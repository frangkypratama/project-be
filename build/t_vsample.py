import glob,re,collections,sys,random
sys.path.insert(0,'.')
from build_site import parse_txt, validate
import verse_align as VA
H=[parse_txt(p) for p in sorted(glob.glob('work/be/*.txt')) if re.search(r'/\d+[a-z]?\.txt$',p)]
D=VA.build_dict(H)
res=[]
for h in H:
  if any('suku kata' in m for m in validate(h)): continue
  for vi,v in enumerate(h['verses'][1:]):
    r,n=VA.align_verse(h,v,D)
    if r: res.append((h,vi+2,r))
random.seed(int(sys.argv[1]))
lo,hi=float(sys.argv[2]),float(sys.argv[3])
pick=[x for x in res if lo<=x[2]['cost']<=hi]
print(len(pick))
for h,vi,r in random.sample(pick,int(sys.argv[4])):
  print('== BE',h['be'],'ayat',vi,'biaya',r['cost'],r['notes'])
  for s,rs in zip(h['sections'],r['rows']):
    for a,b in zip(s['rows'],rs):
      A=a.split();B=b.split()
      # print slot by slot
      sa=[x for w in A for x in (['_'] if w=='_' else w.split('-'))]
      sb=[x for w in B for x in (['_'] if w=='_' else w.split('-'))]
      print('  1:',' '.join(f'{x:<5}' for x in sa)[:230]); print('  k:',' '.join(f'{x:<5}' for x in sb)[:230])

# usage: python3 pg.py PAGE [parts=2] [dpi=300] -> work/pg/pPPP_k.png
import sys, subprocess, os
from PIL import Image
import numpy as np
PDF=os.environ.get("BE_PDF","/mnt/user-data/attachments/cbd9054d-8209-50ff-8db3-998a463a8b89/a89ce26f-buku-ende-hkbp.pdf")
pg=int(sys.argv[1]); parts=int(sys.argv[2]) if len(sys.argv)>2 else 2; dpi=sys.argv[3] if len(sys.argv)>3 else "420"
d=os.path.join(os.path.dirname(os.path.abspath(__file__)),"work","pg"); os.makedirs(d,exist_ok=True)
import tempfile
base=os.path.join(tempfile.mkdtemp(),"raw%d"%pg)
subprocess.run(["pdftoppm","-r",dpi,"-f",str(pg),"-l",str(pg),"-gray","-singlefile",PDF,base],check=True)
im=Image.open(base+".pgm"); a=np.array(im)<140
ys=np.where(a.sum(1)>3)[0]; xs=np.where(a.sum(0)>3)[0]
y0,y1=max(0,ys.min()-10),min(im.size[1],ys.max()+10); x0,x1=max(0,xs.min()-10),min(im.size[0],xs.max()+10)
H=y1-y0; ov=40
for k in range(parts):
    t=y0+k*H//parts-(ov if k else 0); bt=y0+(k+1)*H//parts+(ov if k<parts-1 else 0)
    im.crop((x0,t,x1,bt)).save(os.path.join(d,"p%03d_%d.png"%(pg,k)))
os.remove(base+".pgm"); print("ok",pg,im.size,(x0,y0,x1,y1))

# usage: python3 zoom.py PAGE y0 y1 [x0 x1] (fractions of page) -> work/pg/zoom_PAGE_y0.png at 600dpi
import sys, subprocess, os
from PIL import Image
PDF=os.environ.get("BE_PDF","/mnt/user-data/attachments/cbd9054d-8209-50ff-8db3-998a463a8b89/a89ce26f-buku-ende-hkbp.pdf")
pg=int(sys.argv[1]); y0=float(sys.argv[2]); y1=float(sys.argv[3]); x0=float(sys.argv[4]) if len(sys.argv)>4 else 0.05; x1=float(sys.argv[5]) if len(sys.argv)>5 else 0.97
d=os.path.join(os.path.dirname(os.path.abspath(__file__)),"work","pg")
import tempfile
base=os.path.join(tempfile.mkdtemp(),"z%d"%pg)
if True:
    subprocess.run(["pdftoppm","-r","600","-f",str(pg),"-l",str(pg),"-gray","-singlefile",PDF,base],check=True)
im=Image.open(base+".pgm"); W,H=im.size
c=im.crop((int(x0*W),int(y0*H),int(x1*W),int(y1*H)))
if c.size[0]>2000: c=c.resize((2000,int(c.size[1]*2000/c.size[0])))
out=os.path.join(d,"zoom_%d_%s_%s.png"%(pg,sys.argv[2],sys.argv[3])); c.save(out); print(out,c.size)

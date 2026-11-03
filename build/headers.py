import sys, subprocess, glob, os
from PIL import Image, ImageDraw
PDF=os.environ.get("BE_PDF","/mnt/user-data/attachments/cbd9054d-8209-50ff-8db3-998a463a8b89/a89ce26f-buku-ende-hkbp.pdf")
a,b=int(sys.argv[1]),int(sys.argv[2])
import tempfile
OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),"work","hdr"); os.makedirs(OUT,exist_ok=True)
tmp=tempfile.mkdtemp()
subprocess.run(["pdftoppm","-r","110","-f",str(a),"-l",str(b),"-gray","-x","300","-y","0","-W","300","-H","110",PDF,os.path.join(tmp,"h")],check=True)
fs=sorted(glob.glob(os.path.join(tmp,'h-*.pgm')))
w,h=300,110; cols=5; rows=(len(fs)+cols-1)//cols
sheet=Image.new('L',(cols*(w+70),rows*h),255); d=ImageDraw.Draw(sheet)
for i,f in enumerate(fs):
    x=(i%cols)*(w+70); y=(i//cols)*h
    pg=int(os.path.basename(f).split('-')[1].split('.')[0])
    d.rectangle([x,y,x+66,y+h-1],fill=230); d.text((x+6,y+45),"p%d"%pg,fill=0)
    sheet.paste(Image.open(f),(x+70,y))
out=os.path.join(OUT,f'heads_{a}_{b}.png'); sheet.save(out); print(out, sheet.size)

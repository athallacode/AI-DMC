"""Generate synthetic wireframe references; never read lecturer documents."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parents[1] / 'docs' / 'wireframe'
BG, WHITE, INK, MUTED, BORDER, BLUE, SOFT = '#F5F5F7', '#FFFFFF', '#1D1D1F', '#86868B', '#E5E5EA', '#0B7AA0', '#E6F4FA'
FONT = Path('C:/Windows/Fonts/arial.ttf')

def generate(page, width):
    mobile = width == 375
    height = 960 if mobile else 900
    im = Image.new('RGB', (width, height), BG)
    d = ImageDraw.Draw(im)
    def text(x, y, value, size=15, color=INK):
        d.text((x, y), value, fill=color, font=ImageFont.truetype(str(FONT), size))
    def box(x, y, w, h, fill=WHITE, radius=12):
        d.rounded_rectangle((x, y, x+w, y+h), radius=radius, fill=fill, outline=BORDER, width=1)
    def button(x, y, label, primary=True, w=120):
        box(x,y,w,40,BLUE if primary else SOFT,20)
        text(x+16,y+11,label,14,WHITE if primary else BLUE)
    x = 16 if mobile else 100
    content = width-2*x
    if page == 'login':
        cardw = min(380, width-32)
        cx = (width-cardw)//2
        box(cx,150,cardw,440)
        text(cx+24,180,'AI-DMC',26,BLUE)
        text(cx+24,224,'Masuk',28)
        text(cx+24,272,'Username',13,MUTED)
        box(cx+24,294,cardw-48,40)
        text(cx+24,350,'Password',13,MUTED)
        box(cx+24,372,cardw-48,40)
        button(cx+24,444,'Masuk',w=cardw-48)
        text(cx+24,520,'CoE AIIS - Telkom University',13,MUTED)
    else:
        box(0,0,width,56,radius=0)
        text(x,17,'AI-DMC',16,BLUE)
        if not mobile:
            text(460,19,'Unggah     Verifikasi (2)     Arsip',15)
            text(width-240,19,'Dosen Demo',14,MUTED)
        title = {'upload':'Unggah','review':'Kotak Verifikasi','archive':'Arsip Saya'}[page]
        text(x,88,title,28)
        text(x,130,'Mode demo - hasil simulasi',13,MUTED)
        if page == 'upload':
            box(x,180,content,240)
            text(x+24,236,'Seret berkas ke sini',20)
            text(x+24,273,'PDF, DOCX, JPG, PNG - maks. 20 MB',13,MUTED)
            button(x+24,326,'Pilih berkas')
            text(x,458,'Unggahan terakhir',20)
            for i, name in enumerate(['SK Mengajar.pdf','Laporan Kegiatan.docx','Surat Tugas.pdf']):
                box(x,500+i*72,content,60)
                text(x+16,518+i*72,name,15)
                if not mobile:
                    text(width-300,518+i*72,'Menunggu verifikasi',13,MUTED)
            qwidth = content if mobile else 360
            qx = x if mobile else width-x-qwidth
            box(qx,745,qwidth,100)
            text(qx+16,763,'Antrean unggah',16)
            text(qx+16,795,'SK Mengajar.pdf - Membaca teks',13,MUTED)
            d.rectangle((qx+16,827,qx+qwidth-16,830),fill=BLUE)
        elif page == 'review':
            text(x,158,'2 dokumen menunggu',14,MUTED)
            box(x,200,content,650 if mobile else 530)
            px = x+16
            previeww = content-32 if mobile else 350
            box(px,216,previeww,150 if mobile else 430,BG)
            text(px+20,246,'Pratinjau dokumen',16,MUTED)
            rx = px if mobile else x+400
            ry = 390 if mobile else 228
            text(rx,ry,'SK Mengajar.pdf',16)
            text(rx,ry+35,'Menunggu verifikasi',13,MUTED)
            text(rx,ry+70,'Keyakinan AI 72%',15,BLUE)
            text(rx,ry+96,'AI kurang yakin, mohon dicek.',13,MUTED)
            text(rx,ry+136,'PND > SK mengajar',14)
            text(rx,ry+180,'Nomor dokumen',13,MUTED)
            text(rx,ry+204,'123/AKD/2026',15)
            text(rx,ry+244,'Tanggal terbit',13,MUTED)
            text(rx,ry+268,'15 Agustus 2026',15)
            text(rx,ry+308,'Dosen terkait: Dosen Demo',14)
            by = 794 if mobile else 650
            text(rx,by+12,'Tolak',14,'#E1252B')
            button(rx+55,by,'Koreksi',False,w=100)
            button(rx+166,by,'Setujui',w=110)
        else:
            box(x,180,content,126 if mobile else 64)
            text(x+16,200,'Semua   PND   PNL   PKM',14,BLUE)
            text(x+16 if mobile else x+500,258 if mobile else 200,'Status: Semua     Tahun: Semua',13,MUTED)
            start = 330 if mobile else 270
            if not mobile:
                text(x+16,start,'Nama dokumen',13,MUTED)
                text(x+460,start,'Jenis',13,MUTED)
                text(x+700,start,'Tanggal terbit',13,MUTED)
                text(x+900,start,'Status',13,MUTED)
                start += 34
            for i, name in enumerate(['SK Mengajar.pdf','Surat Tugas.pdf','Laporan Kegiatan.docx']):
                yy = start+i*(130 if mobile else 64)
                box(x,yy,content,114 if mobile else 56)
                text(x+16,yy+16,name,15)
                if mobile:
                    text(x+16,yy+48,'PND - 15 Agustus 2026',13,MUTED)
                    text(x+16,yy+78,'Terverifikasi',13,BLUE)
                else:
                    text(x+460,yy+18,'SK mengajar',14)
                    text(x+700,yy+18,'15 Agustus 2026',14)
                    text(x+900,yy+18,'Terverifikasi',13,BLUE)
        if mobile:
            box(0,height-64,width,64,radius=0)
            text(30,height-40,'Unggah',14,BLUE)
            text(145,height-40,'Verifikasi',14,BLUE)
            text(286,height-40,'Arsip',14,BLUE)
    OUT.mkdir(parents=True,exist_ok=True)
    im.save(OUT / f'{page}-{width}.png')

if __name__ == '__main__':
    for page in ('login','upload','review','archive'):
        for width in (375,1280):
            generate(page,width)
    print('Generated eight wireframe PNGs')

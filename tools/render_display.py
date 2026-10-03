"""Compose actual firmware/GFX host-rendered frames into a review artifact."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'docs/images';out.mkdir(exist_ok=True)
names=['normal','entry-start','entry-half','boost-half','fault']
labels=['NORMAL POWER','MAXIMUM / ENTRY TURN','HALF ENTRY / 180 DEGREES LEFT','BOOST CONTROL / 50%','FAULT / NIGHT OVERRIDE']
canvas=Image.new('RGB',(1040,640),'#e8eef2');draw=ImageDraw.Draw(canvas)
font=ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf',16)
for i,(name,label) in enumerate(zip(names,labels)):
    im=Image.open(ROOT/'build/screen-previews'/(name+'.ppm'))
    im.save(out/(name+'.png'))
    x=20+(i%3)*340;y=45+(i//3)*300
    canvas.paste(im,(x,y));draw.text((x,y-25),label,fill='#183447',font=font)
draw.text((20,605),'Actual firmware layout rendered with Adafruit GFX; LCD hardware, brightness and viewing angle remain untested.',fill='#4f6574',font=font)
canvas.save(out/'display-preview.png')

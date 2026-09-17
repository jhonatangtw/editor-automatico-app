#!/usr/bin/env python3
"""Recorte dos assets IA sobre fundo cinza "chapado" que na prática vem com gradiente.
Flood por borda (cutout.py da motion-vox) NÃO serve aqui: o fundo varia 158→134 do topo ao centro e o
objeto tem luminância no mesmo intervalo — a varredura de tolerância não tem platô.
Método: (1) ajusta uma superfície quadrática ao fundo pelas bordas; (2) resíduo + croma dão a semente;
(3) GrabCut separa nota (verde-cinza, texturizada) de sombra (neutra, lisa, mais escura que o ajuste);
(4) maior componente, fecha buracos, pluma de 0,8 px. Sombra é camada no AE, nunca pixel do asset."""
import sys, numpy as np, cv2
from pathlib import Path
from PIL import Image
D=Path(__file__).resolve().parent
def fit_bg(L, margin):
    """Quadratica ajustada pelas bordas. Sem matmul de matriz grande: o BLAS da Accelerate estoura
    (armadilha registrada no cutout.py da skill). Coordenadas normalizadas em [-1,1]."""
    h,w=L.shape; yy,xx=np.mgrid[0:h,0:w]; xn=(xx/(w-1)*2-1).astype(np.float64); yn=(yy/(h-1)*2-1).astype(np.float64)
    m=np.zeros((h,w),bool); m[:margin,:]=m[-margin:,:]=m[:,:margin]=m[:,-margin:]=True
    cols=[np.ones(m.sum()),xn[m],yn[m],xn[m]**2,yn[m]**2,xn[m]*yn[m]]
    X=np.stack(cols,1); coef,*_=np.linalg.lstsq(X,L[m].astype(np.float64),rcond=None)
    return coef[0]+coef[1]*xn+coef[2]*yn+coef[3]*xn**2+coef[4]*yn**2+coef[5]*xn*yn
def recortar(name, sat_fg=9, res_fg=10, iters=6):
    im=np.array(Image.open(D/"raw"/f"{name}.png").convert("RGB")); h,w,_=im.shape
    f=im.astype(np.float32); L=0.299*f[...,0]+0.587*f[...,1]+0.114*f[...,2]
    fit=fit_bg(L, int(min(h,w)*0.06)); res=L-fit
    sat=f.max(2)-f.min(2)
    mask=np.full((h,w),cv2.GC_PR_BGD,np.uint8)
    m=int(min(h,w)*0.05); mask[:m,:]=mask[-m:,:]=mask[:,:m]=mask[:,-m:]=cv2.GC_BGD
    mask[(np.abs(res)<3)&(sat<5)]=cv2.GC_BGD
    fg=((sat>sat_fg)|(res>res_fg)); fg=cv2.morphologyEx(fg.astype(np.uint8),cv2.MORPH_OPEN,np.ones((5,5),np.uint8))>0
    mask[fg]=cv2.GC_PR_FGD; mask[cv2.erode(fg.astype(np.uint8),np.ones((25,25),np.uint8))>0]=cv2.GC_FGD
    bgr=cv2.cvtColor(im,cv2.COLOR_RGB2BGR); bgm=np.zeros((1,65),np.float64); fgm=np.zeros((1,65),np.float64)
    cv2.grabCut(bgr,mask,None,bgm,fgm,iters,cv2.GC_INIT_WITH_MASK)
    obj=(mask==cv2.GC_FGD)|(mask==cv2.GC_PR_FGD)
    n,lab,st,_=cv2.connectedComponentsWithStats(obj.astype(np.uint8),8)
    if n>1: obj=lab==(1+np.argmax(st[1:,cv2.CC_STAT_AREA]))
    obj=cv2.morphologyEx(obj.astype(np.uint8),cv2.MORPH_CLOSE,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(15,15)))
    cnts,_=cv2.findContours(obj,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE); obj=np.zeros_like(obj); cv2.drawContours(obj,cnts,-1,1,-1)
    obj=cv2.erode(obj,np.ones((3,3),np.uint8))>0
    alpha=np.clip(cv2.GaussianBlur(obj.astype(np.float32),(0,0),0.8),0,1)
    ys,xs=np.where(alpha>0.02); y0,y1,x0,x1=ys.min(),ys.max()+1,xs.min(),xs.max()+1
    rgba=np.dstack([im,(alpha*255).astype(np.uint8)])[y0:y1,x0:x1]
    (D/"cutout").mkdir(exist_ok=True); Image.fromarray(rgba).save(D/"cutout"/f"{name}.png")
    bg=Image.new("RGBA",(x1-x0,y1-y0),(220,224,224,255)); bg.alpha_composite(Image.fromarray(rgba)); bg.convert("RGB").save(D/"cutout"/f"_prev_{name}.png")
    print(f"{name}: {w}x{h} -> {x1-x0}x{y1-y0}  area_obj={obj.mean()*100:.1f}%  fit_fundo={fit.min():.0f}..{fit.max():.0f}")
if __name__=="__main__":
    for n in sys.argv[1:] or ["maco","nota","maco2","nota2"]: recortar(n)

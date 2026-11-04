"""Confere o storyboard contra o TTS real: frase única e em ordem, tetos, proporção por tipo; reescreve a coluna de tempo."""
import json,re,subprocess,os
J=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B=json.load(open(f'{J}/ia/voz/blocos.json')); W=[];t0=0
for b in B:
    a=json.load(open(f"{J}/ia/voz/blocos/{b['id']}_alin.json"));w='';ws=0
    for c,s in zip(a['characters'],a['character_start_times_seconds']):
        if c.isspace():
            if w: W.append((t0+ws,w));w=''
        else:
            if not w: ws=s
            w+=c
    if w: W.append((t0+ws,w))
    t0+=float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',f"{J}/ia/voz/blocos/{b['id']}.mp3"],capture_output=True,text=True).stdout)
FIM=t0
n=lambda x: re.sub(r"[^a-z0-9$%]","",x.lower().replace("’","'"))
NW=[n(w) for _,w in W]
def find(fr):
    p=[n(x) for x in fr.split() if n(x)]
    return [i for i in range(len(NW)) if NW[i:i+len(p)]==p]
SB=f'{J}/_SAMURAI/storyboard.md'; L=open(SB).read().split('\n'); idx=[];rows=[]
for i,l in enumerate(L):
    if re.match(r"\| *\d+ *\|",l):
        c=[x.strip() for x in l.strip().strip('|').split('|')]
        ent=re.findall(r"“([^”]+)”",c[2])[0]; h=find(ent)
        if len(h)!=1: print('PROBLEMA frase',c[0],ent,h)
        idx.append(i); rows.append([c,W[h[0]][0] if h else 0])
tot={};assets=[]
for k,(c,t) in enumerate(rows):
    fim=rows[k+1][1] if k+1<len(rows) else FIM; d=fim-t; tp=c[3]
    if k and t<rows[k-1][1]: print('FORA DE ORDEM',c[0])
    tot[tp]=tot.get(tp,0)+d
    if tp=='D' and d>8 and 'respiro' not in c[4]: print('D > 8 s',c[0],round(d,1))
    teto={'B':6,'R':8,'T':8}.get(tp)
    if teto and d>teto+.05: print(f'teto {tp} #{c[0]} {d:.1f}s (expert volta {d-teto:.1f}s)')
    if tp in 'FM' and d>10: print('card longo',c[0],round(d,1))
    for a in re.findall(r"NOVO:(\w+)",c[5]): assets.append(a)
    c[1]=f"{int(t//60):02d}:{t%60:04.1f} · {d:.1f} s"; L[idx[k]]='| '+' | '.join(c)+' |'
open(SB,'w').write('\n'.join(L))
rep=[a for a in set(assets) if assets.count(a)>1]
print('assets novos',len(assets),'repetidos',rep or 'nenhum')
print({k:f"{v:.0f}s {100*v/FIM:.0f}%" for k,v in sorted(tot.items())},'total',round(FIM,1))

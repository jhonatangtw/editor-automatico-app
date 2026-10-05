#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Monta o corte no Premiere pelo Tools PRO (ExtendScript) e LÊ DE VOLTA cada passo.

Etapas (rode na ordem, uma por vez, conferindo a leitura):

  python3 montar.py diagnostico
  python3 montar.py importar   --video "/caminho/do/bruto.MOV"
  python3 montar.py corte      --plano decupagem/plano-corte.json [--nome "Reels — corte v1"] [--sem-opcionais]
  python3 montar.py takes      --takes decupagem/takes.json [--nome "Reels — takes por frase"]
  python3 montar.py subclipes  --takes decupagem/takes.json
  python3 montar.py cor        --sequencias "Reels — corte v1,Reels — takes por frase" [--look padrao|nenhum|"sat=110,contraste=10"]
  python3 montar.py ler
  python3 montar.py salvar

--so-gerar  imprime o ExtendScript em vez de rodar (para colar na ferramenta
            pr_extendscript do Tools PRO quando o Claude já a tiver carregada).

Regras que este script respeita (cada uma custou horas num job real):
- o bruto é só IMPORTADO, nunca alterado/movido/renomeado;
- a sequência nasce de createNewSequenceFromClips (herda vertical/fps/HDR do
  clipe e NÃO abre o diálogo "Nova sequência", que trava a ponte);
- posição sempre por objeto Time em ticks (string de segundos joga tudo no 0);
- overwriteClip, nunca insertClip (insert empurra o resto);
- lotes pequenos por chamada (o Premiere tem ~2 min por script);
- tudo termina lendo de volta: contagem, buracos, sobreposições, duração.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from comum import ler_json, sair  # noqa: E402

TICK = 254016000000

PRELUDIO = r'''
function achaItem(bin, nome){ for(var i=0;i<bin.children.numItems;i++){ var c=bin.children[i];
  if(c.type==2){ var r=achaItem(c,nome); if(r) return r; } else if(c.name==nome) return c; } return null; }
function achaBin(pai, nome){ for(var i=0;i<pai.children.numItems;i++){ if(pai.children[i].type==2 && pai.children[i].name==nome) return pai.children[i]; } return pai.createBin(nome); }
function achaSeq(nome){ for(var i=0;i<app.project.sequences.numSequences;i++){ if(app.project.sequences[i].name==nome) return app.project.sequences[i]; } return null; }
function t(seg){ var x=new Time(); x.ticks=String(Math.round(seg*TICK)); return x; }
function limpa(tr){ for(var i=tr.clips.numItems-1;i>=0;i--) tr.clips[i].remove(false,false); }
function resumo(q){ var v=q.videoTracks[0], a=q.audioTracks[0], st=q.getSettings(), gaps=0, ov=0;
  for(var i=1;i<v.clips.numItems;i++){ var d=Number(v.clips[i].start.ticks)-Number(v.clips[i-1].end.ticks); if(d>1000) gaps++; if(d<-1000) ov++; }
  var cs=""; try{ cs=st.workingColorSpace.name; }catch(e){}
  return {nome:q.name, largura:st.videoFrameWidth, altura:st.videoFrameHeight, espacoCor:cs, toneMap:String(st.autoToneMapEnabled),
          V1:v.clips.numItems, A1:a.clips.numItems, marcadores:q.markers.numMarkers, buracos:gaps, sobreposicoes:ov,
          duracao:Math.round(Number(q.end)/TICK*1000)/1000}; }
var TICK=254016000000;
'''


def js(corpo, **dados):
    """Monta o script: dados entram como JSON (sem concatenar texto do usuário no código)."""
    linhas = ["var %s=%s;" % (k, json.dumps(v, ensure_ascii=False)) for k, v in dados.items()]
    return PRELUDIO + "\n".join(linhas) + "\n" + corpo


def rodar(codigo, a, rotulo=""):
    if a.so_gerar:
        print("// ---- %s ----" % rotulo)
        print(codigo)
        return None
    from toolspro import extendscript
    ret, log = extendscript(codigo)
    if log:
        print("  log:", log)
    return ret


ACHA_FONTE = r'''
var item=achaItem(app.project.rootItem, FONTE);
if(!item) return {erro:"não achei '"+FONTE+"' no projeto. Rode a etapa importar antes."};
'''


def etapa_diagnostico(a):
    c = js(r'''var s=[]; for(var i=0;i<app.project.sequences.numSequences;i++){ s.push(resumo(app.project.sequences[i])); }
var b=[]; var R=app.project.rootItem; for(var i=0;i<R.children.numItems;i++){ b.push(R.children[i].name+(R.children[i].type==2?"/":"")); }
return {projeto:app.project.name, caminho:app.project.path, raiz:b, sequencias:s};''')
    return rodar(c, a, "diagnostico")


def etapa_importar(a):
    if not a.video or not os.path.isfile(a.video):
        sair("--video precisa apontar para o bruto (arquivo existente)")
    nome = os.path.basename(a.video)
    c = js(r'''var ja=achaItem(app.project.rootItem, NOME);
if(ja) return {ok:true, ja_existia:true, nome:ja.name, caminho:ja.getMediaPath()};
var bin=achaBin(app.project.rootItem, "BRUTO");
var r=app.project.importFiles([CAMINHO], true, bin, false);
var it=achaItem(app.project.rootItem, NOME);
if(!it) return {erro:"importFiles devolveu "+r+" mas o item não apareceu"};
var cs=""; try{ cs=it.getColorSpace().name; }catch(e){}
return {ok:true, nome:it.name, caminho:it.getMediaPath(), espacoCorMidia:cs};''', CAMINHO=os.path.abspath(a.video), NOME=nome)
    return rodar(c, a, "importar")


def _criar_seq(a, nome, fonte):
    c = js(ACHA_FONTE + r'''
if(achaSeq(NOME)) return {erro:"já existe uma sequência '"+NOME+"'. Use outro --nome (nunca sobrescrevo trabalho do aluno)."};
var bin=achaBin(app.project.rootItem, "SEQUENCIAS");
app.project.createNewSequenceFromClips(NOME, [item], bin);
var q=achaSeq(NOME); if(!q) return {erro:"a sequência não foi criada"};
limpa(q.videoTracks[0]); limpa(q.audioTracks[0]);
var st=q.getSettings(); var w=st.videoFrameWidth, h=st.videoFrameHeight;
return {ok:true, seq:resumo(q), largura:w, altura:h};''', NOME=nome, FONTE=fonte)
    return rodar(c, a, "criar sequência")


def etapa_corte(a):
    pl = ler_json(a.plano)
    fonte = a.fonte or pl["fonte"]
    pecas = [p for p in pl["pedacos"] if not (a.sem_opcionais and p.get("opcional"))]
    nome = a.nome or "Reels — corte v1"
    r = _criar_seq(a, nome, fonte)
    if r is not None:
        print(json.dumps(r, ensure_ascii=False, indent=1))
        if r.get("erro"):
            sys.exit(1)
    for k in range(0, len(pecas), a.lote):
        lote = [[p["entrada"], p["saida"], "%s" % p["nome"], p["texto"]] for p in pecas[k:k + a.lote]]
        c = js(ACHA_FONTE + r'''
var q=achaSeq(NOME); var v=q.videoTracks[0]; var out=[];
for(var k=0;k<P.length;k++){ var n=v.clips.numItems; var pos=new Time(); pos.ticks=n?String(v.clips[n-1].end.ticks):"0";
  item.setInPoint(P[k][0],4); item.setOutPoint(P[k][1],4); v.overwriteClip(item,pos);
  var c=v.clips[v.clips.numItems-1]; c.name=P[k][2];
  var m=q.markers.createMarker(c.start.seconds); m.name=P[k][2]; m.comments=P[k][3]+"  (bruto "+P[k][0]+"–"+P[k][1]+" s)";
  out.push(P[k][2]+" "+c.start.seconds.toFixed(2)+"–"+c.end.seconds.toFixed(2)); }
try{ item.clearInPoint(); item.clearOutPoint(); }catch(e){}
return {colocados:out, seq:resumo(q)};''', NOME=nome, FONTE=fonte, P=lote)
        r = rodar(c, a, "corte lote %d" % (k // a.lote + 1))
        if r is not None:
            print(json.dumps(r, ensure_ascii=False, indent=1))
    if not a.so_gerar:
        print("esperado: %d peças, %.2f s (o Premiere arredonda cada borda ao quadro)." % (len(pecas), sum(p["dur"] for p in pecas)))


def etapa_takes(a):
    tk = ler_json(a.takes)
    fonte = a.fonte or tk["fonte"]
    nome = a.nome or "Reels — takes por frase"
    lista = []
    for fr in tk["frases"]:
        for t in fr["takes"]:
            rec = " (RECOMENDADO)" if t["take"] == fr.get("recomendado") else ""
            lista.append([fr["frase"], t["take"], t["entrada"], t["saida"], "F%d.%d %s" % (fr["frase"], t["take"], fr["texto"][:28]),
                          "Frase %d · take %d%s — %s" % (fr["frase"], t["take"], rec, t["texto"]),
                          "bruto %.2f–%.2f s; %s" % (t["fala_ini"], t["fala_fim"], "; ".join(t.get("alertas") or []) or "sem alertas")])
    r = _criar_seq(a, nome, fonte)
    if r is not None:
        print(json.dumps(r, ensure_ascii=False, indent=1))
        if r.get("erro"):
            sys.exit(1)
    prev = 0
    for k in range(0, len(lista), a.lote):
        lote = lista[k:k + a.lote]
        c = js(ACHA_FONTE + r'''
var q=achaSeq(NOME); var v=q.videoTracks[0]; var out=[]; var prev=PREV;
for(var k=0;k<D.length;k++){ var d=D[k]; var n=v.clips.numItems; var fim=n?Number(v.clips[n-1].end.ticks):0;
  var folga=(n==0)?0:((d[0]!=prev)?1.0:0.25); var pos=new Time(); pos.ticks=String(Math.round(fim+folga*TICK));
  item.setInPoint(d[2],4); item.setOutPoint(d[3],4); v.overwriteClip(item,pos);
  var c=v.clips[v.clips.numItems-1]; c.name=d[4];
  var m=q.markers.createMarker(c.start.seconds); m.name=d[5]; m.comments=d[6]; try{ m.setColorByIndex(d[0]%2==0?6:0); }catch(e){}
  prev=d[0]; out.push(d[4]+" "+c.start.seconds.toFixed(2)); }
try{ item.clearInPoint(); item.clearOutPoint(); }catch(e){}
return {colocados:out, seq:resumo(q)};''', NOME=nome, FONTE=fonte, D=lote, PREV=prev)
        prev = lote[-1][0]
        r = rodar(c, a, "takes lote %d" % (k // a.lote + 1))
        if r is not None:
            print(json.dumps(r, ensure_ascii=False, indent=1))
    if not a.so_gerar:
        print("esperado: %d takes em %d frases." % (len(lista), len(tk["frases"])))


def etapa_subclipes(a):
    tk = ler_json(a.takes)
    fonte = a.fonte or tk["fonte"]
    D = [[fr["frase"], "%02d %s" % (fr["frase"], fr["texto"][:30]), t["take"], t["entrada"], t["saida"]]
         for fr in tk["frases"] for t in fr["takes"]]
    for k in range(0, len(D), a.lote):
        c = js(ACHA_FONTE + r'''
var mae=achaBin(app.project.rootItem, "TAKES POR FRASE"); var out=[];
for(var k=0;k<D.length;k++){ var d=D[k]; var b=achaBin(mae, d[1]);
  var s=item.createSubClip("F"+d[0]+"."+d[2]+" "+d[1].substr(3), t(d[3]), t(d[4]), 0, 1, 1);
  if(s){ s.moveBin(b); out.push(d[1]+" / F"+d[0]+"."+d[2]); } else out.push("FALHOU F"+d[0]+"."+d[2]); }
return out;''', FONTE=fonte, D=D[k:k + a.lote])
        r = rodar(c, a, "subclipes lote %d" % (k // a.lote + 1))
        if r is not None:
            print(json.dumps(r, ensure_ascii=False, indent=1))


LOOK_PADRAO = {"sat": 110, "contraste": 10, "realces": -20, "sombras": -10, "brancos": -10}
# nome do controle na seção "Correção básica" do Lumetri (PT-BR e EN) + índice de reserva medido no Premiere 26 PT-BR
LUMETRI = {"sat": (["Saturação", "Saturation"], 16), "contraste": (["Contraste", "Contrast"], 20),
           "realces": (["Realces", "Highlights"], 21), "sombras": (["Sombras", "Shadows"], 22),
           "brancos": (["Brancos", "Whites"], 23), "exposicao": (["Exposição", "Exposure"], 19),
           "temperatura": (["Temperatura", "Temperature"], 14), "pretos": (["Pretos", "Blacks"], 24)}


def etapa_cor(a):
    seqs = [s.strip() for s in a.sequencias.split(",") if s.strip()]
    if not seqs:
        sair("--sequencias com os nomes exatos (separe por vírgula)")
    # 1) espaço de trabalho Rec.709 + tone map automático das mídias HDR (o Reels sai em SDR)
    c = js(r'''var o=[]; for(var s=0;s<SEQS.length;s++){ var q=achaSeq(SEQS[s]); if(!q){ o.push({nome:SEQS[s], erro:"não achei"}); continue; }
  var st=q.getSettings(); var antes=""; try{ antes=st.workingColorSpace.name; }catch(e){}
  var alvo=null, l=st.workingColorSpaceList; for(var i=0;i<l.length;i++){ if(l[i].name=="Rec. 709") alvo=l[i]; }
  if(!alvo){ var nomes=[]; for(var i=0;i<l.length;i++) nomes.push(l[i].name); o.push({nome:q.name, erro:"Rec. 709 não está na lista", lista:nomes}); continue; }
  st.workingColorSpace=alvo; st.autoToneMapEnabled=true; q.setSettings(st);
  var st2=q.getSettings(); o.push({nome:q.name, antes:antes, depois:st2.workingColorSpace.name, toneMap:String(st2.autoToneMapEnabled), tamanho:st2.videoFrameWidth+"x"+st2.videoFrameHeight}); }
return o;''', SEQS=seqs)
    r = rodar(c, a, "espaço de cor")
    if r is not None:
        print(json.dumps(r, ensure_ascii=False, indent=1))
    if a.look == "nenhum":
        return
    V = dict(LOOK_PADRAO)
    if a.look not in ("padrao", ""):
        V = {k.strip(): float(v) for k, v in (x.split("=") for x in a.look.split(","))}
    alvo = {k: [LUMETRI[k][0], LUMETRI[k][1], v] for k, v in V.items() if k in LUMETRI}
    # 2) Lumetri clipe a clipe (camada de ajuste não dá pela API), em lotes, conferindo o valor gravado
    for nome in seqs:
        for ini in range(0, 400, a.lote):
            c = js(r'''app.enableQE(); var q=achaSeq(SEQ); if(!q) return {erro:"não achei "+SEQ};
app.project.openSequence(q.sequenceID); app.project.activeSequence=q;
var qs=qe.project.getActiveSequence(0); if(qs.name!=q.name) return {erro:"sequência ativa errada: "+qs.name};
var v=q.videoTracks[0]; if(INI>=v.clips.numItems) return {fim:true};
var qt=qs.getVideoTrackAt(0); var qi=[]; for(var z=0;z<qt.numItems;z++){ var it=qt.getItemAt(z); if(String(it.type)!="Empty") qi.push(it); }
if(qi.length!=v.clips.numItems) return {erro:"mapa QE x API diferente: "+qi.length+" vs "+v.clips.numItems};
var fx=null, nomeFx=""; var cand=["Cor de Lumetri","Lumetri Color"]; for(var i=0;i<cand.length && !fx;i++){ try{ fx=qe.project.getVideoEffectByName(cand[i]); if(fx) nomeFx=cand[i]; }catch(e){} }
function lum(c){ for(var i=0;i<c.components.numItems;i++){ var n=c.components[i].displayName; if(n.indexOf("Lumetri")>=0) return c.components[i]; } return null; }
function prop(L, nomes, reserva){ for(var j=0;j<Math.min(30,L.properties.numItems);j++){ for(var k=0;k<nomes.length;k++){ if(L.properties[j].displayName==nomes[k]) return L.properties[j]; } } return L.properties[reserva]; }
var out=[]; var hi=Math.min(INI+LOTE, v.clips.numItems);
for(var n=INI;n<hi;n++){ var c=v.clips[n]; var L=lum(c);
  if(!L){ qi[n].addVideoEffect(fx); L=lum(c); }
  if(!L){ out.push(n+": FALHOU (efeito '"+nomeFx+"' não entrou)"); continue; }
  var ok=true; for(var k in ALVO){ var p=prop(L, ALVO[k][0], ALVO[k][1]); p.setValue(ALVO[k][2], true); if(Math.abs(p.getValue()-ALVO[k][2])>0.01) ok=false; }
  out.push(n+": "+(ok?"ok":"DIFERENTE")); }
return {seq:q.name, clipes:out, total:v.clips.numItems};''', SEQ=nome, INI=ini, LOTE=a.lote, ALVO=alvo)
            r = rodar(c, a, "lumetri %s %d" % (nome, ini))
            if r is None:
                break
            if r.get("fim"):
                break
            print(json.dumps(r, ensure_ascii=False))
            if r.get("erro") or ini + a.lote >= r.get("total", 0):
                break


def etapa_ler(a):
    c = js(r'''var s=[]; for(var i=0;i<app.project.sequences.numSequences;i++) s.push(resumo(app.project.sequences[i])); return s;''')
    return rodar(c, a, "ler")


def etapa_salvar(a):
    return rodar(js("app.project.save(); return {salvo:app.project.path};"), a, "salvar")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("etapa", choices=["diagnostico", "importar", "corte", "takes", "subclipes", "cor", "ler", "salvar"])
    ap.add_argument("--video")
    ap.add_argument("--plano")
    ap.add_argument("--takes")
    ap.add_argument("--fonte", help="nome do item do bruto no projeto (padrão: o do plano)")
    ap.add_argument("--nome")
    ap.add_argument("--sem-opcionais", action="store_true")
    ap.add_argument("--sequencias", default="")
    ap.add_argument("--look", default="padrao")
    ap.add_argument("--lote", type=int, default=10)
    ap.add_argument("--so-gerar", action="store_true")
    a = ap.parse_args()
    f = globals()["etapa_" + a.etapa]
    if a.etapa == "corte" and not a.plano:
        sair("--plano decupagem/plano-corte.json")
    if a.etapa in ("takes", "subclipes") and not a.takes:
        sair("--takes decupagem/takes.json")
    r = f(a)
    if r is not None:
        print(json.dumps(r, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

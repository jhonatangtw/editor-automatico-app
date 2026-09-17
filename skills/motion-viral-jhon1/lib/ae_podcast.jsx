// ===== MOTION-VIRAL-JHON1 — biblioteca PODCAST / DOPAMINÉRGICA / EDITORIAL =====
// Carregada pelo lib/rodar.sh DEPOIS de ae_lib.jsx. Tudo aqui nasceu no AD04 (10/09/2026)
// e foi provado por quadro. Convenções: tempos em segundos ABSOLUTOS da comp principal;
// `m` = comp alvo; camadas nomeadas pelo trecho da copy (CARD_*, SPLIT_*, CUT_*, LET_*, ED_*).

// ---------- utilidades ----------
function item(n){ var it=findItem(n); if(!it) throw new Error("item nao importado: "+n); return it; }
function cover(it,w,h){ return Math.max(w/it.width, h/it.height)*100; }          // escala que cobre w×h
function topo(l){ l.moveToBeginning(); return l; }
function acima(l, ref){ l.moveBefore(ref); return l; }                              // acima do talking head, abaixo das legendas
function sfx(m, it, t, db, name){ var l=m.layers.add(it); l.name="sfx_"+name; l.startTime=t; l.property("ADBE Audio Group").property("ADBE Audio Levels").setValue([db,db]); l.moveToEnd(); return l; }
function limparPrefixo(m, prefixos){ for(var i=m.numLayers;i>=1;i--){ var n=m.layer(i).name; for(var k=0;k<prefixos.length;k++) if(n.indexOf(prefixos[k])==0){ m.layer(i).remove(); break; } } }
function semChaves(prop){ while(prop.numKeys>0) prop.removeKey(1); return prop; }

// ---------- talking head: segmentos em sequência ----------
// takes = [[FootageItem, quadrosDeDuracao], ...]; corta cada um em silêncio MEDIDO (quadros vêm do silencedetect)
function talkingHead(nome, takes, dur, fld){ var th=mkComp(nome, dur, fld); var t=0;
  for(var i=0;i<takes.length;i++){ var l=th.layers.add(takes[i][0]); l.name="take"+(i+1); l.startTime=t; l.inPoint=t; l.outPoint=t+F(takes[i][1]);
    var s=cover(takes[i][0],W,H); scl(l).setValue([s,s,100]); pos(l).setValue([W/2,H/2]); l.moveToEnd(); t+=F(takes[i][1]); }
  log(nome+": "+takes.length+" segmentos, fim em "+t.toFixed(3)+"s"); return th; }

// ---------- cartão de foto/vídeo sobre a locutora ----------
// Precomp w×h com matte arredondado (raio 40), borda branca 8 px, Ken Burns 100→kb, blur-in 6 f, sai em 5 f.
function cardPhoto(m, th, fld, name, it, x, y, w, h, t0, t1, kb){
  var c=mkComp("PC_CARD_"+name, t1-t0+0.5, fld); c.width=w; c.height=h;
  var v=c.layers.add(it); v.name="midia"; var s=cover(it,w,h); pos(v).setValue([w/2,h/2]); v.audioEnabled=false;
  key(scl(v),0,[s,s,100],"lin"); key(scl(v),t1-t0,[s*(kb||1.05),s*(kb||1.05),100],"lin");
  var mt=shapeLayer(c,"matte"); var g=grp(mt,"rr"); rect(g,w,h,40,0,0); fill(g,C.white); pos(mt).setValue([w/2,h/2]); v.setTrackMatte(mt,TrackMatteType.ALPHA);
  var bd=shapeLayer(c,"borda"); var g2=grp(bd,"b"); rect(g2,w-8,h-8,36,0,0); stroke(g2,C.white,8); pos(bd).setValue([w/2,h/2]); bd.moveToBeginning();
  var l=m.layers.add(c); l.name="CARD_"+name; l.startTime=t0; l.inPoint=t0; l.outPoint=t1; pos(l).setValue([x,y]); dropShadow(l,20,50,45,90); acima(l,th);
  var bp=blur(l,0).property("ADBE Gaussian Blur 2-0001");
  key(bp,t0,40,"ease"); key(bp,t0+F(6),0,"ease"); key(bp,t1-F(5),0,"ease"); key(bp,t1,30,"in");
  key(opa(l),t0,0,"ease"); key(opa(l),t0+F(3),100,"ease"); key(opa(l),t1-F(3),100,"ease"); key(opa(l),t1,0,"in");
  key(scl(l),t0,[94,94,100],"ease"); key(scl(l),t0+F(6),[100,100,100],"ease"); return l; }

// ---------- cutaway tela cheia (prova grande) ----------
function cutFull(m, th, name, it, t0, t1){ var l=m.layers.add(it); l.name="CUT_"+name; l.startTime=t0; l.inPoint=t0; l.outPoint=t1; var s=cover(it,W,H); pos(l).setValue([W/2,H/2]); l.audioEnabled=false; acima(l,th);
  key(scl(l),t0,[s*1.08,s*1.08,100],"ease"); key(scl(l),t0+F(5),[s,s,100],"ease"); key(scl(l),t1,[s*1.03,s*1.03,100],"lin");
  key(opa(l),t0,0,"lin"); key(opa(l),t0+F(2),100,"lin"); key(opa(l),t1-F(3),100,"lin"); key(opa(l),t1,0,"lin"); return l; }

// ---------- tela dividida: locutora em cima (0–942), mídia embaixo (942–1920) ----------
// bodySrc = footage do take; bodyStart = onde o take começa na MAIN. topoPos/topoScale vêm de reenquadrar() (medido).
function split(m, th, fld, name, bodySrc, bodyStart, it, t0, t1, baseY, topoPos, topoScale){
  var c=mkComp("PC_SPLIT_"+name, t1-t0+0.5, fld);
  var top=c.layers.add(bodySrc); top.name="rhonda_topo"; top.startTime=bodyStart-t0; var ts=topoScale||150; scl(top).setValue([ts,ts,100]); pos(top).setValue(topoPos||[W/2,917.5]); top.audioEnabled=false;
  var mt=solid(c,"matte_topo",C.white,W,942); pos(mt).setValue([W/2,471]); top.setTrackMatte(mt,TrackMatteType.ALPHA);
  var base=c.layers.add(it); base.name="base_"+name; var s=cover(it,W,978); scl(base).setValue([s,s,100]); pos(base).setValue([W/2,baseY||1422]); base.audioEnabled=false; base.moveToEnd();
  key(scl(base),0,[s,s,100],"lin"); key(scl(base),t1-t0,[s*1.04,s*1.04,100],"lin");
  var mb=solid(c,"matte_base",C.white,W,978); pos(mb).setValue([W/2,942+489]); base.setTrackMatte(mb,TrackMatteType.ALPHA);
  var seam=solid(c,"costura",C.white,W,6); pos(seam).setValue([W/2,942]); opa(seam).setValue(55); seam.moveToBeginning();
  var l=m.layers.add(c); l.name="SPLIT_"+name; l.startTime=t0; l.inPoint=t0; l.outPoint=t1; acima(l,th); return l; }

// ---------- reenquadrar o quadro superior do split ----------
// Entrada: medidas do YuNet no take 720×1280 — cxRosto (px), yTopoCabeca (px, topo dos fones/cabelo).
// Regra: escala ≥ 150 (720→1080); margem de 100 px no topo; centra o rosto em x. Devolve {pos, scale}.
function reenquadrar(cxRosto, yTopoCabeca, escala, margemTopo){ var s=(escala||150)/100; var mg=(margemTopo==null?100:margemTopo);
  var px=W/2-(cxRosto-360)*s; var py=mg-(yTopoCabeca-640)*s; return {pos:[Math.round(px),Math.round(py*2)/2], scale:(escala||150)}; }

// ---------- punch-in + tremor no talking head ----------
function punch(th, t, hold, up){ var u=up||107; key(scl(th),t-F(1),[100,100,100],"ease"); key(scl(th),t+F(3),[u,u,100],"ease"); key(scl(th),t+hold,[u,u,100],"ease"); key(scl(th),t+hold+F(6),[100,100,100],"ease"); }
function impacto(th, t){ key(pos(th),t+F(2),[W/2,H/2],"lin"); key(pos(th),t+F(3),[W/2+7,H/2-4],"lin"); key(pos(th),t+F(4),[W/2-5,H/2+3],"lin"); key(pos(th),t+F(5),[W/2,H/2],"lin"); }
// zoom alternado por frase (jump cut sem cortar o take): starts = inícios de frase em segundos
function zoomPorFrase(th, starts, alto){ var sp=semChaves(scl(th)); semChaves(pos(th)); pos(th).setValue([W/2,H/2]); key(sp,0,[100,100,100],"hold");
  for(var i=0;i<starts.length;i++){ var v=(i%2==0)?(alto||106):100; key(sp,starts[i],[v,v,100],"hold"); } }

// ---------- CTA sem texto novo: chevron pulsando ----------
function chevron(m, th, t0, t1){ var sh=shapeLayer(m,"cta_chevron"); var g=grp(sh,"v"); path(g,[[-70,-30],[0,30],[70,-30]],false); stroke(g,C.white,14,null,null,2); pos(sh).setValue([W/2,1560]); dropShadow(sh,4,8,60,90); sh.inPoint=t0; sh.outPoint=t1; acima(sh,th);
  key(opa(sh),t0,0,"ease"); key(opa(sh),t0+F(4),100,"ease"); key(opa(sh),t1-F(4),100,"ease"); key(opa(sh),t1,0,"ease");
  for(var t=t0;t<t1-0.3;t+=0.6){ key(pos(sh),t,[W/2,1548],"ease"); key(pos(sh),t+0.3,[W/2,1572],"ease"); } return sh; }

// ---------- legenda em caixa (verde) e premium ----------
// blocos = [[t0,t1,"texto",zona("hook"|"body"),acento(0|1)], ...]. Centra pela TINTA (sourceRectAtTime).
function legendasCaixa(comp, blocos, fonte, size, corCaixa, corAcento, yHook, yBody){
  var BOXH=103, PAD=44, R=36; var n=0;
  for(var i=0;i<blocos.length;i++){ var b=blocos[i]; var cy=(b[3]=="hook")?(yHook||858):(yBody||1225);
    var tx=text(comp,"leg_"+(i+1)+"_txt",b[2],fonte||"Nunito-ExtraBold",size||60,b[4]?corAcento:C.white,W/2,cy);
    var r=tx.sourceRectAtTime(b[0],false); pos(tx).setValue([W/2, cy-(r.top+r.height/2)]); dropShadow(tx,3,6,45,90);
    var bx=shapeLayer(comp,"leg_"+(i+1)+"_box"); var g=grp(bx,"box"); rect(g,Math.round(r.width)+PAD*2,BOXH,R,0,0); fill(g,corCaixa); pos(bx).setValue([W/2,cy]);
    tx.inPoint=b[0]; tx.outPoint=b[1]; bx.inPoint=b[0]; bx.outPoint=b[1]; bx.moveAfter(tx); n++; }
  log("legendas: "+n+" blocos"); return n; }
// pop no beat (Pinterest) em todas as legendas de uma comp
function legendasPop(comp){ var n=0; for(var i=1;i<=comp.numLayers;i++){ var l=comp.layer(i); if(!l.name.match(/^leg_\d+_box$/)) continue; var tx=findLayer(comp,l.name.replace("_box","_txt")); if(!tx) continue;
  var t0=l.inPoint; var pares=[l,tx]; for(var k=0;k<2;k++){ var p=scl(pares[k]); key(p,t0,[88,88,100],"ease"); key(p,t0+F(2),[106,106,100],"ease"); key(p,t0+F(4),[100,100,100],"ease"); } n++; } return n; }
// premium: pílula fosca preta + Montserrat Bold + acento Playfair dourada com glow. Restiliza uma DUPLICATA da caixa verde.
function legendasPremium(legVerde, fld){ var legP=legVerde.duplicate(); legP.name=legVerde.name+"_PREMIUM"; if(fld) legP.parentFolder=fld; var OURO=[0.906,0.765,0.416]; var n=0;
  for(var i=1;i<=legP.numLayers;i++){ var bx=legP.layer(i); if(!bx.name.match(/^leg_\d+_box$/)) continue; var tx=findLayer(legP,bx.name.replace("_box","_txt")); if(!tx) continue;
    var st=tx.property("ADBE Text Properties").property("ADBE Text Document"); var td=st.value; var fc=td.fillColor; var acento=(fc[0]>0.9&&fc[1]>0.7&&fc[2]<0.5)||(fc[1]>0.25&&fc[0]<0.2&&fc[2]<0.1);
    td.font=acento?"PlayfairDisplayItalic-BoldItalic":"Montserrat-Bold"; td.fontSize=acento?70:58; td.fillColor=acento?OURO:C.white; td.tracking=acento?0:-8; st.setValue(td);
    var r=tx.sourceRectAtTime(bx.inPoint,false); var cy=pos(bx).value[1]; pos(tx).setValue([W/2, cy-(r.top+r.height/2)]);
    var vg=bx.property("ADBE Root Vectors Group").property("box").property("ADBE Vectors Group"); var fp=vg.property("ADBE Vector Graphic - Fill"); fp.property("ADBE Vector Fill Color").setValue([0,0,0,1]); fp.property("ADBE Vector Fill Opacity").setValue(acento?52:42);
    vg.property("ADBE Vector Shape - Rect").property("ADBE Vector Rect Size").setValue([Math.round(r.width)+96,96]);
    var fx0=tx.property("ADBE Effect Parade"); for(var j=fx0.numProperties;j>=1;j--) fx0.property(j).remove(); dropShadow(tx,4,12,70,90);
    if(acento){ var gl=fx(tx,"ADBE Glo2"); gl.property("ADBE Glo2-0002").setValue(55); gl.property("ADBE Glo2-0003").setValue(36); gl.property("ADBE Glo2-0004").setValue(0.5); } n++; }
  log("legendas premium: "+n+" blocos"); return legP; }
// legenda cala sob cena de lettering (opacidade em hold na camada da comp principal)
function calar(legLayer, t0, t1){ var o=opa(legLayer); key(o,t0-F(1),100,"hold"); key(o,t0,0,"hold"); key(o,t1,100,"hold"); }

// ---------- fundo sob cartão: blur + escurecimento animados ----------
// Janelas vêm dos in/out REAIS das camadas CARD_*/OBJ_*; gaps < 0,3 s fundem (nada empilha). Um par de camadas por comp.
function fundoSobCartao(m, th, blurPx, escPct, rampaF){ var BL=blurPx||22, ESC=escPct||40, R=rampaF||8, GAP=0.30;
  for(var i=m.numLayers;i>=1;i--){ var n=m.layer(i).name; if(n=="TH_blur"||n=="TH_escurece") m.layer(i).remove(); }
  var iv=[]; for(var i=1;i<=m.numLayers;i++){ var l=m.layer(i); if(l.name.indexOf("CARD_")==0||l.name.indexOf("OBJ_")==0) iv.push([l.inPoint,l.outPoint]); }
  iv.sort(function(a,b){return a[0]-b[0];}); var jw=[]; for(var i=0;i<iv.length;i++){ if(jw.length&&iv[i][0]<=jw[jw.length-1][1]+GAP) jw[jw.length-1][1]=Math.max(jw[jw.length-1][1],iv[i][1]); else jw.push([iv[i][0],iv[i][1]]); }
  if(!jw.length){ log(m.name+": nenhuma janela de cartao"); return []; }
  var adj=m.layers.addSolid(C.black,"TH_blur",W,H,1,m.duration); adj.adjustmentLayer=true; var bp=blur(adj,0).property("ADBE Gaussian Blur 2-0001");
  var esc=m.layers.addSolid(C.black,"TH_escurece",W,H,1,m.duration); var op=opa(esc); bp.setValueAtTime(0,0); op.setValueAtTime(0,0);
  for(var k=0;k<jw.length;k++){ var t0=jw[k][0], t1=jw[k][1]; key(bp,t0,0,"ease"); key(bp,t0+F(R),BL,"ease"); key(bp,t1-F(R),BL,"ease"); key(bp,t1,0,"ease"); key(op,t0,0,"ease"); key(op,t0+F(R),ESC,"ease"); key(op,t1-F(R),ESC,"ease"); key(op,t1,0,"ease"); }
  esc.moveBefore(th); adj.moveBefore(esc); log(m.name+": fundo sob cartao em "+jw.length+" janelas"); return jw; }

// ---------- câmera 3D de um nó ----------
function camera3D(m){ var cam=m.layers.addCamera("CAM_3D",[W/2,H/2]); cam.autoOrient=AutoOrientType.NO_AUTO_ORIENT; cam.moveToBeginning(); return {layer:cam, z0:pos(cam).value[2]}; }
// dolly + deriva só dentro da cena; fora dela a câmera fica parada (hold no valor padrão)
function camMove(cam, t0, t1, from, to){ var p=pos(cam.layer), Z0=cam.z0; key(p,t0-F(1),[W/2,H/2,Z0],"hold"); key(p,t0,[W/2+from[0],H/2+from[1],Z0+from[2]],"ease"); key(p,t1,[W/2+to[0],H/2+to[1],Z0+to[2]],"ease"); key(p,t1+F(1),[W/2,H/2,Z0],"hold"); }

// ---------- gramática DOPAMINÉRGICA (Pinterest 15551561209923797) ----------
var DOPA={ creme:[0.953,0.937,0.902], preto:[0.04,0.04,0.045], tinta:[0.07,0.07,0.08], verm:[0.88,0.13,0.16], cinza:[0.80,0.78,0.73], fonte:"Montserrat-ExtraBold" };
// cena: fundo 2D + linha-caminho (creme) + vinheta; cala a legenda; swish
function cenaDopa(m, legLayer, swishItem, nome, t0, t1, escuro){ var bg=topo(solid(m,"LET_"+nome+"_bg",escuro?DOPA.preto:DOPA.creme)); bg.inPoint=t0; bg.outPoint=t1;
  if(!escuro){ var ln=topo(shapeLayer(m,"LET_"+nome+"_linha")); var g=grp(ln,"ln"); curvePath(g,[[-700,900],[-120,-200],[700,-1100]],[[0,0],[-260,260],[-200,120]],[[260,-260],[200,-120],[0,0]]); stroke(g,DOPA.cinza,22,null,null,2); pos(ln).setValue([W/2,H/2]); ln.inPoint=t0; ln.outPoint=t1; var te=trim(g).property("ADBE Vector Trim End"); key(te,t0,0,"ease"); key(te,t1,100,"lin"); }
  var adj=topo(solid(m,"LET_"+nome+"_adj",C.black)); adj.adjustmentLayer=true; vignette(adj,escuro?40:18); adj.inPoint=t0; adj.outPoint=t1;
  if(legLayer) calar(legLayer,t0,t1); if(swishItem) sfx(m,swishItem,t0-F(2),-12,nome+"_in"); return bg; }
// palavra 3D com pop 0→112→100 em 5 f; vermelho no preto ganha glow
function palavraDopa(m, popItem, nome, str, t, tFim, x, y, z, size, col, rotZ){ var l=topo(text(m,"LET_"+nome,str,DOPA.fonte,size,col,x,y)); l.threeDLayer=true; pos(l).setValue([x,y,z]); l.inPoint=t; l.outPoint=tFim;
  key(scl(l),t,[0,0,0],"ease"); key(scl(l),t+F(3),[112,112,112],"ease"); key(scl(l),t+F(5),[100,100,100],"ease"); if(rotZ){ key(rot(l),t,rotZ*2,"ease"); key(rot(l),t+F(5),rotZ,"ease"); }
  if(col==DOPA.verm && z<0){ var gl=fx(l,"ADBE Glo2"); gl.property("ADBE Glo2-0002").setValue(60); gl.property("ADBE Glo2-0003").setValue(40); gl.property("ADBE Glo2-0004").setValue(0.35); }
  if(popItem) sfx(m,popItem,t,-13,nome); return l; }
// objeto 3D (cutout) pousando na palavra: 0→115→100 em 7 f com rotação −18→rotZ
function objeto3D(m, nome, it, t, tFim, x, y, z, alt, rotZ){ var l=topo(m.layers.add(it)); l.name="OBJ3D_"+nome; l.threeDLayer=true; var s=(alt/it.height)*100; pos(l).setValue([x,y,z]); l.inPoint=t; l.outPoint=tFim; dropShadow(l,22,50,40,90);
  key(scl(l),t,[0,0,0],"ease"); key(scl(l),t+F(4),[s*1.15,s*1.15,s*1.15],"ease"); key(scl(l),t+F(7),[s,s,s],"ease"); key(rot(l),t,(rotZ||0)-18,"ease"); key(rot(l),t+F(7),rotZ||0,"ease"); return l; }

// ---------- gramática EDITORIAL (Pinterest 1142999580450072622) ----------
var ED={ creme:[0.929,0.914,0.882], preto:[0.045,0.045,0.05], carvao:[0.165,0.165,0.18], serifa:"Fraunces-Regular", chave:"Montserrat-Bold", fantasma:"Anton-Regular" };
// reveal letra a letra com blur (animador de texto, seletor por caracteres)
function revelaLetras(l, t0, dur){ var an=l.property("ADBE Text Properties").property("ADBE Text Animators").addProperty("ADBE Text Animator"); an.name="reveal";
  var props=an.property("ADBE Text Animator Properties"); props.addProperty("ADBE Text Opacity").setValue(0); props.addProperty("ADBE Text Blur").setValue([34,34]);
  var sel=an.property("ADBE Text Selectors").addProperty("ADBE Text Selector"); sel.property("ADBE Text Range Advanced").property("ADBE Text Range Type2").setValue(1);
  var st=sel.property("ADBE Text Percent Start"); st.setValueAtTime(t0,0); st.setValueAtTime(t0+(dur||0.42),100); ease(st,1,"out"); ease(st,2,"ease"); sel.property("ADBE Text Percent End").setValue(100); }
// cena editorial: papel + bandas de luz de janela (creme) + fantasma Anton 3D + vinheta/ruído; cala legenda; swish baixo
function cenaEditorial(m, legLayer, swishItem, nome, t0, t1, escuro, fantasma){
  var bg=topo(solid(m,"ED_"+nome+"_bg",escuro?ED.preto:ED.creme)); bg.inPoint=t0; bg.outPoint=t1;
  if(!escuro){ var lz=topo(shapeLayer(m,"ED_"+nome+"_luz")); var g=grp(lz,"bandas"); for(var k=-2;k<=2;k++) rect(g,2600,230,0,0,k*560); fill(g,C.black,14); rot(lz).setValue(35); blur(lz,70); lz.inPoint=t0; lz.outPoint=t1; key(pos(lz),t0,[W/2-40,H/2],"lin"); key(pos(lz),t1,[W/2+50,H/2-30],"lin"); }
  var gh=topo(text(m,"ED_"+nome+"_fantasma",fantasma,ED.fantasma,560,escuro?C.white:ED.carvao,W/2,H/2+190)); gh.threeDLayer=true; pos(gh).setValue([W/2,H/2+190,420]); opa(gh).setValue(escuro?7:6); gh.inPoint=t0; gh.outPoint=t1; key(scl(gh),t0,[92,92,92],"lin"); key(scl(gh),t1,[100,100,100],"lin");
  var adj=topo(solid(m,"ED_"+nome+"_adj",C.black)); adj.adjustmentLayer=true; vignette(adj,escuro?38:16); noise(adj,3); adj.inPoint=t0; adj.outPoint=t1;
  if(legLayer) calar(legLayer,t0,t1); if(swishItem) sfx(m,swishItem,t0-F(2),-16,nome+"_in"); return bg; }
function serifa(m, nome, str, t, t1, x, y, z, size, col){ var l=topo(text(m,"ED_"+nome,str,ED.serifa,size,col,x,y)); l.threeDLayer=true; pos(l).setValue([x,y,z]); l.inPoint=t; l.outPoint=t1; opa(l).setValueAtTime(t,0); opa(l).setValueAtTime(t+F(6),100); return l; }
function chave(m, popItem, nome, str, t, t1, x, y, z, size, col){ var l=topo(text(m,"ED_"+nome,str,ED.chave,size,col,x,y,null,-10)); l.threeDLayer=true; pos(l).setValue([x,y,z]); l.inPoint=t; l.outPoint=t1; revelaLetras(l,t,0.42); if(popItem) sfx(m,popItem,t,-18,nome); return l; }
function objetoCanto(m, nome, it, t, t1, x, y, z, alt, rotZ){ var l=topo(m.layers.add(it)); l.name="ED_obj_"+nome; l.threeDLayer=true; var s=(alt/it.height)*100; pos(l).setValue([x,y,z]); scl(l).setValue([s,s,s]); rot(l).setValue(rotZ||0); l.inPoint=t; l.outPoint=t1; dropShadow(l,26,60,45,120);
  key(pos(l),t,[x+(x<W/2?-140:140),y+60,z],"ease"); key(pos(l),t+F(10),[x,y,z],"ease"); return l; }
// ornamentos — UM grupo por camada (dois grupos com stroke+fill invalidam a referência; ver armadilhas)
function estrelas(m, nome, t, t1, x, y, col){ var sh=topo(shapeLayer(m,"ED_"+nome+"_estrelas")); for(var k=-1;k<=1;k++){ var g=grp(sh,"e"+k); path(g,[[k*44,-13],[k*44+4,-4],[k*44+13,0],[k*44+4,4],[k*44,13],[k*44-4,4],[k*44-13,0],[k*44-4,-4]],true); fill(g,col); } pos(sh).setValue([x,y]); sh.inPoint=t; sh.outPoint=t1; popIn(sh,t,6); return sh; }
function pino(m, nome, t, t1, x, y, col){ var ln=topo(shapeLayer(m,"ED_"+nome+"_pino_linha")); var g=grp(ln,"linha"); path(g,[[0,0],[0,300]],false); stroke(g,col,2); var te=trim(g).property("ADBE Vector Trim End"); te.setValueAtTime(t,0); te.setValueAtTime(t+0.5,100); pos(ln).setValue([x,y]); ln.inPoint=t; ln.outPoint=t1;
  var st=topo(shapeLayer(m,"ED_"+nome+"_pino_estrela")); var g2=grp(st,"estrela"); path(g2,[[0,-16],[4,-4],[16,0],[4,4],[0,16],[-4,4],[-16,0],[-4,-4]],true); fill(g2,col); pos(st).setValue([x,y]); st.inPoint=t; st.outPoint=t1; popIn(st,t,5); return ln; }
function circulo(m, nome, t, t1, x, y, r, col){ var sh=topo(shapeLayer(m,"ED_"+nome+"_circ")); var g=grp(sh,"c"); ellipse(g,r*2,r*2,0,0); stroke(g,col,2); pos(sh).setValue([x,y]); sh.inPoint=t; sh.outPoint=t1; var te=trim(g).property("ADBE Vector Trim End"); te.setValueAtTime(t,0); te.setValueAtTime(t+0.8,100); return sh; }
// transições da referência: flash branco (saída) e anel desfocado (entrada) — um de cada por vídeo
function flashBranco(m, t){ var f=topo(solid(m,"ED_flash",C.white)); f.inPoint=t-F(4); f.outPoint=t+F(3); opa(f).setValueAtTime(t-F(4),0); opa(f).setValueAtTime(t,100); opa(f).setValueAtTime(t+F(3),0); return f; }
function anel(m, t){ var sh=topo(shapeLayer(m,"ED_anel")); var g=grp(sh,"r"); ellipse(g,400,400,0,0); stroke(g,C.white,90); pos(sh).setValue([W/2,H/2]); blur(sh,45); sh.inPoint=t-F(6); sh.outPoint=t+F(6); key(scl(sh),t-F(6),[20,20,100],"out"); key(scl(sh),t+F(6),[620,620,100],"in"); opa(sh).setValueAtTime(t+F(3),100); opa(sh).setValueAtTime(t+F(6),0); return sh; }

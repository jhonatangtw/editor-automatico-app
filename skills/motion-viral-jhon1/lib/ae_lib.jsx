// ===== MOTION-VIRAL-JHON1 — biblioteca ExtendScript (After Effects 26) =====
// NAO editar as constantes aqui: DEMANDA, SAIDA, COMP_MAIN, FPS e LOGNAME sao injetados
// pelo lib/rodar.sh antes deste arquivo. Rodar sempre por ele.
if (typeof DEMANDA  == "undefined") var DEMANDA  = "~";
if (typeof SAIDA    == "undefined") var SAIDA    = "/tmp";
if (typeof COMP_MAIN== "undefined") var COMP_MAIN= "MAIN";
if (typeof FPS      == "undefined") var FPS      = 24;
if (typeof LOGNAME  == "undefined") var LOGNAME  = "run";
function F(n){ return n/FPS; }
var W = 1080, H = 1920;
var C = {
  paper:[0.862,0.878,0.878], paperCool:[0.812,0.831,0.839], ink:[0.149,0.157,0.169],
  grey:[0.42,0.43,0.44], amber:[0.89,0.643,0.29], red:[0.788,0.282,0.314], white:[1,1,1], black:[0,0,0]
};
var FONT = { lead:"InterItalic-LightItalic", leadReg:"Inter-Italic", sansBold:"Inter-Bold", sansBoldIt:"InterItalic-BoldItalic",
             key:"PlayfairDisplayItalic-BoldItalic", keyLight:"PlayfairDisplay-Italic", num:"Fraunces-9ptBlack", serifBold:"Fraunces-Bold" };
var LOG = [];
function log(s){ LOG.push(String(s)); }
function flush(name){ var f=new File(SAIDA+"/"+name); f.open("w"); f.encoding="UTF-8"; f.lineFeed="Unix"; f.write(LOG.join("\n")); f.close(); LOG=[]; }
function folder(name){ for(var i=1;i<=app.project.numItems;i++){ var it=app.project.item(i); if(it instanceof FolderItem && it.name==name) return it; } var f=app.project.items.addFolder(name); return f; }
function findItem(name){ for(var i=1;i<=app.project.numItems;i++){ if(app.project.item(i).name==name) return app.project.item(i); } return null; }
function importFile(path, fld, newName){ var f=new File(path); if(!f.exists) throw new Error("nao existe: "+path); var nm=newName||f.name; var ex=findItem(nm); if(ex && ex instanceof FootageItem){ if(fld) ex.parentFolder=fld; return ex; } var io=new ImportOptions(f); var it=app.project.importFile(io); if(fld) it.parentFolder=fld; if(newName) it.name=newName; return it; }
function mkComp(name, dur, fld){ var old=findItem(name); if(old) old.remove(); var c=app.project.items.addComp(name, W, H, 1, dur, FPS); if(fld) c.parentFolder=fld; return c; }
function solid(comp, name, col, w, h){ var l=comp.layers.addSolid(col, name, w||W, h||H, 1, comp.duration); return l; }
function P(layer, nm){ return layer.property("ADBE Transform Group").property(nm); }
function pos(l){ return P(l,"ADBE Position"); } function scl(l){ return P(l,"ADBE Scale"); } function opa(l){ return P(l,"ADBE Opacity"); } function rot(l){ return P(l,"ADBE Rotate Z"); } function anc(l){ return P(l,"ADBE Anchor Point"); }
function setv(prop, v){ prop.setValue(v); }
// keyframe com ease: e = "ease" | "in" | "out" | "lin"
function key(prop, t, v, e){ prop.setValueAtTime(t, v); var k=prop.nearestKeyIndex(t); ease(prop, k, e||"ease"); return k; }
function easeArr(prop, inf){ var n=1; var vt=prop.propertyValueType; if(vt==PropertyValueType.TwoD||vt==PropertyValueType.ThreeD) n=(vt==PropertyValueType.TwoD?2:3); if(vt==PropertyValueType.TwoD_SPATIAL||vt==PropertyValueType.ThreeD_SPATIAL) n=1; var a=[]; for(var i=0;i<n;i++) a.push(new KeyframeEase(0, inf)); return a; }
function ease(prop, k, e){ try{ var inInf=33, outInf=33; if(e=="in"){ inInf=5; outInf=85; } if(e=="out"){ inInf=85; outInf=5; } if(e=="lin"){ prop.setInterpolationTypeAtKey(k, KeyframeInterpolationType.LINEAR, KeyframeInterpolationType.LINEAR); return; } if(e=="hold"){ prop.setInterpolationTypeAtKey(k, KeyframeInterpolationType.HOLD, KeyframeInterpolationType.HOLD); return; } prop.setInterpolationTypeAtKey(k, KeyframeInterpolationType.BEZIER, KeyframeInterpolationType.BEZIER); prop.setTemporalEaseAtKey(k, easeArr(prop,inInf), easeArr(prop,outInf)); }catch(err){ log("ease falhou "+prop.name+" k"+k+": "+err); } }
// texto
function text(comp, name, str, font, size, col, x, y, just, tracking){ var l=comp.layers.addText(str); l.name=name; var st=l.property("ADBE Text Properties").property("ADBE Text Document"); var td=st.value; td.resetCharStyle(); td.font=font; td.fontSize=size; td.fillColor=col; td.applyFill=true; td.applyStroke=false; td.tracking=(tracking||0); td.justification=(just=="left"?ParagraphJustification.LEFT_JUSTIFY:(just=="right"?ParagraphJustification.RIGHT_JUSTIFY:ParagraphJustification.CENTER_JUSTIFY)); st.setValue(td); pos(l).setValue([x,y]); return l; }
function textLeading(l, lead){ var st=l.property("ADBE Text Properties").property("ADBE Text Document"); var td=st.value; td.autoLeading=false; td.leading=lead; st.setValue(td); }
// shapes
function shapeLayer(comp, name){ var l=comp.layers.addShape(); l.name=name; return l; }
function grp(l, name){ var g=l.property("ADBE Root Vectors Group").addProperty("ADBE Vector Group"); g.name=name; return g; }
function rect(g, w, h, r, x, y){ var s=g.property("ADBE Vectors Group").addProperty("ADBE Vector Shape - Rect"); s.property("ADBE Vector Rect Size").setValue([w,h]); s.property("ADBE Vector Rect Roundness").setValue(r||0); s.property("ADBE Vector Rect Position").setValue([x||0,y||0]); return s; }
function ellipse(g, w, h, x, y){ var s=g.property("ADBE Vectors Group").addProperty("ADBE Vector Shape - Ellipse"); s.property("ADBE Vector Ellipse Size").setValue([w,h]); s.property("ADBE Vector Ellipse Position").setValue([x||0,y||0]); return s; }
function path(g, verts, closed, inT, outT){ var s=g.property("ADBE Vectors Group").addProperty("ADBE Vector Shape - Group"); var sh=new Shape(); sh.vertices=verts; sh.closed=!!closed; if(inT){ sh.inTangents=inT; sh.outTangents=outT; } s.property("ADBE Vector Shape").setValue(sh); return s; }
function fill(g, col, op){ var f=g.property("ADBE Vectors Group").addProperty("ADBE Vector Graphic - Fill"); f.property("ADBE Vector Fill Color").setValue([col[0],col[1],col[2],1]); if(op!=null) f.property("ADBE Vector Fill Opacity").setValue(op); return f; }
function stroke(g, col, wdt, dash, gap, cap){ var s=g.property("ADBE Vectors Group").addProperty("ADBE Vector Graphic - Stroke"); s.property("ADBE Vector Stroke Color").setValue([col[0],col[1],col[2],1]); s.property("ADBE Vector Stroke Width").setValue(wdt); s.property("ADBE Vector Stroke Line Cap").setValue(cap||2); if(dash){ var d=s.property("ADBE Vector Stroke Dashes"); d.addProperty("ADBE Vector Stroke Dash 1"); d.addProperty("ADBE Vector Stroke Gap 1"); d.property("ADBE Vector Stroke Dash 1").setValue(dash); d.property("ADBE Vector Stroke Gap 1").setValue(gap||dash); } return s; }
function trim(g){ var t=g.property("ADBE Vectors Group").addProperty("ADBE Vector Filter - Trim"); return t; }
function noFillLast(g){ return g; }
// efeitos
function fx(l, match){ return l.property("ADBE Effect Parade").addProperty(match); }
function dropShadow(l, dist, soft, op, dir){ var e=fx(l,"ADBE Drop Shadow"); e.property("ADBE Drop Shadow-0001").setValue([0,0,0,1]); e.property("ADBE Drop Shadow-0002").setValue(op*2.55); e.property("ADBE Drop Shadow-0003").setValue(dir==null?180:dir); e.property("ADBE Drop Shadow-0004").setValue(dist); e.property("ADBE Drop Shadow-0005").setValue(soft); return e; }
function blur(l, amt){ var e=fx(l,"ADBE Gaussian Blur 2"); e.property("ADBE Gaussian Blur 2-0001").setValue(amt); try{ e.property("ADBE Gaussian Blur 2-0003").setValue(true);}catch(x){} return e; }
function vignette(l, amt){ try{ var e=fx(l,"CC Vignette"); e.property(1).setValue(amt); return e; }catch(x){ log("CC Vignette falhou "+x); } }
function noise(l, amt){ try{ var e=fx(l,"ADBE Noise"); e.property("ADBE Noise-0001").setValue(amt); e.property("ADBE Noise-0002").setValue(false); return e; }catch(x){ log("Noise falhou "+x); } }
function tint(l, amt){ var e=fx(l,"ADBE Tint"); e.property("ADBE Tint-0003").setValue(amt); return e; }
// helpers de composicao
function paperBG(comp, name){ var bg=solid(comp, name||"BG_papel", C.paper); return bg; }
function grade(comp){ var a=solid(comp, "ADJ_acabamento", C.black); a.adjustmentLayer=true; vignette(a, 22); noise(a, 2.5); return a; }
function ghost(comp, str, size, y, font){ var fs=Math.min(size,1200); var t=text(comp, "ghost_"+str, str, font||FONT.num, fs, C.ink, W/2, y||H/2+size*0.35); var k=size/fs*100; scl(t).setValue([k,k,100]); opa(t).setValue(6); return t; }
function nullLayer(comp, name){ var n=comp.layers.addNull(comp.duration); n.name=name; pos(n).setValue([W/2,H/2]); return n; }
function parentTo(l, n){ l.parent=n; }
// entrada bloco: fade + subida (frames)
function blockIn(l, t, frames, rise){ var fr=frames||8; var p=pos(l).value; opa(l).setValueAtTime(t,0); opa(l).setValueAtTime(t+F(fr),100); ease(opa(l),1,"ease"); ease(opa(l),2,"ease"); key(pos(l), t, [p[0],p[1]+(rise==null?14:rise)], "ease"); key(pos(l), t+F(fr), p, "ease"); }
function fadeOut(l, t, frames){ var fr=frames||6; var cur=opa(l).valueAtTime(t,false); opa(l).setValueAtTime(t,cur); opa(l).setValueAtTime(t+F(fr),0); }
function popIn(l, t, frames){ var fr=frames||7; var s=scl(l).value; key(scl(l), t, [0,0,100], "ease"); key(scl(l), t+F(fr*0.7), [s[0]*1.05,s[1]*1.05,100], "ease"); key(scl(l), t+F(fr), s, "ease"); opa(l).setValueAtTime(t,0); opa(l).setValueAtTime(t+F(2),100); }
function settle(l, t, frames, from){ var s=scl(l).value; var f=from||104; key(scl(l), t, [s[0]*f/100, s[1]*f/100, 100], "ease"); key(scl(l), t+F(frames||10), s, "ease"); }
function report(comp){ log("== "+comp.name+" "+comp.width+"x"+comp.height+" "+comp.frameRate+"fps dur="+comp.duration.toFixed(3)+" layers="+comp.numLayers); for(var i=1;i<=comp.numLayers;i++){ var l=comp.layer(i); log("  "+i+" | "+l.name+" | in="+l.inPoint.toFixed(3)+" out="+l.outPoint.toFixed(3)+" start="+l.startTime.toFixed(3)+(l.parent?(" | parent="+l.parent.name):"")+(l.enabled?"":" | DESLIGADA")); } }
function frame(comp, t, name){ var d=new Folder(SAIDA+"/frames"); if(!d.exists) d.create(); var f=new File(SAIDA+"/frames/"+name+".png"); try{ comp.saveFrameToPng(t, f); log("frame "+name+" @"+t.toFixed(3)+" -> "+f.fsName); }catch(e){ log("frame falhou "+name+": "+e); } }
function main(){ var m=findItem(COMP_MAIN); if(!m) throw new Error("comp principal '"+COMP_MAIN+"' nao existe — crie no setup ou passe MVJ_COMP"); return m; }
function placeInMain(comp, start, inT, outT){ var m=main(); for(var i=m.numLayers;i>=1;i--){ if(m.layer(i).name==comp.name) m.layer(i).remove(); } var l=m.layers.add(comp); l.name=comp.name; l.startTime=start; if(inT!=null) l.inPoint=inT; if(outT!=null) l.outPoint=outT; l.moveToBeginning(); return l; }
function precomp(name, dur){ return mkComp(name, dur, folder("05_Precomps")); }
function cardLayer(comp, cardCompName, name, x, y, s){ var l=comp.layers.add(findItem(cardCompName)); l.name=name; pos(l).setValue([x,y]); scl(l).setValue([s,s,100]); dropShadow(l, 26, 70, 32, 90); return l; }
function pill(comp, name, str, w, x, y, font, size){ var sh=shapeLayer(comp, name); var g=grp(sh,"pill"); rect(g, w, 84, 42, 0, 0); fill(g, C.white); pos(sh).setValue([x,y]); dropShadow(sh, 10, 30, 28, 90); var t=text(comp, name+"_txt", str, font||FONT.sansBoldIt, size||40, C.ink, x, y+14); t.parent=sh; t.moveBefore(sh); return sh; }
function slideOut(l, t, frames, dx, dy){ var p=pos(l).valueAtTime(t,false); key(pos(l), t, p, "ease"); key(pos(l), t+F(frames), [p[0]+dx, p[1]+dy], "in"); }
function dashedCircle(comp, name, w, h, x, y, col, wdt){ var sh=shapeLayer(comp, name); var g=grp(sh,"circ"); ellipse(g, w, h, 0, 0); stroke(g, col||C.ink, wdt||7, 30, 24, 2); var tr=trim(g); pos(sh).setValue([x,y]); return {layer:sh, trim:tr}; }
function drawIn(trimGroup, t0, t1){ var e=trimGroup.property("ADBE Vector Trim End"); e.setValueAtTime(t0,0); e.setValueAtTime(t1,100); e.setInterpolationTypeAtKey(1,KeyframeInterpolationType.LINEAR,KeyframeInterpolationType.LINEAR); e.setInterpolationTypeAtKey(2,KeyframeInterpolationType.LINEAR,KeyframeInterpolationType.LINEAR); }
function line(comp, name, x0, y0, x1, y1, col, wdt){ var sh=shapeLayer(comp,name); var g=grp(sh,"ln"); path(g,[[x0-W/2,y0-H/2],[x1-W/2,y1-H/2]],false); stroke(g,col,wdt,null,null,2); var t=trim(g); pos(sh).setValue([W/2,H/2]); return {layer:sh, trim:t}; }
function arrowHead(comp, name, x, y, ang, col, size){ var sh=shapeLayer(comp,name); var g=grp(sh,"ah"); var s=size||34; path(g,[[-s,-s*0.6],[0,0],[-s,s*0.6]],true); fill(g,col); pos(sh).setValue([x,y]); rot(sh).setValue(ang); return sh; }
function bar(comp, name, x, y, w, h, col, op){ var sh=shapeLayer(comp,name); var g=grp(sh,"bar"); rect(g,w,h,h/2,0,0); fill(g,col,op==null?100:op); pos(sh).setValue([x,y]); return sh; }
function ticks(comp, name, x, y, w, n, col){ var sh=shapeLayer(comp,name); var g=grp(sh,"ticks"); for(var i=0;i<=n;i++){ var tx=-w/2+i*(w/n); rect(g,3,26,0,tx,0); } fill(g,col,60); pos(sh).setValue([x,y]); return sh; }
function plate(comp, name, w, h, x, y){ var sh=shapeLayer(comp,name); var g=grp(sh,"pl"); rect(g,w,h,28,0,0); fill(g,C.paper); pos(sh).setValue([x,y]); dropShadow(sh,22,60,45,90); return sh; }
function shadowText(l){ dropShadow(l,7,16,60,90); }
function sweep(name, t0, t1, from, to, rotD){ var m=main(); for(var i=m.numLayers;i>=1;i--){ if(m.layer(i).name==name) m.layer(i).remove(); } var sh=shapeLayer(m,name); var g=grp(sh,"sil"); rect(g,760,1400,120,0,0); fill(g,C.ink); rot(sh).setValue(rotD==null?22:rotD); opa(sh).setValue(92); blur(sh,110); sh.inPoint=t0-F(1); sh.outPoint=t1+F(1); key(pos(sh),t0,from,"ease"); key(pos(sh),t1,to,"ease"); sh.moveToBeginning(); return sh; }
function curvePath(g, pts, inT, outT){ return path(g, pts, false, inT, outT); }
function findLayer(comp, name){ for(var i=1;i<=comp.numLayers;i++) if(comp.layer(i).name==name) return comp.layer(i); return null; }
function ramp(l, p0, c0, p1, c1, shape, scatter){ var e=fx(l,"ADBE Ramp"); e.property("ADBE Ramp-0001").setValue(p0); e.property("ADBE Ramp-0002").setValue([c0[0],c0[1],c0[2],1]); e.property("ADBE Ramp-0003").setValue(p1); e.property("ADBE Ramp-0004").setValue([c1[0],c1[1],c1[2],1]); e.property("ADBE Ramp-0005").setValue(shape||2); e.property("ADBE Ramp-0006").setValue(scatter||0); return e; }
// Fundo premium: ramp radial no solid + luz de estúdio em screen + silhueta de profundidade desfocada, todos presos ao BG
function premiumBG(comp, lightPos, depthPos, depthRot, drift){ var bg=findLayer(comp,"BG_papel"); if(!bg){ log("sem BG_papel em "+comp.name); return; }
  var old=bg.property("ADBE Effect Parade"); for(var i=old.numProperties;i>=1;i--) if(old.property(i).matchName=="ADBE Ramp") old.property(i).remove();
  ramp(bg,[540,760],[0.925,0.937,0.937],[540,2150],[0.745,0.776,0.788],2,6);
  var oldL=findLayer(comp,"BG_luz"); if(oldL) oldL.remove(); var oldD=findLayer(comp,"BG_profundidade"); if(oldD) oldD.remove();
  var lz=solid(comp,"BG_luz",C.white); ramp(lz,lightPos,[1,1,1],[lightPos[0]+760,lightPos[1]+760],[0,0,0],2,4); lz.blendingMode=BlendingMode.SCREEN; opa(lz).setValue(42); lz.parent=bg; pos(lz).setValue([W/2,H/2]); lz.moveAfter(bg);
  var dp=shapeLayer(comp,"BG_profundidade"); var g=grp(dp,"sil"); rect(g,900,1500,140,0,0); fill(g,C.ink); rot(dp).setValue(depthRot); opa(dp).setValue(9); blur(dp,150); dp.parent=bg;
  key(pos(dp),0,depthPos,"lin"); key(pos(dp),comp.duration,[depthPos[0]+(drift||40),depthPos[1]-(drift||40)*0.6],"lin"); dp.moveAfter(lz);
  // herda a janela de opacidade do BG (wipe) via inPoint
  if(opa(bg).numKeys>0){ var t=opa(bg).keyTime(opa(bg).numKeys); lz.inPoint=t; dp.inPoint=t; }
  var adj=findLayer(comp,"ADJ_acabamento"); if(adj){ var fp=adj.property("ADBE Effect Parade"); for(var j=1;j<=fp.numProperties;j++){ var e=fp.property(j); if(e.matchName=="CC Vignette") e.property(1).setValue(34); if(e.matchName=="ADBE Noise") e.property("ADBE Noise-0001").setValue(3.5); } }
  log("premiumBG em "+comp.name); }

// ---- encerramento: o rodar.sh chama isto sozinho, nao precisa no roteiro da cena
function fim(){ flush(LOGNAME+".log"); }

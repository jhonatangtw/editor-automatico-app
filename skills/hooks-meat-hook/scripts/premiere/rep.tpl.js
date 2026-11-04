var TARGET="__NAME__", AD="__AD__", HKN=__HK__, CUT=__CUT__, SCALE=__SCALE__;
var p=app.project, root=p.rootItem, TPS=254016000000, log=[];
function child(parent,name){ for(var k=0;k<parent.children.numItems;k++) if(parent.children[k].name==name) return parent.children[k]; return null; }
function seqBy(name){ for(var i=0;i<p.sequences.numSequences;i++) if(p.sequences[i].name==name) return p.sequences[i]; return null; }
function T(sec){ var t=new Time(); t.seconds=sec; return t; }
function setScale(clip,v){ for(var ci=0;ci<clip.components.numItems;ci++) if(clip.components[ci].matchName=="AE.ADBE Motion") clip.components[ci].properties[1].setValue(v,true); }
var src=seqBy("NNN_XX AD01 HK1"), old=seqBy(TARGET);
var S0=Number(src.videoTracks[0].clips[0].end.ticks)/TPS;
var hooksBin=child(child(root,"HOOKS"),"_DECUPADOS"), bodyBin=child(root,"BODY"), seqBin=child(child(root,"01. Sequences"),"ADS HOOKS");
var hk=null, pre="HK"+(HKN<10?"0":"")+HKN+"_"; for(var i=0;i<hooksBin.children.numItems;i++) if(hooksBin.children[i].name.indexOf(pre)==0) hk=hooksBin.children[i];
var body=null; for(var i=0;i<bodyBin.children.numItems;i++) if(bodyBin.children[i].name.indexOf(AD+"_")==0) body=bodyBin.children[i];
// clone
var before={}; for(var i=0;i<p.sequences.numSequences;i++) before[p.sequences[i].sequenceID]=1;
src.clone(); var nw=null; for(var i=0;i<p.sequences.numSequences;i++) if(!before[p.sequences[i].sequenceID]) nw=p.sequences[i];
nw.name=TARGET+"__novo";
var vt=nw.videoTracks[0], at=nw.audioTracks[0];
// tira hook+body antigos de V1/A1
for(var c=vt.clips.numItems-1;c>=0;c--) vt.clips[c].remove(false,false);
for(var c=at.clips.numItems-1;c>=0;c--) at.clips[c].remove(false,false);
// hook novo
vt.overwriteClip(hk,T(0)); at.overwriteClip(hk,T(0));
var hc=vt.clips[0]; setScale(hc,100);
var S1=Number(hc.end.ticks)/TPS, delta=S1-S0;
// move elementos amarrados a emenda (V2, A3, A4) — de tras pra frente se delta>0
function shift(track){ var n=track.clips.numItems, idx=[]; for(var c=0;c<n;c++) idx.push(c); if(delta>0) idx.reverse();
  for(var k=0;k<idx.length;k++){ var cl=track.clips[idx[k]]; cl.move(T(delta)); } }
if(Math.abs(delta)>0.0005){ shift(nw.videoTracks[1]); shift(nw.audioTracks[2]); shift(nw.audioTracks[3]); }
// musica A2: termina 0.834 s depois da emenda
var mus=nw.audioTracks[1].clips[0], musEnd0=Number(mus.end.ticks)/TPS; mus.end=T(musEnd0+delta);
// body
if(CUT>0) body.setInPoint(T(CUT),4);
var bt=new Time(); bt.ticks=String(hc.end.ticks);
vt.overwriteClip(body,bt); at.overwriteClip(body,bt);
if(CUT>0) body.clearInPoint();
var bc=vt.clips[vt.clips.numItems-1]; setScale(bc,SCALE);
// marcadores
while(nw.markers.numMarkers>0) nw.markers.deleteMarker(nw.markers.getFirstMarker());
var parts=hk.name.replace(".mp4","").split("_");
var m=nw.markers.createMarker(0); m.name="HK"+HKN+" · "+parts[1]+"_"+parts[2]; m.end=S1;
var m2=nw.markers.createMarker(S1); m2.name="BODY "+AD+(CUT>0?" (hook original removido)":" (empilhamento: hook original mantido)");
// troca: apaga a antiga, renomeia a nova, move pro bin
p.deleteSequence(old);
nw.name=TARGET;
for(var i=0;i<root.children.numItems;i++){ var it=root.children[i]; if(it.type==1 && it.name==TARGET){ it.moveBin(seqBin); break; } }
// leitura de volta
function list(tr,k){ var o=[]; for(var c=0;c<tr.clips.numItems;c++) o.push(k+":"+tr.clips[c].name.substr(0,14)+" "+tr.clips[c].start.seconds.toFixed(3)+"-"+tr.clips[c].end.seconds.toFixed(3)); return o.join(" | "); }
var out=[TARGET+" emenda="+S1.toFixed(3)+" delta="+delta.toFixed(3)];
out.push(list(nw.videoTracks[0],"V1")); out.push(list(nw.videoTracks[1],"V2"));
for(var a=0;a<4;a++) out.push(list(nw.audioTracks[a],"A"+(a+1)));
var tx=[]; try{ for(var x=0;x<nw.audioTracks[1].transitions.numItems;x++){ var t=nw.audioTracks[1].transitions[x]; tx.push(t.start.seconds.toFixed(2)+"-"+t.end.seconds.toFixed(2)); } }catch(e){}
out.push("A2 transicoes: "+tx.join(", "));
p.save();
return out.join("\n");

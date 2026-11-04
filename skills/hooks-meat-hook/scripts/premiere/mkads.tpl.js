var AD="__AD__", CUT=__CUT__, SCALE=__SCALE__;
var p=app.project,root=p.rootItem;
function child(parent,name,create){ for(var k=0;k<parent.children.numItems;k++) if(parent.children[k].name==name) return parent.children[k]; return create?parent.createBin(name):null; }
var hooksBin=child(child(root,"HOOKS"),"_DECUPADOS"), bodyBin=child(root,"BODY");
var seqBin=child(child(root,"01. Sequences",true),"ADS HOOKS",true);
var body=null; for(var i=0;i<bodyBin.children.numItems;i++) if(bodyBin.children[i].name.indexOf(AD+"_")==0) body=bodyBin.children[i];
var src=null; for(var i=0;i<p.sequences.numSequences;i++) if(p.sequences[i].name=="9x16") src=p.sequences[i];
var ESTR={"Demonstracao":"4 · Demonstração","Confissao":"5 · Confissão pessoal","Omissao":"3 · Qualificação + omissão","Comando":"1 · Comando"};
var TPS=254016000000, out=[];
var hk=[]; for(var i=0;i<hooksBin.children.numItems;i++) if(hooksBin.children[i].name.match(/^HK\d\d_.*\.mp4$/)) hk.push(hooksBin.children[i]);
hk.sort(function(a,b){return a.name<b.name?-1:(a.name>b.name?1:0);});
function setScale(clip,v){ for(var ci=0;ci<clip.components.numItems;ci++) if(clip.components[ci].matchName=="AE.ADBE Motion") clip.components[ci].properties[1].setValue(v,true); }
function clipAt(track,ticks){ for(var c=0;c<track.clips.numItems;c++) if(Math.abs(Number(track.clips[c].start.ticks)-ticks)<TPS/50) return track.clips[c]; return null; }
for(var h=0;h<hk.length;h++){
  var num=parseInt(hk[h].name.substr(2,2),10), name="NNN_XX "+AD+" HK"+num;
  var seq=null; for(var i=0;i<p.sequences.numSequences;i++) if(p.sequences[i].name==name) seq=p.sequences[i];
  if(!seq){ var before={}; for(var i=0;i<p.sequences.numSequences;i++) before[p.sequences[i].sequenceID]=1;
    src.clone(); for(var i=0;i<p.sequences.numSequences;i++) if(!before[p.sequences[i].sequenceID]) seq=p.sequences[i];
    seq.name=name; }
  var vt=seq.videoTracks[0], at=seq.audioTracks[0];
  for(var c=vt.clips.numItems-1;c>=0;c--) vt.clips[c].remove(false,false);
  for(var c=at.clips.numItems-1;c>=0;c--) at.clips[c].remove(false,false);
  while(seq.markers.numMarkers>0) seq.markers.deleteMarker(seq.markers.getFirstMarker());
  var t0=new Time(); t0.ticks="0";
  vt.overwriteClip(hk[h],t0); at.overwriteClip(hk[h],t0);
  var hc=clipAt(vt,0); setScale(hc,100);
  var hEnd=Number(hc.end.ticks);
  var bt=new Time(); bt.ticks=String(hEnd);
  if(CUT>0){ var ip=new Time(); ip.seconds=CUT; body.setInPoint(ip,4); }
  vt.overwriteClip(body,bt); at.overwriteClip(body,bt);
  if(CUT>0) body.clearInPoint();
  var bc=clipAt(vt,hEnd); setScale(bc,SCALE);
  var parts=hk[h].name.replace(".mp4","").split("_");
  var m=seq.markers.createMarker(0); m.name="HK"+num+" · "+parts[1]+"_"+parts[2]; m.comments=ESTR[parts[1]]||parts[1]; m.end=hEnd/TPS;
  var m2=seq.markers.createMarker(hEnd/TPS); m2.name="BODY "+AD+(CUT>0?" (hook original removido)":" (empilhamento: hook original mantido)");
  // mover para o bin
  for(var i=0;i<root.children.numItems;i++){ var it=root.children[i]; if(it.type==1 && it.name==name){ it.moveBin(seqBin); break; } }
  out.push(name+" hook="+(hEnd/TPS).toFixed(2)+"s body_in="+bc.inPoint.seconds.toFixed(2)+" fim="+bc.end.seconds.toFixed(2)+" v="+vt.clips.numItems+" a="+at.clips.numItems);
}
p.save();
return out.join("\n");

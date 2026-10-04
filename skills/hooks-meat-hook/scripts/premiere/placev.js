var p=app.project,root=p.rootItem,hooks=null,seq=null,src=null;
for(var j=0;j<root.children.numItems;j++) if(root.children[j].name=="HOOKS") hooks=root.children[j];
for(var i=0;i<p.sequences.numSequences;i++){ if(p.sequences[i].name=="9x16") src=p.sequences[i]; if(p.sequences[i].name=="HOOKS - ANIMADOS") seq=p.sequences[i]; }
if(!seq){ src.clone(); seq=p.sequences[p.sequences.numSequences-1]; seq.name="HOOKS - ANIMADOS"; }
p.activeSequence=seq;
var byName={}, names=[];
for(var k=0;k<hooks.children.numItems;k++){ var b=hooks.children[k]; if(!b.name.match(/^H\d\d_/)) continue;
  for(var i=0;i<b.children.numItems;i++){ var it=b.children[i]; if(it.name.match(/\.mp4$/)){ byName[it.name]=it; names.push(it.name);} } }
names.sort();
var vt=seq.videoTracks[0], at=seq.audioTracks[0];
for(var c=vt.clips.numItems-1;c>=0;c--) vt.clips[c].remove(false,false);
for(var c=at.clips.numItems-1;c>=0;c--) at.clips[c].remove(false,false);
while(seq.markers.numMarkers>0) seq.markers.deleteMarker(seq.markers.getFirstMarker());
var TPS=254016000000, fr=10594584000;
var ESTR={"Demonstracao":"4 · Demonstração","Confissao":"5 · Confissão pessoal","Omissao":"3 · Qualificação + omissão","Comando":"1 · Comando"};
var t=0, prev="", hookStart=0, out=[];
function mk(h, st, en, parts){ var m=seq.markers.createMarker(st/TPS); m.name=h+"_"+parts[1]+"_"+parts[2]; m.comments=(ESTR[parts[1]]||parts[1])+" · prop: "+parts[2]; m.end=en/TPS; }
var lastParts=null;
for(var n=0;n<names.length;n++){
  var it=byName[names[n]], base=names[n].replace(".mp4",""), h=base.substr(0,3), parts=base.split("_");
  if(prev && h!=prev){ mk(prev, hookStart, t, lastParts); t=Math.round((t+TPS)/fr)*fr; }
  if(h!=prev) hookStart=t;
  var tm=new Time(); tm.ticks=String(t);
  vt.overwriteClip(it, tm); at.overwriteClip(it, tm);
  var clip=null; for(var c=0;c<vt.clips.numItems;c++) if(Math.abs(Number(vt.clips[c].start.ticks)-t)<fr) clip=vt.clips[c];
  for(var ci=0;ci<clip.components.numItems;ci++) if(clip.components[ci].matchName=="AE.ADBE Motion") clip.components[ci].properties[1].setValue(1920/1344*100,true);
  t=Number(clip.end.ticks); prev=h; lastParts=parts;
  out.push(base+" "+clip.start.seconds.toFixed(2)+"-"+clip.end.seconds.toFixed(2));
}
mk(prev, hookStart, t, lastParts);
p.save();
return "v="+vt.clips.numItems+" a="+at.clips.numItems+" markers="+seq.markers.numMarkers+"\n"+out.join("\n");

var p=app.project,seq=null,r=[];
for(var i=0;i<p.sequences.numSequences;i++) if(p.sequences[i].name=="NNN_XX AD01 HK1") seq=p.sequences[i];
function dump(kind,tracks){ for(var t=0;t<tracks.numTracks;t++){ var tr=tracks[t];
  for(var c=0;c<tr.clips.numItems;c++){ var cl=tr.clips[c], comps=[];
    for(var k=0;k<cl.components.numItems;k++){ var cp=cl.components[k], props=[];
      for(var q=0;q<cp.properties.numItems;q++){ var pr=cp.properties[q]; var v=""; try{ v=pr.getValue(); }catch(e){ v="?"; } var tv=false; try{tv=pr.isTimeVarying();}catch(e){}
        props.push(pr.displayName+"="+(typeof v=="object"?String(v):v)+(tv?"(kf)":"")); }
      comps.push(cp.matchName+"["+props.join("; ")+"]"); }
    r.push(kind+(t+1)+" | "+cl.name+" | "+cl.start.seconds.toFixed(3)+"-"+cl.end.seconds.toFixed(3)+" | in="+cl.inPoint.seconds.toFixed(3)+" out="+cl.outPoint.seconds.toFixed(3)+" | media="+(cl.projectItem?cl.projectItem.getMediaPath():"")+"\n      "+comps.join("\n      ")); }
  try{ for(var x=0;x<tr.transitions.numItems;x++){ var tx=tr.transitions[x]; r.push(kind+(t+1)+" TRANSICAO "+tx.name+" "+tx.start.seconds.toFixed(3)+"-"+tx.end.seconds.toFixed(3)+" matchName="+tx.matchName); } }catch(e){ r.push(kind+(t+1)+" transicoes: "+e); }
} }
dump("V",seq.videoTracks); dump("A",seq.audioTracks);
return r.join("\n");

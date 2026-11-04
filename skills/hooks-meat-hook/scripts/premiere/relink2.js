var p=app.project,root=p.rootItem,hooks=null,r=[];
for(var j=0;j<root.children.numItems;j++) if(root.children[j].name=="HOOKS") hooks=root.children[j];
for(var i=0;i<p.sequences.numSequences;i++){ var s=p.sequences[i];
  if(s.name=="HOOKS - ANIMADOS"||s.name=="HOOKS - APROVACAO FRAMES"){
    for(var t=0;t<s.videoTracks.numTracks;t++) for(var c=s.videoTracks[t].clips.numItems-1;c>=0;c--) s.videoTracks[t].clips[c].remove(false,false);
    for(var t=0;t<s.audioTracks.numTracks;t++) for(var c=s.audioTracks[t].clips.numItems-1;c>=0;c--) s.audioTracks[t].clips[c].remove(false,false); } }
for(var k=0;k<hooks.children.numItems;k++){ var b=hooks.children[k]; if(b.name=="_REPROVADOS") continue;
  for(var i=0;i<b.children.numItems;i++){ var it=b.children[i];
    if(it.type==1 && (it.name.match(/^H05-1_|^H05-A_/) || it.isOffline())){ var ok=it.changeMediaPath(it.getMediaPath(), true); r.push(it.name+" ok="+ok+" off="+it.isOffline()); } } }
return r.join("\n");

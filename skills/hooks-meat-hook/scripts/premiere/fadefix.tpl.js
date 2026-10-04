var p=app.project,seq=null; app.enableQE();
for(var i=0;i<p.sequences.numSequences;i++) if(p.sequences[i].name=="__NAME__") seq=p.sequences[i];
p.activeSequence=seq;
var qs=qe.project.getActiveSequence(), q=qs.getAudioTrackAt(1);
var musEnd=seq.audioTracks[1].clips[0].end.seconds;
// remove transicoes que NAO comecam em 0 (o fade-out antigo)
for(var k=q.numTransitions-1;k>=0;k--){ var t=q.getTransitionAt(k); if(String(t.type)=="Transition" && Number(t.start.secs)>0.5) t.remove(); }
var clip=null; for(var k=0;k<q.numItems;k++){ var it=q.getItemAt(k); if(String(it.type)=="Clip") clip=it; }
var tr=qe.project.getAudioTransitionByName("Potência constante");
var ok=clip.addTransition(tr,false,"00:00:06:05","00:00:00:00",__ALIGN__,false,false);
var o=[]; for(var k=0;k<q.numTransitions;k++){ var t=q.getTransitionAt(k); if(String(t.type)=="Transition") o.push(Number(t.start.secs).toFixed(2)+"-"+Number(t.end.secs).toFixed(2)); }
return "__NAME__ musica ate "+musEnd.toFixed(2)+" ok="+ok+" transicoes: "+o.join(" | ");

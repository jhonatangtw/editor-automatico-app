var WIDTH={"H01-A_Demonstracao_Cilindro.png":1520,"H01-B_Demonstracao_Cilindro.png":1520,"H01-C_Demonstracao_Cilindro.png":1536,"H02-A_Confissao_Parque.png":1536,"H03-A_Demonstracao_Pescoco.png":1536,"H03-B_Demonstracao_Pescoco.png":1520,"H03-C_Demonstracao_Pescoco.png":1536,"H04-A_Demonstracao_Coracao.png":1536,"H04-B_Demonstracao_Coracao.png":1536,"H04-C_Demonstracao_Coracao.png":1536,"H05-A_Confissao_Escada.png":1536,"H05-B_Confissao_Escada.png":1536,"H06-A_Omissao_Quarto.png":1536,"H06-B_Omissao_Quarto.png":1536,"H06-C_Omissao_Quarto.png":1536,"H07-A_Comando_Padre.png":1520,"H07-B_Comando_Padre.png":1536,"H07-C_Comando_Padre.png":1536,"H08-A_Omissao_Tornozelo.png":1536,"H08-B_Omissao_Tornozelo.png":1536,"H08-C_Omissao_Tornozelo.png":1536,"H09-A_Omissao_Fazenda.png":1520,"H09-B_Omissao_Fazenda.png":1520,"H10-A_Omissao_Acougue.png":1520,"H10-B_Omissao_Acougue.png":1520,"H10-C_Omissao_Acougue.png":1536};
var p=app.project,root=p.rootItem,sf=null,hooks=null,seq=null;
for(var j=0;j<root.children.numItems;j++) if(root.children[j].name=="HOOKS") hooks=root.children[j];
for(var k=0;k<hooks.children.numItems;k++) if(hooks.children[k].name=="START FRAMES") sf=hooks.children[k];
for(var i=0;i<p.sequences.numSequences;i++) if(p.sequences[i].name=="HOOKS - APROVACAO FRAMES") seq=p.sequences[i];
p.activeSequence=seq;
var items=[]; for(var i=0;i<sf.children.numItems;i++) items.push(sf.children[i]);
var byName={}, names=[]; for(var i=0;i<items.length;i++){ byName[items[i].name]=items[i]; names.push(items[i].name); }
names.sort(); items=[]; for(var i=0;i<names.length;i++) items.push(byName[names[i]]);
var tr=seq.videoTracks[0];
for(var c=tr.clips.numItems-1;c>=0;c--) tr.clips[c].remove(false,false);
while(seq.markers.numMarkers>0){ seq.markers.deleteMarker(seq.markers.getFirstMarker()); }
var TPS=254016000000, fr=10594584000;
function snap(sec){ return Math.round(sec*TPS/fr)*fr; }
var t=0, prevHook="", log=[];
var ESTR={"Demonstracao":"4 · Demonstração","Confissao":"5 · Confissão pessoal","Omissao":"3 · Qualificação + omissão","Comando":"1 · Comando"};
for(var n=0;n<items.length;n++){
  var it=items[n], base=it.name.replace(".png",""), hook=base.substr(0,3);
  if(prevHook && hook!=prevHook) t+=1;
  prevHook=hook;
  var startT=snap(t), endT=snap(t+3);
  var tm=new Time(); tm.ticks=String(startT);
  tr.overwriteClip(it, tm);
  var clip=null; for(var c=0;c<tr.clips.numItems;c++) if(Math.abs(Number(tr.clips[c].start.ticks)-startT)<fr) clip=tr.clips[c];
  var te=new Time(); te.ticks=String(endT); clip.end=te;
  // escala para caber 1080 de largura
  var w=WIDTH[it.name];
  var comps=clip.components;
  for(var ci=0;ci<comps.numItems;ci++){ var cp=comps[ci];
    if(cp.matchName=="AE.ADBE Motion"){ cp.properties[1].setValue(1080/w*100,true); } }
  var m=seq.markers.createMarker(startT/TPS);
  var parts=base.split("_");
  m.name=base; m.comments=(ESTR[parts[1]]||parts[1])+" · prop: "+parts[2];
  m.end=endT/TPS;
  t+=3;
}
return "clips="+tr.clips.numItems+" markers="+seq.markers.numMarkers+" dur="+t+"s";

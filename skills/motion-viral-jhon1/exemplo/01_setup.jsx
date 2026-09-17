// Setup: takes em sequência + cartões + comp principal.
// Rodar:  MVJ_COMP=REELS01_MAIN lib/rodar.sh "<projeto>" exemplo/01_setup.jsx
// O rodar.sh injeta DEMANDA/SAIDA/COMP_MAIN/FPS e fecha em try/catch — não repita isso aqui.
app.beginUndoGroup("setup");

var f01=folder("01_Footage"), f05=folder("05_Precomps");

// in/out de cada take vindos do silencedetect, em QUADROS (nunca estimados)
var takes=[["Take1.mp4",155],["take 2.mp4",175],["Take 3.mp4",148],["Take 4.mp4",200],["take 5 - cta.mp4",230]];

var th=mkComp("PC_00_TALKING_HEAD", 38, f05), t=0;
for(var i=0;i<takes.length;i++){
  var it=importFile(DEMANDA+"/"+takes[i][0], f01);
  var l=th.layers.add(it); l.name="take"+(i+1);
  l.startTime=t; l.inPoint=t; l.outPoint=t+F(takes[i][1]);
  l.moveToEnd();                       // layers.add empilha no topo: reordenar sempre
  log("take"+(i+1)+" in="+l.inPoint.toFixed(3)+" out="+l.outPoint.toFixed(3));
  t+=F(takes[i][1]);
}
log("fim dos takes = "+t.toFixed(3)+" ("+Math.round(t*FPS)+" quadros)");

// cartão = footage + matte arredondado; toca 3 s e congela
function card(nome, src, congelarEm){
  var c=mkComp(nome, 10, f05);
  var v=c.layers.add(src); v.name="video";
  v.timeRemapEnabled=true;
  var tr=v.property("ADBE Time Remapping");     // NÃO apagar as chaves padrão antes de setar
  if(congelarEm!=null){ tr.setValueAtTime(0,congelarEm); tr.setValueAtTime(10,congelarEm); }
  else { tr.setValueAtTime(0,0); tr.setValueAtTime(3,3); tr.setValueAtTime(10,3); }
  var kEnd=tr.nearestKeyIndex(src.duration);
  if(Math.abs(tr.keyTime(kEnd)-src.duration)<0.01) tr.removeKey(kEnd);
  for(var k=1;k<=tr.numKeys;k++) tr.setInterpolationTypeAtKey(k, KeyframeInterpolationType.LINEAR, KeyframeInterpolationType.LINEAR);
  v.outPoint=10;
  var m=shapeLayer(c,"matte_arredondado"); var g=grp(m,"rr");
  rect(g,W,H,96,0,0); fill(g,C.white); pos(m).setValue([W/2,H/2]);
  v.setTrackMatte(m, TrackMatteType.ALPHA);
  return c;
}
var crA=importFile(DEMANDA+"/Criativos/A.mp4", folder("02_Criativos"), "CRIATIVO_A.mp4");
card("PC_CARD_A", crA, null);
card("PC_CARD_A_parado", crA, 1.0);

var main_=mkComp(COMP_MAIN, 38, null);
var thl=main_.layers.add(th); thl.name=th.name; thl.startTime=0;

report(th); report(main_);
frame(main_, 1.0, "setup_1s");

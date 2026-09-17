// Camada dopaminérgica + editorial numa comp DUPLICADA. Rodar depois do 03.
app.beginUndoGroup("dopa");
var f06=folder("06_Precomps"), f07=folder("07_SFX");
var m=findItem(COMP_MAIN).duplicate(); m.name=COMP_MAIN+"_DOPA"; m.parentFolder=app.project.rootFolder;
var th=findLayer(m,"PC_00_TALKING_HEAD"); var leg=findLayer(m,"PC_LEGENDAS");   // pode ser null se ainda não houver legenda
var swish=item("Fast_Swish.wav"), pop=item("CARTOON_POP.mp3"); var cam=camera3D(m);
// legenda premium na versão DOPA
if(leg){ var legP=legendasPremium(leg.source,f06); leg.replaceSource(legP,false); leg.name=legP.name; }
// --- cena DOPAMINÉRGICA: "lose 13 pounds next week" (palavras em 75.77 / 76.49 / 77.33)
cenaDopa(m,leg,swish,"13lb",75.75,77.95,false);
palavraDopa(m,pop,"lose","lose",75.77,77.95,W/2,640,80,90,DOPA.tinta,0);
palavraDopa(m,pop,"13","13 pounds",76.49,77.95,W/2,960,-160,150,DOPA.verm,-2);
palavraDopa(m,pop,"next","next week",77.33,77.95,W/2,1230,40,96,DOPA.tinta,0);
objeto3D(m,"balanca",item("BALANCA_cutout.png"),76.49,77.95,W/2,1560,-40,380,4);
camMove(cam,75.75,77.95,[60,-40,120],[-40,30,-220]);
// --- cena EDITORIAL: "Matcha." (78.71) — preto, anel de entrada, reveal letra a letra
cenaEditorial(m,leg,swish,"matcha",78.69,79.72,true,"MATCHA"); anel(m,78.71);
chave(m,pop,"matcha","Matcha.",78.71,79.72,W/2,1140,-160,170,C.white);
objetoCanto(m,"copo",item("MATCHA_glass_cutout.png"),78.69,79.72,W/2,620,-60,620,-4); estrelas(m,"matcha",79.05,79.72,W/2,1240,C.white);
camMove(cam,78.69,79.72,[-60,0,-40],[50,-20,-220]);
// --- ritmo: zoom alternado por frase (inícios de frase do transcript)
zoomPorFrase(th,[21.47,28.51,34.35,36.53,41.27,50.79,55.15,63.39,69.01,73.27,79.73],106);
report(m); frame(m,77.0,"dopa_13lb"); frame(m,79.2,"ed_matcha");

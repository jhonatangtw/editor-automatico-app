// AD04 condensado — gramática PODCAST. Rodar: MVJ_COMP=AD04_MAIN MVJ_FPS=30 lib/rodar.sh "<projeto>" exemplo/03_podcast_body.jsx
// Todos os tempos vieram do transcript por palavra (00_brief/ancoras_body.json) — nunca estimados.
app.beginUndoGroup("podcast body");
var f01=folder("01_Footage"), f03=folder("03_Broll"), f04=folder("04_Imagens"), f06=folder("06_Precomps"), f07=folder("07_SFX");
var BODY_START=F(335);
// 1) talking head: [footage, quadros] — quadros do silencedetect
var th=talkingHead("PC_00_TALKING_HEAD",[[item("hook 1 - Rogan.mp4"),288],[item("hoos - rhonda.mp4"),47],[item("lip - BODY ad04 Rhonda.mp4"),3689]], F(4024), f06);
var m=mkComp(COMP_MAIN, th.duration, null); var thl=m.layers.add(th); thl.name="PC_00_TALKING_HEAD";
var swish=importFile(DEMANDA+"/07_SFX/Fast_Swish.wav", f07), pop=importFile(DEMANDA+"/07_SFX/CARTOON_POP.mp3", f07);
// 2) cartões nos trechos com objeto ("at Harvard, surrounded by researchers…")
cardPhoto(m,thl,f06,"harvard_lab",item("Rhonda em harvard Lab.png"),540,700,680,880,13.55,15.70); sfx(m,swish,13.50,-14,"c1");
cardPhoto(m,thl,f06,"equipe",item("Rhonada com equipe de cientistas.png"),540,700,680,880,15.75,18.10);   // consecutivo: corte seco, sem re-blur
// 3) prova grande em tela cheia ("3,000 patients")
cutFull(m,thl,"3000_pacientes",item("usar esse - 3mil participantes.mp4"),56.45,60.30); sfx(m,swish,56.40,-14,"cut3000");
// 4) punch-in com tremor nas palavras de impacto
punch(thl,78.71,0.7); impacto(thl,78.71); sfx(m,pop,78.71,-10,"matcha");
// 5) split "tela dividida acima a Dra abaixo…" — topo reenquadrado a partir da medição do YuNet (cx=350, topo da cabeça y=95)
var enq=reenquadrar(350,95,150);
split(m,thl,f06,"ritual_receita",item("lip - BODY ad04 Rhonda.mp4"),BODY_START,item("Dra Rhonda fazendo receita de matcha em live.mp4"),80.20,85.20,1422,enq.pos,enq.scale); sfx(m,swish,80.15,-14,"split1");
// 6) CTA sem texto novo
chevron(m,thl,112.21,114.30);
// 7) legendas em caixa (blocos vêm do JSON gerado pelo pipeline) + fundo sob cartão
// var leg=mkComp("PC_LEGENDAS",m.duration,f06); legendasCaixa(leg,BLOCOS,"Nunito-ExtraBold",60,[0.137,0.314,0.051],[0.957,0.827,0.369],858,1225); placeInMain(leg,0,0,m.duration);
fundoSobCartao(m,thl,22,40,8);
report(m); frame(m,14.5,"card"); frame(m,58.0,"cut"); frame(m,82.5,"split");

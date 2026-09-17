// Uma cena de cutaway completa: fundo premium, herói, dois registros de texto,
// anotação tracejada e saída. Todos os tempos são LOCAIS da cena (0 = início dela).
// A palavra-âncora de cada evento vai no comentário — é o que se confere depois.
app.beginUndoGroup("M1");

var T0=0.00;                       // onde a cena entra na MAIN
var c=precomp("PC_M1_identicos", 6.6);

var bg=paperBG(c);                                     // chão da cena
premiumBG(c, [300,420], [1250,300], 28, 50);           // luz + profundidade + vinheta
grade(c).outPoint=3.2;
ghost(c, "2", 1500, 930+520).parent=bg;                // numeral fantasma (4-6 %)

// push de 3-4 % ao longo da cena
key(scl(bg), 0, [100,100,100], "lin");
key(scl(bg), 2.95, [104,104,100], "lin");

// herói: cartões entram pela lateral com rotação e overshoot
var A=cardLayer(c,"PC_CARD_A","card_A",300,930,38);
key(pos(A),0.10,[-260,930],"ease"); key(pos(A),0.55,[318,930],"ease"); key(pos(A),0.70,[300,930],"ease");
key(rot(A),0.10,-7,"ease");         key(rot(A),0.70,0,"ease");

// lead-in (fala: "esses dois criativos" @0.62) e palavra-chave (fala: "idênticos" @1.68)
var lead=text(c,"lead","esses dois criativos",FONT.lead,56,C.grey,W/2,430);
blockIn(lead,0.62,8,14); fadeOut(lead,2.95,5);
var kw=text(c,"kw_identicos","idênticos",FONT.key,150,C.ink,W/2,1560);
blockIn(kw,1.68,10,26); fadeOut(kw,2.95,5);

// anotação desenhada a velocidade constante
var circ=dashedCircle(c,"anot",1040,1000,W/2,930,C.ink,7);
drawIn(circ.trim,1.75,2.55); fadeOut(circ.layer,2.95,5);

// saída por slide (alternar com wipe/push/sweep na cena seguinte)
slideOut(A,6.30,6,0,980);

var ml=placeInMain(c,T0,T0,6.55);
report(c);
var m=main();
var ts=[0.5,1.2,2.3,3.0,5.0,6.45];                     // um frame por beat
for(var i=0;i<ts.length;i++) frame(m, T0+ts[i], "M1_"+i);

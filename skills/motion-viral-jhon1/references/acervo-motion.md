# Acervo local de referências de motion

15 referências do "Sótão do Matt" (Drive da H&W), classificadas e copiadas para o disco em
15/09/2026. **Mídia em** `~/Documents/Referencias de Motion/` — nunca dentro da skill.

- Catálogo completo (descrição, características, avisos por arquivo): `~/Documents/Referencias de Motion/INDICE.md`
- Contact sheet de 9 quadros por referência: `~/Documents/Referencias de Motion/_mosaicos/<nome>.png`
- Originais intactos no Drive: `Sotao do Matt/Motion References/01_Motion`

Este arquivo responde só uma pergunta: **qual referência abrir para a cena que estou construindo,
e que função da skill ela vira.** Ritmo, tipografia e paleta da identidade continuam em
`IDENTIDADE.md`; as gramáticas continuam em `references/formato-podcast-split.md`.

## Como entra no fluxo

Na **etapa 3 (Referências)** do `SKILL.md`: antes de pedir link ao cliente, procure aqui a cena
equivalente. Se o cliente mandou referência própria, ela manda — o acervo entra como
complemento para as cenas que a referência dele não cobre. O que for usado vai citado no
`ANALISE_REFERENCIAS.md` da demanda, pelo nome do arquivo.

Consulta rápida sem abrir vídeo:

```bash
open ~/Documents/Referencias\ de\ Motion/_mosaicos/OFERTA_preco-riscado-seta-verde_CardioFlush.png
grep -i "contador\|marca-texto\|riscado" ~/Documents/Referencias\ de\ Motion/INDICE.md
```

## Tabela de decisão — cena da copy → referência → função

| A copy pede… | Abra | Vira |
| --- | --- | --- |
| mecanismo / etapas do produto, sem locutor | `01_Produto_Cartoes_Vidro/PRODUTO_cards-vidro-sinapse_MemoFlow` | `cardPhoto` empilhado + `drawIn` no filamento |
| "você vai receber X" / bloco de oferta | `02_Oferta_Preco_CTA/OFERTA_lettering-3-frascos-gratis_MemoPryl` | `fundoSobCartao` + lettering por frase + `popIn` do produto |
| âncora de preço, "de X por Y" | `02_Oferta_Preco_CTA/OFERTA_preco-riscado-seta-verde_CardioFlush` | `text` grande + `line` riscando + `chevron` de seta |
| escolha de kit / tabela de pacotes | `02_Oferta_Preco_CTA/OFERTA_kits-cartoes-cursor_MemoPryl` | 3× `cardPhoto` escalonado + cursor por `key` de posição |
| CTA final | `02_Oferta_Preco_CTA/CTA_botao-pilula-vidro_MemoFlow` | `pill` + `drawIn` na borda + permanência longa |
| estudo, ensaio clínico, citação | `03_Prova_Cientifica/PROVA_estudo-harvard-marca-texto` | `cardPhoto` inclinado + `punch` + `sweep` de marca-texto |
| número de resultado, progresso, curva | `03_Prova_Cientifica/PROVA_grafico-linha-crescente` | `curvePath` + `drawIn` + `ticks` + `plate` de legenda |
| confissão/denúncia com número grande | `04_Lettering_Legenda/LETTERING_contador-numerico-cutaway` | `palavraDopa` + contador por expressão + `cutFull` |
| legenda queimada sobre B-roll | `04_Lettering_Legenda/LEGENDA_pop-palavra-sobre-broll` | `legendasPop` (padrão de cor e sombra) |
| narrativa histórica / autoridade | `05_Editorial_Documentario/EDITORIAL_arquivo-pb-edison` | `cenaEditorial` + `serifa` + `chave` + `revelaLetras` |
| abertura de documentário | `05_Editorial_Documentario/EDITORIAL_template-fiverr-showreel` ⚠️ | só ideia — ver avisos |
| camada dopaminérgica, objeto na palavra | `06_Colagem_Dopaminergica/DOPA_colagem-recorte-tipografia` | `cenaDopa` + `palavraDopa` + `objeto3D` + `flashBranco` |
| lista de opções/benefícios com foto | `07_Cartoes_Foto_Carrossel/CARROSSEL_cartao-polaroid-troca` | `cardPhoto` com troca por empurrão + fundo casado |
| pilha de fotos / galeria | `07_Cartoes_Foto_Carrossel/CARROSSEL_pilha-polaroid-placeit` ⚠️ | ideia de movimento — ver avisos |
| vitrine de várias peças, transição sem corte | `07_Cartoes_Foto_Carrossel/CARROSSEL_posteres-deslizando` | esteira + escala/opacidade por distância do centro |

## O que o acervo ensina por categoria

**Produto + vidro (01) e CTA (02).** `PRODUTO_cards-vidro-sinapse` e `CTA_botao-pilula-vidro` são o
**mesmo sistema visual** — fundo de sinapse claro, frasco cobalto, vidro fosco, contorno luminoso.
Usar os dois no mesmo criativo dá mecanismo e CTA sem trocar de mundo. É o sistema CLARO que a casa
já pratica; combina com a trava de rótulo do produto (ver o catálogo do frasco no projeto da marca).

**Oferta (02).** Três formas de vender o mesmo bloco, e elas não se misturam: lettering por frase
(quando a oferta é uma frase da copy), preço riscado (quando há âncora de valor), cartões com cursor
(quando há escolha de pacote). Escolha **uma** por criativo — as três juntas viram poluição.
O cursor animado do `OFERTA_kits-cartoes-cursor` é o detalhe que faz o cartão parecer página real;
é barato de fazer (`key` de posição + um clique com escala) e vale mais que o cartão em si.

**Prova (03).** As duas referências têm a mesma lição: **a credibilidade está no rodapé pequeno**, não
no elemento grande. O gráfico só convence com a linha "Reported Clinical Observation, 2026" embaixo;
o papel só convence porque é documento real com régua de revista. Elemento de prova sem a
legendinha de fonte vira enfeite.

**Lettering e legenda (04).** `LEGENDA_pop-palavra-sobre-broll` é o contrato de legenda sobre B-roll:
1–2 palavras, caixa-alta, branco com **uma** cor de acento na palavra de valor, sombra dura o
bastante para segurar sobre imagem clara. `LETTERING_contador-numerico-cutaway` mostra o pico: o
número grande vermelho correndo é o único momento em que a cor quente aparece — usar uma vez por
criativo, no clímax.

**Editorial (05).** `EDITORIAL_arquivo-pb-edison` é o primo em preto e branco da gramática EDITORIAL
que a skill já tem em `formato-podcast-split.md` § *Gramática EDITORIAL*. A diferença: manuscrito
em vez de papel liso, anotação à mão (seta, círculo a caneta) em vez de ornamento ✦, e monocromático
integral. Quando a copy for narrativa de superação ou descoberta, é esta a variação.

**Dopaminérgica (06).** `DOPA_colagem-recorte-tipografia` é a melhor referência do acervo para a regra
que a skill já pratica — **objeto entra na palavra que o nomeia**. Lição adicional: o fundo troca
junto com a frase (preto ↔ creme), e isso sozinho já dá o pulso. Vale só na comp `*_DOPA`.

**Carrossel (07).** Os três resolvem "mostrar várias coisas sem cortar". `CARROSSEL_posteres-deslizando`
é o mais reaproveitável: esteira contínua com o cartão central maior e os vizinhos escurecidos —
transição entre cartões sem corte seco, útil em depoimento e print de resultado.

## Avisos ao usar

- **Formato manda o da entrega, não o da referência.** Seis das quinze são 1080×1920 a 30 fps; as
  outras são 4:5, quadradas ou landscape. Medir ritmo numa referência 4:5 e aplicar em 9:16 sem
  reenquadrar desloca tudo.
- **Duas têm marca d'água permanente** (`EDITORIAL_template-fiverr-showreel`, "fiverr";
  `CARROSSEL_pilha-polaroid-placeit`, "Made with Placeit"). São demos de template, não criativo real:
  servem como ideia de movimento e **nunca** como contrato visual ou prova de acabamento.
- **`CARROSSEL_cartao-polaroid-troca` não tem faixa de áudio** — não serve para medir sincronia com fala.
- **Adaptar, não copiar** — a regra da etapa 3 vale igual aqui. As referências de oferta trazem marcas
  reais (MemoPryl, MemoFlow, CardioFlush): copiar o layout é legítimo, copiar rótulo e nome não.
- O catálogo em `INDICE.md` traz por arquivo a resolução, os fps, a duração e o nome original no
  Drive — conferir lá antes de citar número em plano de demanda.

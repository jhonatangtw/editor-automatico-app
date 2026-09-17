# Transições e fundo

## As quatro saídas — alternar, nunca repetir vizinhas

| Tipo | O que acontece | Quando | Implementação |
| --- | --- | --- | --- |
| `slide` | a cena é puxada para fora do quadro e o vídeo aparece atrás | padrão | keyframes de `pos` na **camada do precomp na MAIN**, ease de saída |
| `wipe` | uma folha atravessa a lente; atrás dela o vídeo já está lá | quando se quer "clarão" | sólido `paperCool` cruzando em ~7 quadros, `outPoint` logo depois |
| `push` | a câmera acelera para dentro e o corte cai na velocidade | fecho de ideia | `scl` 104 → 134 % nos 5 últimos quadros, ease `in` |
| `sweep` | silhueta escura desfocada varre e esconde o corte | assinatura da identidade | `sweep(nome, t0, t1, de, para, rot)` — vai na MAIN, acima de tudo |

Hold de 8–18 quadros antes de qualquer saída. Melhor ponto de corte é o **silêncio** entre
palavras — nunca no meio de uma.

**Nada de flash branco nem whip pan.** Quando pedirem flash, entregue o `wipe`: dá o mesmo
clarão, mas material. Quando pedirem efeito de câmera, entregue o `push`.

## Fundo premium

`premiumBG(comp, posLuz, posProfundidade, rotProfundidade, deriva)` monta as três camadas de uma
vez sobre o `BG_papel` da cena:

```
BG_papel          ramp radial  #ECEFEF (centro, y≈760) → #BEC6C9 (borda, y≈2150), dispersão 6
BG_luz            ramp radial branco→preto, blend SCREEN, 42 %, do lado OPOSTO ao herói
BG_profundidade   retângulo tinta 900x1500 r140, blur 150, 9-13 %, derivando 40-60 px na cena
ADJ_acabamento    vinheta 34 + ruído 3,5  (era 22/2,5 no fundo chapado)
```

Três regras que fazem diferença:

1. **A luz vai do lado oposto ao herói.** Herói à esquerda → luz à direita. Luz atrás do herói
   achata tudo de novo.
2. **A profundidade tem que derivar.** Parada, é uma mancha; derivando 40–60 px ao longo da cena,
   vira parallax. Sempre `lin` — aceleração aqui lê como tremor de câmera.
3. **Tudo parenteado ao `BG_papel`**, e as camadas herdam o `inPoint` dele. Assim o `wipe` de
   entrada e o `slide` de saída continuam levando a cena inteira, sem sobra.

Se a cena tem **objeto fotográfico**, baixar o numeral fantasma de 6 % para 4 % — a foto já
carrega textura e os dois competem.

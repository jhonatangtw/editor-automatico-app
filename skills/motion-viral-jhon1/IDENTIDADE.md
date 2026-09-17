# MOTION-VIRAL-JHON1 — identidade visual

```yaml
identidade: MOTION-VIRAL-JHON1
versao: 1
canvas: 1080x1920
fps: 24
origem: explainer editorial de marca medido frame a frame (12 s, 720x1280) + take do Jhon
```

Aprovada em produção no Reels "dois criativos idênticos" (09/09/2026).

## As sete coisas que fazem esta identidade

1. **Estúdio claro como chão do cutaway.** Ramp radial `#ECEFEF` (centro) → `#BEC6C9` (borda),
   dispersão 6. Sobre footage escuro, o corte para o claro **é** o clarão — dispensa flash branco.
2. **Luz de estúdio** em `screen` a 42 %, ramp radial branco→preto, posicionada **do lado oposto
   ao herói** em cada cena. É ela que tira o "chapado" do fundo.
3. **Silhueta de profundidade**: retângulo tinta, blur 150, opacidade 9–13 %, derivando 40–60 px
   ao longo da cena. Dá parallax em 3 planos sem nenhum objeto novo.
4. **Dois registros tipográficos, sempre os dois.** Lead-in em sans light itálica cinza
   (`InterItalic-LightItalic`, 48–64 px) e palavra-chave em serifa bold itálica ~2,3× maior
   (`PlayfairDisplayItalic-BoldItalic`, 130–160 px). Numeral editorial: `Fraunces-9ptBlack`.
5. **Numeral fantasma** atrás do herói — o número da cena ("2", "2s", "R$"), 1100–1500 px,
   opacidade 4–6 %. Nunca decoração: é sempre um dado da cena.
6. **Um acento por cena, tirado da luz prática do próprio take.** No material do Jhon, âmbar
   `#E3A44A` (núcleo medido `#FDF6DF`). Vermelho e verde ficam fora — "morreu" é tinta + risco.
7. **Anotação desenhada**: círculo tracejado (dash 30 / gap 24, 5–7 px) e fita larga (stroke 64,
   ponta redonda), ambos por trim path a velocidade constante — caneta não desacelera no fim.

## Paleta

```yaml
paper:    "#DBE0E0"   paperCool: "#CFD4D6"
ink:      "#26282B"   grey:      "#6B6E70"
amber:    "#E3A44A"   white:     "#FFFFFF"
```

Proporção: **80 % neutros · 15 % massa escura · 5 % acento.**

## Tipografia — as fontes viajam junto

| Função | Fonte | Licença |
| --- | --- | --- |
| lead-in itálico | Inter Italic (Light/Regular) | OFL |
| palavra-chave | Playfair Display Italic Bold | OFL |
| numeral / fantasma | Fraunces Black | OFL |
| legenda falada | Inter Bold | OFL |
| etiqueta | Inter Bold Italic | OFL |

Nenhuma fonte de sistema: a identidade não pode ficar presa a uma máquina.
`fontSize` no AE tem **teto de 1296** — texto maior vai por escala de camada.

## Movimento (contrato medido)

```yaml
beat_por_frase:   1,5-2,5 s
entrada_texto:    bloco — opacidade 0→100 + subida 14-26 px em 8-10 quadros
pouso_objeto:     escala 104 → 100 em 10 quadros, com a sombra junto
cartao_de_foto:   entra pela lateral, rotação ±7 → 0 em ~12 quadros, overshoot 18 px
hold_antes_sair:  8-18 quadros
camera_push:      100 → 103-106 % por cena; push de saída acelera até ~134 % em 5 quadros
ancoragem:        evento visual cai na palavra falada, tolerância ±3 quadros
```

## Sombras por classe

```yaml
cartao_de_foto:  dist 26  soft 70  32%
placa/plate:     dist 22  soft 60  45%
etiqueta/pill:   dist 10  soft 30  28%
texto_sobre_video: dist 5 soft 7   62%   # + glow, ver voz-e-legenda.md
objeto_recortado: dist 24 soft 60  34%
```

## Proibições

neon · bloom · flash branco · whip pan · glitch como transição · gradiente decorativo ·
dashboard SaaS · card arredondado sem função · texto repetindo a narração · máquina de escrever
(revelar caractere a caractere) · impacto de câmera a cada frase · **boil/tremor** (esta
identidade é limpa: o "feito à mão" está no tracejado e na fita, não no tremor).

## Reprovações que definiram a identidade

- **Maço de notas grande demais** (68 % de escala) roubava o quadro do texto → 52 %.
- **Numeral fantasma a 6 %** competia com o objeto fotográfico → 4 % quando há foto na cena.
- **Nota com "ONE DOLLAR" legível** → reprovada; pedir guilloche abstrato (armadilha em
  `references/prompts-asset.md`).
- **Legenda sem glow** sumia sobre a jaqueta preta; **glow forte** engordava a letra → 0,55.

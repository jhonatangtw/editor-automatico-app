# Prompts de asset

Antes de escrever uma palavra na tela, pergunte **que objeto diria aquilo**. E antes de gerar,
pergunte se o material que já existe (o próprio criativo, um frame do take) não resolve.

Gerador usado: `higgsfield generate create nano_banana_pro --prompt "…" --aspect_ratio 3:4 --resolution 2k --json`,
depois `higgsfield generate wait <id> --timeout 8m --json` (a flag é `--timeout`, não `--wait-timeout`).

## Esqueleto — objeto isolado

```
Single isolated object centered on a completely flat plain neutral gray backdrop hex 8A8A8A.
<OBJETO E ESTADO>, photographed straight from directly overhead, perfect top-down view.
<MATERIAL E DESGASTE>. Even soft diffuse light, no cast shadow on the backdrop, object fully
within frame with clear separation from background. Matte finish, no glossy highlights.
Documentary object photograph. No text, no letters, no numbers, no symbols, no brand, no logo
anywhere. No glossy 3D render, no neon, no glow, no gradients, no HDR, no AI-polished look.
```

Fundo: `#8A8A8A` para objeto claro · `#D8D8D8` para objeto escuro.

## Sempre no prompt

| Sempre | Por quê |
| --- | --- |
| `no cast shadow on the backdrop` | sombra é camada no AE, nunca pixel do asset |
| `no text, no letters, no numbers, no logo` | texto de IA é reprovação automática |
| `no glow, no bloom, no neon, no gradients, no HDR` | proibições da identidade |
| `matte finish, no glossy highlights` | material fosco |

## Dinheiro, documento, produto de marca

**Peça a impressão ILEGÍVEL, e seja específico** — "no text" sozinho não basta:

```
The printed design is ONLY a faint abstract geometric guilloche border and one empty plain oval
in the middle — absolutely no lettering of any kind, no words, no letters, no numerals, no digits,
no denomination, no portraits, no faces, no seals, not any real currency.
```

Medido: o prompt genérico voltou com **"ONE DOLLAR" e "THE UNITED STATES OF AMERICA" legíveis**
na borda e foi reprovado. Gere 2 variantes de qualquer asset herói — a rejeitada ensina.

## Recorte — o fundo "chapado" da IA vem com gradiente

```bash
python3 lib/recortar_gradiente.py maco nota
```

Flood-fill por borda **não serve** aqui: o fundo varia (medido 158 → 134 do topo ao centro) e o
objeto cai na mesma faixa de luminância — a varredura de tolerância não tem platô, e o recorte
sai em farrapos. O que funciona:

1. ajuste **quadrático** do fundo pelas bordas (coordenadas normalizadas, sem matmul grande —
   o BLAS da Accelerate estoura com matriz de imagem inteira);
2. resíduo + croma como semente de frente/fundo;
3. **GrabCut** para separar objeto (texturizado, com croma) de sombra (neutra, lisa, mais escura);
4. maior componente, fecha buracos, pluma de 0,8 px, apara ao bounding box.

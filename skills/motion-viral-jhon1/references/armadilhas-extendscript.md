# Armadilhas do After Effects por script

Cada uma custou pelo menos uma rodada. Confira antes de culpar o projeto.

## Como falar com o AE

`osascript -e 'tell application "Adobe After Effects 2026" to DoScriptFile "/caminho/x.jsx"'`
devolve **só um status** — todo retorno tem que ser gravado em arquivo pelo próprio script.
`lib/rodar.sh` já faz isso: injeta `DEMANDA/SAIDA/COMP_MAIN/FPS/LOGNAME`, concatena a
biblioteca, fecha em try/catch e imprime o log.

**DoScript pendurou?** O motor de script está preso — quase sempre um painel CEP com
`evalScript` que nunca voltou. Sintoma: o AE aparece em estado `U` no `ps` com CPU alta.
Só reiniciar o AE resolve.

## Erros que estouram

| Sintoma | Causa | Saída |
| --- | --- | --- |
| `Valor 1500 fora do intervalo de 0,1 a 1296` | teto de `fontSize` | criar em ≤1296 e escalar a camada |
| `Foi localizado um objeto do tipo Error no qual é necessário um número` | concatenar um `Error` em string | logar `e.message`, nunca `e` |
| `resultado numérico inválido (divisão por zero?)` | ler `position` com dimensões separadas | checar `dimensionsSeparated` antes |
| `Não é possível "set value at time"… propriedade oculta` | mexer em Time Remap com a propriedade fechada | ligar `timeRemapEnabled` e **não apagar** as chaves padrão antes de setar |
| `Array não é um número` no `ADBE Glo2` | cor de glow espera índice, não `[r,g,b,a]` | deixar as cores no padrão; mexer só em limiar/raio/intensidade |

## Comportamentos que enganam

1. **`layers.add()` empilha no topo.** Montar cenas em sequência deixa a primeira POR CIMA da
   última. Reordenar no fim (`moveToEnd`/`moveToBeginning`) e **ler a ordem de volta**.
2. **`comp.layer(1)` não é a footage** depois que você adiciona texto. Endereçar por nome
   (`findLayer`) — nunca por índice.
3. **Posição de camada filha é no espaço do pai**, com origem no canto do sólido, não na comp.
   Parentear e **depois** setar a posição local explicitamente.
4. **`layer.enabled=false` desliga só o vídeo.** Para mutar áudio é `layer.audioEnabled=false` —
   é assim que se troca a voz mantendo a imagem.
5. **Importar o mesmo arquivo duas vezes cria item duplicado** e o projeto vira um lixo.
   `importFile()` da biblioteca reaproveita o item existente pelo nome.
6. **Nome de comp com acento não é endereçável** por ferramentas que comparam string exata: o AE
   guarda em Unicode decomposto. Manter nomes de comp em ASCII.
7. **`saveFrameToPng` é a prova por quadro** — com dois detalhes. O nome perde o zero à direita
   (pedir `M1_3.0` grava `M1_3.png`), então não nomeie com decimal ambíguo. E **o arquivo é
   gravado depois do log**: listar a pasta imediatamente depois de ler o log mostra pasta vazia,
   ou pior, um PNG pela metade. O `rodar.sh` já espera cada frame prometido aparecer e parar de
   crescer — se você chamar o AE por fora, espere também.
8. **Ease com `influence` sozinho deixa Position (espacial) linear.** Usar `key(prop,t,v,"ease")`
   da biblioteca, que já aplica `setTemporalEaseAtKey` com a aridade certa da propriedade.
9. **Não existe apagar keyframe** de forma confiável — para anular um movimento, sobrescreva
   com o valor neutro.
10. **AE em português**: `findMenuCommandId('Undo')` devolve 0 e `executeCommand(0)` falha calado.
    Usar id numérico (Desfazer = 16) e **provar** por assinatura do projeto antes/depois.
11. **Em expressão, ler controle por ÍNDICE**: `effect("Valor")(1)` — "Slider" vira
    "Controle deslizante" no PT-BR e a expressão quebra.

12. **Script pesado passa dos 3 min e o runner desiste antes.** 458 camadas de legenda × 6 keyframes
    levaram mais de 180 s; o `rodar.sh` voltou "SEM LOG" com o AE ainda trabalhando, e o
    DoScriptFile seguinte **colidiu** com o que rodava (não executou, sem erro). Sintomas que
    enganam: os frames do script existem mas o log não. Padrão novo: timeout de 600 s, e antes de
    concluir que o AE travou, mandar um script de uma linha (`log("ping")`) com `MVJ_TIMEOUT=45`
    — se ele responde, o AE está vivo e o anterior só demorou. **Salvar o projeto nesse ping.**

13. **`set -o pipefail` + `grep` sem resultado = runner morre calado.** O laço que espera os frames
    prometidos fazia `grep … | while`; num script que não exporta frame o grep devolve 1, o pipefail
    propaga e o `rodar.sh` sai com 1 **depois** de imprimir o log — quem chama com `set -e` aborta
    ali (a finalização do AD04 morreu logo após o save). Cercar o grep com `{ … || true; }`.

## Efeitos deste AE

Funcionam: `ADBE Ramp`, `ADBE Drop Shadow`, `ADBE Gaussian Blur 2`, `ADBE Noise`, `ADBE Tint`,
`ADBE Glo2`, `CC Vignette`, `ADBE Easy Levels2`.
Recusados: `ADBE Levels2` (usar Easy Levels2), `ADBE Add Grain` (usar `ADBE Noise`),
`ADBE Stereo Mixer`.

## Render

```bash
"/Applications/Adobe After Effects 2026/aerender" -project X.aep -comp "NOME" -output Y.mp4
```

O `aerender` lê o **arquivo em disco** — salvar antes (`app.project.save()`), sempre.
**Não usar `-reuse`** (falha com AESend error -1712) nem `-OMtemplate` (os nomes padrão da Adobe
não existem nesta instalação; o módulo default já dá H.264 1080p + AAC).
Referência: 38 s de 1080x1920 com 8 precomps ≈ 1 min.

## Render — o que já quebrou

- **Dois `aerender` no mesmo arquivo de saída** → MP4 de 41 MB **sem moov atom** e log vazio.
  Causa real: eu achei que a rodada anterior tinha morrido porque o pipe `… 2>&1 | grep` **mascara
  o código de saída** do script (o do grep é o que aparece), e disparei uma segunda. Regra: nunca
  concluir "morreu" pelo exit de um pipe; conferir `pgrep -f aerender` antes de renderizar.
  `lib/render.sh` já recusa rodar com aerender vivo e valida a saída com ffprobe.

## Tools PRO (porta 7843)

Catálogo atual: `ae_organizar(_info)`, `ae_smoothify(_info,_resetar)`,
`ae_legendas_importar(_info,_limpar)`, `ae_titulos_info/_inserir`. **Nenhuma cria camada** —
a construção é por ExtendScript; o Tools PRO entra para legenda e para ler a comp de volta.

- O servidor é de **escopo local ao diretório**: `claude mcp get toolspro-ae` só responde com o
  cwd na pasta onde o Tools PRO foi registrado (a HOME do usuário, no registro padrão).
  Fora dali o token "some" e o curl devolve
  `{"error":"token ausente ou invalido"}` — parece token expirado, mas é cwd errado.
  Extrair o token uma vez para um arquivo 600 e reutilizar.
- `ae_legendas_importar` age na comp **ativa** — `comp.openInViewer()` antes.
- `ae_smoothify` pode responder *"carregou … mas smAplicar nao esta no escopo global do host"*:
  é bug da própria ferramenta, não do projeto. Aplicar o ease por script.
- **`ae_organizar` refaz a árvore por tipo** — não usar quando a demanda define a estrutura.

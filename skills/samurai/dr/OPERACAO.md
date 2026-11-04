# Operação da Agência Samurai DR

Versão 1 · 22/10/2026 · modo PRODUTOR · Fase 1 ativa.
Arquitetura completa (diagnóstico, organograma, fontes): https://claude.ai/artifact/JhGTKGaCFkk6YfARXL4h6H

## Decisões já tomadas (não perguntar de novo)

| Decisão | Valor | Quem decidiu |
|---|---|---|
| Modo | PRODUTOR ( + rede HWAffiliate). Afiliado fica para depois. | usuário, 22/10/2026 |
| Onde moram os papéis | `~/.claude/skills/samurai/dr/papeis/`, despachados como `general-purpose`. Nada em `~/.claude/agents/`. | usuário, 22/10/2026 |
| Produção | Dividida em **IA Creator** (gera) e **Editor de Vídeo** (monta). Acessos e ferramentas diferentes, e rodam em paralelo. | usuário pediu os dois papéis, 22/10/2026 |
| Donos dos gates | usuário nos três, até ele nomear outra pessoa (G2 tende a ir para o copywriter do produto). | padrão do Samurai |
| Prazo dos gates | G1 no mesmo dia · G2 em 24 h · G3 em 24 h. Passou do prazo: lembrar uma vez e deixar a demanda parada. | padrão do Samurai |
| Teto de gasto sem novo gate | o valor que o usuário aprovar no G1, em créditos do HWStudio/HeyGen/ElevenLabs | por demanda |

Pendentes (bloqueiam a Fase 2, não a Fase 1): acesso de leitura aos dados de mídia; significado do RCC.csv e ID de afiliado da casa; paradeiro de `<arquivo local da referência>`.

## Fases

- **Fase 1 (ativa):** Samurai · Inteligência · Criativo · Revisor · IA Creator · Editor de Vídeo. Entrega criativo pesquisado, revisado e pronto para o tráfego testar. Não fecha o loop com dado.
- **Fase 2 (inativa, falta dado):** Oferta · Performance. Entram quando houver export de mídia por `ad.id` + RCC + rastreamento (ad.id até o checkout, postback S2S com reembolso, CAPI).
- **Fase 3 (inativa, falta acesso):** Funis · Pós-venda e Voz do Cliente · Parcerias de Afiliados.

Se o gargalo de uma demanda cair num papel inativo, diga isso ao usuário com o que falta. Não simule o papel.

## Fluxo da Fase 1

```
pedido
 └─ Samurai: abre _SAMURAI/, 00_briefing.md, declara gargalo (FATO|HIPÓTESE)
     └─ G1 (escopo, formato, teto de gasto)
         └─ Inteligência → 01_pesquisa/evidencias.md
             └─ Criativo → 03_matriz.md + 04_copy/
                 └─ Revisor (pré) → 06_revisao_pre.md
                     └─ G2 (matriz + roteiros, com os vermelhos marcados)
                         ├─ IA Creator → ativos gerados (avatar, voz, start frames, b-roll)
                         └─ Editor de Vídeo → montagem, legenda, motion, render
                             └─ Revisor (pós) → 06_revisao_pos.md
                                 └─ G3 (corte final)
                                     └─ Samurai: pacote para o tráfego + fecha ledger + aprendizados
```

Atalhos legítimos:
- **Demanda só de produção** (copy já aprovada pelo copywriter, ex.: doc de copy com Body 1..N): pule Inteligência e Criativo. Revisor (pré) roda sobre a copy recebida. G2 vira só "ok nos vermelhos".
- **Variação de criativo existente** (troca de hook, de personagem, de pote): Criativo faz matriz curta; Inteligência só se faltar evidência.
- **Pedido de análise** (dissecar ref, conferir AD): não é demanda de agência — vá direto na skill.

Antes de aceitar "fadiga de criativo" como gargalo, pergunte ao usuário/tráfego: pixel, postback ou CAPI quebraram? CPM ou sazonalidade mudaram? A retenção da VSL caiu? Queda de conversão registrada pode ser só rastreio parado.

## Gates

| Gate | O que se aprova junto | Dono | Prazo |
|---|---|---|---|
| G1 · Escopo | gargalo, formato (AD, VSL, Microlead, Upsell, Lead), quantidade, prazo e teto de gasto de produção | usuário | mesmo dia |
| G2 · Matriz e copy | matriz de testes + roteiros, com os vermelhos do Revisor pré já marcados | usuário (ou copywriter do produto) | 24 h |
| G3 · Corte final | vídeos aprovados pelo Revisor pós | usuário | 24 h |

Extra: gasto de geração acima do teto do G1 abre aprovação própria (mostre o `hwstudio_estimar` antes). Publicar, definir orçamento de mídia, pausar e escalar são do gestor de tráfego, fora da agência.

Junte as aprovações numa mensagem só, curta, com o que precisa de resposta em lista numerada.

## Pasta da demanda

A demanda vive na pasta do job em produção:
`Drive: - Edição de Vídeo -Q3/Arquivo de Edição /{NN. Nicho EN}/{Produto}/{OT|DTC|Offer}/{demanda}/` (atenção ao espaço depois de "Edição"; a pasta do job é criada pelo `replicador-hw` ou pelo usuário). Dentro dela:

```
_SAMURAI/
  00_briefing.md        (modelo em dr/modelos/briefing.md)
  ledger.md             (modelo em dr/modelos/ledger.md)
  01_pesquisa/evidencias.md + dissecações
  03_matriz.md
  04_copy/
  06_revisao_pre.md · 06_revisao_pos.md
  aprendizados.md       (o que esta demanda ensinou, para a próxima)
EXPORT/ FOOTAGE/ PROJECT/ MEDIA/...   (estrutura de sempre, dos papéis de produção)
```

Se ainda não houver pasta do job, use `<pasta de trabalho>/_SAMURAI/{demanda}/` e diga onde ficou. Nunca o scratchpad para o que for entregável.

## Contrato de handoff

Só entre papéis diferentes (dentro do mesmo papel, basta o gate). Modelo em `dr/modelos/handoff.md`. Os campos: objetivo, contexto, evidências, arquivos, restrições, responsável, conclusão, pendências. Handoff sem critério de conclusão objetivo não sai.

## Ledger e custo

Cada demanda tem `ledger.md` com: gerações (ferramenta, quantidade, créditos), tokens/tempo por papel despachado, retrabalho (o que foi refeito e por quê), decisões de gate com data. É daqui que sai o custo real de produção por conceito testado.

Teto de pesquisa por demanda: Inteligência com no máximo 4 subagentes, e só em produto ou ângulo novo.

## Biblioteca de aprendizados

`aprendizados.md` da demanda registra, por linha: o que se tentou, o que aconteceu, tipo (FATO medido | HIPÓTESE), fonte. Hoje quase tudo será de produção (o que deu retrabalho, o que o Revisor barrou, o que o usuário recusou no G3) — isso é aprendizado real e vale. Resultado de mídia só entra quando a Fase 2 existir.

## Referências da casa que todo papel pode ler

- `dr/checklist-alegacoes.md` — FTC, Meta e plataformas, com data de revisão.
- `dr/padroes-de-formato.md` — o que os criativos, VSLs e microleads finalizados da casa têm em comum (medido em vídeos reais).
- `~/.claude/skills/boas-praticas-black-belt/SKILL.md` — armadilhas por ferramenta.
- Memórias do usuário em `a memória do Claude` (índice em `MEMORY.md`).

"""
O leitor do stream-json do `claude -p` (nucleo/leitor_stream.py).

Duas gravações em testes/dados/:

- `stream-ok-real.jsonl` — saída DE VERDADE do CLI 2.1.x para "responda só
  OK", com `--include-partial-messages` (hooks e caminhos da máquina tirados).
  É ela que prova a ordem real dos eventos: o `assistant` de um bloco chega
  ANTES do `content_block_stop`, e o pensamento vem vazio (só a assinatura).
- `stream-ferramentas-sintetico.jsonl` — montada no MESMO formato, com
  TodoWrite, Read com resultado em lista, o portão do pipeline recusando,
  Bash com erro e texto de subagente. Sintética porque rodar o CLI com
  ferramentas de verdade dentro da banca não é aceitável (gasta e mexe em
  disco).

E o caminho sem a flag: as mesmas gravações SEM os `stream_event` têm que
dar o mesmo resultado final — é o que acontece num CLI antigo.
"""

import json
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from nucleo import conversa  # noqa: E402
from nucleo.leitor_stream import LeitorClaude, tarefas_de  # noqa: E402

DADOS = os.path.join(RAIZ, "testes", "dados")


def linhas(nome, sem_pedacos=False):
    with open(os.path.join(DADOS, nome), encoding="utf-8") as f:
        for l in f:
            if sem_pedacos and json.loads(l).get("type") == "stream_event":
                continue
            yield l


class Relogio:
    """Tempo falso: cada evento avança 0,5 s — dá para afirmar durações."""
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        self.t += 0.5
        return self.t


def ler(nome, sem_pedacos=False):
    eventos = []
    lt = LeitorClaude(eventos.append, relogio=Relogio())
    for l in linhas(nome, sem_pedacos):
        lt.linha(l)
    lt.finalizar()
    return lt, eventos


class GravacaoReal(unittest.TestCase):

    def test_resposta_e_uso(self):
        lt, ev = ler("stream-ok-real.jsonl")
        self.assertTrue(lt.conectado)
        self.assertEqual(lt.fala(), "OK")
        self.assertIsNone(lt.erro)
        self.assertEqual(lt.uso["tokens_saida"], 51)
        self.assertEqual(lt.uso["tokens_entrada"], 10 + 14089 + 22376)
        self.assertAlmostEqual(lt.uso["custo_usd"], 0.0316266, places=6)
        self.assertEqual(lt.uso["turnos"], 1)
        self.assertTrue(lt.uso["modelo"].startswith("claude-haiku"))

    def test_texto_aparece_aos_pedacos_antes_do_fim(self):
        lt, ev = ler("stream-ok-real.jsonl")
        # primeiro um passo "parcial", depois a mesma posição vira "texto"
        parciais = [e for e in ev if e.get("tipo") == "parcial"]
        self.assertTrue(parciais, "a tela não recebeu o texto enquanto era escrito")
        atualizados = [e for e in ev if e.get("atualiza") and e.get("tipo") == "texto"]
        self.assertTrue(atualizados)
        self.assertEqual(atualizados[-1]["texto"], "OK")
        # e não duplicou: um texto só no fim
        self.assertEqual([p["tipo"] for p in lt.passos if p["tipo"] == "texto"], ["texto"])

    def test_pensamento_vazio_mostra_so_a_duracao(self):
        lt, _ = ler("stream-ok-real.jsonl")
        pens = [p for p in lt.passos if p["tipo"] == "pensando"]
        self.assertEqual(len(pens), 1)
        self.assertEqual(pens[0]["estado"], "ok")
        self.assertGreater(pens[0]["dur"], 0)
        self.assertEqual(pens[0]["texto"], "")

    def test_sem_a_flag_o_resultado_e_o_mesmo(self):
        lt, ev = ler("stream-ok-real.jsonl", sem_pedacos=True)
        self.assertEqual(lt.fala(), "OK")
        self.assertFalse([e for e in ev if e.get("tipo") == "parcial"])


class ComFerramentas(unittest.TestCase):

    def setUp(self):
        self.lt, self.ev = ler("stream-ferramentas-sintetico.jsonl")
        self.ferr = {p["nome"]: p for p in self.lt.passos if p["tipo"] == "ferramenta"}

    def test_ordem_intercalada(self):
        tipos = [(p["tipo"], p.get("nome")) for p in self.lt.passos]
        self.assertEqual(tipos, [
            ("pensando", None), ("texto", None), ("ferramenta", "TodoWrite"),
            ("ferramenta", "Read"), ("ferramenta", "mcp__editor__etapa_rodar"),
            ("ferramenta", "Bash"), ("texto", None)])

    def test_texto_de_subagente_nao_entra_na_resposta(self):
        self.assertNotIn("subagente", self.lt.fala())
        self.assertEqual(self.lt.fala(),
                         "Vou organizar o trabalho.\n\nA etapa de imagens **precisa da sua aprovação**.")

    def test_tarefas_do_todowrite(self):
        t = self.ferr["TodoWrite"]["tarefas"]
        self.assertEqual([x["estado"] for x in t], ["andamento", "pendente"])
        self.assertEqual(t[0]["ativo"], "Lendo a decupagem")
        self.assertEqual(tarefas_de({"todos": [{"content": "x", "status": "completed"}]}),
                         [{"texto": "x", "ativo": "x", "estado": "feito"}])

    def test_estado_duracao_e_resultado(self):
        r = self.ferr["Read"]
        self.assertEqual(r["estado"], "ok")
        self.assertEqual(r["entrada"], {"file_path": "/x/Projetos/AD07/decupagem.md"})
        self.assertGreater(r["dur"], 0)
        self.assertTrue(r["resultado"].startswith("# Decupagem"))
        self.assertLessEqual(len(r["resultado"]), 4001)     # truncado para a tela
        self.assertLessEqual(len(r["saida"]), 111)
        b = self.ferr["Bash"]
        self.assertEqual(b["estado"], "erro")
        self.assertIn("No such file", b["resultado"])

    def test_recusa_do_portao_vira_marca(self):
        m = self.ferr["mcp__editor__etapa_rodar"]
        self.assertTrue(m["recusado"])
        self.assertIn("gasta crédito", m["porque"])
        self.assertEqual(m["estado"], "ok")      # a ferramenta respondeu; quem disse não foi o portão

    def test_uso(self):
        u = self.lt.uso
        self.assertEqual(u["tokens_entrada"], 43120)
        self.assertEqual(u["tokens_saida"], 512)
        self.assertEqual(u["duracao_ms"], 8123)

    def test_tela_recebe_a_ferramenta_antes_do_resultado(self):
        # o passo nasce "rodando" no content_block_start e é ATUALIZADO depois
        nascidos = [e for e in self.ev if e.get("tipo") == "ferramenta" and not e.get("atualiza")]
        self.assertEqual([e["estado"] for e in nascidos], ["rodando"] * 4)
        idx_read = [i for i, e in enumerate(self.ev) if e.get("nome") == "Read"]
        self.assertEqual(self.ev[idx_read[-1]]["estado"], "ok")

    def test_sem_a_flag_da_o_mesmo_fim(self):
        lt, _ = ler("stream-ferramentas-sintetico.jsonl", sem_pedacos=True)
        self.assertEqual(lt.fala(), self.lt.fala())
        self.assertEqual([(p["tipo"], p.get("nome"), p.get("estado")) for p in lt.passos],
                         [(p["tipo"], p.get("nome"), p.get("estado")) for p in self.lt.passos])

    def test_linha_ruim_nao_derruba(self):
        lt = LeitorClaude()
        self.assertIsNone(lt.linha("isto não é json"))
        self.assertIsNone(lt.linha(""))
        lt.linha('{"type":"user","message":{"content":"texto solto"}}')
        self.assertEqual(lt.finalizar(), [])

    def test_processo_morto_no_meio_marca_interrompido(self):
        lt = LeitorClaude()
        for l in list(linhas("stream-ferramentas-sintetico.jsonl"))[:22]:
            lt.linha(l)
        ps = lt.finalizar()
        self.assertTrue(any(p.get("estado") == "interrompido" for p in ps), ps)
        self.assertFalse(any(p["tipo"] == "parcial" for p in ps))


class GuardadoNoHistorico(unittest.TestCase):

    def test_texto_vai_junto_e_vazio_nao(self):
        ps = [{"tipo": "texto", "texto": "a"}, {"tipo": "parcial", "texto": "b"},
              {"tipo": "texto", "texto": "  "}, {"tipo": "ferramenta", "nome": "Read"}]
        self.assertEqual(conversa._passos_guardados(ps),
                         [{"tipo": "texto", "texto": "a"}, {"tipo": "ferramenta", "nome": "Read"}])

    def test_cli_antigo_recusa_a_flag(self):
        self.assertTrue(conversa._recusou_parciais(
            "error: unknown option '--include-partial-messages'"))
        self.assertFalse(conversa._recusou_parciais("No conversation found with session ID"))


if __name__ == "__main__":
    unittest.main()

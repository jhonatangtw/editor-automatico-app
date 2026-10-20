"""Reabrir uma etapa não apaga o histórico: as aprovações antigas ficam
registradas como invalidadas e deixam de liberar o que vem depois."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nucleo import pipeline  # noqa: E402


def _ate_plano_aprovado():
    est = pipeline.novo()
    for eid in ("analise", "copy", "marcacao", "plano"):
        pipeline.iniciar(est, eid)
        pipeline.entregar(est, eid, {})
        pipeline.aprovar(est, eid, "Aluna", "ok " + eid)
    return est


class TestReabrir(unittest.TestCase):
    def test_aprovacoes_ficam_registradas_e_invalidadas(self):
        est = _ate_plano_aprovado()
        self.assertTrue(pipeline.aprovada(est, "plano"))
        antes = len(est["aprovacoes"])

        pipeline.reabrir(est, "marcacao", "Aluna", "mudar marcação")

        # nada some: as 4 aprovações + o registro da reabertura
        self.assertEqual(len(est["aprovacoes"]), antes + 1)
        por = {a["etapa"]: a for a in est["aprovacoes"] if a["acao"] == "aprovou"}
        self.assertNotIn("invalidada", por["analise"])
        self.assertNotIn("invalidada", por["copy"])
        self.assertTrue(por["marcacao"]["invalidada"])
        self.assertTrue(por["plano"]["invalidada"])
        self.assertEqual(est["aprovacoes"][-1]["acao"], "reabriu")
        self.assertNotIn("invalidada", est["aprovacoes"][-1])

        # e deixam de valer
        self.assertFalse(pipeline.aprovada(est, "plano"))
        self.assertFalse(pipeline.aprovada(est, "marcacao"))
        self.assertTrue(pipeline.aprovada(est, "copy"))

    def test_gasto_volta_a_travar_ate_nova_aprovacao(self):
        est = _ate_plano_aprovado()
        pipeline.reabrir(est, "plano", "Aluna")
        pipeline.iniciar(est, "plano")
        pipeline.entregar(est, "plano", {})
        # plano entregue de novo, mas a aprovação velha não libera o avatar
        with self.assertRaises(pipeline.Bloqueado):
            pipeline.iniciar(est, "avatar")
        pipeline.aprovar(est, "plano", "Aluna", "novo ok")
        pipeline.iniciar(est, "avatar")      # agora passa

    def test_painel_mostra_o_historico(self):
        est = _ate_plano_aprovado()
        pipeline.reabrir(est, "plano", "Aluna")
        hist = pipeline.painel(est)["aprovacoes"]
        self.assertTrue(any(a.get("invalidada") for a in hist))


if __name__ == "__main__":
    unittest.main()

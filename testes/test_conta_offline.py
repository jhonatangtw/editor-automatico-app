"""Modo offline da conta: token inventado + servidor fora do ar NÃO entra; quem
confirmou o acesso há menos de 7 dias, com o mesmo token, continua trabalhando."""
import os
import sys
import time
import unittest
import urllib.error
from unittest import mock

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import app  # noqa: E402
from nucleo import conta, pipeline, projetos  # noqa: E402
from testes.test_area_do_aluno import Base, SERVIDOR  # noqa: E402

FORA = urllib.error.URLError("sem rede")
VALE = {"ok": True, "usuario": {"nome": "Aluna", "email": "a@b.com"}}


class TestOffline(Base):
    def setUp(self):
        super().setUp()
        conta._CACHE.update(quando=0.0, token="")

    def test_token_inventado_offline_nao_entra(self):
        self.sessao(bb_acesso_token="TOKEN-INVENTADO", bb_acesso_nome="Qualquer Um")
        self.usar_http({SERVIDOR + "/api/sessao": FORA})
        e = conta.estado()
        self.assertFalse(e["entrou"])
        self.assertTrue(e["offline"])
        self.assertIn("internet", e["msg"])

    def test_confirmado_ha_pouco_continua_offline(self):
        self.sessao(bb_acesso_token="tk-bom")
        self.usar_http({SERVIDOR + "/api/sessao": VALE})
        self.assertTrue(conta.estado()["entrou"])          # confirmação boa
        self.usar_http({SERVIDOR + "/api/sessao": FORA})
        e = conta.estado()
        self.assertTrue(e["entrou"])
        self.assertTrue(e["offline"])

    def test_confirmacao_velha_pede_conexao(self):
        self.sessao(bb_acesso_token="tk-bom")
        self.usar_http({SERVIDOR + "/api/sessao": VALE})
        conta.estado()
        oito_dias = time.time() + 8 * 86400
        self.usar_http({SERVIDOR + "/api/sessao": FORA})
        with mock.patch("time.time", return_value=oito_dias):
            self.assertFalse(conta.estado()["entrou"])

    def test_token_trocado_nao_herda_a_confirmacao(self):
        self.sessao(bb_acesso_token="tk-bom")
        self.usar_http({SERVIDOR + "/api/sessao": VALE})
        conta.estado()
        d = conta._ler()
        d[conta.CH_TOKEN] = "tk-outro"
        conta._gravar(d)
        self.usar_http({SERVIDOR + "/api/sessao": FORA})
        self.assertFalse(conta.estado()["entrou"])

    def test_login_marca_confirmacao(self):
        self.usar_http({SERVIDOR + "/api/login": {"ok": True, "token": "tk-novo",
                                                  "usuario": {"nome": "A"}}})
        self.assertTrue(conta.entrar("a@b.com", "senha123")["ok"])
        self.usar_http({SERVIDOR + "/api/sessao": FORA})
        self.assertTrue(conta.estado()["entrou"])

    def test_sair_apaga_a_confirmacao(self):
        self.sessao(bb_acesso_token="tk-bom")
        self.usar_http({SERVIDOR + "/api/sessao": VALE, SERVIDOR + "/api/sair": {"ok": True}})
        conta.estado()
        conta.sair()
        self.assertNotIn(conta.CH_VALIDADO_EM, conta._ler())

    # -------------------------------------------------------------- exigir
    def test_exigir_recusa_sem_sessao(self):
        with self.assertRaises(conta.SemAcesso):
            conta.exigir()

    def test_exigir_usa_cache(self):
        self.sessao(bb_acesso_token="tk-bom")
        f = self.usar_http({SERVIDOR + "/api/sessao": VALE})
        conta.exigir()
        conta.exigir()
        self.assertEqual(len(f.para("/api/sessao")), 1)

    def test_etapa_sem_sessao_nao_roda(self):
        """O portão do pipeline passa, mas a conta não: nada é gravado."""
        tmp = self.tmp
        with mock.patch.object(projetos, "RAIZ", os.path.join(tmp, "Projetos")):
            pid = "p-1"
            projetos._gravar(projetos.caminho(pid, "plano.json"), {"job": "x", "beats": []})
            projetos._gravar(projetos.caminho(pid, "pipeline.json"), pipeline.novo())
            antes = projetos.estado_pipeline(pid)
            self.usar_http({SERVIDOR + "/api/sessao": FORA})
            with self.assertRaises(conta.SemAcesso):
                app.rota_etapa_iniciar(pid, pipeline.ORDEM[0], {})
            self.assertEqual(projetos.estado_pipeline(pid), antes)


if __name__ == "__main__":
    unittest.main()

"""fonte(): `ant` instalado sem login não pode passar na frente da chave do cofre."""
import os
import unittest
from unittest import mock

from nucleo import claude, chaves

SEM_LOGIN = ("Active profile: default (fallback — no active_config set)\n"
             "Config dir:      /x/.config/anthropic\n")
LOGADO = ("Active profile:  default (from active_config file)\n"
          "Credentials\n  (active) * Profile (user_oauth) [via active_config]  sk-ant-oat01-...\n")


def _cli_falso(status, token):
    def f(*args, timeout=40):
        if args[:2] == ("auth", "status"):
            return status, None
        if args[:2] == ("auth", "print-credentials"):
            return (token, None) if token else (None, "sem credencial")
        return "", None
    return f


class TestFonte(unittest.TestCase):
    def setUp(self):
        self.env = mock.patch.dict(os.environ, {}, clear=False)
        self.env.start()
        for v in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN"):
            os.environ.pop(v, None)
        self.cofre = mock.patch.object(
            chaves, "ler", lambda s: "sk-ant-api03-TESTE" if s == "claude" else None)
        self.cofre.start()

    def tearDown(self):
        self.cofre.stop()
        self.env.stop()

    def test_sem_login_cai_na_chave(self):
        with mock.patch.object(claude, "_cli", _cli_falso(SEM_LOGIN, None)):
            self.assertEqual(claude.fonte()[0], "chave")
            cab, como = claude._cabecalhos()
            self.assertEqual(cab["x-api-key"], "sk-ant-api03-TESTE")
            self.assertEqual(como, "chave de API")

    def test_status_sem_fallback_mas_sem_token_cai_na_chave(self):
        with mock.patch.object(claude, "_cli", _cli_falso(LOGADO, None)):
            self.assertEqual(claude.fonte()[0], "chave")

    def test_logado_de_verdade_e_perfil(self):
        with mock.patch.object(claude, "_cli", _cli_falso(LOGADO, "sk-ant-oat01-abc")):
            origem, detalhe = claude.fonte()
            self.assertEqual(origem, "perfil")
            self.assertNotIn("profile", detalhe.lower())  # texto em português
            cab, _ = claude._cabecalhos()
            self.assertEqual(cab["Authorization"], "Bearer sk-ant-oat01-abc")

    def test_estado_sem_nada(self):
        with mock.patch.object(claude, "_cli", _cli_falso(SEM_LOGIN, None)), \
             mock.patch.object(chaves, "ler", lambda s: None):
            self.assertFalse(claude.estado()["pronto"])


if __name__ == "__main__":
    unittest.main()

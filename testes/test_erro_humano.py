"""Erro que vai para a tela: português, sem caminho da máquina, sem jargão."""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app  # noqa: E402
from nucleo import ambiente  # noqa: E402
from unittest import mock  # noqa: E402


class TestErroHumano(unittest.TestCase):
    def test_traducoes(self):
        h = app.erro_humano
        self.assertEqual(h(FileNotFoundError(2, "x", os.path.join(app.projetos.RAIZ, "p", "plano.json"))),
                         "Projeto não encontrado.")
        self.assertIn("Pedido inválido", h(json.JSONDecodeError("Expecting value", "", 0)))
        self.assertEqual(h(KeyError("servico")), "Pedido inválido: faltou o campo “servico”.")
        self.assertNotIn("NoneType", h(TypeError("'NoneType' object is not subscriptable")))

    def test_sem_caminho_absoluto(self):
        m = app.erro_humano(ValueError("Não achei /Users/fulano/Documents/job/body.mp4, confira."))
        self.assertEqual(m, "Não achei body.mp4, confira.")
        self.assertNotIn("/Users", app.erro_humano(FileNotFoundError(2, "x", "/Users/a/b.mp4")))

    def test_versao_sem_aviso_em_ingles(self):
        r = mock.Mock(stdout="Warning: could not connect to a running Ollama instance\n"
                             "ollama version is 0.12.0\n", stderr="")
        with mock.patch.object(ambiente.so, "run", return_value=r):
            self.assertEqual(ambiente._versao(["ollama", "--version"]), "ollama version is 0.12.0")


if __name__ == "__main__":
    unittest.main()

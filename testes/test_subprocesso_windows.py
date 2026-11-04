"""No Windows TODO subprocesso nasce sem janela e lê UTF-8 — inclusive `subprocess.run` direto,
que não passa pelo `so.run`. Sem isso o terminal pisca a cada 15 s (checagem de contas) e acento vira "Ã£"."""
import importlib
import platform
import subprocess
import unittest
from unittest import mock

from nucleo import so

NO_WINDOW = 0x08000000


class TestSubprocessoWindows(unittest.TestCase):
    def setUp(self):
        self.recebido = []
        original = subprocess.Popen.__init__

        def gravar(_self, *a, **kw):
            self.recebido.append(kw)
            raise OSError("não executa no teste")

        self.p = [mock.patch.object(platform, "system", return_value="Windows"),
                  mock.patch.object(subprocess, "CREATE_NO_WINDOW", NO_WINDOW, create=True),
                  mock.patch.object(subprocess.Popen, "__init__", gravar)]
        for x in self.p:
            x.start()
        self.original = original
        importlib.reload(so)

    def tearDown(self):
        for x in reversed(self.p):
            x.stop()
        importlib.reload(so)
        self.assertIs(subprocess.Popen.__init__, self.original)

    def _rodar(self, **kw):
        with self.assertRaises(OSError):
            subprocess.run(["codex", "login", "status"], **kw)
        return self.recebido[-1]

    def test_run_direto_sem_janela_e_utf8(self):
        kw = self._rodar(capture_output=True, text=True)
        self.assertEqual(kw["creationflags"], NO_WINDOW)
        self.assertEqual(kw["encoding"], "utf-8")

    def test_binario_nao_ganha_encoding(self):
        kw = self._rodar(capture_output=True)
        self.assertEqual(kw["creationflags"], NO_WINDOW)
        self.assertNotIn("encoding", kw)

    def test_flag_explicita_e_respeitada(self):
        kw = self._rodar(creationflags=0x8)
        self.assertEqual(kw["creationflags"], 0x8)

    def test_recarregar_nao_embrulha_duas_vezes(self):
        embrulhado = subprocess.Popen.__init__
        importlib.reload(so)
        self.assertIs(subprocess.Popen.__init__, embrulhado)


if __name__ == "__main__":
    unittest.main()

"""O Node instalado fora do PATH do app tem de ser achado.

Alunos relataram "o Node está instalado e o app diz que não": nvm/fnm/volta se
registram no .zshrc (o shell de login não lê), o Homebrew não liga node@22, e
no Windows o Node instalado com o app aberto não entra no PATH do processo."""
import os
import shutil
import stat
import sys
import tempfile
import unittest
from unittest import mock

from nucleo import caminho


def _exe(pasta, nome):
    os.makedirs(pasta, exist_ok=True)
    p = os.path.join(pasta, nome)
    with open(p, "w") as f:
        f.write("#!/bin/sh\necho v22.0.0\n")
    os.chmod(p, os.stat(p).st_mode | stat.S_IEXEC)
    return p


@unittest.skipIf(sys.platform.startswith("win"), "cenário do Mac")
class TestNodeForaDoPath(unittest.TestCase):
    def setUp(self):
        self.casa = tempfile.mkdtemp()
        self.env = mock.patch.dict(os.environ, {"HOME": self.casa, "PATH": "/usr/bin:/bin"})
        self.env.start()
        os.environ.pop("NVM_DIR", None)
        self.shell = mock.patch.object(caminho, "_do_shell", return_value=[])
        self.shell.start()

    def tearDown(self):
        self.shell.stop()
        self.env.stop()
        shutil.rmtree(self.casa, ignore_errors=True)
        caminho._esquecer_which()

    def _pos(self, pasta):
        partes = os.environ["PATH"].split(":")
        return partes.index(pasta) if pasta in partes else -1

    def test_nvm_achado_na_versao_mais_nova(self):
        velho = os.path.join(self.casa, ".nvm/versions/node/v9.11.2/bin")
        novo = os.path.join(self.casa, ".nvm/versions/node/v22.11.0/bin")
        for d in (velho, novo):
            _exe(d, "node"); _exe(d, "npm")
        caminho._montar(com_shell=True)
        self.assertGreaterEqual(self._pos(novo), 0, os.environ["PATH"])
        self.assertLess(self._pos(novo), self._pos(velho))

    def test_instalado_com_app_aberto_aparece_no_recarregar(self):
        caminho._montar(com_shell=True)
        d = os.path.join(self.casa, ".volta/bin")
        self.assertEqual(self._pos(d), -1)
        _exe(d, "node"); _exe(d, "npm")
        r = caminho.recarregar()
        self.assertIn(d, r["novos"])

    def test_node_que_ja_funciona_continua_na_frente(self):
        primeiro = os.path.join(self.casa, "meu-node")
        _exe(primeiro, "npm")
        _exe(os.path.join(self.casa, ".nvm/versions/node/v22.0.0/bin"), "npm")
        os.environ["PATH"] = primeiro + ":/usr/bin:/bin"
        caminho._montar(com_shell=False)
        nvm = os.path.join(self.casa, ".nvm/versions/node/v22.0.0/bin")
        self.assertGreaterEqual(self._pos(nvm), 0)
        self.assertLess(self._pos(primeiro), self._pos(nvm))

    def test_ordem_das_versoes(self):
        v = caminho._versao_da_pasta
        self.assertGreater(v("v22.11.0"), v("v9.11.2"))
        self.assertGreater(v("node"), v("node@24"))
        self.assertGreater(v("node@24"), v("node@22"))


class TestWindows(unittest.TestCase):
    def test_pastas_do_instalador_oficial(self):
        with mock.patch.object(caminho.sys, "platform", "win32"), \
             mock.patch.dict(os.environ, {"ProgramFiles": r"C:\Program Files",
                                          "LOCALAPPDATA": r"C:\Users\a\AppData\Local",
                                          "NVM_SYMLINK": r"C:\nvm4w\nodejs"}):
            p = caminho._pastas_node()
        self.assertIn(os.path.join(r"C:\Program Files", "nodejs"), p)
        self.assertIn(r"C:\nvm4w\nodejs", p)

    def test_registro_fora_do_windows_nao_quebra(self):
        with mock.patch.object(caminho.sys, "platform", "darwin"):
            self.assertEqual(caminho._path_do_registro(), [])


if __name__ == "__main__":
    unittest.main()

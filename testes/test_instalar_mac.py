"""A troca do .app no Mac (nucleo/instalar_mac.py): o script que roda depois
que o app fecha. O que não pode acontecer é o aluno ficar sem app."""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from nucleo import instalar_mac as m  # noqa: E402


def app_falso(caminho, marca):
    os.makedirs(os.path.join(caminho, "Contents", "MacOS"))
    with open(os.path.join(caminho, "Contents", "marca"), "w") as f:
        f.write(marca)


def marca(caminho):
    with open(os.path.join(caminho, "Contents", "marca")) as f:
        return f.read()


@unittest.skipUnless(sys.platform == "darwin", "a troca é só do Mac")
class Troca(unittest.TestCase):

    def setUp(self):
        self.t = tempfile.mkdtemp()
        self.dest = os.path.join(self.t, "Aplicativos", m.NOME)
        app_falso(self.dest, "velho")
        # `open` falso: o teste não pode abrir app de verdade
        os.makedirs(os.path.join(self.t, "bin"))
        self.log = os.path.join(self.t, "aberto.log")
        with open(os.path.join(self.t, "bin", "open"), "w") as f:
            f.write('#!/bin/sh\necho "$@" >> "%s"\n' % self.log)
        os.chmod(os.path.join(self.t, "bin", "open"), 0o755)

    def tearDown(self):
        shutil.rmtree(self.t, ignore_errors=True)

    def trocar(self, novo, apagar=""):
        script = os.path.join(self.t, "troca.sh")
        with open(script, "w") as f:
            f.write(m.TROCA)
        env = dict(os.environ, PATH=os.path.join(self.t, "bin") + ":" + os.environ["PATH"])
        subprocess.run(["/bin/bash", script, "999999", novo, self.dest, apagar],
                       env=env, stderr=subprocess.DEVNULL, timeout=60)
        self.assertFalse(os.path.exists(script), "o script tem que se apagar")

    def test_troca_e_reabre(self):
        novo = os.path.join(self.t, "Aplicativos", ".EditorAutomatico-novo.app")
        app_falso(novo, "novo")
        self.trocar(novo)
        self.assertEqual(marca(self.dest), "novo")
        self.assertEqual(os.listdir(os.path.dirname(self.dest)), [m.NOME])
        self.assertIn(self.dest, open(self.log).read())

    def test_falha_devolve_o_antigo(self):
        self.trocar(os.path.join(self.t, "nao-existe.app"))
        self.assertEqual(marca(self.dest), "velho")
        self.assertEqual(os.listdir(os.path.dirname(self.dest)), [m.NOME])

    def test_mover_apaga_a_origem(self):
        orig = os.path.join(self.t, "Downloads", m.NOME)
        app_falso(orig, "novo")
        novo = os.path.join(self.t, "Aplicativos", ".EditorAutomatico-novo.app")
        shutil.copytree(orig, novo)
        self.trocar(novo, orig)
        self.assertEqual(marca(self.dest), "novo")
        self.assertFalse(os.path.exists(orig))


class Local(unittest.TestCase):

    def test_em_aplicativos(self):
        self.assertTrue(m.em_aplicativos("/Applications/" + m.NOME))
        self.assertTrue(m.em_aplicativos(os.path.expanduser("~/Applications/") + m.NOME))
        self.assertFalse(m.em_aplicativos(os.path.expanduser("~/Downloads/") + m.NOME))
        self.assertFalse(m.em_aplicativos("/private/var/folders/x/AppTranslocation/ABC/d/" + m.NOME))
        self.assertFalse(m.em_aplicativos(None))

    def test_desenvolvimento_nao_oferece_mover(self):
        # rodando pelo Python não há .app: nada a mover
        self.assertFalse(m.local()["fora"])


if __name__ == "__main__":
    unittest.main()

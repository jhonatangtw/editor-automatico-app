import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from nucleo import atualizacao  # noqa: E402

HDI = """image-path      : /Users/x/Downloads/EditorAutomatico-0.22.6.dmg
/dev/disk5s1\t41504653-0000\t/Volumes/Editor Automático
================================================
image-path      : /Users/x/Outro.dmg
/dev/disk6s1\tXX\t/Volumes/Outro
"""


class Limpar(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        for n in ("EditorAutomatico-0.21.2.dmg", "EditorAutomatico-0.22.7.dmg",
                  "EditorAutomatico-0.22.8.dmg", "EditorAutomatico.dmg", "Outro.dmg"):
            open(os.path.join(self.dir, n), "w").close()

    def _rodar(self, exe="/Applications/Editor Automático.app/Contents/MacOS/x"):
        chamadas = []

        def run(cmd, **k):
            chamadas.append(cmd)
            return mock.Mock(stdout=HDI if cmd[:2] == ["hdiutil", "info"] else "")
        with mock.patch.object(atualizacao.so, "MAC", True), \
             mock.patch.object(atualizacao, "local", return_value={"version": "0.22.7"}), \
             mock.patch("subprocess.run", side_effect=run):
            r = atualizacao.limpar_instaladores(self.dir, exe)
        return r, chamadas

    def test_ejeta_so_o_do_app_e_apaga_so_versoes_ja_instaladas(self):
        r, chamadas = self._rodar()
        self.assertEqual(r["ejetados"], ["/Volumes/Editor Automático"])
        self.assertIn(["hdiutil", "detach", "/Volumes/Editor Automático", "-quiet"], chamadas)
        self.assertEqual(sorted(os.listdir(self.dir)),
                         ["EditorAutomatico-0.22.8.dmg", "EditorAutomatico.dmg", "Outro.dmg"])

    def test_rodando_do_disco_nao_mexe(self):
        r, chamadas = self._rodar("/Volumes/Editor Automático/Editor Automático.app/Contents/MacOS/x")
        self.assertEqual(r, {"ejetados": [], "apagados": []})
        self.assertEqual(chamadas, [])
        self.assertEqual(len(os.listdir(self.dir)), 5)

    def test_windows_apaga_exe_velho_sem_hdiutil(self):
        for n in ("EditorAutomatico-0.22.5.exe", "EditorAutomatico-0.22.9.exe"):
            open(os.path.join(self.dir, n), "w").close()
        chamadas = []
        with mock.patch.object(atualizacao.so, "MAC", False), \
             mock.patch.object(atualizacao.so, "WIN", True), \
             mock.patch.object(atualizacao, "local", return_value={"version": "0.22.7"}), \
             mock.patch("subprocess.run", side_effect=lambda c, **k: chamadas.append(c)):
            r = atualizacao.limpar_instaladores(self.dir, r"C:\\Users\\x\\EditorAutomatico.exe")
        self.assertEqual(chamadas, [])
        self.assertEqual([os.path.basename(a) for a in r["apagados"]], ["EditorAutomatico-0.22.5.exe"])
        self.assertIn("EditorAutomatico-0.22.9.exe", os.listdir(self.dir))
        self.assertIn("EditorAutomatico-0.21.2.dmg", os.listdir(self.dir))


if __name__ == "__main__":
    unittest.main()

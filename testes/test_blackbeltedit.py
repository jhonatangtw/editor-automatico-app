"""BlackBeltEdit (beta): achar e abrir o app sem nunca levantar exceção."""

import os
import tempfile
import unittest
from unittest import mock

from nucleo import blackbeltedit


class TestBlackBeltEdit(unittest.TestCase):
    def test_sem_app_instalado_diz_isso(self):
        with mock.patch.object(blackbeltedit, "_lugares", return_value=["/nao/existe/BlackBeltEdit.app"]):
            e = blackbeltedit.estado()
            self.assertFalse(e["instalado"])
            self.assertTrue(e["beta"])
            r = blackbeltedit.abrir()
            self.assertFalse(r["ok"])
            self.assertIn("não está instalado", r["msg"] if blackbeltedit.so.MAC else "não está instalado")

    def test_le_versao_do_info_plist(self):
        import plistlib
        with tempfile.TemporaryDirectory() as d:
            app = os.path.join(d, "BlackBeltEdit.app")
            os.makedirs(os.path.join(app, "Contents"))
            with open(os.path.join(app, "Contents", "Info.plist"), "wb") as f:
                plistlib.dump({"CFBundleShortVersionString": "0.8.0"}, f)
            with mock.patch.object(blackbeltedit, "_lugares", return_value=[app]):
                e = blackbeltedit.estado()
                if blackbeltedit.so.MAC:
                    self.assertTrue(e["instalado"])
                    self.assertEqual(e["versao"], "0.8.0")

    def test_arquivo_inexistente_nao_abre(self):
        with mock.patch.object(blackbeltedit, "localizar", return_value="/Applications/BlackBeltEdit.app"):
            r = blackbeltedit.abrir("/nao/existe.fcproj")
            self.assertFalse(r["ok"])

    def test_plist_quebrado_nao_derruba(self):
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "Contents"))
            with open(os.path.join(d, "Contents", "Info.plist"), "wb") as f:
                f.write(b"\x00lixo")
            self.assertEqual(blackbeltedit._versao(d), "")


if __name__ == "__main__":
    unittest.main()

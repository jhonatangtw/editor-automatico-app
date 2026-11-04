"""FFmpeg sem drawtext ganha o botão de atualizar, o FFmpeg do app vence o do
sistema no PATH, e o Earshot aparece como opcional instalável."""
import os
import tempfile
import unittest
from unittest import mock

from nucleo import ambiente, caminho


class TestFFmpeg(unittest.TestCase):
    def _item(self, saida):
        r = mock.Mock(stdout=saida)
        with mock.patch.object(ambiente, "_tem", return_value=True), \
                mock.patch.object(ambiente, "_versao", return_value="ffmpeg version 9"), \
                mock.patch.object(ambiente.so, "run", return_value=r):
            return ambiente._ffmpeg()

    def test_sem_drawtext_oferece_atualizar(self):
        i = self._item(" .. loudnorm A->A\n")
        self.assertEqual(i["acoes"], ["atualizar"])
        self.assertTrue(i["tem"])     # continua funcionando para o resto

    def test_com_drawtext_nao_incomoda(self):
        self.assertNotIn("acoes", self._item(" T. drawtext V->V texto\n"))

    def test_sem_conseguir_perguntar_nao_acusa(self):
        with mock.patch.object(ambiente.so, "run", side_effect=OSError):
            self.assertTrue(ambiente._ffmpeg_tem_drawtext())


class TestPathDoApp(unittest.TestCase):
    def test_bin_do_app_vem_antes_do_shell(self):
        with tempfile.TemporaryDirectory() as home, \
                mock.patch.dict(os.environ, {"HOME": home, "PATH": "/usr/bin"}), \
                mock.patch.object(caminho, "_do_shell", return_value=["/usr/bin", "/bin"]), \
                mock.patch.object(caminho.sys, "platform", "darwin"):
            b = os.path.join(home, ".editorblackbelt", "bin")
            os.makedirs(b)
            self.assertEqual(caminho._montar(com_shell=True).split(":")[0], b)


class TestEarshot(unittest.TestCase):
    def test_opcional_e_instalavel(self):
        with mock.patch.object(ambiente, "_tem", return_value=False):
            i = ambiente._earshot()
        self.assertFalse(i["essencial"])
        self.assertTrue(i["instalavel"])

    def test_versao_fixada_sem_git(self):
        self.assertIn("/archive/", ambiente.EARSHOT)
        self.assertNotIn("git+", ambiente.EARSHOT)

    def test_instalar_despacha(self):
        with mock.patch.object(ambiente, "_instalar_earshot", return_value={"ok": True}) as f:
            ambiente._instalar("earshot")
        f.assert_called_once()


if __name__ == "__main__":
    unittest.main()

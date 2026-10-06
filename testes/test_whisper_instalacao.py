"""O Whisper não pode voltar a depender do pip3 da máquina (quebrava no Mac do aluno)."""
import os
import unittest
from unittest import mock

from nucleo import ambiente


class TestWhisperInstalacao(unittest.TestCase):
    def test_receitas_nao_usam_pip(self):
        for receitas in (ambiente.RECEITAS_MAC, ambiente.RECEITAS_WIN):
            self.assertNotIn("whisper", receitas)

    def test_instalar_whisper_passa_pelo_uv(self):
        with mock.patch.object(ambiente, "_instalar_whisper", return_value={"ok": True}) as f:
            self.assertEqual(ambiente.instalar("whisper"), {"ok": True})
            f.assert_called_once()

    def test_uv_instala_com_python_proprio_no_bin_do_app(self):
        chamadas = []

        def falso(cmd, ao_vivo=None, env=None, shell=False):
            chamadas.append((cmd, env or {}))
            return 0, ""
        with mock.patch.object(ambiente, "_achar_uv", return_value="/x/uv"), \
             mock.patch.object(ambiente, "_rodar", side_effect=falso), \
             mock.patch("shutil.which", return_value="/x/whisper"):
            ambiente._instalar_whisper()
        cmd, env = chamadas[0]
        self.assertEqual(cmd[:3], ["/x/uv", "tool", "install"])
        self.assertIn("3.12", cmd)
        self.assertEqual(env.get("UV_TOOL_BIN_DIR"), ambiente.BIN)

    def test_item_sempre_instalavel(self):
        itens = {i["id"]: i for i in ambiente.conferir(reler_path=False)["itens"]} \
            if isinstance(ambiente.conferir(reler_path=False), dict) else \
            {i["id"]: i for i in ambiente.conferir(reler_path=False)}
        self.assertTrue(itens["whisper"]["instalavel"])


if __name__ == "__main__":
    unittest.main()

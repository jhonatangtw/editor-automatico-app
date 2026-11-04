"""No Windows o login do Claude Code fica em ~/.claude/.credentials.json — nunca chamar `security`."""
import json
import os
import tempfile
import unittest
from unittest import mock

from nucleo import claude, so


class TestClaudeSessaoWindows(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.p = [mock.patch.object(so, "MAC", False), mock.patch.object(claude, "tem_claude_cli", return_value=True),
                  mock.patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": self.tmp})]
        for x in self.p:
            x.start()

    def tearDown(self):
        for x in self.p:
            x.stop()

    def test_logado_pelo_arquivo(self):
        with open(os.path.join(self.tmp, ".credentials.json"), "w") as f:
            json.dump({"claudeAiOauth": {"accessToken": "x", "subscriptionType": "max"}}, f)
        with mock.patch("subprocess.run", side_effect=FileNotFoundError("security")) as r:
            e = claude.sessao_cli()
            r.assert_not_called()
        self.assertTrue(e["ok"])
        self.assertEqual(e["assinatura"], "max")

    def test_sem_arquivo_pede_entrar(self):
        e = claude.sessao_cli()
        self.assertFalse(e["ok"])
        self.assertTrue(e.get("entrar"))
        self.assertNotIn("WinError", e["msg"])


if __name__ == "__main__":
    unittest.main()

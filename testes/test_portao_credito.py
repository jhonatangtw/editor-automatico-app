"""A Conversa roda o Claude com bypass de permissões — então o que gasta crédito
precisa estar BLOQUEADO na linha de comando, e as skills empacotadas precisam
dizer que gerar é só pelo pipeline do app."""
import importlib.util
import os
import re
import sys
import unittest
from unittest import mock

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from nucleo import conversa  # noqa: E402


def _valor(cmd, flag):
    return cmd[cmd.index(flag) + 1]


class TestArgumentosClaude(unittest.TestCase):
    def setUp(self):
        self.p = mock.patch.object(conversa, "_mcp_config", lambda: "/tmp/mcp.json")
        self.p.start()

    def tearDown(self):
        self.p.stop()

    def _cmd(self, **kw):
        return conversa.argumentos_claude("oi", "ctx", "sid-1", False, **kw)

    def test_bloqueia_os_comandos_que_gastam(self):
        bloq = _valor(self._cmd(), "--disallowedTools").split(",")
        for regra in ("Bash(higgsfield generate*)", "Bash(higgsfield *create*)",
                      "Bash(heygen*)", "Bash(mmx*)", "Bash(*higgsfield generate*)"):
            self.assertIn(regra, bloq)
        self.assertTrue(any("api.elevenlabs.io" in r for r in bloq))
        self.assertTrue(any("fal.run" in r for r in bloq))

    def test_nao_bloqueia_o_que_a_conversa_precisa(self):
        cmd = self._cmd()
        bloq = _valor(cmd, "--disallowedTools").split(",")
        self.assertNotIn("Bash", bloq)
        self.assertNotIn("mcp__editor", bloq)
        livre = _valor(cmd, "--allowedTools").split(",")
        for f in ("mcp__editor", "Bash", "Read", "Write", "Edit"):
            self.assertIn(f, livre)
        # cada regra é um padrão de Bash ou um servidor MCP — nada de vírgula solta
        for r in bloq:
            self.assertRegex(r, r"^(Bash\([^,()]+\)|mcp__[a-z0-9_-]+)$")

    def test_bloqueio_vale_tambem_retomando_e_so_nossas(self):
        cmd = conversa.argumentos_claude("oi", "ctx", "sid-1", True, so_nossas=True,
                                         parciais=False)
        self.assertIn("--disallowedTools", cmd)
        self.assertIn("--resume", cmd)
        self.assertIn("--strict-mcp-config", cmd)
        self.assertNotIn("--include-partial-messages", cmd)

    def test_regra_vem_depois_do_bypass(self):
        cmd = self._cmd()
        self.assertEqual(_valor(cmd, "--permission-mode"), "bypassPermissions")
        self.assertIn("--disallowedTools", cmd)


class TestSkillsAvisam(unittest.TestCase):
    def setUp(self):
        sp = importlib.util.spec_from_file_location(
            "limpar_skills", os.path.join(RAIZ, "limpar-skills.py"))
        self.ls = importlib.util.module_from_spec(sp)
        sp.loader.exec_module(self.ls)

    def test_skill_que_ensina_gerar_tem_o_aviso(self):
        raiz = os.path.join(RAIZ, "skills")
        for nome in ("editor-automatico-de-broll", "clone-ad-validado",
                     "advalidado-weightloss", "skill-black-belt"):
            with open(os.path.join(raiz, nome, "SKILL.md"), encoding="utf-8") as f:
                t = f.read()
            self.assertIn(self.ls.MARCA_AVISO, t, nome)
            self.assertIn("etapa_rodar", t, nome)
            # o aviso fica logo depois do cabeçalho, antes do texto da skill
            self.assertTrue(re.match(r"---\n.*?\n---\n\n?" + re.escape(self.ls.MARCA_AVISO),
                                     t, re.S), nome)

    def test_aviso_nao_duplica(self):
        import shutil
        import tempfile
        tmp = tempfile.mkdtemp()
        try:
            os.makedirs(os.path.join(tmp, "x"))
            with open(os.path.join(tmp, "x", "SKILL.md"), "w", encoding="utf-8") as f:
                f.write("---\nname: x\n---\n\n# X\n\nrode `higgsfield generate create kling`\n")
            self.assertEqual(self.ls.avisar_portao(tmp), 1)
            self.assertEqual(self.ls.avisar_portao(tmp), 0)
        finally:
            shutil.rmtree(tmp)


if __name__ == "__main__":
    unittest.main()

"""Conta do Higgsfield recém-criada (sem créditos/plano) tem que aparecer CONECTADA."""
import unittest
from types import SimpleNamespace
from unittest import mock

from nucleo import servicos


def _rodou(stdout, rc=0):
    return SimpleNamespace(returncode=rc, stdout=stdout, stderr="")


class TestHiggsStatus(unittest.TestCase):
    def test_conta_nova_sem_creditos_esta_conectada(self):
        with mock.patch.object(servicos.so, "run", return_value=_rodou('{"credits": null, "email": "a@b.c"}')):
            r = servicos._higgs_status()
        self.assertTrue(r["conectado"])
        self.assertEqual(r["conta"], "a@b.c")

    def test_saida_estranha_com_rc0_continua_conectada(self):
        with mock.patch.object(servicos.so, "run", return_value=_rodou("ok, logged in")):
            self.assertTrue(servicos._higgs_status()["conectado"])

    def test_saldo_com_casas_decimais(self):
        with mock.patch.object(servicos.so, "run", return_value=_rodou(
                '{"credits": 27532.52, "email": "x@y.z", "subscription_plan_type": "ultra"}')):
            r = servicos._higgs_status()
        self.assertEqual(r["saldo"], "27.532 créditos · plano ultra")

    def test_rc_diferente_de_zero_nao_conectado(self):
        with mock.patch.object(servicos.so, "run", return_value=_rodou("", rc=1)):
            self.assertFalse(servicos._higgs_status()["conectado"])


if __name__ == "__main__":
    unittest.main()

"""
Atualização LEVE: troca o código, não o app inteiro.

O app é Python + tela. Quase toda correção mexe em `nucleo/`, `web/` e `app.py`
— o interpretador e as dependências binárias mudam raramente. Mandar o editor
baixar 13 MB e reinstalar para receber uma correção de duas linhas é o tipo de
atrito que faz gente parar de atualizar; e app desatualizado é suporte.

Então: o app EMBUTIDO vira também um carregador. Se existir uma pasta de código
mais nova em `~/.editorblackbelt/app/<versao>`, é ela que roda — usando o
interpretador e as bibliotecas que vieram no pacote instalado.

As três travas, todas aprendidas do jeito difícil:

  * **Só código.** Versão que precise de dependência nova declara
    `precisa_instalador` no `version.json` e cai no caminho do instalador. Sem
    isso, um dia o código novo importaria algo que o pacote antigo não tem e o
    app não abriria mais — pior que não atualizar.

  * **Quarentena.** Antes de rodar código baixado, deixo uma marca no disco. O
    código novo apaga a marca quando consegue subir. Se na abertura seguinte a
    marca ainda estiver lá, é porque ele não subiu: o app IGNORA a pasta e volta
    para o embutido sozinho. Sem isso, uma atualização ruim tijola o app do
    aluno e ele não tem como voltar.

  * **Troca atômica.** Descompacta ao lado e só então renomeia. Extrair por cima
    da pasta em uso deixa metade do código novo com metade do velho — o defeito
    mais difícil de diagnosticar que existe.
"""

import hashlib
import json
import os
import shutil
import zipfile

BASE = os.path.expanduser("~/.editorblackbelt/app")
PONTEIRO = os.path.join(BASE, "ativo.json")
MARCA = os.path.join(BASE, "tentando.flag")
PARTES = ("app.py", "nucleo", "web", "version.json")


def _num(v):
    partes = []
    for p in str(v or "0").strip().lstrip("vV").split("."):
        d = "".join(c for c in p if c.isdigit())
        partes.append(int(d or 0))
    return tuple((partes + [0, 0, 0])[:3])


def ativo():
    """A pasta de código externa que deve rodar, ou None. Stdlib pura de
    propósito: isto roda ANTES de qualquer import do app."""
    try:
        with open(PONTEIRO, encoding="utf-8") as f:
            d = json.load(f)
        pasta = d.get("pasta")
        if not pasta or not os.path.isfile(os.path.join(pasta, "app.py")):
            return None
        return {"pasta": pasta, "versao": d.get("versao")}
    except Exception:
        return None


def em_quarentena():
    """Ficou marca da vez passada = o código externo não subiu."""
    return os.path.isfile(MARCA)


def marcar_tentativa(versao):
    os.makedirs(BASE, exist_ok=True)
    with open(MARCA, "w", encoding="utf-8") as f:
        f.write(str(versao or ""))


def deu_certo():
    """Chamado pelo código externo assim que ele consegue subir."""
    try:
        os.remove(MARCA)
    except OSError:
        pass


def descartar(porque=""):
    """Volta para o código embutido. É o que impede que uma atualização ruim
    deixe o aluno sem app."""
    try:
        os.remove(PONTEIRO)
    except OSError:
        pass
    deu_certo()
    return {"descartado": True, "porque": porque}


def instalar(zip_bytes, versao, sha256=None):
    """Grava a pasta nova e aponta para ela. Não mexe no que está rodando."""
    if sha256:
        visto = hashlib.sha256(zip_bytes).hexdigest()
        if visto.lower() != sha256.lower():
            raise RuntimeError(
                "O pacote baixado não confere com o publicado. Não vou instalar "
                "código que chegou diferente do que foi assinado na Release.")

    os.makedirs(BASE, exist_ok=True)
    destino = os.path.join(BASE, str(versao))
    tmp = destino + ".tmp"
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp, exist_ok=True)

    import io
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        nomes = z.namelist()
        for parte in PARTES:
            if not any(n == parte or n.startswith(parte + "/") for n in nomes):
                raise RuntimeError("O pacote de código veio sem “%s”." % parte)
        # zip com caminho para fora da pasta é ataque conhecido; extrai na mão
        for n in nomes:
            alvo = os.path.realpath(os.path.join(tmp, n))
            if not alvo.startswith(os.path.realpath(tmp) + os.sep):
                raise RuntimeError("O pacote tem caminho suspeito: " + n)
        z.extractall(tmp)

    try:
        with open(os.path.join(tmp, "version.json"), encoding="utf-8") as f:
            dentro = json.load(f).get("version")
    except Exception:
        dentro = None
    if dentro and _num(dentro) != _num(versao):
        raise RuntimeError("O pacote diz ser a versão %s, não a %s." % (dentro, versao))

    shutil.rmtree(destino, ignore_errors=True)
    os.replace(tmp, destino)

    tmpp = PONTEIRO + ".tmp"
    with open(tmpp, "w", encoding="utf-8") as f:
        json.dump({"versao": str(versao), "pasta": destino}, f)
    os.replace(tmpp, PONTEIRO)

    # guarda só as duas últimas — disco de editor vive cheio
    try:
        versoes = sorted((d for d in os.listdir(BASE)
                          if os.path.isdir(os.path.join(BASE, d))),
                         key=_num, reverse=True)
        for velha in versoes[2:]:
            shutil.rmtree(os.path.join(BASE, velha), ignore_errors=True)
    except Exception:
        pass

    return {"ok": True, "pasta": destino, "versao": str(versao)}

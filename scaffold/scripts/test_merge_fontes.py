# -*- coding: utf-8 -*-
"""Teste dirigido do merge_fontes.py — a allowlist de origens.

Nasceu em 19/08/2026 (Auditoria CC F3) do defeito medido em 17/08 e reincidente em
18/08 num caso real do escritorio: `ORIGENS_AUTORIZADAS` mantinha `julia-trf5` (MCP declarado
NAO instalado nesta casa) e nao trazia `carf-jurisprudencia`, que e fonte real e das
mais usadas no tributario. Efeito: pesquisa legitima do CARF rejeitada item a item.

Casos:
  A. item do CARF sobrevive ao merge e recebe prefixo CARF  (RED antes do conserto)
  B. origem inventada segue REJEITADA                       (a guarda nao afrouxou)
  C. toda origem autorizada tem prefixo                     (senao o merge quebra em KeyError)

Uso: py -3 scripts/test_merge_fontes.py
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
MERGE = RAIZ / "merge_fontes.py"


def _item(origem, referencia):
    return {
        "origem_mcp": origem,
        "tribunal": "CARF",
        "tipo": "acordao",
        "referencia": referencia,
        "campo": "ementa",
        "trecho_verbatim": "trecho de teste, verbatim, com tamanho suficiente para o merge",
    }


def _rodar(itens_por_arquivo):
    """Monta workspace temporario, roda o merge, devolve (saida, corpus)."""
    with tempfile.TemporaryDirectory() as tmp:
        ws = Path(tmp)
        for nome, itens in itens_por_arquivo.items():
            (ws / ("fontes-" + nome + ".json")).write_text(
                json.dumps(itens, ensure_ascii=False), encoding="utf-8")
        r = subprocess.run([sys.executable, str(MERGE), str(ws), "--id", "9999999"],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace")
        saida = (r.stdout or "") + (r.stderr or "")
        alvo = ws / "9999999-fontes.json"
        corpus = json.loads(alvo.read_text(encoding="utf-8")) if alvo.exists() else None
        return saida, corpus


def _fontes(corpus):
    """O corpus pode vir como lista ou como dict com a lista dentro — aceita os dois."""
    if corpus is None:
        return []
    if isinstance(corpus, list):
        return corpus
    for chave in ("fontes", "itens", "corpus"):
        if isinstance(corpus.get(chave), list):
            return corpus[chave]
    return []


def caso_a_carf_sobrevive():
    saida, corpus = _rodar({"carf": [_item("carf-jurisprudencia", "Acordao 9303-999.999")]})
    itens = _fontes(corpus)
    assert itens, "CARF rejeitado pelo merge — corpus vazio. Saida: " + saida
    ids = [str(i.get("id", "")) for i in itens]
    assert any(i.startswith("CARF") for i in ids), "CARF entrou sem prefixo: " + repr(ids)


def caso_b_origem_inventada_rejeitada():
    saida, corpus = _rodar({"x": [_item("tribunal-de-marte", "ref 1")]})
    assert not _fontes(corpus), "origem nao autorizada passou — a guarda afrouxou"
    assert ("autorizada" in saida), "rejeicao sem motivo nomeado. Saida: " + saida


def caso_c_prefixo_para_toda_origem():
    sys.path.insert(0, str(RAIZ))
    import merge_fontes as mf
    sem_prefixo = sorted(mf.ORIGENS_AUTORIZADAS - set(mf.PREFIXOS))
    assert not sem_prefixo, "origem autorizada sem prefixo: " + repr(sem_prefixo)


def caso_d_julia_fora_da_allowlist():
    """julia-trf5 e MCP do TRF5, nunca registrado nesta maquina; decidido em 06/08
    (Fase 1 do arsenal) e substituido pelo CARF desde 29/07. Reprova quem reintroduzir."""
    sys.path.insert(0, str(RAIZ))
    import merge_fontes as mf
    assert "julia-trf5" not in mf.ORIGENS_AUTORIZADAS, "julia-trf5 voltou a allowlist"
    assert "julia-trf5" not in mf.PREFIXOS, "julia-trf5 voltou ao PREFIXOS"
    saida, corpus = _rodar({"julia": [_item("julia-trf5", "ref julia")]})
    assert not _fontes(corpus), "item de fonte nao instalada entrou no corpus"


if __name__ == "__main__":
    casos = [("A carf sobrevive", caso_a_carf_sobrevive),
             ("B origem inventada rejeitada", caso_b_origem_inventada_rejeitada),
             ("C prefixo para toda origem", caso_c_prefixo_para_toda_origem),
             ("D julia fora da allowlist", caso_d_julia_fora_da_allowlist)]
    falhas = []
    for nome, fn in casos:
        try:
            fn()
            print("  OK    " + nome)
        except AssertionError as e:
            falhas.append(nome)
            print("  FALHA " + nome + ": " + str(e))
    print("")
    print(str(len(casos) - len(falhas)) + "/" + str(len(casos)) + " casos passaram")
    sys.exit(1 if falhas else 0)

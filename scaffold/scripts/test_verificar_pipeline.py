#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Suite do motor verificar_pipeline.py — nasceu em 27/08/2026 com os 4
defeitos que o code review de 26/08/2026 mediu:

  (i)   RE_ACENTO cego a NFD: documento inteiro legitimo reprovava como
        "sem acentos de portugues" so por estar decomposto.
  (ii)  --etapa combinado com --gate/--etapas retornava antes e o gate saia
        "verde" sem nunca ter rodado (falso verde, o pior tipo de defeito).
  (iii) checagem de abertura e uma JANELA de 400 chars normalizados, mas a
        mensagem dizia so "nao abre com o marcador" — quem lia procurava o
        marcador que estava la, 500 chars adiante.
  (iv)  o docstring de uso tem de ensinar o interpretador CERTO para onde o arquivo
        esta. Nesta copia — a do scaffold, que e material DISTRIBUIDO e roda nas 2
        plataformas — o certo e a forma portatil (`python`), e o caso (iv) PROIBE
        `py -3`. Na copia do workspace de origem o polo e o inverso, porque la a
        forma nua esta quebrada no PATH. E de proposito: cada caso (iv) guarda a
        sua ponta contra a adaptacao da outra viajar por engano.

Uso:  python scripts/test_verificar_pipeline.py
Exit 0 = todos os casos passam; 1 = algum falhou.
"""
import os
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import verificar_pipeline as motor  # noqa: E402

TOTAL = PASSOU = 0


def caso(nome, ok, detalhe=""):
    global TOTAL, PASSOU
    TOTAL += 1
    if ok:
        PASSOU += 1
        print(f"  OK    {nome}")
    else:
        print(f"  FALHA {nome}" + (f" -> {detalhe}" if detalhe else ""))


ETAPAS = {
    "unica": ("-doc.md", "# relatório", "documento concluído.", ["seção obrigatória"], 50),
}

CORPO = ("# relatório\n\n"
         "Seção obrigatória com acentuação: análise, decisão, ônus.\n"
         + ("conteúdo de prova. " * 10) + "\n"
         "documento concluído.\n")


def gravar(pasta, texto, nome="CASO-doc.md"):
    caminho = Path(pasta) / nome
    caminho.write_text(texto, encoding="utf-8")
    return caminho


def rodar_gate(pasta, *args):
    """Roda um gate real (verificar_probatica.py serve de fachada do motor)."""
    return subprocess.run(
        # sys.executable, não "py -3": este arquivo viaja para o scaffold do fork,
        # que roda nas 2 plataformas (mesmo padrão do test_merge_fontes.py)
        [sys.executable, str(AQUI / "verificar_pesquisa.py"), str(pasta)] + list(args),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=120)


def main():
    print("Suite do motor verificar_pipeline.py")

    # ------------------------------------------------ (i) acento em NFD
    nfc = "análise da decisão"
    nfd = unicodedata.normalize("NFD", nfc)
    caso("(i) RED historico: a classe crua NAO casa acento em NFD",
         not motor.RE_ACENTO.search(nfd))
    caso("(i) GREEN: tem_acento() casa NFC e NFD",
         motor.tem_acento(nfc) and motor.tem_acento(nfd))
    caso("(i) tem_acento() continua reprovando texto SEM acento",
         not motor.tem_acento("texto sem acento nenhum aqui"))

    with tempfile.TemporaryDirectory(suffix="-Área motor") as tmp:
        pasta = Path(tmp) / "CASO"
        pasta.mkdir()
        gravar(pasta, unicodedata.normalize("NFD", CORPO))
        problemas = motor.verificar_etapa(str(pasta), "CASO", "unica", ETAPAS)
        caso("(i) documento inteiro em NFD passa no gate",
             problemas == [], str(problemas))

        # -------------------------------------------- (iii) janela de 400 chars
        preambulo = "preâmbulo longo. " * 40  # ~680 chars, empurra o marcador
        gravar(pasta, preambulo + CORPO)
        problemas = motor.verificar_etapa(str(pasta), "CASO", "unica", ETAPAS)
        caso("(iii) marcador fora da janela ainda reprova (comportamento mantido)",
             any("abertura" in p for p in problemas), str(problemas))
        caso("(iii) a mensagem NOMEIA a janela de 400 caracteres",
             any("PRIMEIROS 400" in p for p in problemas), str(problemas))

        gravar(pasta, CORPO.replace("documento concluído.", "fim errado."))
        problemas = motor.verificar_etapa(str(pasta), "CASO", "unica", ETAPAS)
        caso("(iii) mensagem de fechamento tambem nomeia a janela",
             any("ÚLTIMOS 400" in p for p in problemas), str(problemas))

    # ------------------------------------------------ (ii) --etapa x --gate
    with tempfile.TemporaryDirectory(suffix="-Área cli") as tmp:
        pasta = Path(tmp) / "CASO"
        pasta.mkdir()
        # nenhum artefato gravado: com --gate honesto, o gate TEM de reprovar
        r = rodar_gate(pasta, "--etapa", "bnp", "--gate")
        caso("(ii) --etapa com --gate sai 2 (uso incorreto), nunca 0",
             r.returncode == 2, f"exit={r.returncode} out={r.stdout[-120:]}")
        caso("(ii) a mensagem explica a exclusividade",
             "exclusivo" in r.stdout, r.stdout[-120:])
        r = rodar_gate(pasta, "--etapa", "bnp", "--etapas", "bnp,cjf")
        caso("(ii) --etapa com --etapas tambem sai 2",
             r.returncode == 2, f"exit={r.returncode}")
        r = rodar_gate(pasta, "--gate")
        caso("(ii) --gate sozinho segue reprovando workspace vazio (exit 1)",
             r.returncode == 1, f"exit={r.returncode}")
        r = rodar_gate(pasta, "--etapa", "bnp")
        caso("(ii) --etapa sozinha segue funcionando (exit 1, ausente)",
             r.returncode == 1, f"exit={r.returncode}")

        # o falso verde exato do defeito: a etapa pedida VALIDA e as outras 5
        # pendentes — o motor antigo saia 0 com --gate; o gate honesto sai 1.
        (pasta / "CASO-pesquisa-bnp.md").write_text(
            "# pesquisa bnp\n\n" + ("conteúdo de prova com acentuação. " * 20)
            + "\npesquisa bnp concluída.\n", encoding="utf-8")
        r = rodar_gate(pasta, "--etapa", "bnp", "--gate")
        caso("(ii) FALSO VERDE fechado: etapa valida + 5 pendentes nao sai 0",
             r.returncode == 2, f"exit={r.returncode}")
        r = rodar_gate(pasta, "--gate")
        caso("(ii) o gate honesto sobre a MESMA pasta reprova (exit 1)",
             r.returncode == 1 and "PENDENTES: cjf" in r.stdout,
             f"exit={r.returncode}")

    # ------------------------------------------------ (iv) docstring
    doc = (AQUI / "verificar_pipeline.py").read_text(encoding="utf-8")
    # POLO INVERTIDO em relacao a copia do workspace DN, de proposito: la o
    # interpretador nu esta quebrado no PATH e o docstring tem de ensinar `py -3`;
    # aqui o material e DISTRIBUIDO e roda nas 2 plataformas, entao a adaptacao de
    # uma maquina so nao pode viajar junto. Este caso e o guarda contra isso.
    caso("(iv) docstring nao carrega a adaptacao de uma maquina so",
         "py -3 scripts/" not in doc)
    caso("(iv) docstring ensina a forma portatil",
         "python scripts/verificar_<sistema>.py" in doc)

    print(f"\n{PASSOU}/{TOTAL} casos passaram")
    return 0 if PASSOU == TOTAL else 1


if __name__ == "__main__":
    sys.exit(main())

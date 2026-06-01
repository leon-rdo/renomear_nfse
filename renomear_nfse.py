#!/usr/bin/env python3
"""
Renomeia arquivos XML e PDF de NFS-e (padrão nfse.gov.br) para nomes legíveis.

Uso:
  python3 renomear_nfse.py --xml-dir /caminho/XML --pdf-dir /caminho/PDF
  python3 renomear_nfse.py --xml-dir ./XML --canceladas 25,32 --dry-run

Formato gerado:
  NF20 - 2025-01-28 - Empresa Tomadora - R$ 1.500,00.xml
  NF25 - 2025-06-23 - Empresa Tomadora - R$ 1.656,00 [CANCELADA].xml
"""

import argparse
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

# ─────────────────────────────────────────────
# CONSTANTES
# ─────────────────────────────────────────────

# Sufixos jurídicos a remover do nome do tomador
SUFIXOS = [" LTDA", " S.A.", " S/A", " EIRELI", " ME", " EPP", " SA"]

# Preposições e conjunções em português que ficam minúsculas no meio do nome
MINUSCULAS = {"e", "de", "da", "do", "das", "dos", "a", "o", "em", "com", "para"}

NS = {"n": "http://www.sped.fazenda.gov.br/nfse"}

# ─────────────────────────────────────────────
# FUNÇÕES
# ─────────────────────────────────────────────


def title_pt(nome_original: str) -> str:
    """
    Title Case com regras para português:
    - Preposições e conjunções comuns ficam em minúsculo (exceto a 1ª palavra).
    - Siglas (2–4 letras, tudo maiúsculo no original) ficam em caixa alta.
    """
    palavras_orig = nome_original.split()
    resultado = []
    for i, palavra in enumerate(palavras_orig):
        letras = "".join(c for c in palavra if c.isalpha())
        if i > 0 and palavra.lower() in MINUSCULAS:
            resultado.append(palavra.lower())
        elif letras and 2 <= len(letras) <= 4 and letras == letras.upper():
            resultado.append(palavra.upper())
        else:
            resultado.append(palavra.capitalize())
    return " ".join(resultado)


def limpar_nome(nome: str) -> str:
    """Remove sufixos jurídicos e aplica Title Case com regras para português."""
    nome = nome.strip().upper()
    for sufixo in SUFIXOS:
        if nome.endswith(sufixo):
            nome = nome[: -len(sufixo)].rstrip()
            break
    return title_pt(nome)


def formatar_valor(valor: float) -> str:
    """Formata valor no padrão brasileiro: R$ 4.500,00"""
    inteiro, decimal = f"{valor:.2f}".split(".")
    inteiro_fmt = ""
    for i, digito in enumerate(reversed(inteiro)):
        if i and i % 3 == 0:
            inteiro_fmt = "." + inteiro_fmt
        inteiro_fmt = digito + inteiro_fmt
    return f"R$ {inteiro_fmt},{decimal}"


def montar_nome(nf_num: int, data: str, tomador: str, valor: float, ext: str, canceladas: set) -> str:
    """Monta o novo nome do arquivo."""
    cancelada = " [CANCELADA]" if nf_num in canceladas else ""
    return f"NF{nf_num:02d} - {data} - {tomador} - {formatar_valor(valor)}{cancelada}{ext}"


def parse_xml(caminho: Path) -> dict:
    """Extrai os dados relevantes de um arquivo XML de NFS-e."""
    tree = ET.parse(caminho)
    root = tree.getroot()

    inf = root.find(".//n:infNFSe", NS)
    dps = root.find(".//n:infDPS", NS)

    nf_num  = int(inf.find("n:nNFSe", NS).text)
    data    = datetime.fromisoformat(inf.find("n:dhProc", NS).text).strftime("%Y-%m-%d")
    toma    = dps.find("n:toma", NS)
    tomador = limpar_nome(toma.find("n:xNome", NS).text)
    valor   = float(dps.find(".//n:vServ", NS).text)

    return {"nf_num": nf_num, "data": data, "tomador": tomador, "valor": valor}


def renomear(xml_dir: Path, pdf_dir: Path, canceladas: set, dry_run: bool = False) -> None:
    modo = "SIMULAÇÃO — nenhum arquivo será alterado" if dry_run else "EXECUÇÃO"
    print(f"{'─'*60}")
    print(f"  Renomeador de NFS-e  [{modo}]")
    print(f"{'─'*60}")
    print(f"  XML : {xml_dir}")
    print(f"  PDF : {pdf_dir}")
    if canceladas:
        print(f"  Canceladas : NF {', '.join(str(n) for n in sorted(canceladas))}")
    print()

    xml_files = sorted(xml_dir.glob("*.xml"))

    if not xml_files:
        print(f"Nenhum arquivo .xml encontrado em:\n  {xml_dir}")
        return

    ok, erros = 0, []

    for xml_path in xml_files:
        try:
            dados = parse_xml(xml_path)
            nf    = dados["nf_num"]
            label = f"NF {nf:02d}" + (" [CANCELADA]" if nf in canceladas else "")

            novo_xml = montar_nome(nf, dados["data"], dados["tomador"], dados["valor"], ".xml", canceladas)
            novo_pdf = montar_nome(nf, dados["data"], dados["tomador"], dados["valor"], ".pdf", canceladas)

            # PDF com mesmo stem do XML (padrão do portal nfse.gov.br)
            pdf_path = pdf_dir / (xml_path.stem + ".pdf")

            print(f"{label}  |  {dados['data']}  |  {dados['tomador']}  |  {formatar_valor(dados['valor'])}")

            # XML
            destino_xml = xml_dir / novo_xml
            if destino_xml == xml_path:
                print(f"  XML  já nomeado corretamente.")
            else:
                print(f"  XML  {xml_path.name}")
                print(f"    →  {novo_xml}")
                if not dry_run:
                    xml_path.rename(destino_xml)

            # PDF
            if pdf_path.exists():
                destino_pdf = pdf_dir / novo_pdf
                if destino_pdf == pdf_path:
                    print(f"  PDF  já nomeado corretamente.")
                else:
                    print(f"  PDF  {pdf_path.name}")
                    print(f"    →  {novo_pdf}")
                    if not dry_run:
                        pdf_path.rename(destino_pdf)
            else:
                print(f"  PDF  não encontrado — verifique se está em: {pdf_dir}")

            print()
            ok += 1

        except Exception as e:
            erros.append((xml_path.name, e))
            print(f"  ERRO em {xml_path.name}: {e}\n")

    print(f"{'─'*60}")
    print(f"Processados : {ok} de {len(xml_files)} XMLs")
    if erros:
        print(f"\nErros ({len(erros)}):")
        for nome, err in erros:
            print(f"  {nome}: {err}")
    if dry_run:
        print("\nRode sem --dry-run para aplicar as mudanças.")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Renomeia XMLs e PDFs de NFS-e (nfse.gov.br) para nomes legíveis.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
exemplos:
  %(prog)s                                                  # modo interativo
  %(prog)s --xml-dir ./XML --pdf-dir ./PDF
  %(prog)s --xml-dir ~/Downloads/NFs/XML --pdf-dir ~/Downloads/NFs/PDF --canceladas 25,32
  %(prog)s --xml-dir ./XML --dry-run
        """,
    )
    parser.add_argument(
        "--xml-dir",
        type=Path,
        metavar="DIR",
        help="pasta com os arquivos .xml das NFS-e (perguntado interativamente se omitido)",
    )
    parser.add_argument(
        "--pdf-dir",
        type=Path,
        metavar="DIR",
        help="pasta com os arquivos .pdf (perguntado interativamente se omitido)",
    )
    parser.add_argument(
        "--canceladas",
        default="",
        metavar="N,N,...",
        help="números das notas canceladas, separados por vírgula (ex: 25,32)",
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="simula as renomeações sem alterar nenhum arquivo",
    )
    return parser.parse_args()


def pedir_pasta(mensagem: str) -> Path:
    """Solicita um caminho de pasta ao usuário e valida a entrada."""
    while True:
        try:
            entrada = input(mensagem).strip()
        except (EOFError, KeyboardInterrupt):
            print("\nCancelado pelo usuário.")
            sys.exit(0)
        if not entrada:
            print("  Caminho não pode ser vazio. Tente novamente.")
            continue
        pasta = Path(entrada).expanduser().resolve()
        if pasta.is_dir():
            return pasta
        print(f"  Pasta não encontrada: {pasta}\n  Verifique o caminho e tente novamente.")


if __name__ == "__main__":
    args = parse_args()

    # XML dir — argumento ou prompt interativo
    if args.xml_dir:
        xml_dir: Path = args.xml_dir.expanduser().resolve()
        if not xml_dir.is_dir():
            print(f"Erro: --xml-dir não existe ou não é uma pasta: {xml_dir}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Nenhuma pasta informada via argumento. Modo interativo.\n")
        xml_dir = pedir_pasta("Caminho da pasta com os XMLs: ")

    # PDF dir — argumento, prompt interativo ou padrão automático
    if args.pdf_dir:
        pdf_dir: Path = args.pdf_dir.expanduser().resolve()
        if not pdf_dir.is_dir():
            print(f"Aviso: --pdf-dir não existe: {pdf_dir}")
            print("Os PDFs serão ignorados.\n")
    else:
        padrao_pdf = xml_dir.parent / "PDF"
        if not args.xml_dir:
            # modo interativo: perguntar sempre
            pdf_dir = pedir_pasta("Caminho da pasta com os PDFs: ")
        elif padrao_pdf.is_dir():
            pdf_dir = padrao_pdf
        else:
            print(f"Aviso: pasta de PDFs não encontrada em {padrao_pdf}")
            print("Os PDFs serão ignorados. Use --pdf-dir para especificar o caminho correto.\n")
            pdf_dir = padrao_pdf

    canceladas: set = set()
    if args.canceladas.strip():
        try:
            canceladas = {int(n.strip()) for n in args.canceladas.split(",")}
        except ValueError:
            print("Erro: --canceladas deve ser uma lista de números separados por vírgula.", file=sys.stderr)
            sys.exit(1)

    renomear(xml_dir=xml_dir, pdf_dir=pdf_dir, canceladas=canceladas, dry_run=args.dry_run)

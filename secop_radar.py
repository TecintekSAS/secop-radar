#!/usr/bin/env python3
"""
SECOP Radar — Tecintek S.A.S.

Busca procesos de contratación pública recientes en SECOP II (datos abiertos
de Colombia, datos.gov.co) filtrando por palabras clave, departamento, valor
y modalidad. Exporta a CSV y genera un reporte Markdown listo para compartir.

Sin dependencias externas: solo librería estándar de Python 3.9+.

Uso:
    python secop_radar.py --palabras software "desarrollo web" --dias 7
    python secop_radar.py -p dotacion uniformes --departamento Cundinamarca --min 10000000
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass, asdict
from datetime import date, datetime, timedelta

API_URL = "https://www.datos.gov.co/resource/p6dx-8zbt.json"  # SECOP II - Procesos de Contratación
USER_AGENT = "secop-radar/1.0 (+https://github.com/TecintekSAS/secop-radar)"


@dataclass
class Proceso:
    entidad: str
    departamento: str
    ciudad: str
    descripcion: str
    modalidad: str
    estado: str
    precio_base: float
    fecha_publicacion: str
    id_proceso: str
    url: str

    @classmethod
    def desde_api(cls, fila: dict) -> "Proceso":
        url = fila.get("urlproceso") or {}
        if isinstance(url, dict):
            url = url.get("url", "")
        try:
            precio = float(fila.get("precio_base") or 0)
        except ValueError:
            precio = 0.0
        return cls(
            entidad=(fila.get("entidad") or "").strip(),
            departamento=fila.get("departamento_entidad") or "",
            ciudad=fila.get("ciudad_entidad") or "",
            descripcion=" ".join((fila.get("descripci_n_del_procedimiento") or "").split()),
            modalidad=fila.get("modalidad_de_contratacion") or "",
            estado=fila.get("estado_del_procedimiento") or "",
            precio_base=precio,
            fecha_publicacion=(fila.get("fecha_de_publicacion_del") or "")[:10],
            id_proceso=fila.get("id_del_proceso") or "",
            url=url or "",
        )


def _escapar(texto: str) -> str:
    """Escapa comillas simples para SoQL."""
    return texto.replace("'", "''")


def construir_consulta(
    palabras: list[str],
    dias: int = 7,
    departamento: str | None = None,
    valor_minimo: float = 0,
    solo_abiertos: bool = True,
    limite: int = 200,
    hoy: date | None = None,
) -> dict:
    """Arma los parámetros SoQL para la API de Socrata."""
    if not palabras:
        raise ValueError("Debes indicar al menos una palabra clave.")
    hoy = hoy or date.today()
    desde = (hoy - timedelta(days=dias)).isoformat() + "T00:00:00"

    filtros_palabras = " OR ".join(
        f"upper(descripci_n_del_procedimiento) like '%{_escapar(p.upper())}%'" for p in palabras
    )
    condiciones = [f"fecha_de_publicacion_del >= '{desde}'", f"({filtros_palabras})"]
    if departamento:
        condiciones.append(f"upper(departamento_entidad) like '%{_escapar(departamento.upper())}%'")
    if valor_minimo > 0:
        condiciones.append(f"precio_base >= {int(valor_minimo)}")
    if solo_abiertos:
        condiciones.append("estado_del_procedimiento = 'Publicado'")

    return {
        "$where": " AND ".join(condiciones),
        "$order": "fecha_de_publicacion_del DESC",
        "$limit": str(limite),
    }


def consultar(params: dict, timeout: int = 30) -> list[Proceso]:
    url = API_URL + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        datos = json.loads(resp.read().decode("utf-8"))
    vistos, procesos = set(), []
    for fila in datos:
        p = Proceso.desde_api(fila)
        clave = p.id_proceso or p.url
        if clave in vistos:
            continue
        vistos.add(clave)
        procesos.append(p)
    return procesos


def formato_cop(valor: float) -> str:
    return "$" + f"{valor:,.0f}".replace(",", ".")


def exportar_csv(procesos: list[Proceso], ruta: str) -> None:
    with open(ruta, "w", newline="", encoding="utf-8-sig") as f:
        campos = list(Proceso.__dataclass_fields__.keys())
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        for p in procesos:
            w.writerow(asdict(p))


def reporte_markdown(procesos: list[Proceso], palabras: list[str]) -> str:
    total = sum(p.precio_base for p in procesos)
    lineas = [
        f"# Radar SECOP — {datetime.now():%Y-%m-%d %H:%M}",
        "",
        f"**Palabras clave:** {', '.join(palabras)}  ",
        f"**Procesos encontrados:** {len(procesos)}  ",
        f"**Valor total (precio base):** {formato_cop(total)}",
        "",
        "| Fecha | Entidad | Departamento | Objeto | Modalidad | Valor | Enlace |",
        "|---|---|---|---|---|---:|---|",
    ]
    for p in procesos:
        objeto = (p.descripcion[:120] + "…") if len(p.descripcion) > 120 else p.descripcion
        objeto = objeto.replace("|", "/")
        lineas.append(
            f"| {p.fecha_publicacion} | {p.entidad.replace('|', '/')} | {p.departamento} | {objeto} "
            f"| {p.modalidad} | {formato_cop(p.precio_base)} | [Ver]({p.url}) |"
        )
    return "\n".join(lineas) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Radar de oportunidades en SECOP II (Colombia).")
    ap.add_argument("-p", "--palabras", nargs="+", required=True, help="Palabras clave del objeto")
    ap.add_argument("-d", "--dias", type=int, default=7, help="Días hacia atrás (default 7)")
    ap.add_argument("--departamento", help="Filtrar por departamento de la entidad")
    ap.add_argument("--min", type=float, default=0, dest="valor_minimo", help="Valor mínimo en COP")
    ap.add_argument("--todos", action="store_true", help="Incluir procesos no abiertos")
    ap.add_argument("--limite", type=int, default=200)
    ap.add_argument("--csv", default="oportunidades.csv", help="Archivo CSV de salida")
    ap.add_argument("--md", default="reporte.md", help="Reporte Markdown de salida")
    args = ap.parse_args(argv)

    params = construir_consulta(
        args.palabras, args.dias, args.departamento, args.valor_minimo, not args.todos, args.limite
    )
    try:
        procesos = consultar(params)
    except Exception as e:  # red, API caída, etc.
        print(f"Error consultando SECOP: {e}", file=sys.stderr)
        return 1

    exportar_csv(procesos, args.csv)
    with open(args.md, "w", encoding="utf-8") as f:
        f.write(reporte_markdown(procesos, args.palabras))

    print(f"{len(procesos)} procesos encontrados -> {args.csv}, {args.md}")
    for p in procesos[:15]:
        print(f"  {p.fecha_publicacion}  {formato_cop(p.precio_base):>18}  {p.entidad[:45]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

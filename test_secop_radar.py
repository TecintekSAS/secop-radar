import io
import json
import os
import tempfile
import unittest
from datetime import date
from unittest import mock

import secop_radar as sr

FILA = {
    "entidad": "ALCALDIA DE FACATATIVA",
    "departamento_entidad": "Cundinamarca",
    "ciudad_entidad": "Facatativá",
    "descripci_n_del_procedimiento": "Desarrollo de  software\n para gestión documental",
    "modalidad_de_contratacion": "Mínima cuantía",
    "estado_del_procedimiento": "Publicado",
    "precio_base": "25000000",
    "fecha_de_publicacion_del": "2026-10-16T00:00:00.000",
    "id_del_proceso": "CO1.REQ.1",
    "urlproceso": {"url": "https://community.secop.gov.co/x"},
}


class _Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class TestConsulta(unittest.TestCase):
    def test_construir_consulta_filtros(self):
        q = sr.construir_consulta(["software", "o'neil"], dias=3, departamento="Cundinamarca",
                                  valor_minimo=1e6, hoy=date(2026, 10, 19))
        w = q["$where"]
        self.assertIn("fecha_de_publicacion_del >= '2026-10-16T00:00:00'", w)
        self.assertIn("like '%SOFTWARE%'", w)
        self.assertIn("O''NEIL", w)  # comilla escapada
        self.assertIn("CUNDINAMARCA", w)
        self.assertIn("precio_base >= 1000000", w)
        self.assertIn("'Publicado'", w)

    def test_sin_palabras(self):
        with self.assertRaises(ValueError):
            sr.construir_consulta([])

    def test_proceso_desde_api(self):
        p = sr.Proceso.desde_api(FILA)
        self.assertEqual(p.descripcion, "Desarrollo de software para gestión documental")
        self.assertEqual(p.precio_base, 25_000_000)
        self.assertEqual(p.fecha_publicacion, "2026-10-16")
        self.assertEqual(p.url, "https://community.secop.gov.co/x")

    def test_precio_invalido(self):
        p = sr.Proceso.desde_api({**FILA, "precio_base": "N/A"})
        self.assertEqual(p.precio_base, 0)

    def test_consultar_deduplica(self):
        cuerpo = json.dumps([FILA, FILA, {**FILA, "id_del_proceso": "CO1.REQ.2"}]).encode()
        with mock.patch("urllib.request.urlopen", return_value=_Resp(cuerpo)):
            res = sr.consultar({"$limit": "5"})
        self.assertEqual(len(res), 2)

    def test_formato_cop(self):
        self.assertEqual(sr.formato_cop(1234567), "$1.234.567")

    def test_main_genera_archivos(self):
        cuerpo = json.dumps([FILA]).encode()
        with tempfile.TemporaryDirectory() as d, \
                mock.patch("urllib.request.urlopen", return_value=_Resp(cuerpo)):
            csv_p, md_p = os.path.join(d, "o.csv"), os.path.join(d, "r.md")
            code = sr.main(["-p", "software", "--csv", csv_p, "--md", md_p])
            self.assertEqual(code, 0)
            with open(md_p, encoding="utf-8") as f:
                md = f.read()
            self.assertIn("ALCALDIA DE FACATATIVA", md)
            self.assertIn("$25.000.000", md)
            with open(csv_p, encoding="utf-8-sig") as f:
                self.assertIn("CO1.REQ.1", f.read())

    def test_main_error_red(self):
        with mock.patch("urllib.request.urlopen", side_effect=OSError("sin red")):
            self.assertEqual(sr.main(["-p", "x", "--csv", os.devnull, "--md", os.devnull]), 1)


if __name__ == "__main__":
    unittest.main()

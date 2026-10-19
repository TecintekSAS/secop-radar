# 📡 SECOP Radar

**Encuentra oportunidades de contratación pública en Colombia antes que tu competencia.**

SECOP Radar consulta los **datos abiertos de SECOP II** (datos.gov.co) y filtra los procesos publicados recientemente por palabras clave, departamento y valor. Genera un **CSV** (abre en Excel) y un **reporte Markdown** listo para enviar a tu equipo.

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white)
![Sin dependencias](https://img.shields.io/badge/dependencias-0-brightgreen)
![Tests](https://img.shields.io/badge/tests-8%20passing-brightgreen)
![Licencia](https://img.shields.io/badge/licencia-MIT-blue)

> Hecho por **[Tecintek S.A.S.](https://github.com/TecintekSAS)** · Base técnica de nuestra plataforma de inteligencia de licitaciones.

---

## ✨ Qué hace

- 🔎 Busca en el objeto del proceso varias palabras clave a la vez (`software`, `dotación`, `papelería`…)
- 📍 Filtra por **departamento** de la entidad y **valor mínimo** en COP
- 🟢 Por defecto muestra solo procesos **abiertos** (estado *Publicado*)
- 📊 Exporta **CSV** (UTF-8 con BOM, abre directo en Excel) y **reporte Markdown** con enlaces a SECOP
- 🧹 Elimina duplicados y limpia los textos
- 📦 **Cero dependencias**: solo Python estándar

## 🚀 Uso rápido

```bash
git clone https://github.com/TecintekSAS/secop-radar.git
cd secop-radar

# Procesos de software y desarrollo web de los últimos 7 días
python secop_radar.py --palabras software "desarrollo web"

# Dotación y uniformes en Cundinamarca desde $10 millones, últimos 15 días
python secop_radar.py -p dotacion uniformes --departamento Cundinamarca --min 10000000 --dias 15
```

Salida:

```
3 procesos encontrados -> oportunidades.csv, reporte.md
  2026-10-16       $25.000.000  ALCALDIA DE ...
```

### Opciones

| Opción | Descripción | Default |
|---|---|---|
| `-p, --palabras` | Una o varias palabras clave (obligatorio) | — |
| `-d, --dias` | Días hacia atrás | `7` |
| `--departamento` | Departamento de la entidad | todos |
| `--min` | Valor mínimo (precio base, COP) | `0` |
| `--todos` | Incluye procesos no abiertos | solo abiertos |
| `--limite` | Máximo de resultados | `200` |
| `--csv` / `--md` | Archivos de salida | `oportunidades.csv` / `reporte.md` |

## ⏰ Automatízalo

Programa una alerta diaria (Linux/Mac, `crontab -e`):

```cron
0 7 * * 1-5 cd ~/secop-radar && python3 secop_radar.py -p software dotacion papeleria --dias 1
```

En Windows usa el **Programador de tareas**. ¿Lo quieres por WhatsApp o correo? Escríbenos.

## 🧪 Pruebas

```bash
python -m unittest -v
```

Las pruebas simulan la API, no necesitan internet.

## 📚 Fuente de datos

[SECOP II – Procesos de Contratación](https://www.datos.gov.co/Gastos-Gubernamentales/SECOP-II-Procesos-de-Contrataci-n/p6dx-8zbt) · Portal de Datos Abiertos de Colombia (API Socrata). Los datos son públicos; verifica siempre la información final en el portal SECOP antes de presentar una oferta.

## 🗺️ Próximas mejoras

- [ ] Alertas por WhatsApp y Telegram
- [ ] Resumen del pliego con IA
- [ ] Filtro por códigos UNSPSC
- [ ] Panel web

¿Ideas o errores? Abre un *issue*. Las contribuciones son bienvenidas.

## 📫 Contacto

**Tecintek S.A.S.** · Facatativá, Colombia · ✉️ tecintek@gmail.com · 💬 [WhatsApp +57 312 562 0570](https://wa.me/573125620570)

Licencia MIT.

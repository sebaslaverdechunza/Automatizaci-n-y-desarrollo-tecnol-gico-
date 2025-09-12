# app.py — Consolidado con vista previa HTML de "Datos_Deseados"
# ------------------------------------------------------------------------------
# Qué hace este script:
# - Web app Flask para cargar un .xlsx/.csv, validar datos y generar un Excel "anexo".
# - Hoja "Datos_Limpiados": aplica formato numérico SOLO a la columna TGP (0.00) y
#   deja Año/Mes como enteros. El resto se exporta tal cual.
# - Hoja "Datos_Deseados": construida desde "Datos_Limpiados" o desde un layout matriz,
#   con tema blanco, bordes #e5e7eb, años/meses en negrilla y conceptos SIN negrilla.
# - Interfaz: muestra un "Resumen de columnas" y una vista previa HTML de "Datos_Deseados".
# - Autoabre el navegador en http://127.0.0.1:5000/
# ------------------------------------------------------------------------------

from flask import Flask, request, render_template_string, send_file
import pandas as pd
import numpy as np
import unicodedata, re
import io
import threading, time, webbrowser

app = Flask(__name__)
# Límite de carga de archivo: 20 MB
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024  # 20 MB

# ------------------------------------------------------------------------------
# Plantilla HTML incrustada: incluye
# - Formulario de carga de archivo
# - Tabla de "Resumen de columnas"
# - Vista previa HTML de "Datos_Deseados"
# - Botón para descargar el anexo
# NOTA: Para evitar conflictos en Jinja con .values/.items, en la vista previa
#       se accede a dicts con la sintaxis de índice: row['values'], yb['months'], etc.
# ------------------------------------------------------------------------------
HTML = """
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <title>Validador de Anexo</title>
  <style>
    :root { --border:#e5e7eb; --muted:#6b7280; --bg:#f9fafb; }
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial; max-width: 980px; margin: 40px auto; }
    .card { border: 1px solid var(--border); border-radius: 14px; padding: 24px; }
    .btn { background: #111827; color: #fff; border: 0; padding: 10px 16px; border-radius: 10px; cursor: pointer; }
    .mt { margin-top: 14px; }
    .muted { color: var(--muted); font-size: 14px; }
    table { border-collapse: collapse; width: 100%; margin-top: 16px; font-size: 14px; }
    th, td { border: 1px solid var(--border); padding: 8px 10px; text-align: left; }
    th { background: var(--bg); }
    .grid { display: grid; gap: 10px; grid-template-columns: 1fr auto; align-items: end; }
    input[type=file] { padding: 6px; border: 1px solid var(--border); border-radius: 10px; background: #fff; }
  </style>
</head>
<body>
  <h2>Aplicativo de carga y exportación</h2>
  <div class="card">
    <!-- Formulario de carga -->
    <form method="POST" enctype="multipart/form-data">
      <div class="grid">
        <div>
          <label>Seleccione un archivo (.xlsx o .csv):</label><br/>
          <input class="mt" type="file" name="file" accept=".xlsx,.csv" required />
          <p class="muted mt">Si es Excel, se usa la hoja <b>Base</b> si existe; si no, la primera hoja.</p>
        </div>
        <div>
          <button class="btn" type="submit">Validar y generar anexo</button>
        </div>
      </div>
    </form>

    <!-- Mensaje de estado -->
    {% if mensaje %}
      <p class="mt"><b>{{ mensaje }}</b></p>
    {% endif %}

    <!-- Resumen de columnas detectadas -->
    {% if resumen %}
      <div class="mt">
        <p class="muted">Resumen de columnas detectadas:</p>
        <table>
          <thead>
            <tr>
              <th>Columna</th>
              <th>Tipo detectado</th>
              <th>No nulos</th>
              <th>% convertible</th>
              <th>Nulos post-coerce</th>
            </tr>
          </thead>
          <tbody>
            {% for r in resumen %}
              <tr>
                <td>{{ r.columna }}</td>
                <td>{{ r.tipo_detectado }}</td>
                <td>{{ r.no_nulos }}</td>
                <td>{{ r.porc_convertible }}%</td>
                <td>{{ r.nulos_post_coerce }}</td>
              </tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
    {% endif %}

    <!-- Vista previa HTML de "Datos_Deseados" -->
    {% if preview %}
      <div class="mt">
        <p class="muted">Vista rápida de <b>Datos_Deseados</b>:</p>
        <table>
          <thead>
            <tr>
              <th rowspan="2">Concepto</th>
              {% for yb in preview.year_blocks %}
                <th colspan="{{ yb['months']|length }}">{{ yb['year'] }}</th>
              {% endfor %}
            </tr>
            <tr>
              {% for yb in preview.year_blocks %}
                {% for m in yb['months'] %}
                  <th>{{ m }}</th>
                {% endfor %}
              {% endfor %}
            </tr>
          </thead>
          <tbody>
            {% for row in preview.rows %}
              <tr>
                <td>{{ row['concepto'] }}</td>
                {% for v in row['values'] %}
                  <td style="text-align:right">{{ v }}</td>
                {% endfor %}
              </tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
    {% endif %}

    <!-- Botón de descarga -->
    {% if listo %}
      <div class="mt">
        <a class="btn" href="/download">Descargar anexo</a>
      </div>
    {% endif %}
  </div>

  <!-- Nota sobre la heurística numérica -->
  <p class="muted mt">Heurística: una columna es "numérica" si ≥ 70% de sus valores no nulos pueden convertirse (quita %, NBSP y coma→punto).</p>
</body>
</html>
"""

# Buffer de salida del Excel y el resumen a mostrar
buffer_xlsx = None
resumen_reporte = None

# Mapas de meses
MESES_ORDER = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
MAP_MES_NOMBRE_A_NUM = {m:i+1 for i,m in enumerate(MESES_ORDER)}
MAP_MES_NUM_A_NOMBRE = {i+1:m for i,m in enumerate(MESES_ORDER)}

# Conceptos a presentar (en orden)
CONCEPTOS_CANON = [
    "% población en edad de trabajar",
    "Tasa Global de Participación (TGP)",
    "Tasa de Ocupación (TO)",
]

# ==============================================================================
# Utilidades de limpieza/detección
# ==============================================================================

def _normalize_text(s: str) -> str:
    """Normaliza cadenas para comparar (sin tildes, minúsculas, sin signos)."""
    s = str(s or "").strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"[\(\)\[\]\{\}%]", " ", s)
    s = re.sub(r"[^a-z0-9áéíóúüñ\s\.]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _coerce_numeric_series(serie: pd.Series) -> pd.Series:
    """Convierte a numérico: quita NBSP, %, espacios y cambia coma decimal por punto."""
    s = (serie.astype(str)
         .str.replace("\u00A0", "", regex=False)  # NBSP
         .str.replace("%", "", regex=False)       # símbolos de porcentaje
         .str.replace(" ", "", regex=False)       # espacios
         .str.replace(",", ".", regex=False)      # coma → punto
         .str.strip())
    return pd.to_numeric(s, errors="coerce")      # NaN si no se puede

def _df_clean(df: pd.DataFrame) -> pd.DataFrame:
    """Reemplaza ±inf por NaN (xlsxwriter no acepta inf)."""
    return df.replace([np.inf, -np.inf], np.nan)

def _leer_base_robusto(xls: pd.ExcelFile, sheet: str):
    """
    Lee una hoja Excel de forma robusta.
    - df_simple: lectura directa (header detectado por pandas).
    - df_multi: intenta reconstruir columnas MultiIndex si detecta filas 'Concepto'.
    """
    df_simple = pd.read_excel(xls, sheet_name=sheet)

    # Escaneo de las primeras filas sin header para encontrar 'Concepto'
    raw = pd.read_excel(xls, sheet_name=sheet, header=None, nrows=25)
    fila_concepto = None
    for i in range(len(raw)):
        if (raw.iloc[i].astype(str).str.strip().str.lower() == "concepto").any():
            fila_concepto = i; break

    df_multi = None
    if fila_concepto is not None:
        # Probar combinaciones de header
        for hdr in ([fila_concepto, fila_concepto+1],
                    [max(0, fila_concepto-1), fila_concepto]):
            try:
                tmp = pd.read_excel(xls, sheet_name=sheet, header=hdr)
                if isinstance(tmp.columns, pd.MultiIndex):
                    # Rellena niveles vacíos y arma tuplas limpias
                    top = pd.Series([str(a).strip() if pd.notna(a) else "" for a,_ in tmp.columns])
                    top = top.replace("", np.nan).ffill().fillna("")
                    bottom = pd.Series([str(b).strip() if pd.notna(b) else "" for _,b in tmp.columns])
                    tmp.columns = pd.MultiIndex.from_tuples(list(zip(top.tolist(), bottom.tolist())))
                    df_multi = tmp; break
            except Exception:
                continue
    return df_simple, df_multi

def _detectar_cols_anno_mes(df: pd.DataFrame):
    """Detecta columnas de Año y Mes probando alias comunes."""
    cols = {c: str(c).strip().lower() for c in df.columns}
    anno_alias = ["anno", "año", "ano", "anio", "year"]
    mes_alias  = ["mes", "month", "mes_num", "nmes"]
    col_anno = next((c for c, n in cols.items() if n in anno_alias), None)
    col_mes  = next((c for c, n in cols.items() if n in mes_alias), None)
    return (col_anno, col_mes)

def _safe_anno_mes(df: pd.DataFrame):
    """Wrapper seguro que siempre devuelve una tupla (col_anno, col_mes)."""
    try:
        res = _detectar_cols_anno_mes(df)
        if isinstance(res, (tuple, list)) and len(res) == 2:
            return res[0], res[1]
        return (None, None)
    except Exception:
        return (None, None)

def _normalizar_mes_a_num(serie_mes: pd.Series) -> pd.Series:
    """Convierte mes (texto o número) a número 1..12."""
    if pd.api.types.is_numeric_dtype(serie_mes): 
        return serie_mes.astype("Int64")
    s2 = serie_mes.astype(str).str.strip().str[:3].str.title()  # Ene, Feb...
    s_num = s2.map(MAP_MES_NOMBRE_A_NUM)                        # nombre → num
    s_num2 = pd.to_numeric(s2, errors="coerce")                 # por si ya viene numérico
    return s_num.fillna(s_num2).astype("Int64")

# ==============================================================================
# Construcción de la VISTA PREVIA HTML (no afecta el archivo Excel)
# ==============================================================================

def _build_preview_datos_deseados(df_base: pd.DataFrame, df_multi: pd.DataFrame|None):
    """
    Devuelve un dict con:
      - year_blocks: [{year: 2024, months: ["Ene","Feb",...]}...]
      - rows: [{concepto: "...", values: ["77.90","78.00", ...]}...]
    Para que Jinja construya la tabla de vista previa.
    """
    def _fmt(v):
        """Formato '0.00' para números; cadena vacía para NaN/None."""
        try:
            if v is None or (isinstance(v, float) and (pd.isna(v) or np.isinf(v))):
                return ""
            v = float(v)
            return f"{v:.2f}"
        except Exception:
            return ""

    # --- Opción 1: Layout largo (Anno, Mes, Concepto, Valor)
    col_anno, col_mes = _safe_anno_mes(df_base)
    if col_anno and col_mes:
        df = df_base.copy()
        df[col_mes] = _normalizar_mes_a_num(df[col_mes])

        # Detecta columnas de concepto/valor por alias
        norm_cols = {c: _normalize_text(c) for c in df.columns}
        def find_col(keys):
            for c, n in norm_cols.items():
                if any(k in n for k in keys): return c
            return None

        concept_col = find_col(["concepto","indicador","variable","serie",
                                "poblacion en ed trabajar","poblacion en edad de trabajar"])
        value_col   = find_col(["tasa global de participacion","tgp","valor","dato","medida"])

        if concept_col and value_col:
            # Limpia valor y filtra meses válidos
            df[value_col] = _coerce_numeric_series(df[value_col])
            df = df[df[col_mes].isin(range(1,13))]
            df[col_anno] = pd.to_numeric(df[col_anno], errors="coerce").astype("Int64")
            df = df.dropna(subset=[col_anno])
            df[col_anno] = df[col_anno].astype(int)

            # Pivot de filas=concepto, columnas=(año, mes)
            pv = df.pivot_table(index=concept_col, columns=[col_anno, col_mes],
                                values=value_col, aggfunc="first")
            if isinstance(pv.columns, pd.MultiIndex) and len(pv.columns.levels) == 2:
                pv.columns = pd.MultiIndex.from_tuples([(int(a), int(m)) for a, m in pv.columns])

            # Define orden de columnas (año-mes) para render
            year_blocks = []
            order_cols = []
            if len(pv.columns) > 0:
                years = sorted({int(a) for a, _m in pv.columns})
                for a in years:
                    meses = sorted([int(m) for (aa, m) in pv.columns if int(aa) == a])
                    if not meses: continue
                    year_blocks.append({"year": a, "months": [MAP_MES_NUM_A_NOMBRE[m] for m in meses]})
                    for m in meses:
                        order_cols.append((a, m))

            # Busca coincidencias fuzzy de filas de conceptos
            idx_norm_to_orig = { _normalize_text(ix): ix for ix in pv.index.astype(str) }
            def pick(aliases):
                for k, orig in idx_norm_to_orig.items():
                    if any(a in k for a in aliases): return orig
                return None
            aliases = {
                "% población en edad de trabajar": ["poblacion en edad de trabajar","poblacion en ed trabajar","edad de trabajar"],
                "Tasa Global de Participación (TGP)": ["tasa global de participacion","tgp","participacion"],
                "Tasa de Ocupación (TO)": ["tasa de ocupacion","to","ocupacion"],
            }
            rows = []
            for c in CONCEPTOS_CANON:
                rk = pick(aliases[c])
                vals = []
                for a, m in order_cols:
                    v = pv.at[rk, (a, m)] if (rk is not None and (a, m) in pv.columns) else np.nan
                    vals.append(_fmt(v))
                rows.append({"concepto": c, "values": vals})

            return {"year_blocks": year_blocks, "rows": rows}

    # --- Opción 2: Layout matriz (MultiIndex)
    if (df_multi is not None) and isinstance(df_multi.columns, pd.MultiIndex):
        dfm = df_multi.copy()
        # Localiza la columna "Concepto"
        first_col = None
        for col in dfm.columns:
            a = (col[0] if isinstance(col, tuple) and len(col)>0 else str(col))
            if str(a).strip().lower() == "concepto":
                first_col = col; break
        if first_col is None: first_col = dfm.columns[0]

        # Años presentes
        years = []
        for col in dfm.columns:
            if col == first_col: continue
            a = (col[0] if isinstance(col, tuple) and len(col)>0 else "")
            if str(a).strip().isdigit() and (a not in years):
                years.append(a)
        years = sorted(years, key=lambda x: int(x))

        # Bloques año/mes para render
        year_blocks = []
        order_cols = []
        for a in years:
            meses = [m for m in MESES_ORDER if (a, m) in dfm.columns]
            if not meses: continue
            year_blocks.append({"year": int(a), "months": meses})
            for m in meses:
                order_cols.append((a, m))

        # Mapa fuzzy de nombres de fila
        nombres = dfm[first_col].astype(str).tolist()
        norm2idx = { _normalize_text(v): i for i, v in enumerate(nombres) }
        def find_idx(keys):
            for nm, ii in norm2idx.items():
                if any(k in nm for k in keys): return ii
            return None
        fila_pet = find_idx(["poblacion en edad de trabajar","poblacion en ed trabajar","edad de trabajar"])
        fila_tgp = find_idx(["tasa global de participacion","tgp","participacion"])
        fila_to  = find_idx(["tasa de ocupacion","to","ocupacion"])
        fila_map = {CONCEPTOS_CANON[0]: fila_pet, CONCEPTOS_CANON[1]: fila_tgp, CONCEPTOS_CANON[2]: fila_to}

        # Armar filas para la vista previa
        rows = []
        for c in CONCEPTOS_CANON:
            ridx = fila_map.get(c, None)
            vals = []
            for (a, m) in order_cols:
                v = np.nan
                try:
                    if ridx is not None and (a, m) in dfm.columns:
                        v = _coerce_numeric_series(pd.Series([dfm.iloc[ridx][(a, m)]]))[0]
                except Exception:
                    v = np.nan
                vals.append(_fmt(v))
            rows.append({"concepto": c, "values": vals})

        return {"year_blocks": year_blocks, "rows": rows}

    # Si no se pudo construir la preview
    return None

# ==============================================================================
# Escritura de la hoja Excel "Datos_Deseados" (tema blanco + bordes)
# ==============================================================================

def _escribir_datos_deseados_desde_limpios(writer: pd.ExcelWriter,
                                           df_limpio: pd.DataFrame,
                                           df_multi: pd.DataFrame|None):
    """
    Construye la hoja "Datos_Deseados" sobre el writer (xlsxwriter).
    - Tema blanco (bg #FFFFFF), bordes #e5e7eb
    - Cabeceras de AÑO y MESES en negrilla
    - Columna "Concepto" SIN negrilla
    - Valores con formato numérico 0.00
    """
    wb = writer.book
    ws = wb.add_worksheet("Datos_Deseados")
    ws.hide_gridlines(2)  # oculta cuadriculado para un look más limpio

    BORDER_COLOR = "#e5e7eb"

    def make_fmt(base, top=0, bottom=0, left=0, right=0, numfmt=None):
        """Crea formatos con tema blanco y bordes configurables."""
        d = dict(base)
        d["bg_color"] = "#FFFFFF"; d["pattern"] = 1          # relleno blanco
        d["border_color"] = BORDER_COLOR
        if top:    d["top"] = top
        if bottom: d["bottom"] = bottom
        if left:   d["left"] = left
        if right:  d["right"] = right
        if numfmt: d["num_format"] = numfmt
        return wb.add_format(d)

    # Bases de formato (header/month en negrilla; concept sin negrilla; value con alineación derecha)
    base_header  = {"bold": True, "align": "center", "valign": "vcenter"}
    base_month   = {"bold": True, "align": "center", "valign": "vcenter"}
    base_concept = {"align": "left",  "valign": "vcenter"}
    base_value   = {"align": "right", "valign": "vcenter"}

    def mes_nom(n): return MAP_MES_NUM_A_NOMBRE.get(int(n), "")

    first_data_row = 2                        # fila donde empiezan los conceptos
    n_conceptos = len(CONCEPTOS_CANON)
    last_row = first_data_row + n_conceptos - 1

    # A1:A2 "Concepto" (con bordes externos y separador a la derecha)
    ws.merge_range(0, 0, 1, 0, "Concepto",
                   make_fmt(base_header, top=1, bottom=1, left=1, right=1))

    # --- Opción 1: se puede construir desde layout largo
    col_anno, col_mes = _safe_anno_mes(df_limpio)
    if col_anno and col_mes:
        df = df_limpio.copy()

        # Detección robusta de columnas de concepto/valor
        norm_cols = {c: _normalize_text(c) for c in df.columns}
        def find_col(keys):
            for c, n in norm_cols.items():
                if any(k in n for k in keys): return c
            return None
        concept_col = find_col(["concepto","indicador","variable","serie",
                                "poblacion en ed trabajar","poblacion en edad de trabajar"])
        value_col   = find_col(["tasa global de participacion","tgp","valor","dato","medida"])

        if concept_col and value_col:
            # Normaliza mes y valor
            df[col_mes]   = _normalizar_mes_a_num(df[col_mes])
            df[value_col] = _coerce_numeric_series(df[value_col])
            df = df[df[col_mes].isin(range(1, 13))]
            df[col_anno] = pd.to_numeric(df[col_anno], errors="coerce").astype("Int64")
            df = df.dropna(subset=[col_anno]); df[col_anno] = df[col_anno].astype(int)

            # Pivot (filas=concepto, columnas=(año, mes))
            pv = df.pivot_table(index=concept_col, columns=[col_anno, col_mes],
                                values=value_col, aggfunc="first")
            if isinstance(pv.columns, pd.MultiIndex) and len(pv.columns.levels) == 2:
                pv.columns = pd.MultiIndex.from_tuples([(int(a), int(m)) for a, m in pv.columns])

            # Define bloques por año y calcula última columna para bordes externos
            year_blocks, col_ptr = [], 1
            if len(pv.columns) > 0:
                years = sorted({int(a) for a, _ in pv.columns})
                for a in years:
                    meses = sorted([int(m) for (aa, m) in pv.columns if int(aa) == a])
                    if not meses: continue
                    c0 = col_ptr; c1 = c0 + len(meses) - 1
                    year_blocks.append((a, c0, c1, meses))
                    col_ptr = c1 + 1
            last_col = (col_ptr - 1) if col_ptr > 1 else 0

            # Aplica relleno blanco en toda el área visible (tema)
            white_fill = wb.add_format({"bg_color": "#FFFFFF", "pattern": 1})
            ws.set_column(0, max(0, last_col), 12, white_fill)
            for r in range(0, max(last_row, 1) + 1):
                ws.set_row(r, None, white_fill)

            # Cabeceras de AÑO (bordes externos izq/der en extremos)
            for (a, c0, c1, _meses) in year_blocks:
                ws.merge_range(0, c0, 0, c1, str(a),
                               make_fmt(base_header, top=1,
                                        right=(1 if c1 == last_col else 0),
                                        left=(1 if c0 == 1 else 0)))
            # Fila de MESES (borde superior e inferior)
            for (_a, c0, _c1, meses) in year_blocks:
                for k, m in enumerate(meses):
                    cc = c0 + k
                    ws.write(1, cc, mes_nom(m),
                             make_fmt(base_month, top=1, bottom=1,
                                      right=(1 if cc == last_col else 0),
                                      left=(1 if cc == c0 else 0)))
            # Columna Concepto (SIN negrilla; borde derecho como separador)
            for i, concepto in enumerate(CONCEPTOS_CANON):
                r = first_data_row + i
                ws.write(r, 0, concepto,
                         make_fmt(base_concept, left=1, right=1, bottom=(1 if r == last_row else 0)))

            # Valores con formato 0.00 y bordes externos (derecha/abajo)
            idx_norm_to_orig = { _normalize_text(ix): ix for ix in pv.index.astype(str) }
            def pick(aliases):
                for k, orig in idx_norm_to_orig.items():
                    if any(a in k for a in aliases): return orig
                return None
            aliases = {
                "% población en edad de trabajar": ["poblacion en edad de trabajar","poblacion en ed trabajar","edad de trabajar"],
                "Tasa Global de Participación (TGP)": ["tasa global de participacion","tgp","participacion"],
                "Tasa de Ocupación (TO)": ["tasa de ocupacion","to","ocupacion"],
            }
            for i, concepto in enumerate(CONCEPTOS_CANON):
                r = first_data_row + i
                rk = pick(aliases[concepto])
                for (a, c0, _c1, meses) in year_blocks:
                    for k, m in enumerate(meses):
                        cc = c0 + k
                        v = pv.at[rk, (a, m)] if (rk is not None and (a, m) in pv.columns) else np.nan
                        ws.write(r, cc, v,
                                 make_fmt(base_value,
                                          right=(1 if cc == last_col else 0),
                                          bottom=(1 if r == last_row else 0),
                                          numfmt="0.00"))

            # Anchos de columna
            ws.set_column(0, 0, 42)
            if last_col >= 1: ws.set_column(1, last_col, 12)
            return

    # --- Opción 2: reconstrucción desde una tabla matriz (MultiIndex)
    if (df_multi is not None) and isinstance(df_multi.columns, pd.MultiIndex):
        dfm = df_multi.copy()
        # Localiza columna "Concepto"
        first_col = None
        for col in dfm.columns:
            a = (col[0] if isinstance(col, tuple) and len(col)>0 else str(col))
            if str(a).strip().lower() == "concepto":
                first_col = col; break
        if first_col is None: first_col = dfm.columns[0]

        # Años presentes
        years = []
        for col in dfm.columns:
            if col == first_col: continue
            a = (col[0] if isinstance(col, tuple) and len(col)>0 else "")
            if str(a).strip().isdigit() and (a not in years):
                years.append(a)
        years = sorted(years, key=lambda x: int(x))

        # Bloques por año
        year_blocks, col_ptr = [], 1
        for a in years:
            meses = [m for m in MESES_ORDER if (a, m) in dfm.columns]
            if not meses: continue
            c0 = col_ptr; c1 = c0 + len(meses) - 1
            year_blocks.append((int(a), c0, c1, [MAP_MES_NOMBRE_A_NUM[m] for m in meses]))
            col_ptr = c1 + 1
        last_col = (col_ptr - 1) if col_ptr > 1 else 0

        # Relleno blanco de tema
        white_fill = wb.add_format({"bg_color": "#FFFFFF", "pattern": 1})
        ws.set_column(0, max(0, last_col), 12, white_fill)
        for r in range(0, max(last_row, 1) + 1):
            ws.set_row(r, None, white_fill)

        # Cabeceras AÑO
        for (a, c0, c1, _mn) in year_blocks:
            ws.merge_range(0, c0, 0, c1, str(a),
                           make_fmt(base_header, top=1,
                                    right=(1 if c1 == last_col else 0),
                                    left=(1 if c0 == 1 else 0)))
        # Fila de MESES
        for (_a, c0, _c1, mn) in year_blocks:
            for k, m in enumerate(mn):
                cc = c0 + k
                ws.write(1, cc, MAP_MES_NUM_A_NOMBRE[m],
                         make_fmt(base_month, top=1, bottom=1,
                                  right=(1 if cc == last_col else 0),
                                  left=(1 if cc == c0 else 0)))

        # Columna Concepto
        for i, concepto in enumerate(CONCEPTOS_CANON):
            r = first_data_row + i
            ws.write(r, 0, concepto,
                     make_fmt(base_concept, left=1, right=1, bottom=(1 if r == last_row else 0)))

        # Mapa fuzzy para índices de fila
        nombres = dfm[first_col].astype(str).tolist()
        norm2idx = { _normalize_text(v): i for i, v in enumerate(nombres) }
        def find_idx(keys):
            for nm, ii in norm2idx.items():
                if any(k in nm for k in keys): return ii
            return None
        fila_pet = find_idx(["poblacion en edad de trabajar","poblacion en ed trabajar","edad de trabajar"])
        fila_tgp = find_idx(["tasa global de participacion","tgp","participacion"])
        fila_to  = find_idx(["tasa de ocupacion","to","ocupacion"])
        fila_map = {CONCEPTOS_CANON[0]: fila_pet, CONCEPTOS_CANON[1]: fila_tgp, CONCEPTOS_CANON[2]: fila_to}

        # Escribe valores con formato 0.00
        for i, concepto in enumerate(CONCEPTOS_CANON):
            r = first_data_row + i
            ridx = fila_map.get(concepto, None)
            for (ay, c0, _c1, mn) in year_blocks:
                for k, m in enumerate(mn):
                    cc = c0 + k
                    mtxt = MAP_MES_NUM_A_NOMBRE[m]
                    v = np.nan
                    try:
                        if ridx is not None and (str(ay), mtxt) in dfm.columns:
                            v = _coerce_numeric_series(pd.Series([dfm.iloc[ridx][(str(ay), mtxt)]]))[0]
                    except Exception:
                        v = np.nan
                    ws.write(r, cc, v,
                             make_fmt(base_value,
                                      right=(1 if cc == last_col else 0),
                                      bottom=(1 if r == last_row else 0),
                                      numfmt="0.00"))

        ws.set_column(0, 0, 42)
        if last_col >= 1: ws.set_column(1, last_col, 12)
        return

    # --- Fallback: si no hay meses/años, solo imprime la columna Concepto con tema
    white_fill = wb.add_format({"bg_color": "#FFFFFF", "pattern": 1})
    ws.set_column(0, 0, 42, white_fill)
    for i, concepto in enumerate(CONCEPTOS_CANON):
        r = first_data_row + i
        ws.set_row(r, None, white_fill)
        ws.write(r, 0, concepto, make_fmt(base_concept, left=1, right=1, bottom=(1 if r == last_row else 0)))

# ==============================================================================
# Pipeline principal: validaciones + exportación de hojas + estilos
# ==============================================================================

def procesar_df(df_base: pd.DataFrame, df_multi: pd.DataFrame|None = None):
    """
    - Detecta columnas numéricas con heurística (≥70% convertible).
    - Genera las hojas: Datos_Limpiados, Validaciones, Reporte_Columnas y Datos_Deseados.
    - Devuelve el binario del Excel en memoria + resumen de columnas.
    """
    df_limpio = df_base.copy()
    reporte, validaciones = [], []

    # Heurística numérica por columna
    for col in df_base.columns:
        serie = df_base[col]
        n_no_nulos = int(serie.notna().sum())
        conv_test = pd.to_numeric(serie, errors="coerce")
        porc = (conv_test.notna().sum() / n_no_nulos * 100) if n_no_nulos else 0.0
        es_num = porc >= 70  # Umbral configurable
        if es_num:
            df_limpio[col] = _coerce_numeric_series(serie)
        reporte.append({
            "columna": str(col),
            "tipo_detectado": "numérica" if es_num else "no numérica",
            "no_nulos": n_no_nulos,
            "porc_convertible": round(porc, 2),
            "nulos_post_coerce": int(df_limpio[col].isna().sum())
        })

    # Validaciones simples de ejemplo
    posibles_id = [c for c in df_base.columns if str(c).lower() in
                   ["id","codigo","cod_mpio","cod_departamento","departamento","municipio"]]
    for c in posibles_id:
        falt = int(df_limpio[c].isna().sum())
        if falt > 0:
            validaciones.append({"regla":"Obligatorio no nulo","columna":c,"detalle":f"{falt} valores faltantes"})

    for r in reporte:
        if r["tipo_detectado"]=="numérica":
            col = r["columna"]
            mask = df_limpio[col].isna() & df_base[col].notna()
            n_bad = int(mask.sum())
            if n_bad>0:
                ejemplos = df_base.loc[mask, col].astype(str).head(3).tolist()
                validaciones.append({"regla":"Numérica coercible","columna":col,
                                     "detalle":f"{n_bad} valores no numéricos. Ejemplos: {ejemplos}"})

    # --- Exportación de hojas a un Excel en memoria (BytesIO)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        # 1) Datos_Limpiados (sin redondeo; formato se pone por columna)
        df_out = _df_clean(df_limpio)
        df_out.to_excel(writer, sheet_name="Datos_Limpiados", index=False, na_rep="")

        # 2) Estilos SOLO para TGP (0.00) y Año/Mes (0)
        wb = writer.book
        ws_limpios = writer.sheets["Datos_Limpiados"]
        fmt_2dec = wb.add_format({"num_format": "0.00"})
        fmt_int  = wb.add_format({"num_format": "0"})

        col_anno, col_mes = _safe_anno_mes(df_out)

        # Detecta la columna TGP por alias
        norm_cols = {c: _normalize_text(c) for c in df_out.columns}
        tgp_col = None
        for c, n in norm_cols.items():
            if ("tasa global de participacion" in n) or (n == "tgp") or ("global de participacion" in n):
                tgp_col = c; break

        # Aplica formato de números a las columnas seleccionadas
        if tgp_col is not None:
            j = df_out.columns.get_loc(tgp_col)
            ws_limpios.set_column(j, j, 12, fmt_2dec)   # TGP = 0.00
        if col_anno and col_anno in df_out.columns:
            j = df_out.columns.get_loc(col_anno)
            ws_limpios.set_column(j, j, 10, fmt_int)    # Año = 0
        if col_mes and col_mes in df_out.columns:
            j = df_out.columns.get_loc(col_mes)
            ws_limpios.set_column(j, j, 10, fmt_int)    # Mes = 0

        # Ancho razonable para el resto
        for j, col in enumerate(df_out.columns):
            if col in {tgp_col, col_anno, col_mes}:
                continue
            ws_limpios.set_column(j, j, 18)

        # 3) Hojas de Validaciones/Reporte
        (_df_clean(pd.DataFrame(validaciones)) if validaciones else
         pd.DataFrame(columns=["regla","columna","detalle"]))\
            .to_excel(writer, sheet_name="Validaciones", index=False, na_rep="")
        _df_clean(pd.DataFrame(reporte)).to_excel(writer, sheet_name="Reporte_Columnas", index=False, na_rep="")

        # 4) Hoja "Datos_Deseados" con tema y bordes
        _escribir_datos_deseados_desde_limpios(writer, df_limpio, df_multi)

    output.seek(0)
    return output, reporte, validaciones

# ==============================================================================
# Rutas Flask
# ==============================================================================

@app.route("/", methods=["GET","POST"])
def index():
    """
    GET: muestra el formulario.
    POST: procesa el archivo, arma el Excel y muestra resumen + vista previa.
    """
    global buffer_xlsx, resumen_reporte
    if request.method == "POST":
        f = request.files.get("file")
        if not f or not f.filename:
            return render_template_string(HTML, mensaje="Adjunta un archivo (.xlsx o .csv).", listo=False)

        fname = f.filename.lower()
        try:
            df_multi = None
            if fname.endswith(".csv"):
                # Carga CSV directamente
                df = pd.read_csv(f)
            elif fname.endswith(".xlsx"):
                # Lee Excel: usa hoja 'Base' si existe, si no la primera
                xls = pd.ExcelFile(f)
                base_candidates = [sh for sh in xls.sheet_names if sh.lower().strip() == "base"]
                sheet = base_candidates[0] if base_candidates else xls.sheet_names[0]
                df, df_multi = _leer_base_robusto(xls, sheet)
            else:
                return render_template_string(HTML, mensaje="Formato no soportado. Usa .xlsx o .csv.", listo=False)
        except Exception as e:
            return render_template_string(HTML, mensaje=f"Error leyendo el archivo: {e}", listo=False)

        try:
            # Genera el anexo y el resumen
            buffer_xlsx, resumen_reporte, _ = procesar_df(df, df_multi)
            # Construye la vista previa para la interfaz
            preview = _build_preview_datos_deseados(df, df_multi)
        except Exception as e:
            return render_template_string(HTML, mensaje=f"Error procesando datos: {e}", listo=False)

        # Render con mensaje, resumen, preview y botón de descarga
        return render_template_string(
            HTML,
            mensaje="✅ Anexo listo.",
            listo=True,
            resumen=resumen_reporte,
            preview=preview
        )

    # GET simple: solo el formulario
    return render_template_string(HTML, mensaje=None, listo=False)

@app.route("/download")
def download():
    """Devuelve el archivo Excel generado como adjunto."""
    if buffer_xlsx is None:
        return render_template_string(HTML, mensaje="Primero carga y valida un archivo.", listo=False)
    return send_file(buffer_xlsx, as_attachment=True, download_name="anexo.xlsx",
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

def _open_browser(url="http://127.0.0.1:5000/"):
    """Abre el navegador automáticamente al iniciar el servidor."""
    time.sleep(0.6)
    try: webbrowser.open_new(url)
    except Exception: pass

if __name__ == "__main__":
    # Hilo para abrir el navegador y evitar bloquear el main thread de Flask
    threading.Thread(target=_open_browser, daemon=True).start()
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)

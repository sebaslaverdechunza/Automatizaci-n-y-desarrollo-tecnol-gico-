# 📊 Pregunta 1 – Aplicativo de carga y exportación

Imagina que debes construir un aplicativo sencillo (puede ser en **R Shiny, Flask/Django en Python** o cualquier framework web básico) que:

+ Permita cargar un archivo tabular (ej. .csv o .xlsx).
+ Genere automáticamente un archivo extraíble en formato Excel (el “anexo”), con las validaciones mínimas de estructura (por ejemplo, que todas las columnas numéricas sean realmente numéricas).
    
👉 **Pregunta**: Describe el diseño del aplicativo (interfaz y lógica interna) y escribe un pseudocódigo o fragmento de código que muestre cómo implementarías:

- La carga del archivo.
- La validación mínima de los datos.
- La exportación en formato Excel.
---
## **Solución:**

### 1). Descripción breve

Aplicación web mínima (**Flask**) que:

+ Carga archivos .xlsx o .csv.
+ Valida estructura básica y detecta columnas numéricas con una heurística (≥70% de valores convertibles).
+ Genera un anexo Excel con hojas:

     + Datos_Limpiados (valores numéricos convertidos; TGP con formato 0.00; Año/Mes como enteros),

     + Validaciones (hallazgos y advertencias),

     + Reporte_Columnas (perfilado básico),

     + Datos_Deseados (matriz final por Concepto × Año/Mes).

+ Interfaz con: carga de archivo, tabla Resumen de columnas y vista previa HTML de Datos_Deseados; botón Descargar anexo.

> Se asume que la base puede venir en una hoja Base (o la primera hoja si no existe) y que “Total Nacional” es una referencia de cómo se espera ver la información.
---

### 2). Diseño del aplicativo

**Interfaz (UI)**

+ Formulario para subir .xlsx/.csv.
+ Resumen de columnas: nombre, tipo detectado (numérica/no numérica), % convertible, nulos tras conversión.
+ Vista previa de la tabla Datos_Deseados (cabeceras por Año, fila de Meses y filas de Conceptos).
+ Botón “Descargar anexo”.

**Lógica interna (backend)**

1. Ingesta

    + Si es .xlsx: lee hoja Base (si existe); adicionalmente intenta reconstruir cabeceras multi-nivel si detecta filas con “Concepto”.

    + Si es .csv: lectura directa.

2. Perfilado y validación mínima

    + Para cada columna: intenta convertir a numérico tras limpieza (quita %, NBSP, espacios; coma→punto).

    + Heurística: si ≥70% de valores no nulos se convierten, la columna se trata como numérica.

    + Registra advertencias (nulos en IDs comunes, valores no convertibles, etc.).

3. Normalización auxiliar

    + Detecta Año/Mes por alias (año/ano/anno/year, mes/month), mapea Ene..Dic ↔ 1..12.

4. Construcción de hojas

    + **Datos_Limpiados**: datos post-coerción (sin redondear a nivel de dato); solo TGP se formatea a 0.00 en Excel; Año/Mes como 0.

    + **Datos_Deseados**: si existen Año/Mes y una columna de valores (TGP), pivotea a Concepto × (Año, Mes). Aplica estilo: tema blanco, años/meses en negrilla, conceptos sin negrilla, bordes #e5e7eb, valores con 0.00.

5. Exportación

    + Crea un BytesIO y escribe con xlsxwriter.

    + Ofrece descarga como anexo_validado.xlsx.

---

### 3). Pseudocódigo (bosquejo)

```text
POST /:
  archivo = request.files["file"]
  if ext == .xlsx:
      df_simple, df_multi = leer_base_robusto(xlsx, sheet="Base" o primera)
  elif ext == .csv:
      df_simple = read_csv(...)
      df_multi = None
  else:
      error("Formato no soportado")

  df_limpio, resumen, validaciones = validar_y_convertir(df_simple)
  binario_excel = construir_excel(df_limpio, df_multi, validaciones, resumen)
  preview = construir_preview_html(df_limpio o df_multi)

  render(template, resumen=resumen, preview=preview, link_descarga=/download)
```
**Validación mínima:**

```text
validar_y_convertir(df):
  for col in df.columns:
    s_limpia = limpiar_texto_num(df[col])    # quita %, NBSP, espacios, coma→punto
    conv = to_numeric(s_limpia, errors="coerce")
    porc = porcentaje_no_nulos(conv)
    if porc >= 70%:
       df[col] = conv                        # convierte a numérico
       reporta(tipo="numérica", porc=porc)
    else:
       reporta(tipo="no numérica", porc=porc)
  valida_nulos_en_IDs(df)
  return df, resumen, validaciones
```

**Exportación a Excel:**

```text
construir_excel(df_limpio, df_multi, validaciones, resumen):
  with ExcelWriter(engine="xlsxwriter") as writer:
    # Hoja 1: Datos_Limpiados
    escribir(df_limpio)
    formatear(TGP -> "0.00", Año/Mes -> "0")

    # Hoja 2: Validaciones
    escribir(validaciones)

    # Hoja 3: Reporte_Columnas
    escribir(resumen)

    # Hoja 4: Datos_Deseados
    if (Año, Mes detectados) y (columna valor detectada):
        pv = pivotear_por(Concepto x (Año, Mes))
        aplicar_estilos_tema_blanco_bordes(pv)
    else if df_multi:
        reconstruir_desde_multiindex_y_estilar()

  return bytes_del_archivo

```
---
### 4). Ejecutar (app.py)

**Requisitos**: Python 3.10+ · `Flask`, `pandas`, `numpy`, `openpyxl`, `xlsxwriter`

```bash
(Opción A)

python -m venv .venv
# En PowerShell (si aplica): Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
# Activar venv:
#   PS:   .\.venv\Scripts\Activate.ps1
#   CMD:  .\.venv\Scripts\activate.bat
#   macOS/Linux: source .venv/bin/activate

(Opción B)

PS C:\Users\USUARIO\Documents\PRUEBAS\DANE - AUTOMATIZACIONES\app_validador> & "C:/Users/USUARIO/Documents/PRUEBAS/DANE - AUTOMATIZACIONES/app_validador/.venv/Scripts/python.exe" "c:/Users/USUARIO/Documents/PRUEBAS/DANE - AUTOMATIZACIONES/app_validador/app.py"


pip install Flask pandas numpy openpyxl XlsxWriter
python app.py
```
> Abrir en http://127.0.0.1:5000/, subir archivo y Descargar anexo.
---

 # 📊 Pregunta 2 – Diagrama de procesos para la GEIH

Considerando que una operación como la **GEIH** pasa por:

    + Recolección de datos
    + Carga y validación
    + Construcción de factores de expansión
    + Generación de bases de datos validadas
    + Estimación de errores estándar y varianzas
    + Producción de anexos/tablas de salida

    
👉 **Pregunta**: Diseña un **diagrama de procesos** (puede ser un flujo con cajas y flechas, pseudodiagrama o explicación textual detallada) que muestre cómo automatizarías esas fases, identificando:

    - Entradas y salidas de cada fase.
    - Herramientas/lenguajes que usarías (ej. R, Python, SQL, ETL).
    - Puntos críticos donde pondrías validaciones automáticas.
---

## **Solución:**

Este documento presenta un **bosquejo general** de cómo automatizar el proceso de la **Gran Encuesta Integrada de Hogares (GEIH)**.  
El objetivo no es una implementación completa, sino un esquema conceptual que demuestre habilidades de diseño de pipelines, mostrando de manera clara:

- Las **fases principales** (recolección, validación, factores, bases validadas, estimación y producción de anexos).  
- Las **entradas y salidas** de cada fase.  
- Las **herramientas y lenguajes** adecuados (Python, R, SQL, orquestadores ETL).  
- Los **puntos críticos de validación automática** donde se asegura la calidad y consistencia de los datos.

---
## Glosario de capas de datos

+ **Bronze** → Datos crudos, tal como llegan (sin cambios, solo estandarizados).
+ **Silver** → Datos limpios, con tipos corregidos, sin duplicados, listos para análisis preliminar.
+ **Gold** → Datos ya validados y enriquecidos, con todas las reglas de negocio aplicadas, factores de expansión incorporados y listos para producir indicadores oficiales.

---

## 🚀 Diseño del proceso (flujo general)

```text
[Inicio: Fuentes de Datos Externas]
          |
          v
+----------------------------------+
| Fase 1: Recolección de Datos     |
+----------------------------------+
   (Archivos crudos + metadatos)
          |
          v
+----------------------------------+   
| Fase 2: Carga y Validación       |  <-- (Vuelve a Fase 1 si falla validación)
+----------------------------------+
   (Silver + bitácora de calidad)
          |
          v
+----------------------------------+   
| Fase 3: Factores de Expansión    |  <-- (Vuelve a Fase 2 si factores inconsistentes)
+----------------------------------+
   (Factores calibrados)
          |
          v
+----------------------------------+
| Fase 4: Bases Validadas (Gold)   |
+----------------------------------+
   (Tablas persona/hogar de análisis)
          |
          v
+----------------------------------+  
| Fase 5: Estimación de EE y Varianzas |  <-- (Vuelve a Fase 4 si varianzas anómalas)
+----------------------------------+
   (Indicadores con EE/CV/IC)
          |
          v
+----------------------------------+
| Fase 6: Anexos / Tablas de Salida|
+----------------------------------+
   (Excel, CSV, dashboards, API)
          |
          v
[Fin: Productos Finales]
```

> **Nota:** “Vuelve a Fase X” representa un **feedback loop**: si una validación falla en una fase, el pipeline regresa a la fase previa para corrección antes de continuar.

---

## Resumen del flujo general

| Fase                      | Entradas                                     | Salidas                                                   | Herramientas                      | Validaciones críticas                                        |
| ------------------------- | -------------------------------------------- | --------------------------------------------------------- | --------------------------------- | ------------------------------------------------------------ |
| 1. Recolección            | Formularios (CAPI/CATI/ODK) + metadatos      | Crudos (CSV/JSON/Parquet), manifiestos                    | ODK/CSPro/SurveyCTO               | Saltos lógicos, rangos duros (edad 0–110), ocupación–horas   |
| 2. Carga y validación     | Crudos                                       | Bronze (estandarizado), Silver (tipos/llaves), reporte DQ | Python/R, Great Expectations, SQL | Esquema, tipos, IDs únicos, reglas lógicas y geográficas     |
| 3. Factores de expansión  | Silver + marco + proyecciones                | Factores base y calibrados (dominio/estrato)              | R `samplesize4surveys, survey` / Python `statsmodels` | Suma pesos ≈ población; pesos > 0; estabilidad histórica     |
| 4. Bases validadas (Gold) | Silver + factores                            | Gold (persona/hogar) + codebook                           | SQL/dbt, pandas/data.table        | Integridad hogar–persona; cobertura por dominio; derivadas   |
| 5. Estimación de EE y Varianzas | Gold + diseño (estrato, UPM, fpc) + factores | Indicadores con EE, CV, IC                                | R `samplesize4surveys, survey` (estándar)             | CV ≤ umbrales; n efectivo; coherencia temporal               |
| 6. Anexos / salida        | Indicadores validados                        | Excel/CSV, dashboards, API                                | Python (xlsxwriter/FastAPI), BI   | Formatos (decimales/hojas), totales consistentes, versionado |

---

## ⚙️ Orquestación y control

+ **Orquestador**: Airflow o Prefect (DAG mensual con retries y alertas).
+ **Capas de datos**: Bronze → Silver → Gold (lineage y trazabilidad).
+ **Versionado**: Git para código; convenciones de datasets versionados.
+ **Seguridad**: control de accesos y anonimización de microdatos cuando aplique.

---

## <img width="25" height="25" alt="image" src="https://github.com/user-attachments/assets/6ec57bed-b386-492a-82b2-8ceb2eba4c79" /> Pseudodiagrama de automatización (ejemplo con Prefect)

```python
from prefect import flow, task   # Prefect permite orquestar pipelines con tareas y flujos

# ------------------ FASE 1: Recolección de datos (Bronze) ------------------
@task(retries=2)                  # Si falla, intenta 2 veces más (robustez)
def ingest():
    # Simula la ingesta de datos crudos desde formularios/campo
    # Retorna la "capa Bronze": datos sin procesar, estandarizados
    return "bronze"

# ------------------ FASE 2: Carga y Validación (Silver) ------------------
@task
def validate(bronze):
    # Recibe datos Bronze
    # Aplica validaciones (tipos correctos, IDs únicos, rangos)
    # Retorna:
    #   - "silver": datos limpios y listos
    #   - "dq_report": reporte de calidad con errores detectados
    return "silver", "dq_report"

# ------------------ FASE 3: Factores de Expansión ------------------
@task
def build_weights(silver):
    # Recibe datos Silver
    # Calcula factores de expansión (pesos para representar población total)
    # Retorna "weights": factores calibrados
    return "weights"

# ------------------ FASE 4: Bases validadas (Gold) ------------------
@task
def assemble_gold(silver, weights):
    # Combina datos Silver con los factores de expansión
    # Integra tablas de hogares y personas → base final validada
    # Retorna "gold": base Gold lista para análisis
    return "gold"

# ------------------ FASE 5: Estimación de indicadores ------------------
@task
def estimate(gold):
    # Recibe la base Gold
    # Calcula indicadores (ej. tasa de desempleo) + errores estándar / CV
    # Retorna "indicadores": dataset con resultados estadísticos
    return "indicadores"

# ------------------ FASE 6: Producción de anexos/tablas ------------------
@task
def make_annex(indicadores):
    # Recibe indicadores
    # Genera los anexos/tablas oficiales en Excel, CSV, dashboards
    # Retorna archivo final (ej. "anexos.xlsx")
    return "anexos.xlsx"

# ------------------ ORQUESTACIÓN DEL PIPELINE ------------------
@flow
def geih_pipeline():
    # Orquesta las fases en orden secuencial:
    bronze = ingest()                             # 1. Ingesta (Bronze)
    silver, dq = validate(bronze)                 # 2. Validación (Silver + reporte DQ)
    weights = build_weights(silver)               # 3. Factores de expansión
    gold = assemble_gold(silver, weights)         # 4. Base validada (Gold)
    indicadores = estimate(gold)                  # 5. Indicadores + EE
    anexos = make_annex(indicadores)              # 6. Anexos de salida
    return anexos                                 # Resultado final del pipeline
```
---

✅ Conclusión  
Este diseño organiza la operación de la GEIH en fases claras con sus entradas, salidas, herramientas y validaciones críticas, asegurando trazabilidad y control de calidad en todo el pipeline.




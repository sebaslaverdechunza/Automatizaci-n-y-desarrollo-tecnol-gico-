# 📊 Validador y Exportador de Anexos (Pregunta 1 – Aplicativo de carga y exportación)

Aplicativo web sencillo para cargar archivos tabulares (`.csv` o `.xlsx`), validar mínimamente la estructura y exportar un archivo Excel (“anexo”) con los datos limpios y un registro de errores.

Este ejercicio corresponde a la **Pregunta 1 – Aplicativo de carga y exportación**.

---

## 🚀 Instalación y ejecución

### 1. Clonar o copiar el repositorio
Ubícate en la carpeta de trabajo y crea un entorno virtual:

```bash
python -m venv .venv
```

### 2. Activar el entorno virtual
Windows PowerShell:

```bash
.\.venv\Scripts\Activate.ps1
```
### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Ejecutar el aplicativo

```bash
streamlit run app.py
```

La aplicación se abrirá en tu navegador en:
http://localhost:8501/
---

🖥️ Interfaz del aplicativo

+ Subida de archivo (.csv o .xlsx).

+ Si es Excel: detección automática de hojas y selector de cuál procesar.

+ Opcionales:

     + Columnas obligatorias: asegura que ciertas variables estén presentes.

     + Columnas porcentaje: permite forzar que se validen como %.

+ Botón Validar y generar anexo.

+ Panel de resultados:

     + Resumen de validación.

     + Vista previa (primeras 20 filas).

     + Errores detectados.

     + Botón de descarga del anexo validado.
 

 ---
 
✅ Pregunta 1 – Aplicativo de carga y exportación

## 🖥️ Diseño del aplicativo

### Interfaz
- **Input de archivo**: cargar un `.csv` o `.xlsx`.
- **Selector de hoja** (si es Excel; por defecto se usa `Base`).
- **Botón de validación y exportación**.
- **Vista previa**: primeras filas del archivo cargado.
- **Botón de descarga**: genera el anexo Excel con:
  - `Datos_Limpios` → tabla con columnas numéricas convertidas.
  - `Errores_Validacion` → lista de celdas que no pudieron convertirse.

### Lógica interna
1. **Carga del archivo** en memoria (con `pandas`).
2. **Detección de columnas numéricas**: si ≥80% de los valores pueden convertirse a número.
3. **Conversión y validación**:  
   - Se normalizan separadores de miles/decimales.  
   - Se registran celdas no convertibles indicando fila y columna.  
4. **Exportación**: se genera un Excel con dos hojas (datos limpios + errores).

---

## 🔎 Pseudocódigo

INICIO
  archivo <- subir (.csv | .xlsx)
  si es Excel:
      hoja <- seleccionar (por defecto “Base”)

  df <- leer_archivo(archivo, hoja)

  clean <- copiar(df)
  errores <- []

  PARA cada columna en df:
    si es numérica:
      parsed <- normalizar_y_convertir(columna)
      registrar errores si no convertible
      si columna es porcentaje:
        registrar errores si valor <0 o >100
        guardar como fracción (Excel %)
      sino:
        guardar como numérico

  generar Excel con:
    - Hoja Datos_Limpios
    - Hoja Errores_Validacion
  ofrecer descarga
FIN

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




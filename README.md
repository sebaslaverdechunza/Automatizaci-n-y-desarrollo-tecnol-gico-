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
| Fase 3: Factores de Expansión    |   <-- (Vuelve a Fase 2 si factores inconsistentes)
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
| Fase 5: EE y Varianzas           |     <-- (Vuelve a Fase 4 si varianzas anómalas)
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
---

## Resumen del flujo general

| Fase                      | Entradas                                     | Salidas                                                   | Herramientas                      | Validaciones críticas                                        |
| ------------------------- | -------------------------------------------- | --------------------------------------------------------- | --------------------------------- | ------------------------------------------------------------ |
| 1. Recolección            | Formularios (CAPI/CATI/ODK) + metadatos      | Crudos (CSV/JSON/Parquet), manifiestos                    | ODK/CSPro/SurveyCTO               | Saltos lógicos, rangos duros (edad 0–110), ocupación–horas   |
| 2. Carga y validación     | Crudos                                       | Bronze (estandarizado), Silver (tipos/llaves), reporte DQ | Python/R, Great Expectations, SQL | Esquema, tipos, IDs únicos, reglas lógicas y geográficas     |
| 3. Factores de expansión  | Silver + marco + proyecciones                | Factores base y calibrados (dominio/estrato)              | R `survey` / Python `statsmodels` | Suma pesos ≈ población; pesos > 0; estabilidad histórica     |
| 4. Bases validadas (Gold) | Silver + factores                            | Gold (persona/hogar) + codebook                           | SQL/dbt, pandas/data.table        | Integridad hogar–persona; cobertura por dominio; derivadas   |
| 5. EE y Varianzas         | Gold + diseño (estrato, UPM, fpc) + factores | Indicadores con EE, CV, IC                                | R `survey` (estándar)             | CV ≤ umbrales; n efectivo; coherencia temporal               |
| 6. Anexos / salida        | Indicadores validados                        | Excel/CSV, dashboards, API                                | Python (xlsxwriter/FastAPI), BI   | Formatos (decimales/hojas), totales consistentes, versionado |


---

## 🧩 Orquestación y control

+ **Orquestador**: Airflow o Prefect (DAG mensual con retries y alertas).
+ **Capas de datos**: Bronze → Silver → Gold (lineage y trazabilidad).
+ **Versionado**: Git para código; convenciones de datasets versionados.
+ **Seguridad**: control de accesos y anonimización de microdatos cuando aplique.

---

## <img width="280" height="280" alt="image" src="https://github.com/user-attachments/assets/6ec57bed-b386-492a-82b2-8ceb2eba4c79" /> Pseudodiagrama de automatización (ejemplo con Prefect)

```PYTHON
from prefect import flow, task

@task(retries=2)
def ingest(): return "bronze"

@task
def validate(bronze): return "silver", "dq_report"

@task
def build_weights(silver): return "weights"

@task
def assemble_gold(silver, weights): return "gold"

@task
def estimate(gold): return "indicadores"

@task
def make_annex(indicadores): return "anexos.xlsx"

@flow
def geih_pipeline():
    bronze = ingest()
    silver, dq = validate(bronze)
    weights = build_weights(silver)
    gold = assemble_gold(silver, weights)
    indicadores = estimate(gold)
    anexos = make_annex(indicadores)
    return anexos


## 📥 1. Recolección de datos

     Qué hace: Enumeradores capturan la información en campo (hogares y personas).
     Entradas: cuestionarios en tablets o formularios web.
     Salidas: archivos crudos (CSV/JSON/Excel) + metadatos (fecha, encuestador, ubicación).

- **Entradas**: formularios de campo (CAPI, CATI, ODK, CSPro).  
- **Salidas**: archivos crudos (CSV/JSON/Parquet) + manifiestos (metadatos de enumerador, fecha, GPS).  
- **Herramientas**: sistemas de captura; exportadores a S3/GCS/FTP.  
- **Validaciones críticas**:  
  - Saltos lógicos del cuestionario.  
  - Rangos duros (edad 0–110, personas en hogar ≥1).  
  - Consistencia básica (ocupado ⇒ horas>0).  
```


---

## 🔍 2. Carga y validación

     Qué hace: Ingresa los archivos crudos a un sistema de almacenamiento y verifica su calidad.
     Entradas: Archivos crudos.
     Salidas: Datos limpios de primera capa (“Silver”) + reporte de errores.
     Validaciones típicas:
          - Que no falten columnas.
          - Que los IDs sean únicos.
          - Que los valores estén en rango (ej. edad no negativa).

- **Entradas**: archivos crudos.  
- **Salidas**:  
  - Capa **Bronze** (crudos estandarizados, inmutables).  
  - Capa **Silver** (con tipos corregidos, claves limpias).  
  - Bitácora de errores de calidad.  
- **Herramientas**: Python (pandas), R (data.table), Great Expectations.  
- **Validaciones críticas**:  
  - Presencia de columnas esperadas.  
  - Tipos correctos (numéricos, strings).  
  - Unicidad de IDs.  
  - Reglas lógicas (ej. menores de 12 no deberían tener ocupación).

---

## ⚖️ 3. Factores de expansión

     Qué hace: genera pesos para que cada persona/hogar represente a la población total.
     Entradas: bases limpias + marco muestral + proyecciones de población.
     Salidas: factores ajustados y calibrados (un número por registro).
     Valida: que la suma de factores ≈ población oficial.
          
- **Entradas**: base Silver + marco muestral + población proyectada.  
- **Salidas**: factores base y calibrados por dominio/estrato.  
- **Herramientas**: R (`survey`, `srvyr`), Python (`statsmodels`).  
- **Validaciones críticas**:  
  - Suma de pesos ≈ población objetivo.  
  - Pesos positivos y razonables.  
  - Comparación histórica de distribución de pesos.  

---

## 🗄️ 4. Bases de datos validadas (Gold)

    Qué hace: integra datos de hogares y personas en una base lista para análisis (“Gold”).
    Entradas: datos Silver + factores.
    Salidas: tablas finales (hogar/persona) con variables derivadas (ej. tasas de participación).
    Valida: consistencia entre hogar y persona, y cobertura por dominios.

- **Entradas**: Silver + factores.  
- **Salidas**: tablas integradas (persona, hogar) listas para análisis.  
- **Herramientas**: Python (pandas), R (data.table), SQL/dbt.  
- **Validaciones críticas**:  
  - Integridad hogar-persona.  
  - Cobertura mínima por dominio.  
  - Variables derivadas consistentes (ej. tasas calculadas).  

---

## 📊 5. Estimación de errores estándar y varianzas

    Qué hace: calcula no solo los indicadores (ej. tasa de desempleo), sino también su precisión (errores estándar, coeficientes de variación).
    Entradas: bases Gold + diseño muestral (estratos, UPM) + factores.
    Salidas: indicadores con EE y CV por dominio/periodo.
    Valida: que los errores no sean excesivos y que haya casos suficientes por grupo.

- **Entradas**: base Gold + diseño muestral (estratos, UPM, fpc) + factores.  
- **Salidas**: indicadores con estimaciones, EE, CV e intervalos de confianza.  
- **Herramientas**: R (`survey`) como estándar; Python (`statsmodels.survey`).  
- **Validaciones críticas**:  
  - CV dentro de umbrales.  
  - Casos efectivos por dominio.  
  - Coherencia temporal.  

---

## 📑 6. Producción de anexos/tablas de salida

    Qué hace: genera los productos finales para publicar.
    Entradas: indicadores validados.
    Salidas: Excel, CSV, tableros (Power BI, Metabase) o API para consulta automática.
    Valida: formatos correctos, totales consistentes, decimales uniformes.

- **Entradas**: indicadores validados.  
- **Salidas**:  
  - Archivos Excel/CSV con tablas oficiales.  
  - Dashboards (Power BI, Metabase).  
  - API (FastAPI) para consulta automática.  
- **Herramientas**: Python (`xlsxwriter`, FastAPI), R (`openxlsx`, `flextable`).  
- **Validaciones críticas**:  
  - Formatos correctos (decimales, nombres de hoja).  
  - Totales y tasas reproducen resultados auditados.  

---

## ⚙️ Orquestación y control
- **Orquestador**: Airflow o Prefect con DAG mensual.  
- **Monitoreo**: alertas en caso de errores.  
- **Versionado**: Git para código; versionado de datasets (Bronze/Silver/Gold).  
- **Seguridad**: control de accesos y anonimización de microdatos.

---

## 🧩 Pseudodiagrama de automatización (Prefect)

```python
from prefect import flow, task

@task
def ingest(): return "bronze"

@task
def validate(bronze): return "silver", "dq_report"

@task
def build_weights(silver): return "weights"

@task
def assemble_gold(silver, weights): return "gold"

@task
def estimate(gold): return "indicadores"

@task
def make_annex(indicadores): return "anexos.xlsx"

@flow
def geih_pipeline():
    bronze = ingest()
    silver, dq = validate(bronze)
    weights = build_weights(silver)
    gold = assemble_gold(silver, weights)
    indicadores = estimate(gold)
    anexos = make_annex(indicadores)
    return anexos
```

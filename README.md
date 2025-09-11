# 📊 Validador y Exportador de Anexos

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


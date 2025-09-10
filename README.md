# Aplicativo de carga y exportación

Este aplicativo sencillo permite cargar un archivo tabular (`.csv` o `.xlsx`), realizar una validación mínima de las columnas numéricas y exportar un **anexo en formato Excel** con los datos limpios y un registro de errores de validación.

---

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

```text
INICIO

mostrar input de archivo (csv/xlsx)
si xlsx:
    seleccionar hoja (default: "Base")

leer archivo a dataframe
crear copia clean

numeric_cols <- []
PARA cada columna c EN dataframe:
    si >=80% de valores parseables a número:
        numeric_cols.agregar(c)

errores <- []
PARA cada columna c EN numeric_cols:
    parsed <- convertir valores a número
    SI valor original no vacío Y parsed es NA:
        registrar error (fila_excel, columna, valor_original)
    reemplazar columna por parsed en clean

exportar Excel con dos hojas:
    - Datos_Limpios: clean
    - Errores_Validacion: errores

mostrar botón de descarga

FIN

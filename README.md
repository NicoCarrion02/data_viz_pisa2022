# PISA 2022: Desempeño, Brechas Educativas y Bienestar Estudiantil

Dashboard analítico e interactivo desarrollado en **Streamlit** y **Plotly** para explorar los microdatos de la evaluación internacional **PISA 2022 (OCDE)**. La herramienta está diseñada para investigadoras/es en ciencias de datos educativas y analistas de política pública, permitiendo transitar fluidamente desde el panorama macro global hasta el nivel de subgrupos socioeconómicos y de género.


## Resumen del Proyecto

Los reportes educativos globales suelen concentrarse en promedios y rankings por país, invisibilizando dinámicas internas clave. Este proyecto resuelve esa limitación mediante un ecosistema interactivo que analiza una muestra de +588k estudiantes evaluados en 79 países y territorios, abordando tres dimensiones críticas:

1. **Rendimiento Académico**: Desempeño en Matemáticas, Lectura y Ciencias.
2. **Equidad Estructural**: Cuantificación de brechas socioeconómicas y disparidades de género.
3. **Bienestar Emocional**: Evaluación de la ansiedad hacia el aprendizaje y sentido de pertenencia escolar.

## Características Principales

* **Sincronización Bidireccional Acumulativa (Linked Selection)**: Interactividad total entre el mapa mundial y el ranking de barras. Al hacer clic en un país (o varios), todos los paneles y KPIs de la aplicación se filtran y actualizan automáticamente.
* **Mapeo Acumulativo de Estado**: Selección y deselección múltiple con un solo clic (sin necesidad de atajos de teclado) gestionada por una máquina de estados en `st.session_state`.
* **Diseño Adaptativo Auto-Ajustable**: Renderizado sobre capas transparentes que soporta nativamente el cambio entre Modo Claro y Modo Oscuro en Streamlit sin pérdida de legibilidad en etiquetas ni métricas.
* **Procesamiento de Alta Eficiencia**: Carga en memoria caché mediante archivos `.parquet` e ingesta optimizada con **Polars** y **Pandas**, logrando tiempos de respuesta de UI inferiores a 50 ms.

## Estructura del Repositorio

```text
proyecto_pisa/
│
├── data/
│   └── pisa2022.parquet        # Dataset procesado PISA 2022 (~588k filas)
│
├── etl.py                      # Módulo de ingesta, agregaciones y cálculo de métricas
├── app.py                      # Aplicación Streamlit y renderizado de visualizaciones
├── requirements.txt            # Dependencias del proyecto
└── README.md                   # Documentación técnica

```

## 🛠️ Instalación y Ejecución Local

### Prerrequisitos

Asegúrate de contar con **Python 3.10** o superior instalado en tu sistema.

### 1. Clonar el repositorio

```bash
git clone [https://github.com/tu-usuario/pisa2022-dashboard.git](https://github.com/tu-usuario/pisa2022-dashboard.git)
cd pisa2022-dashboard

```

### 2. Crear entorno virtual (Recomendado)

```bash
# En Linux/macOS
python3 -m venv venv
source venv/bin/activate

# En Windows
python -m venv venv
venv\Scripts\activate

```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt

```

### 4. Ejecutar la aplicación

```bash
streamlit run app.py

```

La aplicación se abrirá automáticamente en tu navegador predeterminado en `http://localhost:8501`.

## Dataset y Preprocesamiento

El dataset proviene de la base pública oficial de la OCDE para PISA 2022. Para transformar el contenido del zip a parquet se puede usar el siguiente código (asumiendo que se almacenó en ``data/``):

```python
import pandas as pd

def sas_to_parquet():
    df = pd.read_sas(
        "data/CY08MSP_STU_QQQ.SAS7BDAT",
        format="sas7bdat"
    )
    print("Loaded SAS file into DataFrame")

    for col in df.select_dtypes(include=[object]).columns:
        df[col] = df[col].apply(lambda x: x.decode("utf-8") if isinstance(x, bytes) else x)

    df.to_parquet("data/pisa2022.parquet", index=False)
    print("Converted SAS file to Parquet format and saved as data/pisa2022.parquet")
```

* **Tamaño final**: 588,276 estudiantes (post limpieza) x 7 variables principales.
* **Variables seleccionadas**:
* `CNT`: Código ISO de 3 caracteres por país.
* `PV1MATH`, `PV1READ`, `PV1SCIE`: Primeros valores plausibles en Matemáticas, Lectura y Ciencias.
* `ANXMAT`: Índice de ansiedad hacia las matemáticas (Escala WLE, $\mu=0, \sigma=1$).
* `ESCS`: Índice socioeconómico global discretizado en cuartiles ($Q_1$ Bajo a $Q_4$ Alto).
* `ST004D01T`: Identificación de género (Femenino / Masculino).

## Marco de Diseño de Visualización (Modelo de Tamara Munzner)

| Nivel | Decisión de Diseño en el Dashboard |
| --- | --- |
| **1. Domain Problem** | Revelar brechas internas y la paradoja entre rendimiento académico y ansiedad en PISA 2022. |
| **2. Data Abstraction** | Mapeo de variables continuas (puntajes/ansiedad), categóricas (país/género) y ordinales (cuartiles nivel socioeconómico). |
| **3. Task Abstraction** | Comparar promedios globales, identificar anomalías (países con alta nota y baja ansiedad) y cuantificar brechas socioeconómicas. |
| **4. Idiom & Encoding** | Mapa Coroplético (Viridis) + Barras Horizontales Ordenadas (Largo) + Boxplots (Distribución/Dispersion) + KPI Metrics (Delta $vs.$ Mundo). |
| **5. Algorithm** | Manejo de estado centralizado en Streamlit con agregaciones precalculadas en memoria caché (`@st.cache_data`). |

## Principales Hallazgos de la Data

* **Severidad de la Brecha Socioeconómica**: Existe una diferencia promedio mundial de 123.3 puntos entre el cuartil socioeconómico más bajo $Q_1$ ($382.5$ pts) y el más alto $Q_4$ ($505.8$ pts), lo equivalente a más de 3 años de escolaridad lectiva.
* **Inversión de Brecha por Género**: Mientras que los hombres superan a las mujeres en Matemáticas por un margen reducido (+6.4 pts), las mujeres superan drásticamente a los hombres en Lectura por **+24.7 puntos**.
* **Paradoja del Bienestar**: Países de alto desempeño académico como Singapur ($574.9$ pts) y Japón ($536.3$ pts) exhiben niveles de ansiedad estandarizada elevados (+0.16 y +0.33 respectivamente), mientras que naciones como Estonia ($513.4$ pts) logran un alto rendimiento manteniendo niveles de ansiedad neutrales (+0.01).
import pandas as pd

def procesar_datos_completos(ruta_parquet: str) -> pd.DataFrame:
    """Carga y procesa los datos incluyendo las 3 materias principales."""
    cols = ["CNT", "ST004D01T", "ESCS", "PV1MATH", "PV1READ", "PV1SCIE", "ANXMAT"]
    df = pd.read_parquet(ruta_parquet, columns=cols)
    
    # Limpiamos nulos
    df = df.dropna(subset=["CNT", "ESCS"])
    
    # Estandarización
    df["Genero"] = df["ST004D01T"].map({1.0: "Femenino", 2.0: "Masculino", 1: "Femenino", 2: "Masculino"})
    df["Nivel_Socioeconomico"] = pd.qcut(df["ESCS"], 4, labels=["Q1 (Bajo)", "Q2", "Q3", "Q4 (Alto)"])
    
    df = df.rename(columns={"PV1MATH": "Matemáticas", "PV1READ": "Lectura", "PV1SCIE": "Ciencias"})
    return df

def calcular_resumen_macro(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula promedios a nivel país."""
    resumen = df.groupby("CNT").agg(
        Matematicas_Avg=("Matemáticas", "mean"),
        Lectura_Avg=("Lectura", "mean"),
        Ciencias_Avg=("Ciencias", "mean"),
        Ansiedad_Avg=("ANXMAT", "mean"),
        Muestra_Estudiantes=("CNT", "count")
    ).reset_index()
    
    return resumen
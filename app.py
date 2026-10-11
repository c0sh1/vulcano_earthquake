import datetime
import joblib
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
 
st.set_page_config(page_title="Terremotos en Tenerife", page_icon="🌋")
 
st.title("¿Cuántos terremotos habrá en Tenerife?")
st.write(
    "Predicción del número de terremotos de magnitud 1,0 o superior, "
    "en Tenerife y el mar que la rodea. Datos del IGN."
)
 
st.warning(
    "Esta app NO predice erupciones. Solo estima cuántos terremotos pequeños "
    "cabe esperar en un día normal. Para información oficial, consulta al IGN."
)
 
 
# Cargo el modelo y la serie una sola vez
@st.cache_resource
def cargar_modelo():
    return joblib.load("models/modelo_terremotos.pkl")
 
 
@st.cache_data
def cargar_serie():
    return pd.read_csv("data/serie_tenerife.csv", parse_dates=["fecha"])
 
 
modelo = cargar_modelo()
serie = cargar_serie()
 
ultimo_dia = serie["fecha"].max().date()
 
# _______________Elección del usuario__________________

st.sidebar.header("Datos para la predicción")
 
DIAS_FUTURO = 30   # hasta cuántos días después del catálogo se puede predecir
 
# Se pueden elegir días que tengan 7 días anteriores en el catálogo,
# y hasta 30 días después del último día del catálogo

primer_dia = serie["fecha"].min().date() + datetime.timedelta(days=7)
dia_siguiente = ultimo_dia + datetime.timedelta(days=1)
 
fecha = st.sidebar.date_input(
    "Día que quiero predecir",
    value=dia_siguiente,
    min_value=primer_dia,
    max_value=ultimo_dia + datetime.timedelta(days=DIAS_FUTURO),
)
fecha = pd.Timestamp(fecha)
 
 
def predecir(dia, siete_dias):
    """Predice un día a partir de los terremotos de los 7 días anteriores."""
    # Las columnas tienen que ir en el mismo orden que en el entrenamiento
    entrada = pd.DataFrame({
        "dia_semana": [dia.dayofweek],
        "mes": [dia.month],
        "dia_mes": [dia.day],
        "dia_ano": [dia.dayofyear],
        "ayer": [siete_dias[-1]],
        "hace_7": [siete_dias[0]],
        "media_7": [sum(siete_dias) / 7],
    })
    return modelo.predict(entrada)[0]
 
 
# Si el día elegido está más allá del catálogo, no tengo los terremotos reales
# de los días anteriores. Los relleno con las predicciones del propio modelo un día detrás de otro.

fechas = serie["fecha"].tolist()
valores = serie["terremotos"].astype(float).tolist()
dias_rellenados = 0
 
while fechas[-1] < fecha - pd.Timedelta(days=1):
    siguiente = fechas[-1] + pd.Timedelta(days=1)
    valores.append(predecir(siguiente, valores[-7:]))
    fechas.append(siguiente)
    dias_rellenados += 1
 
historia = pd.DataFrame({"fecha": fechas, "terremotos": valores})
historia["es_prediccion"] = historia["fecha"] > pd.Timestamp(ultimo_dia)
 
# Los 7 días anteriores a la fecha elegida
anteriores = historia[historia["fecha"] < fecha].tail(7)["terremotos"].tolist()
 
# Opción para probar qué pasaría con otro valor el día anterior
simular = st.sidebar.checkbox("Simular otro valor para el día anterior")
if simular:
    anteriores[-1] = st.sidebar.slider(
        "Terremotos del día anterior", min_value=0, max_value=150, value=int(round(anteriores[-1]))
    )
 
ayer = anteriores[-1]
 
st.sidebar.caption(
    f"Terremotos de los 7 días anteriores: {[round(x, 1) for x in anteriores]}. "
    "El modelo usa el del día anterior, el de hace 7 días y la media de los 7."
)
 
# ____________Predicción____________

prediccion = predecir(fecha, anteriores)
 
# Si el día ya pasó, busco cuántos terremotos hubo de verdad
real = serie.loc[serie["fecha"] == fecha, "terremotos"]
hay_real = len(real) > 0 and not simular
 
col1, col2 = st.columns(2)
col1.metric("Predicción para el " + fecha.strftime("%d/%m/%Y"), f"{prediccion:.1f} terremotos")
if hay_real:
    col2.metric("Lo que pasó de verdad", f"{int(real.iloc[0])} terremotos")
else:
    col2.metric("Un día normal (mediana desde 2017)", f"{serie['terremotos'].median():.0f} terremotos")
 
# El modelo se entrenó con todos los datos anteriores al 07/08/2026 (los últimos 60 días son el test)
if hay_real and fecha < pd.Timestamp("2026-08-07"):
    st.caption(
        "Ojo: este día se usó para entrenar el modelo, así que aquí acierta más de lo normal. "
        "Para ver cómo acierta de verdad, elige un día a partir del 07/08/2026."
    )
 
# Aviso cuando hay días anteriores que no son reales sino predichos

if dias_rellenados > 0:
    st.warning(
        f"El catálogo acaba el {ultimo_dia.strftime('%d/%m/%Y')}. Para llegar a este día, "
        f"la app ha rellenado {dias_rellenados} días con sus propias predicciones. "
        "Cuanto más lejos está el día, más se parece la predicción a un día normal "
        "(entre 2 y 3 terremotos): el modelo no sabe qué pasó en esos días."
    )
 
# Qué porcentaje de días de la serie tuvieron menos terremotos que el día anterior
porcentaje = (serie["terremotos"] < ayer).mean() * 100
 
if dias_rellenados > 0 and not simular:
    st.info(f"Para el día anterior no hay dato real: se usa la predicción ({ayer:.1f} terremotos).")
elif ayer == 0:
    st.info("El día anterior no hubo terremotos, algo que pasa en 1 de cada 5 días.")
else:
    st.info(
        f"El día anterior hubo {ayer:.0f} terremotos. Eso es más que el "
        f"{porcentaje:.0f} % de los días desde 2017."
    )
 
st.caption(
    "En las pruebas el modelo se equivocó de media en 1,5 terremotos al día "
    "(el baseline, 1,9). No es capaz de anticipar un enjambre: solo acierta el nivel normal."
)
 
# _______________Gráfico__________________

st.subheader("Los 60 días anteriores y la predicción")
 
ultimos_60 = historia[historia["fecha"] < fecha].tail(60)
reales = ultimos_60[~ultimos_60["es_prediccion"]]
predichos = ultimos_60[ultimos_60["es_prediccion"]]
 
fig, ax = plt.subplots(figsize=(10, 4))
ax.bar(reales["fecha"], reales["terremotos"], width=1, label="Terremotos registrados")
if len(predichos) > 0:
    ax.bar(predichos["fecha"], predichos["terremotos"], width=1, color="lightgray",
           label="Días rellenados con predicciones")
ax.scatter([fecha], [prediccion], color="red", zorder=3, s=60, label="Predicción")
if hay_real:
    ax.scatter([fecha], [real.iloc[0]], color="black", marker="x", zorder=3, s=60, label="Lo que pasó")
ax.set_ylabel("Terremotos al día")
ax.legend()
fig.autofmt_xdate()
st.pyplot(fig)
 
# ____________Serie completa____________

st.subheader("Toda la serie desde 2017")
st.line_chart(serie.set_index("fecha")["terremotos"])
 
st.caption(
    "Fuente: catálogo de terremotos del Instituto Geográfico Nacional (IGN). "
    "Proyecto de clase, sin valor oficial."
)
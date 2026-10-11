import datetime
import joblib
import matplotlib.pyplot as plt
import pandas as pd
import steamlit as st

st.set_page_config(page_title="Terremotos en Tenerife", page_icon="🌋")

st.title("¿Cuántos terremotos habrá en Tenerife?")
st.write(
    "Predicción del número de terremotos de magnitud 1,0 o superior "
    "en Tenerife y el mar que la rodea. Datos del IGN."
)
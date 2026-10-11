# ¿Cuántos terremotos habrá mañana en Tenerife?

Proyecto de **forecasting**: desde los datos en bruto del Instituto Geográfico Nacional (IGN) hasta una app de Streamlit que hace predicciones.

**Pregunta:** un técnico de guardia de vigilancia volcánica quiere saber cuántos terremotos cabe esperar mañana en Tenerife, para distinguir un día normal de uno raro.

**Variable objetivo:** número de terremotos de magnitud 1,0 o más localizados en un día en Tenerife y el mar que la rodea.

> ⚠️ Este proyecto **no predice erupciones**. Solo estima cuántos terremotos pequeños (>=1) cabe esperar en un día.

## Datos

Catálogo de terremotos del IGN, descargado en CSV desde su web:
https://www.ign.es/web/ign/portal/sis-catalogo-terremotos

| Archivo | Contenido |
|---|---|
| `data/catalogo_ign_1981_2017.csv` | Terremotos de Canarias, de 1981 a septiembre de 2017 |
| `data/catalogo_ign_2017_2026.csv` | Terremotos de toda España, de enero de 2017 al 6 de octubre de 2026 |
| `data/serie_tenerife.csv` | La serie diaria que genera el notebook: una fila por día con el número de terremotos |

Los dos catálogos los descargué a mano desde el buscador de la web del IGN.

## Proceso

El notebook `notebook/EDA.ipynb` sigue estos pasos:

1. **Datos y pregunta.** Carga de los dos catálogos (separados por `;` y con espacios delante de cada valor).
2. **Limpieza.** Nulos, duplicados (720 terremotos repetidos entre los dos archivos), valores imposibles y el último día, que estaba incompleto. De 119.744 filas quedan 8.393 terremotos en Tenerife desde 2017, que dan una serie de 3.565 días.
3. **EDA.** Serie en el tiempo, reparto de la variable objetivo, efecto del calendario, relación con los días anteriores, mapa de correlaciones y comparación con la crisis de El Hierro en 2011.
4. **Modelos.** Baseline, `LinearRegression` y `RandomForestRegressor`, primero solo con variables de calendario y después añadiendo valores pasados de la serie (ayer, hace 7 días y la media de los 7 días anteriores).
5. **Guardar el modelo.** El mejor se guarda con `joblib` en `models/modelo_terremotos.pkl`.
6. **App.** `app.py`, hecha con Streamlit.

### Dos decisiones importantes

- **Empiezo en 2017.** Hasta 2015 había unos 100 terremotos al año y en 2017 casi 1.000. La diferencia se debe sobre todo a que se detectan terremotos más pequeños, no a que haya más.
- **Solo cuento magnitud 1,0 o más.** Los más pequeños dependen de lo sensible que sea la red de estaciones cada año.

## Resultados

Test con los **últimos 60 días** de la serie, sin barajar. El error es el MAE, en terremotos al día.

| Modelo | MAE |
|---|---|
| Baseline: el valor de hace 7 días | 1,93 |
| Siempre la media del entrenamiento | 1,50 |
| LinearRegression | 1,47 |
| **RandomForestRegressor (el guardado)** | **1,46** |

- El Random Forest mejora al baseline un **24 %**, pero casi no mejora a predecir siempre la media.
- La única variable que ayuda de verdad es lo que pasó el día anterior. El calendario no explica nada: a un volcán le da igual que sea lunes o agosto.
- **Ningún modelo ve venir un enjambre.** Solo aciertan el nivel normal de fondo.
- Repitiendo la prueba con el último año como test (que sí tiene enjambres) sale lo mismo: baseline 5,67, media 3,87, Random Forest 3,61.

## La app

- Se elige un día y la app saca del catálogo los terremotos de los 7 días anteriores para hacer la predicción.
- En días pasados muestra también lo que pasó de verdad.
- Hay una opción para simular otro valor para el día anterior.
- Se puede elegir hasta 30 días después del final del catálogo. Para esos días, la app rellena los días que faltan con sus propias predicciones, así que cuanto más lejos, más se parece la predicción a un día normal.

## Estructura

```
├── app.py                         App de Streamlit
├── requirements.txt               Librerías necesarias
├── notebook/
│   └── EDA.ipynb                  Notebook con todo el proceso
├── data/
│   ├── catalogo_ign_1981_2017.csv
│   ├── catalogo_ign_2017_2026.csv
│   └── serie_tenerife.csv         La genera el notebook
└── models/
    └── modelo_terremotos.pkl      Lo genera el notebook
```

## Cómo ejecutarlo

Instalar las librerías:

```
pip install -r requirements.txt
```

Abrir la app (desde la carpeta principal del proyecto, donde está `app.py`):

```
streamlit run app.py
```

Para volver a entrenar el modelo hay que ejecutar el notebook entero. Como está dentro de `notebook/`, sus rutas empiezan por `../` (por ejemplo, `../data/...`).

## Limitaciones

- La zona incluye el mar entre Tenerife y Gran Canaria, donde cae la mitad de los terremotos. No es una serie "del Teide".
- El corte de magnitud 1,0 reduce el problema de la detección de terremotos pequeños, pero no lo elimina del todo.
- Los últimos 60 días fueron tranquilos, así que el test principal no incluye ningún enjambre.
- El error medido vale para predecir **un día** por delante. Las predicciones a varios días de la app no están evaluadas.

## Qué probaría con más tiempo

- Modelos específicos de series temporales, como Holt-Winters o Prophet.
- Predecir el total de la semana en vez del día.
- Añadir otras medidas que usan los científicos, como la emisión de gases o la deformación del terreno.

---

Fuente de los datos: catálogo de terremotos del Instituto Geográfico Nacional (IGN). Proyecto de clase, sin valor oficial.
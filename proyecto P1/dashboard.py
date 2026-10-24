
import streamlit as st
import pandas as pd
import plotly.express as px
from conexion import conectar_mysql

# ==========================================
# 1. CONFIGURACION DEL DASHBOARD
# ==========================================

st.set_page_config(
    page_title="Dashboard MISD",
    page_icon="📊",
    layout="wide"
)

st.title("Dashboard de Procesamiento MISD")
st.caption("Computacion Paralela | Python + MySQL")


# ==========================================
# 2. CONSULTAR BASE DE DATOS
# ==========================================

def cargar_datos():

    conexion = conectar_mysql()

    try:
        consulta = """
            SELECT
                c.id AS ejecucion,
                r.id AS registro,
                r.litros,
                c.mililitros,
                c.centilitros,
                c.metros_cubicos,
                c.tiempo_microsegundos,
                c.fecha_procesamiento
            FROM registros_litros r
            INNER JOIN resultados_conversion c
                ON r.id = c.registro_id
            ORDER BY c.id
        """

        cursor = conexion.cursor(dictionary=True)

        try:
            cursor.execute(consulta)
            filas = cursor.fetchall()
        finally:
            cursor.close()

        return pd.DataFrame(filas)

    finally:
        conexion.close()


# ==========================================
# 3. CARGAR REGISTROS
# ==========================================

try:
    datos = cargar_datos()

except Exception as error:
    st.error(f"Error de conexion: {error}")
    st.stop()

if datos.empty:
    st.warning("No existen resultados en MySQL.")
    st.stop()


# ==========================================
# 4. FILTROS INTERACTIVOS
# ==========================================

st.sidebar.header("Filtros")

registros = sorted(datos["registro"].unique())

seleccionados = st.sidebar.multiselect(
    "Seleccionar registros",
    options=registros,
    default=registros
)
filtrados = datos[
    datos["registro"].isin(seleccionados)
].copy()

unidad = st.sidebar.selectbox(
    "Unidad de conversion",
    ["mililitros", "centilitros", "metros_cubicos"]
)




# ==========================================
# 5. INDICADORES GENERALES
# ==========================================

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Registros",
    filtrados["registro"].nunique()
)

col2.metric("Hilos utilizados", 3)

col3.metric(
    "Total litros",
    f"{filtrados['litros'].sum():,.2f}"
)

col4.metric(
    "Tiempo ultimo registro",
    f"{datos.iloc[-1]['tiempo_microsegundos']:.2f} us"
)


# ==========================================
# 6. GRAFICO DE CONVERSIONES
# ==========================================

st.subheader("Conversiones por registro")

fig = px.bar(
    filtrados,
    x="registro",
    y=unidad,
    color="registro",
    title=f"Conversion de litros a {unidad}"
)

st.plotly_chart(fig, use_container_width=True)


# ==========================================
# 7. ANALISIS DE TIEMPOS
# ==========================================

st.subheader("Tiempo de procesamiento")

fig_tiempo = px.line(
    datos,
    x="ejecucion",
    y="tiempo_microsegundos",
    markers=True,
    title="Tiempo registrado por conversion"
)

st.plotly_chart(fig_tiempo, use_container_width=True)

st.caption(
    "El tiempo corresponde al procesamiento completo "
    "de los tres hilos, no al tiempo individual de cada fila."
)


# ==========================================
# 8. TABLA INTERACTIVA
# ==========================================

st.subheader("Resultados almacenados en MySQL")

st.dataframe(
    filtrados,
    use_container_width=True,
    hide_index=True
)


# ==========================================
# 9. DESCARGAR RESULTADOS
# ==========================================

csv = filtrados.to_csv(index=False).encode("utf-8-sig")

st.download_button(
    "Descargar resultados CSV",
    data=csv,
    file_name="resultados_misd.csv",
    mime="text/csv"
)

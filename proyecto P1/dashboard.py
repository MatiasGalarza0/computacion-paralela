
Relaciones:
 registros.id = resultados_mimd.id_mimd
 registros.id = resultados_misd.id_misd
 registros.id = resultados_simd.id_simd

No modifica tablas ni requiere fechas o tiempos de procesamiento.
"""
import io
import zipfile

import pandas as pd
import plotly.express as px
import streamlit as st

from conexion import conectar_mysql


st.set_page_config(page_title="Paralela Lab | Proyecto P1", page_icon="🧠", layout="wide", initial_sidebar_state="expanded")

COLORES = {"MIMD": "#9B83FF", "MISD": "#43C9A7", "SIMD": "#FFAC63"}
GENERO_COLORES = {"Femenino": "#FF78B5", "Masculino": "#5EAFFF"}
INDICADORES = {
    "Glucosa": ("glucosa_mg_dL", "glucosa_mmol_L", "#9B83FF"),
    "Colesterol": ("colesterol_mg_dL", "colesterol_mmol_L", "#43C9A7"),
    "Triglicéridos": ("trigliceridos_mg_dL", "trigliceridos_mmol_L", "#FFAC63"),
}
CLAVES = {"MIMD": "id_mimd", "MISD": "id_misd", "SIMD": "id_simd"}
EDADES = [0, 17, 29, 44, 59, 74, 150]
ETIQUETAS_EDAD = ["Menos de 18", "18–29", "30–44", "45–59", "60–74", "75+"]
TEMPLATE = "plotly_dark"

st.markdown("""
<style>
:root {color-scheme:dark}
.stApp {background: #0C1020; color: #EEF1FC}
[data-testid="stSidebar"] {background: linear-gradient(170deg,#171B35 0%,#101429 100%);border-right:1px solid #343C62}
[data-testid="stSidebar"] * {color:#F1F1FB}
.block-container {padding-top:1.8rem;max-width:1460px}
.hero {background:linear-gradient(105deg,#312560,#162B4C 70%,#143D4C); border:1px solid #414B76; padding:24px 27px;border-radius:20px;margin-bottom:20px}
.hero h1 {margin:0;font-size:2.15rem;line-height:1.25;color:white}
.hero p {margin:8px 0 0;color:#D1D9EC}
.pill {display:inline-block;background:#ffffff17;border:1px solid #ffffff3d;border-radius:50px;padding:5px 12px;color:#E3E7FA;font-size:.8rem;margin-bottom:12px}
.small-box {background: #191F39; border:1px solid #3E456A;border-radius:14px;padding:13px 15px;margin:6px 0 12px}
.small-box h3 {font-size:.97rem;color:white;margin:0 0 6px}
.small-box p {font-size:.87rem;color:#C6D0EA;margin:0}
[data-testid="stMetric"] {background:#1A2038;padding:17px;border:1px solid #394369;border-radius:15px}
[data-testid="stMetricLabel"] {color:#B9C8EB}
[data-testid="stMetricValue"] {color:#FFFFFF}
[data-testid="stDataFrame"] {border-radius:12px;overflow:hidden}
section.main hr {border-color:#343C60}
</style>
""", unsafe_allow_html=True)


def tarjeta(titulo, descripcion, color="#9B83FF"):
    st.markdown(
        f'<div class="small-box" style="border-left:4px solid {color}"><h3>{titulo}</h3><p>{descripcion}</p></div>',
        unsafe_allow_html=True,
    )


def grafico(fig, height=365):
    fig.update_layout(
        template=TEMPLATE,
        paper_bgcolor="#14192D",
        plot_bgcolor="#14192D",
        font=dict(color="#E5EAFA"),
        height=height,
        margin=dict(l=18, r=18, t=65, b=30),
        legend_title_text="",
    )
    st.plotly_chart(fig, use_container_width=True)


def leer_tabla(conexion, tabla):
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(f"SELECT * FROM `{tabla}`")
        return pd.DataFrame(cursor.fetchall())
    finally:
        cursor.close()


@st.cache_data(ttl=60, show_spinner="Consultando MySQL...")
def cargar_mysql():
    """Únicamente SELECT: no inserta, actualiza ni elimina nada."""
    conexion = conectar_mysql()
    tablas = {}
    errores = {}
    try:
        for tabla in ("registros", "resultados_mimd", "resultados_misd", "resultados_simd"):
            try:
                tablas[tabla] = leer_tabla(conexion, tabla)
            except Exception as error:
                tablas[tabla] = pd.DataFrame()
                errores[tabla] = str(error)
    finally:
        conexion.close()
    return tablas, errores


def preparar_personas(df):
    if "id" not in df.columns:
        raise ValueError("La tabla registros necesita una columna 'id'.")
    copia = df.copy()
    if "genero" not in copia and "genereo" in copia:
        copia = copia.rename(columns={"genereo": "genero"})
    if "genero" not in copia:
        copia["genero"] = "Sin especificar"
    if "edad" not in copia:
        copia["edad"] = pd.NA
    for campo in ["id", "edad", "glucosa_mg_dL", "colesterol_mg_dL", "trigliceridos_mg_dL"]:
        if campo in copia:
            copia[campo] = pd.to_numeric(copia[campo], errors="coerce")
    copia = copia.dropna(subset=["id"]).drop_duplicates(subset=["id"], keep="last")
    copia["id"] = copia["id"].astype("int64")
    copia["genero"] = copia["genero"].fillna("Sin especificar").astype(str)
    copia["rango_edad"] = pd.cut(copia["edad"], bins=EDADES, labels=ETIQUETAS_EDAD, include_lowest=True)
    return copia


def preparar_resultados(resultados, arquitectura):
    """Conserva el ID de registros, no el ID técnico del resultado.

    Importante: MISD y SIMD pueden tener además su propia columna 'id'.
    Nunca se debe hacer JOIN con esa columna auxiliar.
    """
    clave = CLAVES[arquitectura]
    if resultados.empty and clave not in resultados.columns:
        return pd.DataFrame({clave: pd.Series(dtype="int64")})
    if clave not in resultados.columns:
        raise ValueError(f"En resultados_{arquitectura.lower()} falta la columna '{clave}'.")
    datos = resultados.copy()
    # MISD y SIMD traen 'id' (PK propia): no reemplaza registros.id.
    if "id" in datos.columns:
        datos = datos.drop(columns=["id"])
    datos[clave] = pd.to_numeric(datos[clave], errors="coerce")
    datos = datos.dropna(subset=[clave])
    for indicador in INDICADORES.values():
        campo = indicador[1]
        if campo in datos:
            datos[campo] = pd.to_numeric(datos[campo], errors="coerce")
    datos[clave] = datos[clave].astype("int64")
    return datos


def relacionar(personas, resultados, arquitectura):
    """El resultado conserva personas.id y una fila por persona, sin id_x/id_y."""
    clave = CLAVES[arquitectura]
    original = preparar_resultados(resultados, arquitectura)
    repetidos = int(original.duplicated(subset=[clave]).sum()) if clave in original else 0
    original = original.drop_duplicates(subset=[clave], keep="last")
    unidos = personas.merge(original, left_on="id", right_on=clave, how="inner", validate="one_to_one")
    return unidos, repetidos


def aplicar_filtros(df, generos, edades):
    if df.empty:
        return df.copy()
    return df[df["genero"].isin(generos) & df["edad"].between(*edades)].copy()


def conversiones(df):
    return {
        nombre: int(df[campo].notna().sum()) if campo in df else 0
        for nombre, (_orig, campo, _color) in INDICADORES.items()
    }


def csv_bytes(df):
    return df.to_csv(index=False).encode("utf-8-sig")


def archivo_zip(tablas, relacionadas, filtradas):
    salida = io.BytesIO()
    with zipfile.ZipFile(salida, "w", zipfile.ZIP_DEFLATED) as zipf:
        for nombre, df in tablas.items():
            if not df.empty:
                zipf.writestr(f"tablas_originales/{nombre}.csv", csv_bytes(df))
        for arquitectura, df in relacionadas.items():
            if not df.empty:
                zipf.writestr(f"relacionadas/{arquitectura.lower()}_completo.csv", csv_bytes(df))
        for arquitectura, df in filtradas.items():
            if not df.empty:
                zipf.writestr(f"filtradas/{arquitectura.lower()}_filtrado.csv", csv_bytes(df))
    return salida.getvalue()


# Cargar y validar sin esconder errores reales.
st.sidebar.markdown("## 🧠 PARALELA LAB")
st.sidebar.caption("Computación Paralela · MySQL / baseproyecto")
if st.sidebar.button("↻ Actualizar datos", use_container_width=True):
    cargar_mysql.clear()
    st.rerun()

try:
    tablas, errores = cargar_mysql()
    if "registros" in errores:
        raise RuntimeError("No se pudo consultar registros: " + errores["registros"])
    personas = preparar_personas(tablas["registros"])
except Exception as error:
    st.error(f"No se pudieron cargar los datos de MySQL: {error}")
    st.info("Inicia MySQL en XAMPP y comprueba que conexion.py use la base baseproyecto.")
    st.stop()

relacionadas = {}
duplicados = {}
for arq in CLAVES:
    try:
        relacionadas[arq], duplicados[arq] = relacionar(personas, tablas[f"resultados_{arq.lower()}"], arq)
    except Exception as error:
        relacionadas[arq] = pd.DataFrame(columns=personas.columns)
        duplicados[arq] = 0
        errores[f"resultados_{arq.lower()}"] = str(error)

st.sidebar.divider()
seccion = st.sidebar.radio(
    "Navegación",
    ["🏠 Inicio", "🟣 MIMD", "🟢 MISD", "🟠 SIMD", "👥 Clasificación", "📊 Comparación", "📥 Descargas"],
    label_visibility="collapsed",
)
st.sidebar.divider()
st.sidebar.markdown("**Filtros de población**")
generos_disponibles = sorted(personas["genero"].dropna().unique().tolist())
generos = st.sidebar.multiselect("Género", generos_disponibles, default=generos_disponibles)
lim_inf = int(personas["edad"].min()) if personas["edad"].notna().any() else 0
lim_sup = int(personas["edad"].max()) if personas["edad"].notna().any() else 100
if lim_inf < lim_sup:
    edades = st.sidebar.slider("Edad", min_value=lim_inf, max_value=lim_sup, value=(lim_inf, lim_sup))
else:
    edades = (lim_inf, lim_sup)
personas_filtradas = aplicar_filtros(personas, generos, edades)
filtradas = {arq: aplicar_filtros(df, generos, edades) for arq, df in relacionadas.items()}

for tabla, error in errores.items():
    if not tablas.get(tabla, pd.DataFrame()).empty and tabla not in ("registros",):
        st.warning(f"No fue posible relacionar {tabla}: {error}")
    elif tabla.startswith("resultados_"):
        st.warning(f"No se pudo consultar {tabla}: {error}")
for arq, n in duplicados.items():
    if n:
        st.warning(f"{arq}: {n} IDs repetidos en la tabla de resultados. Se utiliza la última fila por identificador para no duplicar personas.")


def encabezado(titulo, detalle, etiqueta="P1 · COMPUTACIÓN PARALELA"):
    st.markdown(
        f'<div class="hero"><span class="pill">{etiqueta}</span><h1>{titulo}</h1><p>{detalle}</p></div>',
        unsafe_allow_html=True,
    )


def descarga(nombre, df, key):
    st.download_button("⬇ Descargar CSV", csv_bytes(df), f"{nombre}.csv", "text/csv", key=key, use_container_width=True)


if seccion == "🏠 Inicio":
    encabezado("Explorador de arquitecturas", "Indicadores de salud · procesamiento, clasificación y comparación de resultados")
    columnas = st.columns(4)
    columnas[0].metric("Personas únicas", f"{personas_filtradas['id'].nunique():,}")
    for columna, arq in zip(columnas[1:], CLAVES):
        columna.metric(f"Resultados {arq}", f"{filtradas[arq]['id'].nunique():,}")

    a, b = st.columns(2)
    with a:
        genero_df = personas_filtradas.groupby("genero", as_index=False).agg(personas=("id", "nunique"))
        if not genero_df.empty:
            fig = px.pie(genero_df, names="genero", values="personas", hole=.55, color="genero",
                         color_discrete_map=GENERO_COLORES, title="Composición por género")
            grafico(fig)
    with b:
        edades_df = personas_filtradas.groupby("rango_edad", observed=False).agg(personas=("id", "nunique")).reset_index()
        if not edades_df.empty:
            fig = px.bar(edades_df, x="rango_edad", y="personas", title="Personas por rango de edad",
                         labels={"rango_edad": "Edad", "personas": "Personas únicas"}, text_auto=True,
                         color_discrete_sequence=["#68A2FF"])
            grafico(fig)
    tarjeta("Personas ≠ resultados", "Los conteos se calculan con registros.id. Una misma persona puede tener resultados en varias arquitecturas; no se suman como si fueran personas diferentes.")
    resumen = pd.DataFrame([
        {"Arquitectura": a, "Personas con resultados": filtradas[a]["id"].nunique(),
         "Conversiones almacenadas": sum(conversiones(filtradas[a]).values())}
        for a in CLAVES
    ])
    grafico(px.bar(resumen, x="Arquitectura", y="Conversiones almacenadas", color="Arquitectura", text_auto=True,
                   color_discrete_map=COLORES, title="Operaciones almacenadas por arquitectura"))

elif seccion in ("🟣 MIMD", "🟢 MISD", "🟠 SIMD"):
    arq = seccion.split()[-1]
    datos = filtradas[arq]
    encabezado(f"Arquitectura {arq}",
               {"MIMD": "Bloques diferentes: glucosa, colesterol y triglicéridos.",
                "MISD": "Tres conversiones sobre los registros del conjunto de datos.",
                "SIMD": "Misma conversión de glucosa en tres bloques de registros."}[arq],
               f"RESULTADOS REALES · {arq}")
    counts = conversiones(datos)
    cols = st.columns(4)
    cols[0].metric("Personas con resultados", f"{datos['id'].nunique():,}")
    for col, indicador in zip(cols[1:], INDICADORES):
        col.metric(indicador, f"{counts[indicador]:,}")
    if datos.empty:
        st.info(f"No hay resultados de {arq} para los filtros actuales. Comprueba su tabla MySQL.")
    else:
        if arq == "MIMD":
            tarjeta("Distribución por bloques", "Cada registro tiene una conversión. El hilo 1 procesa glucosa, el hilo 2 colesterol y el hilo 3 triglicéridos.", COLORES[arq])
        elif arq == "MISD":
            tarjeta("Las mismas personas, tres resultados", "El programa de clase calcula tres conversiones por registro. Por eso el número de conversiones puede superar al número de personas.", COLORES[arq])
        else:
            tarjeta("Una operación por registro", "Tres hilos aplican el cálculo de glucosa sobre partes diferentes del dataset.", COLORES[arq])
        conversion_df = pd.DataFrame([{"Indicador": nombre, "Cantidad": counts[nombre]} for nombre in INDICADORES])
        grafico(px.bar(conversion_df, x="Indicador", y="Cantidad", color="Indicador", text_auto=True,
                       title="Cantidad de resultados por conversión", color_discrete_sequence=list(COLORES.values())))
        disponibles = [n for n, (_origen, convertido, _color) in INDICADORES.items()
                       if convertido in datos.columns and datos[convertido].notna().any()]
        if disponibles:
            elegido = st.selectbox("Indicador convertido", disponibles)
            original, convertido, color = INDICADORES[elegido]
            a, b = st.columns(2)
            with a:
                fig = px.histogram(datos.dropna(subset=[convertido]), x=convertido, nbins=28,
                                   color_discrete_sequence=[color], title=f"Distribución de {elegido} (mmol/L)",
                                   labels={convertido: f"{elegido} (mmol/L)"})
                grafico(fig)
            with b:
                df_e = datos.dropna(subset=[convertido])
                por_edad = df_e.groupby("rango_edad", observed=False)[convertido].mean().reset_index()
                grafico(px.bar(por_edad, x="rango_edad", y=convertido, color_discrete_sequence=[color],
                               title=f"Promedio de {elegido} por edad", labels={"rango_edad": "Edad", convertido: "mmol/L"}))
            if original in datos.columns:
                grafico(px.box(datos.dropna(subset=[original]), x="genero", y=original, color="genero",
                               color_discrete_map=GENERO_COLORES, points=False,
                               title=f"Valores originales de {elegido} por género (mg/dL)"))
        st.subheader("Resultados relacionados con registros")
        st.dataframe(datos, use_container_width=True, hide_index=True)
        descarga(f"resultados_{arq.lower()}_filtrados", datos, f"arq_{arq}")

elif seccion == "👥 Clasificación":
    encabezado("Clasificación de los indicadores", "Explora la composición de la población y analiza las mediciones originales por edad y género")
    tab1, tab2, tab3 = st.tabs(["👤 Población", "🧪 Indicadores", "📋 Registros"])
    with tab1:
        c1, c2 = st.columns(2)
        tabla = personas_filtradas.groupby(["rango_edad", "genero"], observed=False).agg(personas=("id", "nunique")).reset_index()
        with c1:
            if not tabla.empty:
                grafico(px.bar(tabla, x="rango_edad", y="personas", color="genero", barmode="group",
                               color_discrete_map=GENERO_COLORES, title="Género y edad", labels={"personas": "Personas"}))
        with c2:
            if not personas_filtradas.empty:
                grafico(px.histogram(personas_filtradas, x="edad", nbins=25, color_discrete_sequence=["#8B8CFA"],
                                   title="Distribución de edades"))
        st.dataframe(tabla, hide_index=True, use_container_width=True)
        descarga("clasificacion_poblacion", tabla, "export_poblacion")
    with tab2:
        nombre = st.selectbox("Indicador", list(INDICADORES), key="clasificacion_indicador")
        campo = INDICADORES[nombre][0]
        if campo not in personas_filtradas.columns:
            st.info(f"No se encuentra la columna {campo} en registros.")
        else:
            medido = personas_filtradas.dropna(subset=[campo]).copy()
            if medido.empty:
                st.info("Sin valores de este indicador para los filtros.")
            else:
                # Los cortes se fijan con el conjunto ORIGINAL, no cambian al filtrar.
                referencia = personas[campo].dropna()
                q1, q2 = referencia.quantile([1 / 3, 2 / 3]).tolist()
                medido["nivel"] = pd.cut(medido[campo], bins=[float("-inf"), q1, q2, float("inf")],
                                         labels=["Bajo", "Medio", "Alto"], include_lowest=True)
                a, b = st.columns(2)
                with a:
                    nivel = medido.groupby("nivel", observed=False).size().reset_index(name="personas")
                    grafico(px.bar(nivel, x="nivel", y="personas", color="nivel", text_auto=True,
                                   title=f"Niveles estadísticos de {nombre}",
                                   color_discrete_map={"Bajo": "#3EC9A7", "Medio": "#FEB95E", "Alto": "#F47690"}))
                with b:
                    grafico(px.box(medido, x="rango_edad", y=campo, color="genero", color_discrete_map=GENERO_COLORES,
                                   points=False, title=f"{nombre} por edad y género (mg/dL)"))
                st.caption(f"Cortes estadísticos del conjunto completo: {q1:.2f} y {q2:.2f} mg/dL. Los niveles bajo, medio y alto no son diagnósticos médicos.")
                st.dataframe(medido[["id", "edad", "genero", campo, "nivel"]], hide_index=True, use_container_width=True)
                descarga(f"clasificacion_{nombre.lower()}", medido, "export_indicador")
    with tab3:
        st.dataframe(personas_filtradas, use_container_width=True, hide_index=True)
        descarga("registros_filtrados", personas_filtradas, "export_registros_filtrados")

elif seccion == "📊 Comparación":
    encabezado("Comparación de arquitecturas", "Consulta la cantidad de personas procesadas y las conversiones almacenadas en MySQL")
    filas = []
    for a in CLAVES:
        conteos = conversiones(filtradas[a])
        filas.append({"Arquitectura": a, "Personas": filtradas[a]["id"].nunique(), **conteos,
                      "Conversiones": sum(conteos.values())})
    comparacion = pd.DataFrame(filas)
    a, b = st.columns(2)
    with a:
        grafico(px.bar(comparacion, x="Arquitectura", y="Personas", color="Arquitectura", text_auto=True,
                       color_discrete_map=COLORES, title="Personas únicas con resultados"))
    with b:
        grafico(px.bar(comparacion, x="Arquitectura", y="Conversiones", color="Arquitectura", text_auto=True,
                       color_discrete_map=COLORES, title="Conversiones totales almacenadas"))
    st.subheader("Conversiones por indicador")
    largo = comparacion.melt(id_vars="Arquitectura", value_vars=list(INDICADORES),
                             var_name="Indicador", value_name="Cantidad")
    grafico(px.bar(largo, x="Arquitectura", y="Cantidad", color="Indicador", barmode="group",
                   title="Indicadores por arquitectura"))
    st.dataframe(comparacion, hide_index=True, use_container_width=True)
    tarjeta("Interpretación", "Más conversiones no significa que una arquitectura sea más rápida. Aquí se compara el trabajo guardado, no tiempos ni rendimiento de CPU.")
    descarga("comparacion_arquitecturas", comparacion, "comparacion_csv")

elif seccion == "📥 Descargas":
    encabezado("Centro de descargas", "Exporta las tablas originales, los datos filtrados y las relaciones con la información de cada persona")
    st.subheader("Tablas originales de baseproyecto")
    for tabla in ("registros", "resultados_mimd", "resultados_misd", "resultados_simd"):
        datos = tablas[tabla]
        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown(f"**{tabla}** · {len(datos):,} filas")
        with c2:
            descarga(tabla, datos, f"desc_{tabla}")
    st.divider()
    st.subheader("Datos relacionados y filtrados")
    for arq in CLAVES:
        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown(f"**{arq}** · {len(filtradas[arq]):,} personas visibles")
        with c2:
            descarga(f"{arq.lower()}_relacionado_filtrado", filtradas[arq], f"desc_fil_{arq}")
    st.divider()
    st.download_button("📦 Descargar todas las tablas en un ZIP", archivo_zip(tablas, relacionadas, filtradas),
                       file_name="tablas_paralela_lab.zip", mime="application/zip", use_container_width=True)
    st.caption("Archivos CSV compatibles con Excel. Ninguna descarga modifica tu base MySQL.")

st.caption("Proyecto P1 · MySQL en modo lectura · sin tiempo ni fecha de procesamiento")

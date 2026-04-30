mport streamlit as st
import pandas as pd

# 1. Configuración de la página (Debe ser la primera instrucción de Streamlit)
st.set_page_config(
    page_title="Consulta Agrícola Colombia",
    page_icon="🌾",
    layout="wide"
)

# 2. Función para cargar los datos con Caché
# El decorador @st.cache_data evita que se recargue el archivo cada vez que interactúas con la app
@st.cache_data
def load_data(uploaded_file):
    try:
        # Cargamos el dataframe leyendo directamente el archivo subido
        df = pd.read_excel(uploaded_file)
        
        # Limpieza inicial: asegurarnos de que las métricas sean numéricas
        columnas_metricas = ['Área sembrada (ha)', 'Área cosechada (ha)', 'Producción (t)', 'Rendimiento (t/ha)']
        for col in columnas_metricas:
            if col in df.columns:
                # Convertimos comas a puntos si vienen como texto (opcional, por si acaso)
                if df[col].dtype == object:
                df[col] = df[col].astype(str).str.replace(',', '.')
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    return df
except Exception as e:
    st.error(f"Hubo un problema al leer el archivo Excel: {e}")
    return pd.DataFrame() # Retorna dataframe vacío si falla

# 3. Interfaz de Usuario (UI)
def main():
    st.title("🌾 Consulta de Desempeño Agrícola (2019 - 2024)")
    st.markdown("Esta aplicación permite visualizar la evolución de la siembra, cosecha y producción agrícola en los distintos departamentos de Colombia.")
    
    # Widget para que el usuario suba el archivo de Excel
    archivo_subido = st.file_uploader("Sube aquí tu base de datos (formato .xlsx o .xls)", type=["xlsx", "xls"])
    
    if archivo_subido is None:
        st.info("Por favor, sube un archivo de Excel para comenzar el análisis.")
        st.stop() # Detiene la ejecución hasta que haya un archivo
    
    # Cargamos los datos
    with st.spinner('Cargando base de datos...'):
        df = load_data(archivo_subido)
        
    if df.empty:
        st.stop() # Detiene la ejecución si no hay datos

    st.markdown("---")
    
    # 4. Filtros en la barra lateral o en columnas
    st.subheader("🔍 Filtros de búsqueda")
    
    col1, col2 = st.columns(2)
    
    # Extraer valores únicos limpios (sin nulos) y ordenados alfabéticamente
    lista_deptos = sorted(df['Departamento'].dropna().unique().tolist())
    lista_cultivos = sorted(df['Cultivo'].dropna().unique().tolist())
    
    with col1:
        # Selectbox en lugar de input de texto
        depto_input = st.selectbox("1. Selecciona el Departamento:", lista_deptos)
        
    with col2:
        cultivo_input = st.selectbox("2. Selecciona el Cultivo:", lista_cultivos)

    # 5. Lógica de Filtrado
    filtro = (df['Departamento'] == depto_input) & (df['Cultivo'] == cultivo_input)
    df_filtrado = df[filtro].copy()
    
    st.markdown("---")

    # 6. Mostrar Resultados
    if df_filtrado.empty:
        st.warning(f"No hay registros agrícolas para **{cultivo_input}** en **{depto_input}**.")
    else:
        st.success(f"Mostrando resultados para **{cultivo_input}** en **{depto_input}**.")
        
        columnas_metricas = ['Área sembrada (ha)', 'Área cosechada (ha)', 'Producción (t)']
        
        # Agrupación anual
        if 'Año' in df_filtrado.columns:
            resumen_anual = df_filtrado.groupby('Año')[columnas_metricas].sum().reset_index()
            
            # 6.1 Tarjetas de métricas (KPIs) usando el último año disponible en la búsqueda
            ultimo_ano = resumen_anual['Año'].max()
            datos_ultimo_ano = resumen_anual[resumen_anual['Año'] == ultimo_ano]
            
            st.markdown(f"### 📈 Métricas destacadas ({ultimo_ano})")
            kpi1, kpi2, kpi3 = st.columns(3)
            kpi1.metric("Área Sembrada Total", f"{datos_ultimo_ano['Área sembrada (ha)'].values[0]:,.2f} ha")
            kpi2.metric("Área Cosechada Total", f"{datos_ultimo_ano['Área cosechada (ha)'].values[0]:,.2f} ha")
            kpi3.metric("Producción Total", f"{datos_ultimo_ano['Producción (t)'].values[0]:,.2f} t")
            
            # 6.2 Mostrar Tabla y Gráfico en dos columnas
            st.markdown("### 📊 Resumen Departamental por Año")
            
            col_tabla, col_grafico = st.columns([1, 2])
            
            with col_tabla:
                # Mostramos el dataframe limpio
                st.dataframe(resumen_anual, use_container_width=True, hide_index=True)
                
            with col_grafico:
                # Gráfico de barras de Producción vs Año
                st.bar_chart(data=resumen_anual, x='Año', y='Producción (t)', color="#2e7b32")
                
        # 6.3 Desplegable para ver el detalle municipal (reemplaza el input 's/n')
        with st.expander("📍 Ver detalle desglosado por Municipio y Periodo"):
            columnas_detalle = ['Año', 'Municipio', 'Cultivo', 'Área sembrada (ha)', 
                                'Área cosechada (ha)', 'Producción (t)', 'Rendimiento (t/ha)']
            
            columnas_presentes = [col for col in columnas_detalle if col in df_filtrado.columns]
            
            st.dataframe(df_filtrado[columnas_presentes].sort_values(by=['Año', 'Municipio']), 
                         use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()

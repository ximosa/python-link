import streamlit as st
import google.generativeai as genai
import os
import textwrap

# Obtener la API Key de las variables de entorno
try:
    GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
    genai.configure(api_key=GOOGLE_API_KEY)
    MODEL = "gemini-pro"
except KeyError:
    st.error("La variable de entorno _GOOGLE_API_KEY no está configurada.")
    st.stop()  # Detener la app si no hay API Key

def dividir_texto(texto, max_tokens=1000):
    """Divide el texto en fragmentos más pequeños."""
    tokens = texto.split()
    fragmentos = []
    fragmento_actual = []
    cuenta_tokens = 0

    for token in tokens:
        cuenta_tokens += 1
        if cuenta_tokens <= max_tokens:
            fragmento_actual.append(token)
        else:
            fragmentos.append(" ".join(fragmento_actual))
            fragmento_actual = [token]
            cuenta_tokens = 1
    if fragmento_actual:
        fragmentos.append(" ".join(fragmento_actual))
    return fragmentos

def limpiar_transcripcion_gemini(texto):
    """
    Limpia una transcripción usando Gemini.

    Args:
      texto (str): La transcripción sin formato.

    Returns:
      str: La transcripción formateada.
    """
    prompt = f"""
    Actúa como un lector profundo y reflexivo, y un narrador excepcional. Escribe en primera persona, como si tú hubieras vivido la experiencia o reflexionado sobre los temas presentados.
    Sigue estas pautas con máxima precisión:
    - Reescribe el siguiente texto utilizando tus propias palabras, y asegúrate de que la longitud del texto resultante sea al menos igual, idealmente un poco mayor, que la del texto original.
    - No reduzcas la información. Al contrario, expande cada punto y concepto, añade detalles, ejemplos y matices para enriquecer el texto.
    - No generes un resumen conciso. Necesito un texto parafraseado y expandido, cuyo tamaño sea comparable o superior al texto original.
    - Crea un título atractivo y preciso que capture la esencia del contenido expandido.
    - Evita menciones directas de nombres de personajes o autores; refiérete a ellos genéricamente (ej: "una persona", "un personaje").
    - Reflexiona sobre la experiencia general, las ideas principales, los temas y las emociones transmitidas por el texto.
    - Utiliza un lenguaje personal, evocador y narrativo. Como si estuvieras compartiendo tus propias reflexiones tras una profunda experiencia.
    - No uses nombres propios ni lugares específicos; refiérete a ellos como "un lugar", "una persona", etc.
    - Emplea un lenguaje claro y directo, que fluya naturalmente para una lectura en voz alta.
    - Escribe en un estilo narrativo, como si contaras una historia, manteniendo una coherencia lógica y un hilo conductor claro.
    - Evita cualquier formato (asteriscos, negritas, encabezados); devuelve solo el texto formateado.

    {texto}

    Texto corregido:
    """
    try:
        model = genai.GenerativeModel(MODEL)
        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        st.error(f"Error al procesar con Gemini: {e}")
        return None


def procesar_transcripcion(texto):
    """Procesa el texto dividiendo en fragmentos y usando Gemini."""
    fragmentos = dividir_texto(texto)
    texto_limpio_completo = ""
    for i, fragmento in enumerate(fragmentos):
        st.write(f"Procesando fragmento {i+1}/{len(fragmentos)}")
        texto_limpio = limpiar_transcripcion_gemini(fragmento)
        if texto_limpio:
            texto_limpio_completo += texto_limpio + " "  # Agregar espacio para evitar que las frases se unan
    return texto_limpio_completo.strip()

def descargar_texto(texto_formateado):
    """
    Genera un enlace de descarga para el texto formateado.

    Args:
        texto_formateado (str): El texto formateado.

    Returns:
        streamlit.components.v1.html: Enlace de descarga.
    """
    return st.download_button(
        label="Descargar Texto",
        data=texto_formateado.encode('utf-8'),
        file_name="transcripcion_formateada.txt",
        mime="text/plain"
    )


st.title("Limpiador de Transcripciones de YouTube (con Gemini)")

transcripcion = st.text_area("Pega aquí tu transcripción sin formato:")
procesar_button = st.button("Procesar Texto") # Botón para iniciar el procesamiento

if procesar_button:
    if transcripcion:
         with st.spinner("Procesando con Gemini..."):
             texto_limpio = procesar_transcripcion(transcripcion)
             if texto_limpio:
                 st.subheader("Transcripción Formateada:")
                 st.write(texto_limpio)
                 descargar_texto(texto_limpio)
    else:
        st.warning("Por favor, introduce el texto a procesar.")

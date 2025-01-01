import streamlit as st
import google.generativeai as genai
import os

# Obtener la API Key de las variables de entorno
try:
    GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
    genai.configure(api_key=GOOGLE_API_KEY)
    MODEL = "gemini-1.5-flash" # Cambiamos el modelo
except KeyError:
    st.error("La variable de entorno _GOOGLE_API_KEY no está configurada.")
    st.stop()  # Detener la app si no hay API Key



def limpiar_transcripcion_gemini(texto):
    """
    Limpia una transcripción usando Gemini.

    Args:
      texto (str): La transcripción sin formato.

    Returns:
      str: La transcripción formateada.
    """
    prompt = f"""
       Actúa como un lector profundo y reflexivo, con una habilidad excepcional para la expansión textual. Escribe en primera persona, como si tú hubieras vivido la experiencia o reflexionado sobre los temas presentados.
    Sigue estas pautas con extrema precisión:
    - Reescribe el siguiente texto utilizando tus propias palabras, y asegúrate de que la longitud del texto resultante sea al menos igual o incluso un poco mayor que la longitud del texto original.
    - No reduzcas la información en ningún caso. Al contrario, intenta expandir cada punto y concepto si es posible, agregando detalles, ejemplos y matices.
    - No generes un resumen. Quiero un texto parafraseado y expandido, cuyo tamaño sea comparable o superior al texto original.
    - Dale un título preciso y llamativo que refleje el contenido expandido del texto.
    - Evita mencionar nombres de personajes o del autor directamente. Refiérete a ellos de manera genérica (ej: "una persona", "un personaje").
    - Concentra la reflexión en la experiencia general, las ideas principales, los temas, y las emociones transmitidas por el texto.
    - Utiliza un lenguaje evocador, personal, y narrativo. Como si estuvieras compartiendo tus propias conclusiones tras una profunda y reflexiva experiencia.
    - No uses nombres propios ni nombres de lugares específicos. Refiérete a ellos como "un lugar", "una persona", "otro personaje", etc.
    - Usa un lenguaje claro, directo y que fluya de manera natural para facilitar la lectura en voz alta.
    - Escribe en un estilo narrativo, como si estuvieras contando una historia, manteniendo una coherencia y una progresión lógica en el texto.
    - Evita cualquier formato (asteriscos, negritas, encabezados). Proporciona solamente el texto formateado.

    {texto}

    Texto corregido:
    """
    try:
        model = genai.GenerativeModel(MODEL)
        response = model.generate_content(prompt, generation_config={"temperature": 0.4})
        return response.text

    except Exception as e:
        st.error(f"Error al procesar con Gemini: {e}")
        return None


def procesar_transcripcion(texto):
    """Procesa el texto  usando Gemini."""
    with st.spinner("Procesando con Gemini..."):
        texto_limpio = limpiar_transcripcion_gemini(texto)
        return texto_limpio

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
        texto_limpio = procesar_transcripcion(transcripcion)
        if texto_limpio:
            st.subheader("Transcripción Formateada:")
            st.write(texto_limpio)
            descargar_texto(texto_limpio)
    else:
        st.warning("Por favor, introduce el texto a procesar.")

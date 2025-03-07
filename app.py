import streamlit as st
import google.generativeai as genai
import os
import textwrap

st.set_page_config(
    page_title="texto-largo",
    layout="wide"
)

# Obtener la API Key de las variables de entorno
try:
    GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]

    genai.configure(api_key=GOOGLE_API_KEY)

    # Listar los modelos disponibles
    available_models = [model.name for model in genai.list_models() if 'generateContent' in model.supported_generation_methods]

    if not available_models:
        st.error("No se encontraron modelos disponibles que soporten 'generateContent'.  Verifica tu API Key y permisos.")
        st.stop()

    # Widget de selección de modelo
    MODEL = st.selectbox("Selecciona un modelo Gemini:", available_models)

    st.write(f"Usando modelo: {MODEL}")


except KeyError:
    st.error("La variable de entorno GOOGLE_API_KEY no está configurada.")
    st.stop()  # Detener la app si no hay API Key

def dividir_texto(texto, max_tokens=3000):
    """Divide el texto en fragmentos más pequeños, intentando mantener la coherencia semántica.
    Ajusta el tamaño de los fragmentos para que sean lo más grandes posible sin exceder el límite de tokens,
    y trata de evitar cortar las frases a la mitad.
    """
    # Divide el texto en frases utilizando separadores comunes.
    frases = texto.split('. ')  # Divide por puntos seguidos de espacio.  Añade más separadores si es necesario (?!; etc.)

    fragmentos = []
    fragmento_actual = ""
    cuenta_tokens = 0

    for frase in frases:
        tokens_frase = len(frase.split())  # Estima el número de tokens en la frase

        if cuenta_tokens + tokens_frase <= max_tokens:
            # La frase cabe en el fragmento actual.
            fragmento_actual += frase + ". " # Añade la frase al fragmento y un espacio.
            cuenta_tokens += tokens_frase
        else:
            # La frase no cabe en el fragmento actual.  Crea un nuevo fragmento.
            if fragmento_actual:  # Si hay algo en el fragmento actual, lo añade a la lista.
                fragmentos.append(fragmento_actual.strip())  # Elimina espacios al principio/final
            fragmento_actual = frase + ". "  # Empieza un nuevo fragmento con la frase actual.
            cuenta_tokens = tokens_frase

    # Añade el último fragmento si no está vacío.
    if fragmento_actual:
        fragmentos.append(fragmento_actual.strip())

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
    Actúa como un escritor creativo y conversacional. Reescribe el siguiente texto para hacerlo más atractivo y fácil de entender, como si estuvieras contándole una historia a un amigo.

    **Instrucciones detalladas:**

    1.  **Parafrasea y Expande:** Usa tus propias palabras para reescribir el texto, expandiendo cada punto y concepto. Añade detalles, ejemplos, analogías y matices para enriquecer el contenido y hacerlo más interesante.  Asegúrate de que la longitud del texto resultante sea significativamente mayor que la del original. No te limites a un resumen; profundiza en cada idea.

    2.  **Tono Conversacional:** Escribe en un tono ameno, informal y cercano. Usa un lenguaje natural y evita la jerga técnica a menos que sea absolutamente necesario. Explica los conceptos complejos de forma sencilla y accesible.

    3.  **Reflexiones Personales:** Incorpora tus propias reflexiones, opiniones y experiencias relacionadas con el tema.  Pregúntate por qué es importante, cómo se aplica a la vida cotidiana y qué implicaciones tiene.  Haz que el lector se sienta conectado con el tema a un nivel personal.

    4.  **Estructura Narrativa:** Organiza el texto de forma lógica y coherente, como si estuvieras contando una historia.  Crea una introducción atractiva, desarrolla los puntos principales de manera clara y concisa, y concluye con un resumen de las ideas clave y una reflexión final.

    5.  **Título Atractivo:** Crea un título que capture la esencia del contenido de forma atractiva y que invite al lector a seguir leyendo.

    **Consideraciones:**

    *   Evita mencionar nombres propios o lugares específicos a menos que sea esencial para la comprensión.
    *   No uses formatos especiales como negritas o listas.  Devuelve solo el texto formateado.
    *   Asegúrate de que el texto resultante sea original y no una simple copia del texto original.
    *   Adapta el estilo de escritura al público objetivo (lectores generales).

    **Texto a reescribir:**

    {texto}

    **Texto corregido:**
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

import streamlit as st
import google.generativeai as genai
import os
import textwrap
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Obtener la API Key de las variables de entorno
try:
    GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
    genai.configure(api_key=GOOGLE_API_KEY)
    MODEL = "gemini-pro"
except KeyError:
    st.error("La variable de entorno GOOGLE_API_KEY no está configurada.")
    st.stop()  # Detener la app si no hay API Key

def contar_tokens(texto):
    """Cuenta el número de tokens en un texto."""
    model = genai.GenerativeModel(MODEL)
    return model.count_tokens(texto).total_tokens


def dividir_texto(texto, max_tokens=2500):
    """Divide el texto en fragmentos más pequeños por tokens."""
    fragmentos = []
    texto_restante = texto
    while texto_restante:
        fragmento_actual = ""
        tokens_actuales = 0
        while texto_restante and tokens_actuales < max_tokens:
           
           
            fragmento_candidato =  texto_restante
            tokens_candidatos= contar_tokens(fragmento_candidato)
            if tokens_candidatos <= max_tokens:
                
                fragmento_actual = fragmento_candidato
                texto_restante = ""
                tokens_actuales = tokens_candidatos
                
            else:
               
                
                texto_candidato_dividido = texto_restante.split(" ",1)
               
                if len(texto_candidato_dividido) > 1:
                   fragmento_candidato_palabra = texto_candidato_dividido[0]
                   tokens_candidatos = contar_tokens(fragmento_candidato_palabra)
                   if tokens_actuales + tokens_candidatos <= max_tokens:
                       fragmento_actual += fragmento_candidato_palabra + " "
                       tokens_actuales += tokens_candidatos
                       texto_restante = texto_candidato_dividido[1]

                   else:
                        break
                else:
                  
                  fragmento_actual = texto_restante
                  texto_restante = ""
                  tokens_actuales = contar_tokens(fragmento_actual)

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
       Actúa como un lector profundo y reflexivo. Escribe en primera persona, como si tú hubieras vivido la experiencia o reflexionado sobre los temas presentados.
    Sigue estas pautas:
    - Reescribe el siguiente texto utilizando tus propias palabras, y asegúrate de mantener una longitud similar al texto original.
    No reduzcas la información, e intenta expandir cada punto si es posible.
    No me generes un resumen, quiero un texto parafraseado y expandido con una longitud comparable al texto original.
    - Dale un titulo preciso y llamativo.
    - Evita mencionar nombres de personajes o del autor.
    - Concentra el resumen en la experiencia general, las ideas principales, los temas y las emociones transmitidas por el texto.
    - Utiliza un lenguaje evocador y personal, como si estuvieras compartiendo tus propias conclusiones tras una profunda reflexión.
    - No uses nombres propios ni nombres de lugares específicos, refiérete a ellos como "un lugar", "una persona", "otro personaje", etc.
    - Usa un lenguaje claro y directo
    - Escribe como si estuvieras narrando una historia
    - Evita los asteriscos en el texto, dame tan solo el texto sin encabezados ni texto en negrita
    -Importante, el texto debe adaptarse para que el lector de voz de google lo lea lo mejor posible
    - Limita el texto a 10.000 caracteres
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
            texto_limpio_completo += texto_limpio + " " # Agregar espacio para evitar que las frases se unan
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

st.title("Limpiador de Texto con Gemini")
max_tokens = st.number_input("Número máximo de tokens por fragmento", min_value=500, max_value=10000, value=2500, step=100)
transcripcion = st.text_area("Pega aquí el texto que quieres procesar:")
procesar_button = st.button("Procesar Texto")


if procesar_button:
    if transcripcion:
         with st.spinner("Procesando con Gemini..."):
              texto_limpio = procesar_transcripcion(transcripcion)
              if texto_limpio:
                 st.subheader("Texto Formateado:")
                 st.write(texto_limpio)
                 descargar_texto(texto_limpio)
    else:
        st.warning("Por favor, introduce el texto a procesar.")

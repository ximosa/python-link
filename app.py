import streamlit as st
import google.generativeai as genai
import os
import textwrap
import concurrent.futures
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Obtener la API Key de las variables de entorno
try:
    GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
    genai.configure(api_key=GOOGLE_API_KEY)
    MODEL = "gemini-pro"
except KeyError:
    st.error("La variable de entorno _GOOGLE_API_KEY no está configurada.")
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
    logging.info(f"Fragmentos creados: {fragmentos}")
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
        {texto}

        Texto corregido:
    """
    logging.info(f"Limpiando texto con Gemini: {texto[:50]}...")
    try:
        model = genai.GenerativeModel(MODEL)
        response = model.generate_content(prompt)
        if response and response.text:
            return response.text
        else:
            logging.error(f"Error en Gemini. No se ha podido procesar el texto: {texto[:50]}...")
            return None
    except Exception as e:
        logging.error(f"Error al procesar con Gemini: {e}")
        return None


def procesar_transcripcion(texto):
    """Procesa el texto dividiendo en fragmentos y usando Gemini."""
    fragmentos = dividir_texto(texto)
    logging.info(f"Fragmentos a procesar: {len(fragmentos)}")
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_fragment = {executor.submit(limpiar_transcripcion_gemini, fragmento): fragmento for fragmento in fragmentos}
        texto_limpio_completo = ""
        for future in concurrent.futures.as_completed(future_to_fragment):
            fragmento = future_to_fragment[future]
            try:
              texto_limpio = future.result()
              if texto_limpio:
                  texto_limpio_completo += texto_limpio + " "
                  st.write(f"Fragmento procesado: {fragmento[:50]}...")
              else:
                  st.error(f"Error al procesar fragmento: {fragmento[:50]}...")
            except Exception as e:
                st.error(f"Error al obtener el resultado del fragmento: {fragmento[:50]}... Error: {e}")
    
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
procesar_button = st.button("Procesar Texto")  # Botón para iniciar el procesamiento

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

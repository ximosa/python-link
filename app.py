import streamlit as st
import google.generativeai as genai
import os
import textwrap
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# Obtener la API Key de las variables de entorno
try:
    GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
    genai.configure(api_key=GOOGLE_API_KEY)
    MODEL = "gemini-pro"
except KeyError:
    st.error("La variable de entorno GOOGLE_API_KEY no está configurada.")
    st.stop()  # Detener la app si no hay API Key

def obtener_texto_de_url(url, processed_urls=None, max_pages=5):
    """
    Obtiene el texto principal de una URL y de las páginas enlazadas (hasta un límite).

    Args:
        url (str): La URL a analizar.
         processed_urls (set): Conjunto de URLs ya procesadas (para evitar bucles).
        max_pages (int): El número máximo de páginas a seguir.

    Returns:
        str: El texto extraído de la página y los enlaces, o None si hay un error.
    """
    if processed_urls is None:
        processed_urls = set()

    if url in processed_urls or len(processed_urls) >= max_pages:
        return "" # Si ya procesamos esta URL o excedemos el límite, detente
    
    processed_urls.add(url)

    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extraer el texto principal de la página
        textos = [p.text for p in soup.find_all('p')]
        texto_principal = "\n".join(textos)

         # Extraer enlaces y sus textos
        enlaces = []
        for a in soup.find_all('a', href=True):
            enlace = a['href']
            if enlace.startswith("http"): # Filtrar enlaces completos
               enlaces.append(f"[{a.text.strip()}]({enlace})")


        texto_enlaces = f"\n\nEnlaces:\n{' '.join(enlaces)}"

        # Buscar el enlace a la siguiente página (puedes necesitar ajustar el selector)
        next_link = soup.find('a', string=lambda text: text and "siguiente" in text.lower())
        
        if next_link:
            next_url = urljoin(url, next_link['href'])
             # Llamar recursivamente para procesar la siguiente página
            texto_siguiente_pagina = obtener_texto_de_url(next_url, processed_urls, max_pages)
            return f"Texto principal:\n{texto_principal}\n{texto_enlaces}\n{texto_siguiente_pagina}"

        return f"Texto principal:\n{texto_principal}\n{texto_enlaces}"

    except requests.exceptions.RequestException as e:
         st.error(f"Error al acceder a la URL: {e}")
         return None
    except Exception as e:
        st.error(f"Error al analizar la URL: {e}")
        return None


def dividir_texto(texto, max_tokens=2000):
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

st.title("Limpiador de Texto Web (con Gemini)")

url = st.text_input("Introduce la URL de la página web:")

if url:
    with st.spinner("Obteniendo texto de la URL y procesando con Gemini..."):
         texto_web = obtener_texto_de_url(url)
         if texto_web:
             texto_limpio = procesar_transcripcion(texto_web)
             if texto_limpio:
                st.subheader("Texto Formateado:")
                st.write(texto_limpio)
                descargar_texto(texto_limpio)

import streamlit as st
import frontend
from openai import OpenAI
from PIL import Image
import tempfile
import emoji
import re
from elevenlabs import ElevenLabs
from pydub import AudioSegment
import random
from pathlib import Path
import os
import random


# Configuración de la página
PRIMARY_COLOR = "#4b83c0"
SECONDARY_COLOR = "#878889"
BACKGROUND_COLOR = "#ffffff"

ICOMEX_LOGO_PATH = "logos/ICOMEX_Logos_sin_fondo.png"
PAISA_AVATAR_PATH = "logos/paisabot_avatar_chat.png"
USER_LOGO_PATH = "logos/user_avatar.png"

st.set_page_config(page_title="PaisaBot - Asesor Virtual", layout="centered", page_icon=PAISA_AVATAR_PATH)

# Inicializar estilos personalizados
frontend.render_custom_styles()

background_tracks = [
    {"path": "instrumentales/milonga_arrabalera_1.mp3", "total_duration": 103, "intro_duration": 14},
    {"path": "instrumentales/milonga_arrabalera_2.mp3", "total_duration": 25, "intro_duration": 10},
    {"path": "instrumentales/milonga_arrabalera_3.mp3", "total_duration": 29, "intro_duration": 11},
    {"path": "instrumentales/milonga_arrabalera_4.mp3", "total_duration": 56, "intro_duration": 10.5},
    {"path": "instrumentales/milonga_arrabalera_5.mp3", "total_duration": 31, "intro_duration": 6},
    {"path": "instrumentales/milonga_campera_1.mp3", "total_duration": 118, "intro_duration": 9},
    {"path": "instrumentales/milonga_campera_2.mp3", "total_duration": 80, "intro_duration": 1},
    {"path": "instrumentales/milonga_campera_3.mp3", "total_duration": 38, "intro_duration": 1},
    {"path": "instrumentales/milonga_campera_4.mp3", "total_duration": 110, "intro_duration": 16},
    {"path": "instrumentales/milonga_campera_5.mp3", "total_duration": 190, "intro_duration": 16},
    {"path": "instrumentales/milonga_oriental_1.mp3", "total_duration": 126, "intro_duration": 12},
    {"path": "instrumentales/milonga_oriental_2.mp3", "total_duration": 116, "intro_duration": 1},
    {"path": "instrumentales/milonga_oriental_3.mp3", "total_duration": 71, "intro_duration": 1},
    {"path": "instrumentales/milonga_oriental_4.mp3", "total_duration": 41, "intro_duration": 12},
    {"path": "instrumentales/milonga_oriental_5.mp3", "total_duration": 30, "intro_duration": 1},
    {"path": "instrumentales/milonga_pampeana_1.mp3", "total_duration": 101, "intro_duration": 17},
    {"path": "instrumentales/milonga_pampeana_2.mp3", "total_duration": 101, "intro_duration": 1},
    {"path": "instrumentales/milonga_pampeana_3.mp3", "total_duration": 84, "intro_duration": 1},
    {"path": "instrumentales/milonga_pampeana_4.mp3", "total_duration": 69, "intro_duration": 14.5},
    {"path": "instrumentales/milonga_pampeana_5.mp3", "total_duration": 69, "intro_duration": 0.5},
    {"path": "instrumentales/milonga_pampeana_6.mp3", "total_duration": 55, "intro_duration": 1},
    {"path": "instrumentales/milonga_pampeana_7.mp3", "total_duration": 25, "intro_duration": 1},
    {"path": "instrumentales/milonga_payada_1.mp3", "total_duration": 125, "intro_duration": 1},
    {"path": "instrumentales/milonga_payada_2.mp3", "total_duration": 53, "intro_duration": 1},
]

def generate_mito_realidad_file(statements, filename="mito_realidad.txt", num=5):
    """
    Genera un archivo .txt con afirmaciones seleccionadas aleatoriamente.
    """
    # Seleccionar afirmaciones aleatorias
    selected_statements = random.sample(statements, num)
    header = "# Mito o realidad\n\n"
    content = header + "\n\n".join(selected_statements)
    
    # Definir la ruta del archivo
    file_path = Path(__file__).parent / filename
    
    # Escribir el contenido en el archivo
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)
    
    return file_path

def combine_audio_with_background(voice_path):
    """
    Combina el audio generado con una pista de fondo en formato MP3.
    Incrementa el volumen de la voz un 35%.
    """
    try:
        # Cargar el audio de la voz
        voice_audio = AudioSegment.from_file(voice_path)

        # Aumentar el volumen de la voz en un 35%
        voice_audio = voice_audio + 35 / 10  # Convertir porcentaje a dB (decibelios)

        voice_duration = len(voice_audio) / 1000  # Duración en segundos

        # Filtrar pistas válidas
        valid_tracks = [
            track for track in background_tracks
            if track["total_duration"] >= voice_duration + track["intro_duration"] + 2
        ]

        if not valid_tracks:
            st.error("No hay pistas musicales disponibles que cumplan con los requisitos.")
            return None

        # Seleccionar una pista al azar
        selected_track = random.choice(valid_tracks)
        background_audio = AudioSegment.from_file(selected_track["path"])

        # Recortar la pista de fondo
        total_cut_duration = selected_track["intro_duration"] + voice_duration + 2
        trimmed_background = background_audio[:total_cut_duration * 1000]

        # Superponer la voz
        combined_audio = trimmed_background.overlay(voice_audio, position=selected_track["intro_duration"] * 1000)

        # Aplicar fade out en los últimos 2 segundos
        final_audio = combined_audio.fade_out(duration=2000)

        # Exportar el audio combinado
        output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
        final_audio.export(output_path, format="mp3")

        return output_path

    except Exception as e:
        st.error(f"Error al combinar audio: {e}")
        return None

# Cachear las imágenes
@st.cache_data
def load_image(image_path):
    return Image.open(image_path)

def clean_message_for_audio(message_content):
    # Replace for pronunciation
    message_content = message_content.replace("I-COMEX","ICÓMEX")
    message_content = message_content.replace("km","kilómetros")
    message_content = message_content.replace("1950", "mil novecientos cincuenta")
    message_content = message_content.replace("2954575326", "dos nueve cinco cuatro, cincuenta y siete, cincuenta y tres, veintiseis.")
    message_content = message_content.replace("agencia@icomexlapampa.org","agencia, arroba, icomexlapampa, punto, org.")
    message_content = message_content.replace("08:00 a 15:00 hs","ocho a quince horas")
    message_content = message_content.replace("https://maps.app.goo.gl/RET62U9mK9JecpmT9","")
    message_content = message_content.replace("!",".")
    message_content = message_content.replace("¡","")
    # Remove Markdown bold (**text** -> text)
    message_content = re.sub(r"\*\*(.*?)\*\*", r"\1", message_content)
    # Remove emojis
    message_content = emoji.replace_emoji(message_content, replace="")
    # Remove all "#" characters
    message_content = message_content.replace("#", "")
    # Replace line breaks with spaces
    message_content = message_content.replace(":", "...")
    
    # Reemplazar párrafos que terminan en punto seguido de salto de línea doble por "..."
    #message_content = re.sub(r'\,\s*\n', '--\n', message_content)
    #message_content = re.sub(r'\.\s*\n\s*\n', ' <break time="3s" />\n\n', message_content)
    message_content = message_content.replace(".", '<break time="1s" />')
    message_content = re.sub(r'<break time="1s" />  $', '.', message_content)
    message_content = re.sub(r'<break time="1s" />$', '.', message_content)    
    return message_content

# def load_instructions(topic):
#     # Definir el directorio base para instrucciones
#     instructions_dir = Path(__file__).parent / "instructions"

#     # Diccionario de archivos de instrucciones
#     INSTRUCTIONS_FILES = {
#         "Mito o realidad": instructions_dir / "instructions_mito_realidad.txt",
#         "Trivia": instructions_dir / "instructions_trivia.txt",
#         "Payador con IA": instructions_dir / "instructions_payador.txt",
#     }

#     try:
#         with open(INSTRUCTIONS_FILES[topic], "r", encoding="utf-8") as file:
#             return file.read().strip()
#     except FileNotFoundError:
#         st.error(f"No se encontró el archivo de instrucciones para {topic}. Verifica el repositorio y la carpeta.")
#         return None

def load_instructions(topic):
    # Definir el directorio base para instrucciones
    instructions_dir = Path(__file__).parent / "instructions"
    mito_realidad_file = Path(__file__).parent / "mito_realidad.txt"
    trivia_file = Path(__file__).parent / "trivia.txt"

    # Diccionario de archivos de instrucciones
    INSTRUCTIONS_FILES = {
        "Mito o realidad": instructions_dir / "instructions_mito_realidad.txt",
        "Trivia": instructions_dir / "instructions_trivia.txt",
        "Payador con IA": instructions_dir / "instructions_payador.txt",
    }

    try:
        # Leer el contenido base de instrucciones
        with open(INSTRUCTIONS_FILES[topic], "r", encoding="utf-8") as base_file:
            base_content = base_file.read().strip()

        # Si el modo es "Mito o realidad", agregar afirmaciones aleatorias
        if topic == "Mito o realidad":
            # Leer todas las afirmaciones de mito_realidad.txt
            with open(mito_realidad_file, "r", encoding="utf-8") as mito_file:
                all_statements = [
                    statement.strip()
                    for statement in mito_file.read().split('""",\n"""')
                ]  # Separar por bloques de texto

            # Determinar cuántas afirmaciones seleccionar (máximo 5 o el total disponible)
            num_statements = min(5, len(all_statements))

            # Seleccionar afirmaciones aleatorias
            selected_statements = random.sample(all_statements, num_statements)

            # Crear un formato para las afirmaciones seleccionadas
            additional_content = "# Mito o realidad\n\n"
            additional_content += "\n\n".join(
                [f"{i+1}. {statement.strip()}" for i, statement in enumerate(selected_statements)]
            )

            # Combinar el contenido base con las afirmaciones seleccionadas
            return f"{base_content}\n\n{additional_content}"

        # Si el modo es "Trivia", agregar preguntas aleatorias
        elif topic == "Trivia":
            # Leer todas las preguntas de trivia.txt
            with open(trivia_file, "r", encoding="utf-8") as trivia_file:
                all_questions = [
                    question.strip()
                    for question in trivia_file.read().split('""",\n"""')
                ]  # Separar por bloques de texto

            # Determinar cuántas preguntas seleccionar (máximo 5 o el total disponible)
            num_questions = min(5, len(all_questions))

            # Seleccionar preguntas aleatorias
            selected_questions = random.sample(all_questions, num_questions)

            # Crear un formato para las preguntas seleccionadas
            additional_content = "# Trivia\n\n"
            additional_content += "\n\n".join(
                [f"{i+1}. {question.strip()}" for i, question in enumerate(selected_questions)]
            )

            # Combinar el contenido base con las preguntas seleccionadas
            return f"{base_content}\n\n{additional_content}"

        # Si no es "Mito o realidad" ni "Trivia", devolver solo el contenido base
        return base_content

    except FileNotFoundError as e:
        st.error(f"Error al cargar las instrucciones para {topic}: {e}")
        return None


# # Function to load instructions
# def load_instructions(topic):
#     INSTRUCTIONS_FILES = {
#         "Mito o realidad": "instructions\instructions_mito_realidad.txt",
#         "Trivia": "instructions\instructions_trivia.txt",
#         "Payador con IA": "instructions\instructions_payador.txt"
#     }
#     try:
#         with open(INSTRUCTIONS_FILES[topic], "r", encoding="utf-8") as file:
#             return file.read().strip()
#     except FileNotFoundError:
#         st.error(f"No se encontró el archivo de instrucciones para {topic}.")
#         return None

paisa_logo = load_image(PAISA_AVATAR_PATH)
user_logo = load_image(USER_LOGO_PATH)

# Inicialización del estado
if "selected_topic" not in st.session_state:
    st.session_state.selected_topic = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "initial_message_shown" not in st.session_state:
    st.session_state.initial_message_shown = False
if "subtitle_shown" not in st.session_state:
    st.session_state.subtitle_shown = False
if "rendered_message_ids" not in st.session_state:
    st.session_state.rendered_message_ids = set()
if "show_form" not in st.session_state:
    st.session_state.show_form = False

# Renderizar el encabezado (siempre visible)
frontend.render_title()

def generar_audio_elevenlabs_sdk(texto, voice_id="ZtseFBfK9giRDiPkiE6o"):
    try:
        # Inicializa el cliente de ElevenLabs con la clave API
        client = ElevenLabs(api_key=st.secrets["elevenlabs"]["api_key"])

        # Generar el audio usando el SDK
        audio_generator = client.text_to_speech.convert(
            voice_id=voice_id,
            model_id="eleven_multilingual_v2",
            text=texto,
            voice_settings={
                "stability": 0.30,
                "similarity_boost": 0.77,
                "style": 0.8,
                "use_speaker_boost": True
            }
        )

        # Guardar en un archivo temporal
        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        with open(temp_audio.name, "wb") as f:
            for chunk in audio_generator:  # Iterar sobre el generador
                f.write(chunk)

        return temp_audio.name

    except Exception as e:
        st.error(f"Error al generar audio: {e}")
        return None

# Renderizar subtítulo dinámico basado en el tema seleccionado
if st.session_state.selected_topic:
    if not st.session_state.subtitle_shown:
        frontend.render_subheader(st.session_state.selected_topic)
        st.session_state.subtitle_shown = True
    else:
        st.subheader(st.session_state.selected_topic)

# Renderizar la introducción y botones solo si no se ha seleccionado un tema
if st.session_state.selected_topic is None:
    frontend.render_intro()

# Mostrar chat y mensajes si se seleccionó un tema
if st.session_state.selected_topic:
    # Cargar las instrucciones del sistema solo una vez
    if not st.session_state.initial_message_shown:
        instructions = load_instructions(st.session_state.selected_topic)
        if instructions:
            st.session_state.messages.append({"role": "system", "content": instructions})
        st.session_state.messages.append({"role": "assistant", "content": st.session_state.initial_message})
        st.session_state.initial_message_shown = True

    # Renderizar mensajes existentes
    for i, message in enumerate(st.session_state.messages):
        if message["role"] != "system":
            message_id = f"{message['role']}-{i}"
            if message_id not in st.session_state.rendered_message_ids:
                if message["role"] == "assistant":
                    frontend.render_dynamic_message(message, avatar=paisa_logo)
                else:
                    frontend.render_chat_message(message["role"], message["content"], avatar=user_logo)
                st.session_state.rendered_message_ids.add(message_id)
            else:
                frontend.render_chat_message(message["role"], message["content"],
                                             avatar=paisa_logo if message["role"] == "assistant" else user_logo)

    # # Renderizar el campo de entrada
    # if prompt := frontend.render_input():
    #     st.session_state.messages.append({"role": "user", "content": prompt})
    #     frontend.render_chat_message("user", prompt, avatar=user_logo)

    #     client = OpenAI(api_key=st.secrets["openai"]["api_key"])
    #     response = client.chat.completions.create(
    #         model="gpt-4o-mini",
    #         messages=st.session_state.messages,
    #         temperature=0.5,                    
    #         frequency_penalty=0, 
    #         presence_penalty=-1   
    #     )

    #     response_content = response.choices[0].message.content
    #     response_message = {"role": "assistant", "content": response_content}
    #     st.session_state.messages.append(response_message)

    #     # Renderizar el mensaje del chatbot
    #     frontend.render_dynamic_message(response_message, avatar=paisa_logo)
    #     st.session_state.rendered_message_ids.add(f"assistant-{len(st.session_state.messages) - 1}")

    #     # Limpiar el texto antes de enviarlo a Eleven Labs
    #     texto_limpio = clean_message_for_audio(response_content)
    #     # Generar el audio de la voz
    #     audio_path = generar_audio_elevenlabs_sdk(texto_limpio)
    #     if audio_path:
    #         # Combinar con música de fondo
    #         final_audio_path = combine_audio_with_background(audio_path)
    #         if final_audio_path:
    #             st.audio(final_audio_path, format="audio/mp3")
    # Configuración de los parámetros de OpenAI por modo
    TOPIC_CONFIG = {
        "Mito o realidad": {
            "model": "gpt-4o-mini",
            "temperature": 0.3,
            "frequency_penalty": -0.5,
            "presence_penalty": -0.5,
        },
        "Trivia": {
            "model": "gpt-4o-mini",
            "temperature": 0.1,
            "frequency_penalty": -0.5,
            "presence_penalty": -0.5,
        },
        "Payador con IA": {
            "model": "gpt-4o-mini",
            "temperature": 0.5,
            "frequency_penalty": 0,
            "presence_penalty": -1,
        },
        "default": {
            "model": "gpt-4o-mini",
            "temperature": 0.5,
            "frequency_penalty": 0,
            "presence_penalty": -1,
        },
    }
    # Verificar el modo seleccionado para obtener la configuración
    selected_topic = st.session_state.selected_topic
    if selected_topic in TOPIC_CONFIG:
        config = TOPIC_CONFIG[selected_topic]
    else:
        config = TOPIC_CONFIG["default"]

    # Renderizar el campo de entrada y procesar la respuesta
    if prompt := frontend.render_input():
        st.session_state.messages.append({"role": "user", "content": prompt})
        frontend.render_chat_message("user", prompt, avatar=user_logo)

        # Llamada al API de OpenAI con la configuración seleccionada
        client = OpenAI(api_key=st.secrets["openai"]["api_key"])
        response = client.chat.completions.create(
            model=config["model"],
            messages=st.session_state.messages,
            temperature=config["temperature"],
            frequency_penalty=config["frequency_penalty"],
            presence_penalty=config["presence_penalty"],
        )

        # Extraer el contenido de la respuesta
        response_content = response.choices[0].message.content
        response_message = {"role": "assistant", "content": response_content}
        st.session_state.messages.append(response_message)

        # Renderizar el mensaje del chatbot
        frontend.render_dynamic_message(response_message, avatar=paisa_logo)
        st.session_state.rendered_message_ids.add(f"assistant-{len(st.session_state.messages) - 1}")

        # Generar y reproducir audio solo si está en el modo "Payador con IA"
        # if selected_topic == "Payador con IA":
        #     texto_limpio = clean_message_for_audio(response_content)
        #     audio_path = generar_audio_elevenlabs_sdk(texto_limpio)
        #     if audio_path:
        #         final_audio_path = combine_audio_with_background(audio_path)
        #         if final_audio_path:
        #             st.audio(final_audio_path, format="audio/mp3")
# import os
# import time
from flask import Blueprint, render_template, request, jsonify
# from werkzeug.utils import secure_filename
# from transformers import AutoModelForCausalLM, AutoTokenizer
# from PyPDF2 import PdfReader
# import docx

chat_ai_bp = Blueprint('chat_ai', __name__)

# Configurar un directorio de caché local
# CACHE_DIR = "./cache"
# os.makedirs(CACHE_DIR, exist_ok=True)

# # Configurar el tokenizador y el modelo
# MODEL_NAME = "EleutherAI/gpt-neo-1.3B"  # Modelo ligero para CPU
# tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, cache_dir=CACHE_DIR)
# model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, cache_dir=CACHE_DIR)

# # Asignar un token de padding si no está definido
# if tokenizer.pad_token is None:
#     tokenizer.pad_token = tokenizer.eos_token  # Reutilizar el token de fin de secuencia como token de padding

# # Ruta de los manuales
# MANUALS_FOLDER = os.path.join('app', 'static', 'manuals')

# # Variable global para almacenar el contexto de los manuales
# manuals_context = ""

# def load_manuals():
#     """
#     Carga y concatena el contenido de todos los manuales en la carpeta MANUALS_FOLDER.
#     """
#     manuals_content = ""

#     for filename in os.listdir(MANUALS_FOLDER):
#         filepath = os.path.join(MANUALS_FOLDER, filename)
#         if filename.endswith('.txt'):
#             with open(filepath, 'r', encoding='utf-8') as file:
#                 manuals_content += file.read() + "\n"
#         elif filename.endswith('.pdf'):
#             try:
#                 reader = PdfReader(filepath)
#                 if reader.is_encrypted:
#                     try:
#                         reader.decrypt("")  # Intenta descifrar con una contraseña vacía
#                     except Exception as e:
#                         print(f"Advertencia: No se pudo descifrar el archivo PDF {filename}. Error: {e}")
#                         continue
#                 for page in reader.pages:
#                     manuals_content += page.extract_text() + "\n"
#             except Exception as e:
#                 print(f"Error al procesar el archivo PDF {filename}: {e}")
#         elif filename.endswith('.docx'):
#             doc = docx.Document(filepath)
#             for paragraph in doc.paragraphs:
#                 manuals_content += paragraph.text + "\n"

#     return manuals_content

# # Cargar el contenido de los manuales al iniciar la aplicación
# manuals_context = load_manuals()

# # Ruta para el módulo de Chat IA
# @chat_ai_bp.route('/', methods=['GET', 'POST'])
# def chat_ai():
#     global manuals_context  # Asegurarse de usar la variable global
#     if request.method == 'POST':
#         try:
#             # Obtener la pregunta del cuerpo de la solicitud JSON
#             data = request.get_json()
#             question = data.get('question') if data else None

#             if not question or question.strip() == "":
#                 return jsonify({"error": "Por favor, ingresa una pregunta válida."}), 400

#             # Crear el prompt combinando el contexto de los manuales y la pregunta del usuario
#             prompt = f"Contexto:\n{manuals_context}\n\nPregunta:\n{question}\n\nRespuesta en español:"

#             # Tokenizar el prompt para verificar su longitud
#             prompt_tokens = tokenizer.encode(prompt)

#             # Configurar el límite de tokens para la salida generada
#             max_new_tokens = 200  # Longitud máxima de la salida generada
#             max_total_tokens = 2048  # Límite total de tokens permitido por el modelo

#             # Si el prompt excede el espacio disponible, trunca el contexto de los manuales
#             if len(prompt_tokens) + max_new_tokens > max_total_tokens:
#                 max_context_length = max_total_tokens - max_new_tokens
#                 truncated_manuals_context = tokenizer.decode(prompt_tokens[:max_context_length], skip_special_tokens=True)
#                 prompt = f"Contexto:\n{truncated_manuals_context}\n\nPregunta:\n{question}\n\nRespuesta en español:"

#             # Tokenizar la entrada con truncación y padding
#             inputs = tokenizer(
#                 prompt,
#                 return_tensors="pt",
#                 truncation=True,
#                 max_length=max_total_tokens - max_new_tokens,  # Dejar espacio para la salida generada
#                 padding="max_length"  # Asegura que la entrada tenga un tamaño fijo
#             )

#             # Generar respuesta con el modelo GPT-Neo
#             outputs = model.generate(
#                 inputs["input_ids"],
#                 attention_mask=inputs["attention_mask"],  # Pasar la máscara de atención
#                 max_new_tokens=max_new_tokens,  # Longitud máxima de la respuesta generada
#                 num_return_sequences=1,
#                 pad_token_id=tokenizer.pad_token_id  # Usar el token de padding configurado
#             )
#             response = tokenizer.decode(outputs[0], skip_special_tokens=True)

#             # Extraer solo la respuesta generada (sin el contexto ni la pregunta)
#             response = response.replace(prompt, "").strip()

#             return jsonify({"response": response}), 200
#         except Exception as e:
#             return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500

#     return render_template('chat_ai.html')

# @chat_ai_bp.route('/reload-manuals', methods=['POST'])
# def reload_manuals():
#     """
#     Recarga el contenido de los manuales desde la carpeta MANUALS_FOLDER.
#     """
#     global manuals_context  # Asegurarse de usar la variable global
#     try:
#         manuals_context = load_manuals()
#         return jsonify({"message": "Los manuales se han recargado exitosamente."}), 200
#     except Exception as e:
#         return jsonify({"error": f"Error al recargar los manuales: {str(e)}"}), 500

# # Ruta para cargar manuales en texto plano, PDF o DOCX
# @chat_ai_bp.route('/upload-manual', methods=['POST'])
# def upload_manual():
#     if 'file' not in request.files:
#         return jsonify({"error": "No se encontró ningún archivo."}), 400

#     file = request.files['file']
#     if file.filename == '':
#         return jsonify({"error": "El archivo no tiene nombre."}), 400

#     # Validar formato del archivo
#     if not allowed_file(file.filename):
#         return jsonify({"error": "Formato de archivo no permitido. Solo se aceptan .txt, .pdf y .docx."}), 400

#     # Guardar el archivo en la carpeta app/static/manuals
#     manuals_folder = os.path.join('app', 'static', 'manuals')
#     os.makedirs(manuals_folder, exist_ok=True)  # Asegurarse de que la carpeta exista
#     filename = secure_filename(file.filename)
#     file.save(os.path.join(manuals_folder, filename))

#     return jsonify({"message": f"Archivo {filename} cargado exitosamente."})

# def allowed_file(filename):
#     """
#     Verifica si el archivo tiene una extensión permitida.
#     """
#     allowed_extensions = {'txt', 'pdf', 'docx'}
#     return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

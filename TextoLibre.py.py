from flask import Flask, request, jsonify, make_response
from flask_cors import CORS, cross_origin  # Importa cross_origin
import traceback
import guidance
import json
import logging

logging.basicConfig(level=logging.DEBUG)  # Configurar el logging

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})  # Configura CORS para permitir solicitudes desde localhost:3000

# Configura el modelo de lenguaje para ejecutar programas de guidance
guidance.llm = guidance.llms.OpenAI(model="text-davinci-003", api_key="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")


def generate_guidance_template(num_sessions, methodology, session_duration):
    sessions = ''.join([generate_session_template(i) for i in range(1, num_sessions + 1)])
    return f'''
Metodología: {methodology}
Duración de Sesiones: {session_duration} minutos
{sessions}
'''


def generate_session_template(session_number):
    return f'''
#### Sesión {session_number}
## 🚀 Objetivo de Clase: 
- "{{{{gen 'objetivo_sesion{session_number}' max_tokens=50}}}}"

## ✅ Actividades: 
1. "{{{{gen 'actividad1_sesion{session_number}' max_tokens=50}}}}"
2. "{{{{gen 'actividad2_sesion{session_number}' max_tokens=50}}}}"
3. "{{{{gen 'actividad3_sesion{session_number}' max_tokens=50}}}}"

## ✅ Evaluación: 
1. "{{{{gen 'pregunta1_evaluacion_sesion{session_number}' max_tokens=50}}}}"
2. "{{{{gen 'pregunta2_evaluacion_sesion{session_number}' max_tokens=50}}}}"
3. "{{{{gen 'pregunta3_evaluacion_sesion{session_number}' max_tokens=50}}}}"

## 🎨 Dinámica: 
1. "{{{{gen 'dinamica1_sesion{session_number}' max_tokens=50}}}}"
2. "{{{{gen 'dinamica2_sesion{session_number}' max_tokens=50}}}}"
3. "{{{{gen 'dinamica3_sesion{session_number}' max_tokens=50}}}}"
'''


@app.route('/api/generateDetailedPlan', methods=["POST", "OPTIONS"])
@cross_origin()

def generateDetailedPlan():
    app.logger.debug("Solicitud recibida en /api/generateDetailedPlan")  # Log al recibir la solicitud

    if request.method == "OPTIONS":  # Si el método de la solicitud es OPTIONS
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

    
    try:
        if request.content_type != 'application/json':
            return jsonify({'error': 'Content-Type must be application/json'}), 415

        data = request.json
        app.logger.debug(f"Datos recibidos: {data}")  # Log para los datos recibidos

        texto_libre = data.get('texto_libre', '').strip()
        materia = data.get('materia', '').strip()
        grado = data.get('grado', '').strip()
        asignatura = data.get('asignatura', '').strip()
        num_sesiones = data.get('num_sesiones', 1)         # Nuevo parámetro
        metodologia = data.get('metodologia', '').strip()  # Nuevo parámetro
        duracion_sesion = data.get('duracion_sesion', 45)  # Nuevo parámetro, default a 45 minutos si no se especifica

        sessions_template = generate_guidance_template(num_sesiones, metodologia, duracion_sesion)

        program = guidance(f'''
# Planificación Detallada
## Materia: {{materia}}
## Grado: {{grado}}
## Asignatura: {{asignatura}}
## Actividad Propuesta: {{texto_libre}}
{sessions_template}
''')

        guidance_result = program(texto_libre=texto_libre, materia=materia, grado=grado, asignatura=asignatura)

        result_dict = {k: v for k, v in guidance_result.variables().items() if k != "llm"}

        return jsonify({'generated_plan': result_dict}), 200

    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({'error': 'Error interno del servidor'}), 500

if __name__ == "__main__":
    app.logger.debug("Iniciando servidor en http://0.0.0.0:5000")  # Log al iniciar el servidor
    app.run(host='0.0.0.0', port=5000, debug=True)
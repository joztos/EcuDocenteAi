from flask import Flask, request, jsonify, make_response
from flask_cors import CORS, cross_origin
import traceback
import guidance
import os
from dotenv import load_dotenv

# Cargar las variables de entorno
load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})
guidance.llm = guidance.llms.OpenAI(model="text-davinci-003", api_key=openai_api_key)

def filter_unserializable(data):
    if isinstance(data, dict):
        return {k: filter_unserializable(v) for k, v in data.items() if k != 'llm'}
    return data

@app.route('/api/generateMicroPlan', methods=["POST", "OPTIONS"])
@cross_origin()
def generateMicroPlan():
    if request.method == "OPTIONS":
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response 

    try:
        if request.content_type != 'application/json':
            return jsonify({'error': 'Content-Type must be application/json'}), 415

        data = request.json
        tema = data.get('tema', '').strip()
        metodologia = data.get('metodologia', '').strip().upper()
        num_sesiones = data.get('num_sesiones', 0)
        duracion_sesiones = data.get('duracion_sesiones', '').strip()
        grado = data.get('grado', '').strip()
        edad = data.get('edad', '').strip()

        if not tema or not metodologia or not num_sesiones or not duracion_sesiones or not grado or not edad:
            return jsonify({'error': 'Todos los campos son requeridos y no pueden estar vacíos'}), 400

        guidance_results = []
        for i in range(num_sesiones):
            program_objetivo = guidance('''
            Genera un objetivo de clase centrado en el tema {{tema}} para estudiantes de {{grado}} con edad de {{edad}} años utilizando la metodología {{metodologia}}.
            Objetivo de Clase: "{{gen 'objetivo' max_tokens=300}}"
            ''')
            guidance_objetivo = program_objetivo(tema=tema, grado=grado, edad=edad, metodologia=metodologia).variables()["objetivo"]

            program_content = guidance('''
            Basado en el objetivo: {{objetivo}} y el tema {{tema}} para estudiantes de {{grado}} con edad de {{edad}} años, considerando la metodología {{metodologia}}.
            Sesión {{session_number}} de {{duracion_sesiones}}:
            Actividades: 
            {{#geneach 'actividades' num_iterations=3}}
            - {{gen 'this' max_tokens=200}}{{/geneach}}
            Preguntas de Evaluación: 
            {{#geneach 'preguntas_evaluacion' num_iterations=3}}
            {{@index+1}}. {{gen 'this' max_tokens=200}}{{/geneach}}
            Dinámica: {{gen 'dinamica' max_tokens=300}}
            ''')
            guidance_result = program_content(objetivo=guidance_objetivo, tema=tema, grado=grado, edad=edad, session_number=i+1, duracion_sesiones=duracion_sesiones, metodologia=metodologia)
            guidance_results.append(guidance_result.variables())

        result_dict = {"session_{}".format(i+1): guidance_results[i] for i in range(num_sesiones)}
        result_dict = filter_unserializable(result_dict)
        return jsonify({'generated_plan': result_dict}), 200

    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({'error': 'Error interno del servidor'}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)

from flask import Flask, request, jsonify, make_response
from flask_cors import CORS, cross_origin
import traceback
import guidance
import json
import os
from dotenv import load_dotenv
from functools import wraps
import jwt

# Cargar las variables de entorno
load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')
jwt_secret_key = os.getenv('JWT_SECRET_KEY')

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})
guidance.llm = guidance.llms.OpenAI(model="text-davinci-003", api_key=openai_api_key)

METODOLOGIAS = {
    'BLOOM': ['Conocimiento', 'Comprensión', 'Aplicación', 'Análisis', 'Síntesis', 'Evaluación'],
    'ERCA': ['Experiencia', 'Reflexión', 'Conceptualización', 'Aplicación'],
    'MONTESSORI': ['EnfoqueMontessori'],
    'NEURO-EDUCACION': ['EnfoqueNeuroeducativo']
}

# Decorador para validar JWT
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 403
        
        try:
            jwt.decode(token, jwt_secret_key, algorithms=["HS256"])
        except:
            return jsonify({'error': 'Token is invalid'}), 403
        
        return f(*args, **kwargs)
    return decorated

def divide_etapas(metodologia, num_sesiones):
    etapas = METODOLOGIAS[metodologia]
    sesiones = []
    
    if metodologia in ['MONTESSORI', 'NEURO-EDUCACION']:
        return [[etapas[0]] for _ in range(num_sesiones)]
    
    etapas_por_sesion = len(etapas) // num_sesiones
    extra_etapas = len(etapas) % num_sesiones

    for i in range(num_sesiones):
        start = i * etapas_por_sesion + min(i, extra_etapas)
        end = start + etapas_por_sesion + (1 if i < extra_etapas else 0)
        sesiones.append(etapas[start:end])

    return sesiones

def filter_unserializable(data):
    if isinstance(data, dict):
        return {k: filter_unserializable(v) for k, v in data.items() if k != 'llm'}
    return data

@app.route('/api/generateMicroPlan', methods=["POST", "OPTIONS"])
@cross_origin()
#@token_required
def generateMicroPlan():
    if request.method == "OPTIONS":
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response 

    try:
        if request.content_type != 'application/json':
            return jsonify({'error': 'Content-Type must be application/json'}), 415

        data = request.json
        destreza = data.get('destreza', '').strip()
        indicador = data.get('indicador', '').strip()
        metodologia = data.get('metodologia', '').strip().upper()  
        grado = data.get('grado', '').strip()
        edad = data.get('edad', '').strip()
        num_sesiones = int(data.get('num_sesiones', '').strip())
        duracion_sesiones = data.get('duracion_sesiones', '').strip()

        if not destreza or not indicador or not metodologia or not grado or not edad or not num_sesiones or not duracion_sesiones:
            return jsonify({'error': 'Todos los campos son requeridos y no pueden estar vacíos'}), 400

        sesiones_etapas = divide_etapas(metodologia, num_sesiones)
        session_objectives = []

        for etapas in sesiones_etapas:
            program_objetivo = guidance('''
            Genera un objetivo de clase para cada sesión del plan de estudios centrado en la destreza {{destreza}} y el indicador {{indicador}} para estudiantes de {{grado}} con edad de {{edad}} años, tomando en cuenta las etapas {{etapas}}.
            Objetivo de Clase: 
            "{{gen 'objetivo' max_tokens=200}}"
            ''')
            guidance_objetivo = program_objetivo(destreza=destreza, indicador=indicador, grado=grado, edad=edad, etapas=', '.join(etapas))
            session_objectives.append(guidance_objetivo.variables()["objetivo"])

        guidance_results = []
        for i, (objetivo, etapas) in enumerate(zip(session_objectives, sesiones_etapas)):
            program_content = guidance('''
            Genera planes de estudio y preguntas de evaluación basados en el objetivo: {{objetivo}} y la destreza {{destreza}} con el indicador {{indicador}} para estudiantes de {{grado}} con edad de {{edad}} años, considerando las etapas {{etapas}}.
            Sesión {{session_number}} de {{duracion_sesiones}}:
            Actividades: 
            {{#geneach 'actividades' num_iterations=5}}
            - {{gen 'this' max_tokens=120}}{{/geneach}}
            Preguntas de Evaluación: 
            {{#geneach 'preguntas_evaluacion' num_iterations=3}}
            {{@index+1}}. {{gen 'this' max_tokens=120}}{{/geneach}}
            Dinámica:
            {{gen 'dinamica' max_tokens=200}}
            ''')
            guidance_result = program_content(objetivo=objetivo, destreza=destreza, indicador=indicador, grado=grado, edad=edad, session_number=i+1, duracion_sesiones=duracion_sesiones, etapas=', '.join(etapas))
            guidance_results.append(guidance_result.variables())

        result_dict = {"session_{}".format(i+1): guidance_results[i] for i in range(num_sesiones)}
        result_dict = filter_unserializable(result_dict)

        return jsonify({'generated_plan': result_dict}), 200

    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({'error': 'Error interno del servidor'}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)

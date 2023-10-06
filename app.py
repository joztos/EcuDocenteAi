from flask import Flask, request, jsonify, make_response
from flask_cors import CORS, cross_origin
import traceback
import guidance
import json

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})
guidance.llm = guidance.llms.OpenAI(model="text-davinci-003", api_key="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")

METODOLOGIAS = {
    'BLOOM': ['Conocimiento', 'Comprensión', 'Aplicación', 'Análisis', 'Síntesis', 'Evaluación'],
    'ERCA': ['Experiencia', 'Reflexión', 'Conceptualización', 'Aplicación']
}

def divide_etapas(metodologia, num_sesiones):
    etapas = METODOLOGIAS[metodologia]
    sesiones = []
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
        texto_libre = data.get('texto_libre', '').strip()
        metodologia = data.get('metodologia', '').strip().upper()  
        grado = data.get('grado', '').strip()
        edad = data.get('edad', '').strip()
        num_sesiones = int(data.get('num_sesiones', '').strip())
        duracion_sesiones = data.get('duracion_sesiones', '').strip()

        if not texto_libre or not metodologia or not grado or not edad or not num_sesiones or not duracion_sesiones:
            return jsonify({'error': 'Texto libre, metodologia, grado, edad, número de sesiones y duración de sesiones son requeridos y no pueden estar vacíos'}), 400

        sesiones_etapas = divide_etapas(metodologia, num_sesiones)
        session_objectives = []
        for etapas in sesiones_etapas:
            program_objetivo = guidance('''
            Eres un asistente que genera un objetivo de clase para cada sesión del plan de estudios para estudiantes de {{grado}} con edad de {{edad}} años, utilizando la metodología {{metodologia}} y basándose en el tema {{texto_libre}}. Crea un objetivo que integre estos elementos de forma natural.
            Objetivo de Clase: 
            "{{gen 'objetivo' max_tokens=200}}"
            ''')
            guidance_objetivo = program_objetivo(texto_libre=texto_libre, metodologia=metodologia, grado=grado, edad=edad)
            session_objectives.append(guidance_objetivo.variables()["objetivo"])

        guidance_results = []
        for i, (objetivo, etapas) in enumerate(zip(session_objectives, sesiones_etapas)):
            program_content = guidance('''
            Eres un asistente que genera planes de estudio y preguntas de evaluación basados en el objetivo: {{objetivo}} y el tema {{texto_libre}} para estudiantes de {{grado}} con edad de {{edad}} años, utilizando una metodología de {{metodologia}}.
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
            guidance_result = program_content(objetivo=objetivo, texto_libre=texto_libre, metodologia=metodologia, grado=grado, edad=edad, session_number=i+1, duracion_sesiones=duracion_sesiones)
            guidance_results.append(guidance_result.variables())

        result_dict = {"session_{}".format(i+1): guidance_results[i] for i in range(num_sesiones)}
        result_dict = filter_unserializable(result_dict)

        return jsonify({'generated_plan': result_dict}), 200

    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({'error': 'Error interno del servidor'}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)

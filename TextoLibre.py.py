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

@app.route('/api/generateMicroPlan', methods=["POST", "OPTIONS"])
@cross_origin()
def generateMicroPlan():
    # ... (resto del código previo hasta la validación de datos)
    
    sesiones_etapas = divide_etapas(metodologia, num_sesiones)
    guidance_results = []
    
    for i, etapas in enumerate(sesiones_etapas):
        program = guidance('''
Eres un asistente que genera planes de estudio y preguntas de evaluación para estudiantes de {{grado}} con edad de {{edad}} años, utilizando una metodología de {{metodologia}} y enfocándote en las etapas {{etapas}}.
Plan de estudio basado en el texto libre: {{texto_libre}}
Objetivo de Clase: 
"{{gen 'objetivo' max_tokens=50}}"
Sesión {{session_number}} de {{duracion_sesiones}}:
Actividades: 
{{#geneach 'actividades' num_iterations=5}}
- {{gen 'this' max_tokens=90}}{{/geneach}}
Preguntas de Evaluación: 
{{#geneach 'preguntas_evaluacion' num_iterations=3}}
{{@index+1}}. {{gen 'this' max_tokens=100}}{{/geneach}}
Dinámica:
{{gen 'dinamica' max_tokens=100}}
        ''')
        guidance_result = program(texto_libre=texto_libre, metodologia=metodologia, grado=grado, edad=edad, session_number=i+1, duracion_sesiones=duracion_sesiones, etapas=', '.join(etapas))
        guidance_results.append(guidance_result.variables())

    # Aquí estamos convirtiendo la lista de resultados en un diccionario para la respuesta JSON
    result_dict = {"session_{}".format(i+1): guidance_results[i] for i in range(num_sesiones)}
    
    return jsonify({'generated_plan': result_dict}), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)

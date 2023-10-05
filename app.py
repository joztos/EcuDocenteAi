from flask import Flask, request, jsonify, make_response
from flask_cors import CORS, cross_origin
import traceback
import guidance
import json

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

guidance.llm = guidance.llms.OpenAI(model="text-davinci-003", api_key="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")

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
        metodologia = data.get('metodologia', '').strip()
        grado = data.get('grado', '').strip()
        edad = data.get('edad', '').strip()
        num_sesiones = int(data.get('num_sesiones', '').strip())
        duracion_sesiones = data.get('duracion_sesiones', '').strip()

        if not texto_libre or not metodologia or not grado or not edad or not num_sesiones or not duracion_sesiones:
            return jsonify({'error': 'Texto libre, metodologia, grado, edad, número de sesiones y duración de sesiones son requeridos y no pueden estar vacíos'}), 400
# ... (resto del código previo)

        program = guidance('''
Eres un asistente que genera planes de estudio y preguntas de evaluación para estudiantes de {{grado}} con edad de {{edad}} años, utilizando una metodología de {{metodologia}}.
Utiliza el siguiente formato para generar el plan de estudio:

Plan de estudio basado en el texto libre: {{texto_libre}}
Objetivo de Clase: 
"{{gen 'objetivo' max_tokens=50}}"
{{#geneach 'sesiones' num_iterations=num_sesiones}}
Sesión {{@index+1}} de {{duracion_sesiones}}:
Actividades: 
{{#geneach 'actividades' num_iterations=5}}
- {{gen 'this' max_tokens=90}}{{/geneach}}
Preguntas de Evaluación: 
{{#geneach 'preguntas_evaluacion' num_iterations=3}}
{{@index+1}}. {{gen 'this' max_tokens=100}}{{/geneach}}
Dinámica:
Materiales:
{{gen 'materiales_dinamica' max_tokens=80}}
Descripción Específica:
{{gen 'descripcion_dinamica' max_tokens=100}}
{{/geneach}}
''')


        guidance_result = program(texto_libre=texto_libre, metodologia=metodologia, grado=grado, edad=edad, num_sesiones=num_sesiones, duracion_sesiones=duracion_sesiones)

        result_dict = {k: v for k, v in guidance_result.variables().items() if k != "llm"}
        
        return jsonify({'generated_plan': result_dict}), 200

    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({'error': 'Error interno del servidor'}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)

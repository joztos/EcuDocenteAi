from flask import Flask, request, jsonify, make_response
from flask_cors import CORS, cross_origin
from supabase_py import create_client
import guidance
import json

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

# Configuración de Supabase y Guidance
SUPABASE_URL = "https://nvvcwnjblwivlgqfkkbq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im52dmN3bmpibHdpdmxncWZra2JxIiwicm9sZSI6ImFub24iLCJpYXQiOjE2OTE1NDI0NjYsImV4cCI6MjAwNzExODQ2Nn0.d-aYp0rG3Ni9LhguheL228DkyG55voDZ9kq_vABrs-E"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)  # Inicializa el cliente Supabase

# Configura el modelo de lenguaje para ejecutar programas de guidance, # set the default language model that execute guidance programs

guidance.llm = guidance.llms.OpenAI(model="text-davinci-003", api_key="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")


# Carga del mapeo
with open('mapeo.json', 'r') as f:
    mapeo = json.load(f)

@app.route('/api/getskills', methods=['POST'])
def get_destrezas():
    try:
        data = request.json
        asignatura = data.get('asignatura')
        
        if not asignatura:
            return jsonify({'error': 'Asignatura no proporcionada'}), 400
        
        response = supabase.table('oficialecu').select('skill').eq('asignatura', asignatura).execute()
        
        if 'error' in response:
            return jsonify({'error': 'Error al obtener datos de Supabase'}), 500
        
        skills = [row['skill'] for row in response.get('data', [])]
        
        return jsonify({'destrezas': skills}), 200
        
    except Exception as e:
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/api/getIndicadores', methods=["POST"])
def getIndicadores():
    filters = request.get_json()
    if not filters:
        return jsonify({'message': 'Bad Request: JSON data required'}), 400
    
    try:
        destreza_id = filters["destreza_id"]
        indicadores = mapeo.get(str(destreza_id), [])
        return jsonify({'indicadores': indicadores}), 200
    except KeyError:
        return jsonify({'message': "Error: Falta uno o más detalles requeridos en los filtros."}), 400
    except Exception as err:
        return jsonify({'message': 'Error en la consulta a la base de datos'}), 500

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
        destreza = data.get('destreza', '').strip()
        indicador = data.get('indicador', '').strip()
        metodologia = data.get('metodologia', '').strip()
        temporalidad = data.get('temporalidad', '').strip()

        if not destreza or not indicador or not metodologia or not temporalidad:
            return jsonify({'error': 'Todos los campos son requeridos y no pueden estar vacíos'}), 400

        plans = []
        num_blocks = 1 if temporalidad == "dia" else 5
        for i in range(num_blocks):
            day_or_block = f"Día {i+1}" if temporalidad == "semana" else ""
            program = guidance(f'''
            Plan de Clase {day_or_block} para la destreza: {{destreza}}, el indicador: {{indicador}}, y la metodología: {metodologia}
            🚀 Objetivo de Clase: "{{gen 'objetivo' max_tokens=80}}"
            ✅ Actividades: "{{gen 'actividades' max_tokens=500}}"
            ✅ Evaluación: "{{gen 'evaluacion' max_tokens=300}}"
            🎨 Dinámica: "{{gen 'dinamica' max_tokens=400}}"
            ''')

            guidance_result = program(destreza=destreza, indicador=indicador, metodologia=metodologia, temporalidad=temporalidad)
            result_dict = {k: v for k, v in guidance_result.variables().items() if k != "llm"}
            plans.append(result_dict)

        return jsonify({'generated_plans': plans}), 200

    except Exception as e:
        return jsonify({'error': 'Error interno del servidor'}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)

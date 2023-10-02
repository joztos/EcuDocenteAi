from flask import Flask, request, jsonify, make_response
from flask_cors import CORS  # Ya no necesitas importar cross_origin aquí
import traceback
from supabase_py import create_client
import guidance
import json

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})


# Configura y verifica el resto de las variables de entorno y servicios
SUPABASE_URL = "https://nvvcwnjblwivlgqfkkbq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im52dmN3bmpibHdpdmxncWZra2JxIiwicm9sZSI6ImFub24iLCJpYXQiOjE2OTE1NDI0NjYsImV4cCI6MjAwNzExODQ2Nn0.d-aYp0rG3Ni9LhguheL228DkyG55voDZ9kq_vABrs-E"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)  # Inicializa el cliente Supabase

# Configura el modelo de lenguaje para ejecutar programas de guidance
guidance.llm = guidance.llms.OpenAI(model="gpt-3.5-turbo", api_key="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")

# Carga el mapeo al inicio
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

        if not destreza or not indicador:
            return jsonify({'error': 'Destreza e indicador son requeridos y no pueden estar vacíos'}), 400

        program = guidance('''
        # Plan de Clase para la destreza: {{destreza}} y el indicador: {{indicador}}
        ## 🚀 Objetivo de Clase: "{{gen 'objetivo' max_tokens=50}}"
        ## ✅ Actividades: "{{gen 'actividades' max_tokens=500}}"
        ## ✅ Evaluación: "{{gen 'evaluacion' max_tokens=300}}"
        ## 🎨 Dinámica: "{{gen 'dinamica' max_tokens=400}}"
        ''')

        guidance_result = program(destreza=destreza, indicador=indicador)
        return jsonify({'generated_plan': guidance_result}), 200

    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({'error': 'Error interno del servidor'}), 500



if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)


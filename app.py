from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase_py import create_client
import openai
import json

app = Flask(__name__)
CORS(app)

# Configura y verifica el resto de las variables de entorno y servicios

SUPABASE_URL="https://nvvcwnjblwivlgqfkkbq.supabase.co"
SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im52dmN3bmpibHdpdmxncWZra2JxIiwicm9sZSI6ImFub24iLCJpYXQiOjE2OTE1NDI0NjYsImV4cCI6MjAwNzExODQ2Nn0.d-aYp0rG3Ni9LhguheL228DkyG55voDZ9kq_vABrs-E"



if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase URL or Key not provided.")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)  # Inicializa el cliente Supabase

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

@app.route('/api/testSupabase', methods=['GET'])
def test_supabase():
    try:
        response = supabase.table('oficialecu').select('*').limit(1).execute()
        
        if response.error:
            return jsonify({'error': 'Error al obtener datos de Supabase', 'details': str(response.error)}), 500
        
        return jsonify({'data': response.data}), 200
    except Exception as e:
        return jsonify({'error': 'Error interno del servidor', 'details': str(e)}), 500

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

@app.route('/api/generateMicroPlan', methods=["POST"])
def generateMicroPlan():
    try:
        data = request.get_json()
        destreza = data.get("destreza")
        indicador = data.get("indicador")

        if not destreza or not indicador:
            return jsonify({'message': 'Error: destreza and indicador are required.'}), 400
        
        message = f"Create a class microplan based on the following skills: {destreza}, and indicators: {indicador}."
        
        # Hardcodear la clave API
        openai.api_key = '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'
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": message}
            ]
        )
        generatedPlan = response['choices'][0]['message']['content'].strip()
        return jsonify({'microplan': generatedPlan}), 200
    
    except openai.error.OpenAIError as e:
        return jsonify({'message': 'Error interacting with OpenAI API.'}), 500
    
    except Exception as e:
        return jsonify({'message': 'Unexpected internal server error.'}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)

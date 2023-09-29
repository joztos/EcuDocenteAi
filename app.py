from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase_py import create_client  # Importa solo create_client
import openai
import json
import os  # Importa os para acceder a las variables de entorno
from dotenv import load_dotenv  # Importa load_dotenv de python-dotenv

load_dotenv()  # Carga las variables de entorno del archivo .env



app = Flask(__name__)
CORS(app)

# Usa las variables de entorno para las claves y URLs
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Inicializa OpenAI
openai.api_key = OPENAI_API_KEY

# Crea el cliente Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)  # No necesitas especificar el tipo aquí



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
        
        print("Respuesta completa de Supabase:", response)  # Imprime la respuesta completa de Supabase
        
        if 'error' in response:  # Asegúrate de que 'error' es una clave en el diccionario
            print("Error de Supabase:", response['error'])  # Accede a 'error' como clave del diccionario
            return jsonify({'error': 'Error al obtener datos de Supabase'}), 500
        
        skills = [row['skill'] for row in response.get('data', [])]  # Usa get para acceder a 'data' en el diccionario
        
        return jsonify({'destrezas': skills}), 200
        
    except Exception as e:
        print("Error General:", e)  # Imprime el error general
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
        
        # Busca los indicadores en el mapeo
        indicadores = mapeo.get(str(destreza_id), [])
        
        return jsonify({'indicadores': indicadores}), 200
    except KeyError:
        return jsonify({'message': "Error: Falta uno o más detalles requeridos en los filtros."}), 400
    except Exception as err:
        print(err)
        return jsonify({'message': 'Error en la consulta a la base de datos'}), 500

@app.route('/api/generateMicroPlan', methods=["POST"])
def generateMicroPlan():
    data = request.get_json()
    destreza = data.get("destreza")
    indicador = data.get("indicador")
    
    if not destreza or not indicador:
        return jsonify({'message': 'Error: destreza and indicador are required.'}), 400
    
    message = f"Create a class microplan based on the following skills: {destreza}, and indicators: {indicador}."
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": message}
            ]
        )
        generatedPlan = response['choices'][0]['message']['content'].strip()
        return jsonify({'microplan': generatedPlan}), 200
    
    except Exception as e:
        print(e)
        return jsonify({'message': 'Error generating microplan.'}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)

import json
import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import openai

app = Flask(__name__)
CORS(app)

OPENAI_API_KEY = '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'

# Load the mapping at startup
with open('mapeo.json', 'r') as f:
    mapeo = json.load(f)

database_url = 'https://nvvcwnjblwivlgqfkkbq.supabase.co'
headers = {
    "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im52dmN3bmpibHdpdmxncWZra2JxIiwicm9sZSI6ImFub24iLCJpYXQiOjE2OTE1NDI0NjYsImV4cCI6MjAwNzExODQ2Nn0.d-aYp0rG3Ni9LhguheL228DkyG55voDZ9kq_vABrs-E"
}


@app.route('/api/getDestrezas', methods=["POST"])
def getDestrezas():
    filters = request.get_json()
    if not filters:
        return jsonify({'message': 'Bad Request: JSON data required'}), 400

    try:
        asignatura = filters["asignatura"]

        response = requests.get(
            f'{database_url}/DestrezasOne?select=id,"DESTREZAS CON CRITERIO DE DESEMPEÑO"&asignatura=eq.{asignatura}', 
            headers=headers
        )
        
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Content: {response.content}")

        if response.status_code != 200:
            print(f"Error response from database: {response.content}")
            return jsonify({'message': 'Error en la consulta a la base de datos'}), 500
        
        destrezas = [{"id": row['id'], "name": row['DESTREZAS CON CRITERIO DE DESEMPEÑO']} for row in response.json()]
        return jsonify({'destrezas': destrezas}), 200
    
    except KeyError:
        return jsonify({'message': "Error: Falta uno o más detalles requeridos en los filtros."}), 400
    except Exception as err:
        print(err)
        return jsonify({'message': 'Error en la consulta a la base de datos'}), 500




@app.route('/api/getIndicadores', methods=["POST"])
def getIndicadores():
    filters = request.get_json()
    if not filters:
        return jsonify({'message': 'Bad Request: JSON data required'}), 400

    try:
        destreza_id = filters["destreza_id"]

        # Look up the indicators in the mapping
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

import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import openai

app = Flask(__name__)
CORS(app)

OPENAI_API_KEY = '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'

with open('mapeo.json', 'r') as f:
    mapeo = json.load(f)

database_url = 'https://emtfsucnrfiuvcywkdqq.supabase.co/rest/v1'
headers = {
    "apikey": "YOUR_API_KEY_HERE"
}

@app.route('/api/getDestrezas', methods=["POST"])
def getDestrezas():
    filters = request.get_json()
    asignaturasub = filters.get("asignaturasub")

    response = requests.get(
        f'{database_url}/DestrezasOne?select=id,"DESTREZAS CON CRITERIO DE DESEMPEÑO"&asignaturasub=eq.{asignaturasub}', 
        headers=headers
    )

    if response.status_code != 200:
        return jsonify({'message': 'Error en la consulta a la base de datos'}), 500

    destrezas = [{"id": row['id'], "name": row['DESTREZAS CON CRITERIO DE DESEMPEÑO']} for row in response.json()]
    return jsonify({'destrezas': destrezas}), 200

@app.route('/api/getIndicadores', methods=["POST"])
def getIndicadores():
    filters = request.get_json()
    destreza_id = filters.get("destreza_id")
    indicadores = mapeo.get(str(destreza_id), [])
    return jsonify({'indicadores': indicadores}), 200

@app.route('/api/generateMicroPlan', methods=["POST"])
def generateMicroPlan():
    data = request.get_json()
    destreza = data.get("destreza")
    indicador = data.get("indicador")
    message = f"Create a class microplan based on the skill: {destreza}, and indicator: {indicador}."

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": message}
        ]
    )
    generatedPlan = response['choices'][0]['message']['content'].strip()
    return jsonify({'microplan': generatedPlan}), 200

@app.route('/api/generateFullPlan', methods=["POST"])
def generateFullPlan():
    data = request.get_json()
    destreza = data.get("destreza")
    indicador = data.get("indicador")
    temporalidad = data.get("temporalidad")
    metodologia = data.get("metodologia")

    message = f"Create a {temporalidad} class plan using the {metodologia} methodology based on the skill: {destreza}, and indicator: {indicador}."

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": message}
        ]
    )
    generatedPlan = response['choices'][0]['message']['content'].strip()
    return jsonify({'plan': generatedPlan}), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)

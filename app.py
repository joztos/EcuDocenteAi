from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

database_url = 'https://emtfsucnrfiuvcywkdqq.supabase.co/rest/v1'
headers = {
    "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVtdGZzdWNucmZpdXZjeXdrZHFxIiwicm9sZSI6ImFub24iLCJpYXQiOjE2ODY4NTAyNzYsImV4cCI6MjAwMjQyNjI3Nn0.sQxAXBaNmYtfAPPKggSwy79LNKv_gEbVodzWTm7RzhY"
}

@app.route('/api/getDestrezas', methods=["POST"])
def getDestrezas():
    filters = request.get_json()
    if not filters:
        return jsonify({'message': 'Bad Request: JSON data required'}), 400

    try:
        asignaturasub = filters["asignaturasub"]

        response = requests.get(
            f'{database_url}/DestrezasOne?select="DESTREZAS%20CON%20CRITERIO%20DE%20DESEMPE%C3%91O"&asignaturasub=eq.{asignaturasub}', 
            headers=headers
        )

        if response.status_code != 200:
            print(f"Error response from database: {response.content}")
            return jsonify({'message': 'Error en la consulta a la base de datos'}), 500

        destrezas = [row['DESTREZAS CON CRITERIO DE DESEMPEÑO'] for row in response.json()]
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
        criterio_de_evaluacioni = filters["criterio_de_evaluacioni"]

        response = requests.get(
            f'{database_url}/Indicadores?select=indicador&criterio_de_evaluacioni=eq.{criterio_de_evaluacioni}', 
            headers=headers
        )

        if response.status_code != 200:
            print(f"Error response from database: {response.content}")
            return jsonify({'message': 'Error en la consulta a la base de datos'}), 500

        indicadores = [row['indicador'] for row in response.json()]
        return jsonify({'indicadores': indicadores}), 200
    except KeyError:
        return jsonify({'message': "Error: Falta uno o más detalles requeridos en los filtros."}), 400
    except Exception as err:
        print(err)
        return jsonify({'message': 'Error en la consulta a la base de datos'}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)

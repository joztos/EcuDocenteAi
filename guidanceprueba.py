import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from guidance.llms import OpenAI
from llama_index.program import GuidancePydanticProgram
from pydantic import BaseModel
from typing import List
import json

app = Flask(__name__)
CORS(app)

OPENAI_API_KEY = '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'

with open('mapeo.json', 'r') as f:
    mapeo = json.load(f)

database_url = 'https://emtfsucnrfiuvcywkdqq.supabase.co/rest/v1'
headers = {
    "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVtdGZzdWNucmZpdXZjeXdrZHFxIiwicm9sZSI6ImFub24iLCJpYXQiOjE2ODY4NTAyNzYsImV4cCI6MjAwMjQyNjI3Nn0.sQxAXBaNmYtfAPPKggSwy79LNKv_gEbVodzWTm7RzhY"
}
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
    


class EntradaPlaneacion(BaseModel):
    destreza: str
    indicador: str
    metodologia: str
    temporalidad: int

class SalidaPlaneacion(BaseModel):
    objetivo: str
    bloques: List[str]  # Ejemplo, ajusta según sea necesario

@app.route('/api/generateFullPlan', methods=["POST"])
def generate_full_plan():
    try:
        data = request.get_json()
        entrada = EntradaPlaneacion(**data)

        prompt_template_str = (
            '{{ "objetivo": "Generar un plan de clase con destreza: {destreza}, '
            'indicador: {indicador}, metodología: {metodologia} y temporalidad: {temporalidad}", "plan": { ... } }}'
        ).format(**entrada.dict())  # Asegúrate de que el contenido del string esté formateado correctamente

        program = GuidancePydanticProgram(
            output_cls=SalidaPlaneacion,
            prompt_template_str=prompt_template_str,
            guidance_llm=OpenAI("GPT-3.5"),
            verbose=True,
        )

        salida = program()  # Generar salida basada en el modelo Pydantic
        return jsonify(salida.dict()), 200

    except Exception as e:
        app.logger.error(f"Error generating plan: {e}")
        return jsonify({'message': 'Error generating plan.', 'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
import json
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from guidance.llms import OpenAI
from llama_index.program import GuidancePydanticProgram
from pydantic import BaseModel
from typing import List

# Configuración
app = Flask(__name__)
CORS(app)

OPENAI_API_KEY = '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'

with open('mapeo.json', 'r') as f:
    mapeo = json.load(f)

database_url = 'https://emtfsucnrfiuvcywkdqq.supabase.co/rest/v1'
headers = {
    "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVtdGZzdWNucmZpdXZjeXdrZHFxIiwicm9sZSI6ImFub24iLCJpYXQiOjE2ODY4NTAyNzYsImV4cCI6MjAwMjQyNjI3Nn0.sQxAXBaNmYtfAPPKggSwy79LNKv_gEbVodzWTm7RzhY"
}

class EntradaPlaneacion(BaseModel):
    destreza: str
    indicador: str
    metodologia: str
    temporalidad: int  # Representa el número de lecciones pedagógicas a generar

class Actividad(BaseModel):
    titulo: str
    descripcion: str
    duracion: int

class Bloque(BaseModel):
    nombre: str
    actividades: List[Actividad]  # Cada bloque (lección pedagógica) contiene varias actividades

class SalidaPlaneacion(BaseModel):
    objetivo: str
    bloques: List[Bloque]  # La cantidad de bloques es controlada por el valor de 'temporalidad'
@app.route('/api/generateFullPlan', methods=["POST"])
def generate_full_plan():
    try:
        data = request.get_json()
        entrada = EntradaPlaneacion(**data)
        
        # Formatear el prompt con valores específicos del usuario
        prompt_template_str = f"""{{
    "objetivo": "Generar un plan de clase con destreza: {{entrada.destreza}}, indicador: {{entrada.indicador}}, metodología: {{entrada.metodologia}} y temporalidad: {{entrada.temporalidad}}",
    "plan": {{
        "titulo": "# 📚 Plan de Clase:",
        "objetivo_de_clase": {{
            "encabezado": "## 🚀 Objetivo de Clase:",
            "descripcion": "Proporcionar el objetivo a conseguir en relación con la destreza: '{{entrada.destreza}}' y el indicador: '{{entrada.indicador}}'."
        }},
        ...
}}
"""

                
                "actividades": {{
                    "encabezado": "## ✅ Actividades:",
                    "detalle": [{{#geneach 'actividades' num_iterations={{{entrada.temporalidad}}}}}
                        {{"minuto_a_minuto": "{{gen 'actividad'}}"}}
                    {{/geneach}}]
                }},
                "evaluacion": {{
                    "encabezado": "## ✅ Evaluación:",
                    "preguntas": [{{#geneach 'evaluacion' num_iterations=5}}
                        {{"pregunta": "{{gen 'pregunta'}}", "opciones": [{{#geneach 'opciones' num_iterations=4}}
                            "{{gen 'opcion'}}"{{/geneach}}]
                        ]}}
                    {{/geneach}}]
                }},
                "dinamica": {{
                    "encabezado": "## 🎨 Dinámica:",
                    "propuesta": "{{gen 'dinamica'}}",
                    "materiales": [{{#geneach 'materiales' num_iterations=3}}
                        "{{gen 'material'}}"{{/geneach}}
                    ]}
                }}
            }}
        }}"""
        
        program = GuidancePydanticProgram(
            output_cls=SalidaPlaneacion,
            prompt_template_str=prompt_template_str,
            guidance_llm=OpenAI("GPT-3.5"),
            verbose=True,
        )
        
        salida = program()  # Generar salida basada en el modelo Pydantic
        return jsonify(salida.dict()), 200

    except Exception as e:
        print(e)
        return jsonify({'message': 'Error generating plan.'}), 500

        
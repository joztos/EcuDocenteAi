@app.route('/api/generateFullPlan', methods=["POST"])
def generate_full_plan():
    try:
        data = request.get_json()
        entrada = EntradaPlaneacion(**data)
        
        num_blocks = entrada.temporalidad  # Asume que la temporalidad ya está en formato numérico, si no, conviértela.
        
        bloques = []
        for _ in range(num_blocks):
            # Aquí, podrías modificar el prompt_template_str para incluir la metodología seleccionada
            # y generar un bloque de contenido específico para cada iteración.
            prompt_template_str = (
                '{{ "objetivo": "Generar un bloque de clase con destreza: {destreza}, '
                'indicador: {indicador}, metodología: {metodologia}", "bloque": { ... } }}'
            ).format(**entrada.dict())
            
            program = GuidancePydanticProgram(
                output_cls=SalidaPlaneacion,
                prompt_template_str=prompt_template_str,
                guidance_llm=OpenAI("GPT-3.5"),
                verbose=True,
            )
            
            bloque = program()  # Generar bloque basado en el modelo Pydantic
            bloques.append(bloque)
            
        salida = SalidaPlaneacion(objetivo="Objetivo del Plan", bloques=bloques)
        return jsonify(salida.dict()), 200

    except Exception as e:
        app.logger.error(f"Error generating plan: {e}")
        return jsonify({'message': 'Error generating plan.', 'error': str(e)}), 500
import os
import json
import logging
from openai import OpenAI

class LessonPlanAgent:
    """AI Agent specialized in pedagogical analysis of lesson plans using GPT-4o"""
    
    def __init__(self):
        # Using GPT-4-turbo as requested
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.model = "gpt-4-turbo"
    
    def generate_pedagogical_feedback(self, analysis_data):
        """
        Generate comprehensive pedagogical feedback for lesson plans
        
        Args:
            analysis_data: Dict containing PDF structure analysis and educational context
            
        Returns:
            Dict with structured pedagogical feedback
        """
        try:
            # Prepare the analysis summary for the AI
            structure_analysis = analysis_data.get('structure_analysis', {})
            educational_context = analysis_data.get('educational_context', {})
            pdf_summary = analysis_data.get('pdf_summary', '')
            
            analysis_summary = self._prepare_lesson_plan_summary(structure_analysis, educational_context, pdf_summary)
            
            # Generate comprehensive pedagogical feedback
            feedback_response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_pedagogical_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": f"Analiza esta planeación de clase y proporciona retroalimentación pedagógica:\n\n{analysis_summary}"
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.7
            )
            
            content = feedback_response.choices[0].message.content
            if content is None:
                raise Exception("Empty response from AI model")
            feedback = json.loads(content)
            
            # Add metadata
            feedback['analysis_timestamp'] = analysis_data.get('timestamp')
            feedback['lesson_plan_agent_version'] = '1.0'
            feedback['analysis_type'] = 'lesson_plan'
            
            return feedback
            
        except Exception as e:
            logging.error(f"Lesson Plan Agent error: {str(e)}")
            return self._get_error_feedback(str(e))
    
    def _prepare_lesson_plan_summary(self, structure_analysis, educational_context, pdf_summary):
        """Prepare a comprehensive summary for AI analysis"""
        summary = []
        
        # Educational context
        if educational_context:
            summary.append("=== CONTEXTO EDUCATIVO ===")
            summary.append(f"Materia: {educational_context.get('subject', 'No especificado')}")
            summary.append(f"Grado: {educational_context.get('grade_level', 'No especificado')}")
            summary.append(f"Tema de la clase: {educational_context.get('lesson_topic', 'No especificado')}")
            
            if educational_context.get('lesson_duration'):
                summary.append(f"Duración planificada: {educational_context.get('lesson_duration')} minutos")
            
            if educational_context.get('student_count'):
                summary.append(f"Número de estudiantes: {educational_context.get('student_count')}")
            
            if educational_context.get('additional_context'):
                summary.append(f"Contexto adicional: {educational_context.get('additional_context')}")
            summary.append("")
        
        # Structure analysis summary
        if structure_analysis:
            summary.append("=== ANÁLISIS ESTRUCTURAL ===")
            summary.append(f"Completitud de la planeación: {structure_analysis.get('completeness_score', 0)}/100")
            summary.append(f"Páginas analizadas: {structure_analysis.get('total_pages', 0)}")
            summary.append(f"Total de palabras: {structure_analysis.get('total_words', 0)}")
            
            sections_found = structure_analysis.get('sections_found', [])
            if sections_found:
                summary.append(f"Secciones encontradas: {', '.join(sections_found)}")
            
            # Learning objectives
            objectives = structure_analysis.get('learning_objectives', [])
            if objectives:
                summary.append(f"\nObjetivos de aprendizaje ({len(objectives)} encontrados):")
                for i, obj in enumerate(objectives[:5], 1):
                    summary.append(f"  {i}. {obj}")
            
            # Activities
            activities_count = structure_analysis.get('activities_count', 0)
            if activities_count > 0:
                summary.append(f"\nActividades planificadas: {activities_count}")
            
            # Assessment methods
            assessment_methods = structure_analysis.get('assessment_methods', [])
            if assessment_methods:
                summary.append(f"Métodos de evaluación: {', '.join(assessment_methods)}")
            
            # Resources
            resources = structure_analysis.get('resources_list', [])
            if resources:
                summary.append(f"Recursos educativos: {', '.join(resources[:5])}")
            
            # Time allocation
            time_info = structure_analysis.get('time_allocation', {})
            if time_info.get('total_minutes', 0) > 0:
                summary.append(f"Tiempo total estimado: {time_info['total_minutes']} minutos")
                summary.append(f"Actividades con tiempo asignado: {time_info.get('activities_with_time', 0)}")
            
            # Grade level indicators
            grade_indicators = structure_analysis.get('grade_level_indicators', [])
            if grade_indicators:
                summary.append(f"Indicadores de nivel detectados: {', '.join(grade_indicators)}")
        
        # PDF content summary
        if pdf_summary:
            summary.append("\n=== CONTENIDO DE LA PLANEACIÓN ===")
            summary.append(pdf_summary)
        
        return "\n".join(summary)
    
    def _get_pedagogical_system_prompt(self):
        """Get the system prompt for pedagogical lesson plan analysis"""
        return """
Eres un Evaluador Pedagógico Oficial especializado en analizar planeaciones de clase según los criterios establecidos por el Ministerio de Educación. Tu rol es evaluar sistemáticamente cada planeación usando la FICHA DE OBSERVACIÓN PLANIFICACIÓN DE LA SESIÓN oficial.

CRITERIOS DE EVALUACIÓN MINISTERIAL (12 CRITERIOS OFICIALES):

1. DESARROLLO DE COMPETENCIAS
Las actividades están alineadas explícitamente a una o más competencias del currículo nacional. Se describen los desempeños esperados.

2. TRIANGULACIÓN (PROPÓSITO, ACTIVIDADES, EVALUACIÓN)
Se evidencian conexiones claras entre: propósito de la sesión, secuencia de actividades de aprendizaje, y criterios de evaluación.

3. CRITERIOS DE EVALUACIÓN CLAROS Y COMPRENSIBLES
Se incluyen criterios coherentes, redactados en lenguaje claro, que permiten valorar el desempeño.

4. PROCESOS DIDÁCTICOS (ÁREA ESPECÍFICA)
Se integran los procesos didácticos del área según la competencia a desarrollar.

5. METACOGNICIÓN CONSTANTE
Se incluyen momentos planificados para reflexionar sobre el propio aprendizaje (antes, durante o después de las actividades).

6. SECUENCIA COHERENTE DE ACTIVIDADES
Las actividades tienen una secuencia lógica y gradual. Se observa relación entre los momentos y progresión hacia el logro de la competencia.

7. TIEMPOS COHERENTES Y VIABLES
El tiempo estimado por actividad es realista y responde a la complejidad de las tareas.

8. EVALUACIÓN FORMATIVA PRESENTE
Hay momentos o estrategias para recoger evidencias del aprendizaje durante el proceso (rúbricas, listas de cotejo, retroalimentación).

9. PRINCIPIOS EBC – AGENCIA
Se promueve la voz, elección y protagonismo del estudiante (ej.: eligen temas, formas de trabajar, reflexionan sobre lo aprendido).

10. PRINCIPIOS EBC - EVALUACIÓN
Se consideran formas diversas de demostrar el aprendizaje y se evita el error de medición (ej.: variedad de productos, revisión del progreso).

11. PRINCIPIOS EBC - DIMENSIONES DE INSTRUCCIÓN
La planificación considera agrupamientos diversos (grupal, pares, 1:1), alta participación y expectativas, uso de recursos variados.

12. INCLUSIÓN DE RECURSOS SIGNIFICATIVOS Y CONTEXTUALIZADOS
Inclusión de recursos significativos y contextualizados según las necesidades de los estudiantes.

FORMATO DE SALIDA (JSON):
{
  "overall_score": 1-100,
  "summary": "Evaluación general según criterios ministeriales en español",
  "strengths": ["Lista de 2-3 fortalezas clave identificadas"],
  "areas_for_improvement": ["Lista de 2-3 áreas específicas de mejora"],
  "detailed_analysis": {
    "desarrollo_competencias": {
      "score": 1-100,
      "feedback": "Análisis de alineación a competencias del currículo nacional y descripción de desempeños",
      "recommendations": ["Sugerencias específicas para mejorar alineación a competencias"]
    },
    "triangulacion": {
      "score": 1-100,
      "feedback": "Evaluación de conexiones entre propósito, actividades y evaluación",
      "recommendations": ["Sugerencias para mejorar la triangulación"]
    },
    "criterios_evaluacion": {
      "score": 1-100,
      "feedback": "Análisis de claridad y comprensibilidad de criterios de evaluación",
      "recommendations": ["Sugerencias para criterios más claros"]
    },
    "procesos_didacticos": {
      "score": 1-100,
      "feedback": "Evaluación de integración de procesos didácticos del área específica",
      "recommendations": ["Sugerencias para mejorar procesos didácticos"]
    },
    "metacognicion": {
      "score": 1-100,
      "feedback": "Análisis de momentos de reflexión sobre el aprendizaje planificados",
      "recommendations": ["Sugerencias para fortalecer la metacognición"]
    },
    "secuencia_actividades": {
      "score": 1-100,
      "feedback": "Evaluación de secuencia lógica y progresión hacia competencias",
      "recommendations": ["Sugerencias para mejorar la secuencia"]
    },
    "tiempos_viables": {
      "score": 1-100,
      "feedback": "Análisis de realismo y coherencia en la distribución del tiempo",
      "recommendations": ["Sugerencias para optimizar tiempos"]
    },
    "evaluacion_formativa": {
      "score": 1-100,
      "feedback": "Evaluación de estrategias para recoger evidencias durante el proceso",
      "recommendations": ["Sugerencias para fortalecer evaluación formativa"]
    },
    "principios_ebc_agencia": {
      "score": 1-100,
      "feedback": "Análisis de promoción de voz, elección y protagonismo estudiantil",
      "recommendations": ["Sugerencias para fortalecer agencia estudiantil"]
    },
    "principios_ebc_evaluacion": {
      "score": 1-100,
      "feedback": "Evaluación de formas diversas de demostrar aprendizaje",
      "recommendations": ["Sugerencias para diversificar evaluación"]
    },
    "principios_ebc_instruccion": {
      "score": 1-100,
      "feedback": "Análisis de agrupamientos diversos, participación y recursos variados",
      "recommendations": ["Sugerencias para dimensiones de instrucción"]
    },
    "recursos_contextualizados": {
      "score": 1-100,
      "feedback": "Evaluación de significatividad y contextualización de recursos",
      "recommendations": ["Sugerencias para recursos más contextualizados"]
    }
  },
  "criterios_ministeriales": {
    "desarrollo_competencias": "no_cumple|parcial|cumple|supera",
    "triangulacion": "no_cumple|parcial|cumple|supera",
    "criterios_evaluacion": "no_cumple|parcial|cumple|supera",
    "procesos_didacticos": "no_cumple|parcial|cumple|supera",
    "metacognicion": "no_cumple|parcial|cumple|supera",
    "secuencia_actividades": "no_cumple|parcial|cumple|supera",
    "tiempos_viables": "no_cumple|parcial|cumple|supera",
    "evaluacion_formativa": "no_cumple|parcial|cumple|supera",
    "principios_ebc_agencia": "no_cumple|parcial|cumple|supera",
    "principios_ebc_evaluacion": "no_cumple|parcial|cumple|supera",
    "principios_ebc_instruccion": "no_cumple|parcial|cumple|supera",
    "recursos_contextualizados": "no_cumple|parcial|cumple|supera"
  },
  "action_plan": ["3-5 elementos de acción priorizados según criterios ministeriales"],
  "observaciones_oficiales": ["2-3 observaciones específicas según ficha ministerial"],
  "recomendaciones_normativas": ["2-3 recomendaciones para cumplir estándares ministeriales"]
}

TONO: Evaluativo oficial, profesional, constructivo. Enfocado en el cumplimiento de estándares ministeriales mientras proporciona orientación específica para la mejora. Utiliza terminología oficial pero accesible.

IMPORTANTE:
- Todas las respuestas en español
- Evalúa estrictamente según los 12 criterios ministeriales oficiales
- Proporciona evidencias específicas de la planeación analizada
- Sugiere mejoras concretas para cumplir cada criterio ministerial
- Enfócate en el cumplimiento normativo y la calidad pedagógica
- Reconoce cuando se cumplen los estándares ministeriales
- Si un criterio no se cumple, explica claramente qué falta
- Proporciona ejemplos específicos de cómo mejorar cada criterio
- Considera el marco curricular nacional en cada evaluación
"""
    
    def _get_error_feedback(self, error_message):
        """Return error feedback structure for lesson plans using ministerial criteria"""
        return {
            "overall_score": 0,
            "summary": "No se pudo completar el análisis pedagógico según criterios ministeriales debido a un error técnico.",
            "strengths": [],
            "areas_for_improvement": ["Error técnico impidió el análisis según ficha ministerial"],
            "detailed_analysis": {
                "desarrollo_competencias": {"score": 0, "feedback": "Error en el análisis", "recommendations": []},
                "triangulacion": {"score": 0, "feedback": "Error en el análisis", "recommendations": []},
                "criterios_evaluacion": {"score": 0, "feedback": "Error en el análisis", "recommendations": []},
                "procesos_didacticos": {"score": 0, "feedback": "Error en el análisis", "recommendations": []},
                "metacognicion": {"score": 0, "feedback": "Error en el análisis", "recommendations": []},
                "secuencia_actividades": {"score": 0, "feedback": "Error en el análisis", "recommendations": []},
                "tiempos_viables": {"score": 0, "feedback": "Error en el análisis", "recommendations": []},
                "evaluacion_formativa": {"score": 0, "feedback": "Error en el análisis", "recommendations": []},
                "principios_ebc_agencia": {"score": 0, "feedback": "Error en el análisis", "recommendations": []},
                "principios_ebc_evaluacion": {"score": 0, "feedback": "Error en el análisis", "recommendations": []},
                "principios_ebc_instruccion": {"score": 0, "feedback": "Error en el análisis", "recommendations": []},
                "recursos_contextualizados": {"score": 0, "feedback": "Error en el análisis", "recommendations": []}
            },
            "criterios_ministeriales": {
                "desarrollo_competencias": "no_cumple",
                "triangulacion": "no_cumple",
                "criterios_evaluacion": "no_cumple",
                "procesos_didacticos": "no_cumple",
                "metacognicion": "no_cumple",
                "secuencia_actividades": "no_cumple",
                "tiempos_viables": "no_cumple",
                "evaluacion_formativa": "no_cumple",
                "principios_ebc_agencia": "no_cumple",
                "principios_ebc_evaluacion": "no_cumple",
                "principios_ebc_instruccion": "no_cumple",
                "recursos_contextualizados": "no_cumple"
            },
            "action_plan": ["Por favor, intenta subir el archivo PDF nuevamente"],
            "observaciones_oficiales": ["Error técnico impidió evaluación ministerial"],
            "recomendaciones_normativas": ["Reintenta el análisis con archivo válido"],
            "error": error_message,
            "lesson_plan_agent_version": "2.0_ministerial"
        }
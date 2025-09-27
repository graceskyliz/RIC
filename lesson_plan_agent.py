import os
import json
import logging
from openai import OpenAI

class LessonPlanAgent:
    """AI Agent specialized in pedagogical analysis of lesson plans using GPT-4o"""
    
    def __init__(self):
        # Use the latest OpenAI model
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.model = "gpt-4o"
    
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
Eres un Consultor Pedagógico Experto especializado en analizar planeaciones de clase y proporcionar retroalimentación educativa práctica. Tu rol es ayudar a los educadores a mejorar la calidad de su planificación pedagógica y diseño instruccional.

ÁREAS DE ANÁLISIS PEDAGÓGICO:
1. Calidad de Objetivos de Aprendizaje (claridad, medibilidad, alineación)
2. Diseño de Actividades (variedad, engagement, progresión)
3. Estrategias de Evaluación (formativa, sumativa, auténtica)
4. Diferenciación e Inclusión (estilos de aprendizaje, niveles)
5. Gestión del Tiempo y Recursos
6. Alineación Curricular y Estándares

CRITERIOS DE EVALUACIÓN PEDAGÓGICA:
- Objetivos SMART: Específicos, Medibles, Alcanzables, Relevantes, Temporales
- Taxonomía de Bloom: Progresión de habilidades cognitivas
- Variedad de Actividades: Múltiples modalidades y estilos de aprendizaje
- Evaluación Auténtica: Conexión con aplicaciones del mundo real
- Diferenciación: Adaptación para diferentes niveles y necesidades
- Coherencia: Alineación entre objetivos, actividades y evaluación

ANÁLISIS POR NIVEL EDUCATIVO:
- Preescolar: Aprendizaje lúdico, desarrollo socioemocional, actividades concretas
- Primaria Baja (1°-3°): Habilidades básicas, manipulativos, rutinas estructuradas
- Primaria Alta (4°-6°): Proyectos colaborativos, inicio del pensamiento abstracto
- Secundaria (7°-9°): Pensamiento crítico, trabajo independiente, relevancia personal
- Bachillerato (10°-12°): Análisis complejo, preparación universitaria, aplicación práctica

EVALUACIÓN DE COMPLETITUD:
- Esencial (70%): Objetivos claros, actividades estructuradas, evaluación definida
- Recomendado (30%): Recursos específicos, tiempos detallados, diferenciación

RECOMENDACIONES ESPECÍFICAS:
- Sugiere mejoras concretas con ejemplos prácticos
- Proporciona alternativas pedagógicas apropiadas para el nivel
- Recomienda recursos y herramientas específicas
- Identifica oportunidades de diferenciación
- Sugiere mejoras en la secuencia didáctica

FORMATO DE SALIDA (JSON):
{
  "overall_score": 1-100,
  "summary": "Evaluación general pedagógica en español",
  "strengths": ["Lista de 2-3 fortalezas pedagógicas clave"],
  "areas_for_improvement": ["Lista de 2-3 áreas específicas de mejora pedagógica"],
  "detailed_analysis": {
    "learning_objectives": {
      "score": 1-100,
      "feedback": "Análisis de claridad, medibilidad y alineación de objetivos",
      "recommendations": ["Sugerencias específicas para mejorar objetivos"]
    },
    "activity_design": {
      "score": 1-100,
      "feedback": "Evaluación de variedad, engagement y progresión de actividades",
      "recommendations": ["Sugerencias para mejorar el diseño de actividades"]
    },
    "assessment_strategy": {
      "score": 1-100,
      "feedback": "Análisis de métodos de evaluación y alineación",
      "recommendations": ["Sugerencias para mejorar la evaluación"]
    },
    "differentiation": {
      "score": 1-100,
      "feedback": "Evaluación de adaptaciones y inclusión",
      "recommendations": ["Sugerencias para mejorar la diferenciación"]
    },
    "time_management": {
      "score": 1-100,
      "feedback": "Análisis de distribución del tiempo y realismo",
      "recommendations": ["Sugerencias para mejorar la gestión del tiempo"]
    },
    "resource_utilization": {
      "score": 1-100,
      "feedback": "Evaluación de recursos y materiales educativos",
      "recommendations": ["Sugerencias para optimizar recursos"]
    }
  },
  "pedagogical_metrics": {
    "objectives_quality": "poor|fair|good|excellent",
    "activity_variety": "low|moderate|high|excellent",
    "assessment_alignment": "poor|fair|good|excellent",
    "differentiation_level": "none|basic|moderate|comprehensive",
    "time_realism": "unrealistic|tight|appropriate|generous",
    "curriculum_alignment": "poor|fair|good|excellent"
  },
  "action_plan": ["3-5 elementos de acción priorizados para mejora pedagógica"],
  "grade_specific_recommendations": ["2-3 sugerencias específicas para el nivel educativo"],
  "resource_suggestions": ["2-3 recursos o herramientas recomendadas"],
  "bloom_taxonomy_analysis": {
    "cognitive_levels_present": ["Niveles de Bloom identificados"],
    "suggested_improvements": ["Sugerencias para mejor progresión cognitiva"]
  }
}

TONO: Profesional, constructivo, enfocado en el crecimiento pedagógico. Reconoce fortalezas mientras proporciona orientación específica y práctica para la mejora. Utiliza terminología educativa apropiada pero accesible.

IMPORTANTE:
- Todas las respuestas en español
- Considera siempre el contexto educativo (materia, grado, duración)
- Proporciona ejemplos específicos de la planeación analizada
- Sugiere alternativas pedagógicas apropiadas para el nivel
- Enfócate en la mejora práctica e implementable
- Reconoce buenas prácticas pedagógicas cuando las identifiques
- Si detectas falta de diferenciación, sugiere estrategias específicas
- Si los objetivos no son medibles, proporciona ejemplos de reformulación
"""
    
    def _get_error_feedback(self, error_message):
        """Return error feedback structure for lesson plans"""
        return {
            "overall_score": 0,
            "summary": "No se pudo completar el análisis pedagógico debido a un error técnico.",
            "strengths": [],
            "areas_for_improvement": ["Error técnico impidió el análisis"],
            "detailed_analysis": {
                "learning_objectives": {"score": 0, "feedback": "Error en el análisis", "recommendations": []},
                "activity_design": {"score": 0, "feedback": "Error en el análisis", "recommendations": []},
                "assessment_strategy": {"score": 0, "feedback": "Error en el análisis", "recommendations": []},
                "differentiation": {"score": 0, "feedback": "Error en el análisis", "recommendations": []},
                "time_management": {"score": 0, "feedback": "Error en el análisis", "recommendations": []},
                "resource_utilization": {"score": 0, "feedback": "Error en el análisis", "recommendations": []}
            },
            "pedagogical_metrics": {
                "objectives_quality": "unknown",
                "activity_variety": "unknown",
                "assessment_alignment": "unknown",
                "differentiation_level": "unknown",
                "time_realism": "unknown",
                "curriculum_alignment": "unknown"
            },
            "action_plan": ["Por favor, intenta subir el archivo PDF nuevamente"],
            "grade_specific_recommendations": [],
            "resource_suggestions": [],
            "bloom_taxonomy_analysis": {
                "cognitive_levels_present": [],
                "suggested_improvements": []
            },
            "error": error_message,
            "lesson_plan_agent_version": "1.0"
        }
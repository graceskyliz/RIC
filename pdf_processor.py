import re
import logging
from io import BytesIO
from PyPDF2 import PdfReader
from typing import Dict, List, Optional

class PDFProcessor:
    """PDF processing for lesson plan text extraction and analysis"""
    
    def __init__(self):
        # Common section headers in Spanish lesson plans
        self.section_patterns = {
            'objetivos': [
                r'objetivos?\s+(?:de\s+)?(?:aprendizaje|específicos?|generales?)',
                r'propósitos?\s+(?:de\s+la\s+)?(?:clase|lección)',
                r'metas?\s+(?:de\s+)?aprendizaje',
                r'qué\s+aprenderán',
                r'logros?\s+esperados?'
            ],
            'contenidos': [
                r'contenidos?\s+(?:temáticos?|curriculares?)?',
                r'temas?\s+(?:a\s+)?(?:desarrollar|tratar)',
                r'materias?\s+(?:de\s+estudio)?',
                r'conceptos?\s+(?:clave|principales?)'
            ],
            'actividades': [
                r'actividades?\s+(?:de\s+)?(?:aprendizaje|enseñanza)?',
                r'estrategias?\s+(?:didácticas?|metodológicas?)',
                r'desarrollo\s+(?:de\s+la\s+)?clase',
                r'secuencia\s+didáctica',
                r'metodología'
            ],
            'evaluacion': [
                r'evaluación\s+(?:de\s+)?(?:aprendizajes?)?',
                r'assessment',
                r'criterios?\s+de\s+evaluación',
                r'instrumentos?\s+de\s+evaluación',
                r'rúbricas?'
            ],
            'recursos': [
                r'recursos?\s+(?:didácticos?|educativos?)?',
                r'materiales?\s+(?:educativos?|de\s+apoyo)?',
                r'herramientas?',
                r'tecnología\s+educativa'
            ],
            'tiempo': [
                r'tiempo\s+(?:estimado|asignado)',
                r'duración\s+(?:de\s+la\s+)?(?:clase|actividad)',
                r'cronograma',
                r'distribución\s+del\s+tiempo'
            ]
        }
        
        # Common grade level indicators
        self.grade_indicators = {
            'preescolar': ['preescolar', 'jardín', 'kinder', 'inicial'],
            'primaria_baja': ['1°', '2°', '3°', 'primero', 'segundo', 'tercero', 'grado'],
            'primaria_alta': ['4°', '5°', '6°', 'cuarto', 'quinto', 'sexto'],
            'secundaria': ['7°', '8°', '9°', 'séptimo', 'octavo', 'noveno', 'secundaria'],
            'bachillerato': ['10°', '11°', '12°', 'décimo', 'once', 'doce', 'bachillerato', 'preparatoria']
        }

    def extract_text_from_pdf(self, pdf_file_path: str) -> str:
        """
        Extract text from PDF file
        
        Args:
            pdf_file_path: Path to the PDF file
            
        Returns:
            Extracted text content
        """
        try:
            logging.info(f"Starting PDF text extraction from {pdf_file_path}")
            
            with open(pdf_file_path, 'rb') as file:
                reader = PdfReader(file)
                
                text_content = []
                
                for page_num, page in enumerate(reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():
                            text_content.append(f"--- Página {page_num + 1} ---\n{page_text}")
                    except Exception as e:
                        logging.warning(f"Error extracting text from page {page_num + 1}: {str(e)}")
                        continue
                
                full_text = "\n\n".join(text_content)
                
                if not full_text.strip():
                    raise Exception("No se pudo extraer texto del PDF")
                
                logging.info(f"Successfully extracted {len(full_text)} characters from PDF")
                return full_text
                
        except Exception as e:
            logging.error(f"PDF text extraction error: {str(e)}")
            raise e

    def analyze_lesson_plan_structure(self, text: str) -> Dict:
        """
        Analyze lesson plan structure from extracted text
        
        Args:
            text: Extracted PDF text
            
        Returns:
            Dictionary with structured lesson plan analysis
        """
        try:
            logging.info("Starting lesson plan structure analysis")
            
            # Clean and normalize text
            cleaned_text = self._clean_text(text)
            
            # Extract sections
            sections = self._extract_sections(cleaned_text)
            
            # Analyze content structure
            structure_analysis = {
                'total_words': len(cleaned_text.split()),
                'total_pages': text.count('--- Página'),
                'sections_found': list(sections.keys()),
                'sections_content': sections,
                'grade_level_indicators': self._detect_grade_level(cleaned_text),
                'learning_objectives': self._extract_learning_objectives(sections.get('objetivos', '')),
                'activities_count': self._count_activities(sections.get('actividades', '')),
                'assessment_methods': self._extract_assessment_methods(sections.get('evaluacion', '')),
                'resources_list': self._extract_resources(sections.get('recursos', '')),
                'time_allocation': self._extract_time_info(sections.get('tiempo', '') + sections.get('actividades', ''))
            }
            
            # Calculate completeness score
            structure_analysis['completeness_score'] = self._calculate_completeness_score(sections)
            
            logging.info("Lesson plan structure analysis completed")
            return structure_analysis
            
        except Exception as e:
            logging.error(f"Lesson plan structure analysis error: {str(e)}")
            return self._get_basic_structure_analysis()

    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        # Remove excessive whitespace and normalize
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n+', '\n', text)
        # Remove page markers for content analysis
        text = re.sub(r'--- Página \d+ ---', '', text)
        return text.strip()

    def _extract_sections(self, text: str) -> Dict[str, str]:
        """Extract different sections from the lesson plan"""
        sections = {}
        text_lower = text.lower()
        
        for section_name, patterns in self.section_patterns.items():
            section_content = ""
            
            for pattern in patterns:
                match = re.search(pattern, text_lower)
                if match:
                    start_pos = match.start()
                    # Find the end of this section (next section or end of text)
                    end_pos = len(text)
                    
                    # Look for the next section
                    next_sections = []
                    for other_section, other_patterns in self.section_patterns.items():
                        if other_section != section_name:
                            for other_pattern in other_patterns:
                                other_match = re.search(other_pattern, text_lower[start_pos + 50:])
                                if other_match:
                                    next_sections.append(start_pos + 50 + other_match.start())
                    
                    if next_sections:
                        end_pos = min(next_sections)
                    
                    section_content = text[start_pos:end_pos].strip()
                    break
            
            if section_content:
                sections[section_name] = section_content[:1000]  # Limit to prevent excessive data
        
        return sections

    def _detect_grade_level(self, text: str) -> List[str]:
        """Detect grade level indicators in the text"""
        detected_levels = []
        text_lower = text.lower()
        
        for level, indicators in self.grade_indicators.items():
            for indicator in indicators:
                if indicator in text_lower:
                    detected_levels.append(level)
                    break
        
        return detected_levels

    def _extract_learning_objectives(self, objectives_text: str) -> List[str]:
        """Extract learning objectives from objectives section"""
        objectives = []
        
        if not objectives_text:
            return objectives
        
        # Look for numbered or bulleted objectives
        patterns = [
            r'(?:^|\n)\s*[\d\-\*•]\s*(.+?)(?=\n|$)',
            r'(?:^|\n)\s*(?:que|el estudiante|los estudiantes?)\s+(.+?)(?=\n|$)',
            r'(?:^|\n)\s*(?:identificar|reconocer|comprender|analizar|aplicar|evaluar)\s+(.+?)(?=\n|$)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, objectives_text, re.MULTILINE | re.IGNORECASE)
            objectives.extend([match.strip() for match in matches if len(match.strip()) > 10])
        
        return objectives[:5]  # Limit to top 5 objectives

    def _count_activities(self, activities_text: str) -> int:
        """Count the number of activities in the activities section"""
        if not activities_text:
            return 0
        
        # Count numbered activities, bullet points, or activity indicators
        activity_patterns = [
            r'(?:^|\n)\s*[\d\-\*•]\s*(?:actividad|ejercicio|tarea)',
            r'(?:primera|segunda|tercera|cuarta|quinta)\s+(?:actividad|fase)',
            r'(?:inicio|desarrollo|cierre)\s*:',
            r'(?:^|\n)\s*(?:paso|etapa)\s+\d+'
        ]
        
        total_count = 0
        for pattern in activity_patterns:
            matches = re.findall(pattern, activities_text, re.MULTILINE | re.IGNORECASE)
            total_count += len(matches)
        
        return max(total_count, 1) if activities_text.strip() else 0

    def _extract_assessment_methods(self, evaluation_text: str) -> List[str]:
        """Extract assessment methods from evaluation section"""
        methods = []
        
        if not evaluation_text:
            return methods
        
        assessment_keywords = [
            'observación', 'rúbrica', 'lista de cotejo', 'portafolio',
            'examen', 'prueba', 'quiz', 'proyecto', 'presentación',
            'autoevaluación', 'coevaluación', 'heteroevaluación'
        ]
        
        text_lower = evaluation_text.lower()
        for keyword in assessment_keywords:
            if keyword in text_lower:
                methods.append(keyword.title())
        
        return methods

    def _extract_resources(self, resources_text: str) -> List[str]:
        """Extract educational resources from resources section"""
        resources = []
        
        if not resources_text:
            return resources
        
        # Look for resource items
        resource_patterns = [
            r'(?:^|\n)\s*[\d\-\*•]\s*(.+?)(?=\n|$)',
            r'(?:libro|texto|material|recurso|herramienta)\s*:?\s*(.+?)(?=\n|$)'
        ]
        
        for pattern in resource_patterns:
            matches = re.findall(pattern, resources_text, re.MULTILINE | re.IGNORECASE)
            resources.extend([match.strip() for match in matches if len(match.strip()) > 3])
        
        return resources[:10]  # Limit to top 10 resources

    def _extract_time_info(self, time_text: str) -> Dict[str, int]:
        """Extract time allocation information"""
        time_info = {
            'total_minutes': 0,
            'activities_with_time': 0,
            'time_distribution': {}
        }
        
        if not time_text:
            return time_info
        
        # Look for time patterns
        time_patterns = [
            r'(\d+)\s*(?:minutos?|min\.?)',
            r'(\d+)\s*(?:horas?|hr\.?)',
            r'(\d+)\s*(?:hrs?\.?)'
        ]
        
        total_minutes = 0
        activities_with_time = 0
        
        for pattern in time_patterns:
            matches = re.findall(pattern, time_text, re.IGNORECASE)
            for match in matches:
                minutes = int(match)
                if 'hora' in pattern or 'hr' in pattern:
                    minutes *= 60
                total_minutes += minutes
                activities_with_time += 1
        
        time_info['total_minutes'] = total_minutes
        time_info['activities_with_time'] = activities_with_time
        
        return time_info

    def _calculate_completeness_score(self, sections: Dict[str, str]) -> int:
        """Calculate how complete the lesson plan is based on sections found"""
        essential_sections = ['objetivos', 'contenidos', 'actividades']
        recommended_sections = ['evaluacion', 'recursos', 'tiempo']
        
        essential_found = sum(1 for section in essential_sections if section in sections and sections[section].strip())
        recommended_found = sum(1 for section in recommended_sections if section in sections and sections[section].strip())
        
        # Essential sections worth 70%, recommended worth 30%
        essential_score = (essential_found / len(essential_sections)) * 70
        recommended_score = (recommended_found / len(recommended_sections)) * 30
        
        return int(essential_score + recommended_score)

    def _get_basic_structure_analysis(self):
        """Return basic structure analysis when detailed analysis fails"""
        return {
            'total_words': 0,
            'total_pages': 0,
            'sections_found': [],
            'sections_content': {},
            'grade_level_indicators': [],
            'learning_objectives': [],
            'activities_count': 0,
            'assessment_methods': [],
            'resources_list': [],
            'time_allocation': {'total_minutes': 0, 'activities_with_time': 0},
            'completeness_score': 0
        }

    def get_analysis_summary(self, structure_analysis: Dict) -> str:
        """Generate a summary of the PDF analysis for AI processing"""
        summary = []
        
        summary.append("=== ANÁLISIS DE PLANEACIÓN (PDF) ===")
        summary.append(f"Páginas analizadas: {structure_analysis.get('total_pages', 0)}")
        summary.append(f"Total de palabras: {structure_analysis.get('total_words', 0)}")
        summary.append(f"Puntuación de completitud: {structure_analysis.get('completeness_score', 0)}/100")
        summary.append("")
        
        sections_found = structure_analysis.get('sections_found', [])
        if sections_found:
            summary.append(f"Secciones encontradas: {', '.join(sections_found)}")
        
        objectives = structure_analysis.get('learning_objectives', [])
        if objectives:
            summary.append(f"Objetivos de aprendizaje detectados: {len(objectives)}")
            for i, obj in enumerate(objectives[:3], 1):
                summary.append(f"  {i}. {obj[:100]}...")
        
        activities_count = structure_analysis.get('activities_count', 0)
        if activities_count > 0:
            summary.append(f"Actividades planificadas: {activities_count}")
        
        assessment_methods = structure_analysis.get('assessment_methods', [])
        if assessment_methods:
            summary.append(f"Métodos de evaluación: {', '.join(assessment_methods)}")
        
        time_info = structure_analysis.get('time_allocation', {})
        if time_info.get('total_minutes', 0) > 0:
            summary.append(f"Tiempo total estimado: {time_info['total_minutes']} minutos")
        
        return "\n".join(summary)
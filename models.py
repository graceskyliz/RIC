from app import db
from datetime import datetime
import json

class ClassroomAnalysis(db.Model):
    """Unified model for both audio and PDF lesson analysis"""
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    upload_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    analysis_timestamp = db.Column(db.DateTime)
    
    # Analysis type
    analysis_type = db.Column(db.String(20), default='audio')  # 'audio' or 'pdf'
    
    # Educational context (shared)
    subject = db.Column(db.String(100))  # Materia/asignatura
    grade_level = db.Column(db.String(50))  # Grado escolar
    lesson_topic = db.Column(db.String(255))  # Tema de la clase
    additional_context = db.Column(db.Text)  # Contexto adicional
    
    # PDF-specific context
    lesson_duration = db.Column(db.Integer)  # Duration in minutes
    student_count = db.Column(db.Integer)  # Number of students
    learning_objectives = db.Column(db.Text)  # Extracted learning objectives
    
    # Audio-specific results (nullable for PDF analysis)
    transcription_text = db.Column(db.Text)
    transcription_data = db.Column(db.Text)  # JSON string for detailed transcription
    prosody_data = db.Column(db.Text)  # JSON string for prosodic metrics
    
    # PDF-specific results (nullable for audio analysis)
    pdf_text_content = db.Column(db.Text)  # Extracted PDF text
    lesson_plan_structure = db.Column(db.Text)  # JSON string for lesson structure analysis
    pedagogical_analysis = db.Column(db.Text)  # JSON string for pedagogical feedback
    
    # AI feedback (shared for both types)
    ric_feedback = db.Column(db.Text)  # JSON string for AI-generated feedback
    
    # Analysis status
    status = db.Column(db.String(50), default='uploaded')  # uploaded, processing, completed, error
    error_message = db.Column(db.Text)
    
    def get_transcription_data(self):
        """Parse transcription data from JSON"""
        if self.transcription_data:
            try:
                return json.loads(self.transcription_data)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_transcription_data(self, data):
        """Store transcription data as JSON"""
        self.transcription_data = json.dumps(data)
    
    def get_prosody_data(self):
        """Parse prosody data from JSON"""
        if self.prosody_data:
            try:
                return json.loads(self.prosody_data)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_prosody_data(self, data):
        """Store prosody data as JSON"""
        self.prosody_data = json.dumps(data)
    
    def get_ric_feedback(self):
        """Parse RIC feedback from JSON"""
        if self.ric_feedback:
            try:
                return json.loads(self.ric_feedback)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_ric_feedback(self, data):
        """Store RIC feedback as JSON"""
        self.ric_feedback = json.dumps(data)
    
    def get_lesson_plan_structure(self):
        """Parse lesson plan structure from JSON"""
        if self.lesson_plan_structure:
            try:
                return json.loads(self.lesson_plan_structure)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_lesson_plan_structure(self, data):
        """Store lesson plan structure as JSON"""
        self.lesson_plan_structure = json.dumps(data)
    
    def get_pedagogical_analysis(self):
        """Parse pedagogical analysis from JSON"""
        if self.pedagogical_analysis:
            try:
                return json.loads(self.pedagogical_analysis)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_pedagogical_analysis(self, data):
        """Store pedagogical analysis as JSON"""
        self.pedagogical_analysis = json.dumps(data)
    
    def get_educational_context(self):
        """Get educational context as dictionary"""
        context = {
            'subject': self.subject or 'General',
            'grade_level': self.grade_level or 'No especificado',
            'lesson_topic': self.lesson_topic or 'Tema general',
            'additional_context': self.additional_context or '',
            'analysis_type': self.analysis_type or 'audio'
        }
        
        # Add PDF-specific context if applicable
        if self.analysis_type == 'pdf':
            context.update({
                'lesson_duration': self.lesson_duration,
                'student_count': self.student_count,
                'learning_objectives': self.learning_objectives or ''
            })
        
        return context
    
    def is_audio_analysis(self):
        """Check if this is an audio analysis"""
        return self.analysis_type == 'audio'
    
    def is_pdf_analysis(self):
        """Check if this is a PDF analysis"""
        return self.analysis_type == 'pdf'


# Keep backward compatibility alias
AudioAnalysis = ClassroomAnalysis

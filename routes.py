import os
import logging
from datetime import datetime
from flask import render_template, request, jsonify, flash, redirect, url_for, send_file
from werkzeug.utils import secure_filename
from app import app, db
from models import ClassroomAnalysis, AudioAnalysis  # AudioAnalysis is alias for backward compatibility
from audio_processor import AudioProcessor
from ric_agent import RICAgent
from pdf_processor import PDFProcessor
from lesson_plan_agent import LessonPlanAgent
import json

AUDIO_EXTENSIONS = {'mp3', 'wav', 'm4a', 'ogg', 'flac'}
PDF_EXTENSIONS = {'pdf'}
ALLOWED_EXTENSIONS = AUDIO_EXTENSIONS | PDF_EXTENSIONS

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_audio_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in AUDIO_EXTENSIONS

def is_pdf_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in PDF_EXTENSIONS

@app.route('/')
def index():
    """Main page with analysis type selection"""
    return render_template('index.html')

@app.route('/upload-choice')
def upload_choice():
    """Page to choose between audio and PDF analysis"""
    return render_template('upload_choice.html')

@app.route('/upload-audio')
def upload_audio_page():
    """Audio upload page"""
    recent_analyses = ClassroomAnalysis.query.filter_by(analysis_type='audio').order_by(ClassroomAnalysis.upload_timestamp.desc()).limit(5).all()
    return render_template('audio_upload.html', recent_analyses=recent_analyses)

@app.route('/upload-pdf')
def upload_pdf_page():
    """PDF upload page"""
    recent_analyses = ClassroomAnalysis.query.filter_by(analysis_type='pdf').order_by(ClassroomAnalysis.upload_timestamp.desc()).limit(5).all()
    return render_template('pdf_upload.html', recent_analyses=recent_analyses)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle both audio and PDF file uploads with educational context"""
    try:
        # Check for either audio or PDF file
        file = None
        analysis_type = None
        
        if 'audio_file' in request.files and request.files['audio_file'].filename:
            file = request.files['audio_file']
            analysis_type = 'audio'
        elif 'pdf_file' in request.files and request.files['pdf_file'].filename:
            file = request.files['pdf_file']
            analysis_type = 'pdf'
        
        if not file or not analysis_type:
            flash('No file selected', 'error')
            return redirect(url_for('index'))
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('index'))
        
        if file.filename is None or not allowed_file(file.filename):
            if analysis_type == 'audio':
                flash('Invalid file format. Please upload MP3, WAV, M4A, OGG, or FLAC files.', 'error')
            else:
                flash('Invalid file format. Please upload PDF files.', 'error')
            return redirect(url_for('index'))
        
        # Save the file
        if file.filename is None:
            flash('Invalid filename', 'error')
            return redirect(url_for('index'))
        
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Get educational context from form
        subject = request.form.get('subject', '').strip()
        grade_level = request.form.get('grade_level', '').strip()
        lesson_topic = request.form.get('lesson_topic', '').strip()
        additional_context = request.form.get('additional_context', '').strip()
        
        # Create database record
        analysis = ClassroomAnalysis()
        analysis.filename = filename
        analysis.original_filename = file.filename
        analysis.analysis_type = analysis_type
        analysis.subject = subject
        analysis.grade_level = grade_level
        analysis.lesson_topic = lesson_topic
        analysis.additional_context = additional_context
        analysis.status = 'uploaded'
        
        # Add PDF-specific context if applicable
        if analysis_type == 'pdf':
            lesson_duration = request.form.get('lesson_duration', '').strip()
            student_count = request.form.get('student_count', '').strip()
            learning_objectives = request.form.get('learning_objectives', '').strip()
            
            analysis.lesson_duration = int(lesson_duration) if lesson_duration.isdigit() else None
            analysis.student_count = int(student_count) if student_count.isdigit() else None
            analysis.learning_objectives = learning_objectives
        
        db.session.add(analysis)
        db.session.commit()
        
        if analysis_type == 'audio':
            flash('Audio uploaded successfully! Speech analysis is starting...', 'success')
        else:
            flash('PDF uploaded successfully! Lesson plan analysis is starting...', 'success')
        
        return redirect(url_for('analyze', analysis_id=analysis.id))
        
    except Exception as e:
        logging.error(f"Upload error: {str(e)}")
        flash('Error uploading file. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/analyze/<int:analysis_id>')
def analyze(analysis_id):
    """Display analysis page and trigger processing for both audio and PDF"""
    analysis = ClassroomAnalysis.query.get_or_404(analysis_id)
    
    # If not yet processed, start appropriate processing
    if analysis.status == 'uploaded':
        try:
            if analysis.is_audio_analysis():
                process_audio_analysis(analysis)
            elif analysis.is_pdf_analysis():
                process_pdf_analysis(analysis)
        except Exception as e:
            logging.error(f"Analysis error: {str(e)}")
            analysis.status = 'error'
            analysis.error_message = str(e)
            db.session.commit()
    
    # Use appropriate template based on analysis type
    if analysis.is_pdf_analysis():
        return render_template('lesson_analysis.html', analysis=analysis)
    else:
        return render_template('analysis.html', analysis=analysis)

@app.route('/api/analysis/<int:analysis_id>/status')
def get_analysis_status(analysis_id):
    """Get current analysis status via API"""
    analysis = ClassroomAnalysis.query.get_or_404(analysis_id)
    return jsonify({
        'status': analysis.status,
        'error_message': analysis.error_message,
        'analysis_type': analysis.analysis_type
    })

@app.route('/api/analysis/<int:analysis_id>/results')
def get_analysis_results(analysis_id):
    """Get analysis results via API for both audio and PDF"""
    analysis = ClassroomAnalysis.query.get_or_404(analysis_id)
    
    if analysis.status != 'completed':
        return jsonify({'error': 'Analysis not completed'}), 400
    
    results = {
        'analysis_type': analysis.analysis_type,
        'feedback': analysis.get_ric_feedback()
    }
    
    if analysis.is_audio_analysis():
        results.update({
            'transcription': analysis.get_transcription_data(),
            'prosody': analysis.get_prosody_data()
        })
    elif analysis.is_pdf_analysis():
        results.update({
            'lesson_structure': analysis.get_lesson_plan_structure(),
            'pedagogical_analysis': analysis.get_pedagogical_analysis()
        })
    
    return jsonify(results)

@app.route('/history')
def history():
    """View analysis history for both audio and PDF"""
    analyses = ClassroomAnalysis.query.order_by(ClassroomAnalysis.upload_timestamp.desc()).all()
    return render_template('history.html', analyses=analyses)

@app.route('/dashboard')
def dashboard():
    """Show progress dashboard with analytics"""
    return render_template('dashboard.html')

@app.route('/api/progress')
def get_progress_data():
    """Get comprehensive progress analytics"""
    try:
        # Basic counts
        total_analyses = ClassroomAnalysis.query.count()
        audio_analyses = ClassroomAnalysis.query.filter_by(analysis_type='audio').count()
        pdf_analyses = ClassroomAnalysis.query.filter_by(analysis_type='pdf').count()
        
        # Status distribution
        completed_analyses = ClassroomAnalysis.query.filter_by(status='completed').count()
        processing_analyses = ClassroomAnalysis.query.filter_by(status='processing').count()
        error_analyses = ClassroomAnalysis.query.filter_by(status='error').count()
        uploaded_analyses = ClassroomAnalysis.query.filter_by(status='uploaded').count()
        
        # Subject distribution (top 10)
        subject_stats = db.session.query(
            ClassroomAnalysis.subject, 
            db.func.count(ClassroomAnalysis.id).label('count')
        ).filter(
            ClassroomAnalysis.subject.isnot(None)
        ).group_by(ClassroomAnalysis.subject).order_by(
            db.func.count(ClassroomAnalysis.id).desc()
        ).limit(10).all()
        
        # Grade level distribution
        grade_stats = db.session.query(
            ClassroomAnalysis.grade_level, 
            db.func.count(ClassroomAnalysis.id).label('count')
        ).filter(
            ClassroomAnalysis.grade_level.isnot(None)
        ).group_by(ClassroomAnalysis.grade_level).order_by(
            db.func.count(ClassroomAnalysis.id).desc()
        ).limit(10).all()
        
        # Recent activity (last 7 days)
        from datetime import datetime, timedelta
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_activity = db.session.query(
            db.func.date(ClassroomAnalysis.upload_timestamp).label('date'),
            db.func.count(ClassroomAnalysis.id).label('count')
        ).filter(
            ClassroomAnalysis.upload_timestamp >= week_ago
        ).group_by(
            db.func.date(ClassroomAnalysis.upload_timestamp)
        ).order_by(
            db.func.date(ClassroomAnalysis.upload_timestamp)
        ).all()
        
        # Success rate calculation
        success_rate = (completed_analyses / total_analyses * 100) if total_analyses > 0 else 0
        
        # Average processing time for completed analyses
        completed_with_times = ClassroomAnalysis.query.filter(
            ClassroomAnalysis.status == 'completed',
            ClassroomAnalysis.analysis_timestamp.isnot(None)
        ).all()
        
        processing_times = []
        for analysis in completed_with_times:
            if analysis.analysis_timestamp and analysis.upload_timestamp:
                diff = analysis.analysis_timestamp - analysis.upload_timestamp
                processing_times.append(diff.total_seconds())
        
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        # Most active time periods
        hour_stats = db.session.query(
            db.func.extract('hour', ClassroomAnalysis.upload_timestamp).label('hour'),
            db.func.count(ClassroomAnalysis.id).label('count')
        ).group_by(
            db.func.extract('hour', ClassroomAnalysis.upload_timestamp)
        ).order_by(
            db.func.count(ClassroomAnalysis.id).desc()
        ).limit(5).all()
        
        # Recent analyses with details
        recent_analyses = ClassroomAnalysis.query.order_by(
            ClassroomAnalysis.upload_timestamp.desc()
        ).limit(10).all()
        
        recent_list = []
        for analysis in recent_analyses:
            recent_list.append({
                'id': analysis.id,
                'filename': analysis.original_filename,
                'type': analysis.analysis_type,
                'subject': analysis.subject or 'General',
                'grade': analysis.grade_level or 'No especificado',
                'status': analysis.status,
                'upload_time': analysis.upload_timestamp.strftime('%Y-%m-%d %H:%M'),
                'processing_time': analysis.analysis_timestamp.strftime('%Y-%m-%d %H:%M') if analysis.analysis_timestamp else None
            })
        
        return jsonify({
            'total_stats': {
                'total_analyses': total_analyses,
                'audio_analyses': audio_analyses,
                'pdf_analyses': pdf_analyses,
                'completed_analyses': completed_analyses,
                'processing_analyses': processing_analyses,
                'error_analyses': error_analyses,
                'uploaded_analyses': uploaded_analyses,
                'success_rate': round(success_rate, 1),
                'avg_processing_time': round(avg_processing_time, 1)
            },
            'distributions': {
                'subjects': [{'name': s.subject or 'Sin especificar', 'count': s.count} for s in subject_stats],
                'grades': [{'name': g.grade_level or 'Sin especificar', 'count': g.count} for g in grade_stats],
                'status': [
                    {'name': 'Completados', 'count': completed_analyses, 'color': '#10b981'},
                    {'name': 'Procesando', 'count': processing_analyses, 'color': '#f59e0b'},
                    {'name': 'Error', 'count': error_analyses, 'color': '#ef4444'},
                    {'name': 'Pendientes', 'count': uploaded_analyses, 'color': '#6b7280'}
                ]
            },
            'activity_trends': {
                'recent_activity': [{'date': str(r.date), 'count': r.count} for r in recent_activity],
                'hourly_activity': [{'hour': int(h.hour), 'count': h.count} for h in hour_stats]
            },
            'recent_analyses': recent_list
        })
        
    except Exception as e:
        logging.error(f"Error getting progress data: {str(e)}")
        return jsonify({'error': 'Error al obtener datos de progreso'}), 500

def process_audio_analysis(analysis):
    """Process audio file and generate analysis"""
    try:
        analysis.status = 'processing'
        db.session.commit()
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], analysis.filename)
        
        # Initialize processors
        audio_processor = AudioProcessor()
        ric_agent = RICAgent()
        
        logging.info(f"Starting transcription for {analysis.filename}")
        
        # Step 1: Transcribe audio
        transcription_result = audio_processor.transcribe_audio(filepath)
        analysis.transcription_text = transcription_result['text']
        analysis.set_transcription_data(transcription_result)
        db.session.commit()
        
        logging.info(f"Starting prosodic analysis for {analysis.filename}")
        
        # Step 2: Analyze prosody
        prosody_result = audio_processor.analyze_prosody(filepath)
        analysis.set_prosody_data(prosody_result)
        db.session.commit()
        
        logging.info(f"Starting RIC feedback generation for {analysis.filename}")
        
        # Step 3: Generate RIC feedback with educational context
        educational_context = analysis.get_educational_context()
        combined_data = {
            'transcription': transcription_result,
            'prosody': prosody_result,
            'educational_context': educational_context
        }
        
        feedback = ric_agent.generate_educational_feedback(combined_data)
        analysis.set_ric_feedback(feedback)
        
        # Mark as completed
        analysis.status = 'completed'
        analysis.analysis_timestamp = datetime.utcnow()
        db.session.commit()
        
        logging.info(f"Analysis completed for {analysis.filename}")
        
    except Exception as e:
        logging.error(f"Processing error for {analysis.filename}: {str(e)}")
        analysis.status = 'error'
        analysis.error_message = str(e)
        db.session.commit()
        raise e

def process_pdf_analysis(analysis):
    """Process PDF file and generate pedagogical analysis"""
    try:
        analysis.status = 'processing'
        db.session.commit()
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], analysis.filename)
        
        # Initialize processors
        pdf_processor = PDFProcessor()
        lesson_plan_agent = LessonPlanAgent()
        
        logging.info(f"Starting PDF text extraction for {analysis.filename}")
        
        # Step 1: Extract text from PDF
        pdf_text = pdf_processor.extract_text_from_pdf(filepath)
        analysis.pdf_text_content = pdf_text[:10000]  # Store first 10K characters
        db.session.commit()
        
        logging.info(f"Starting lesson plan structure analysis for {analysis.filename}")
        
        # Step 2: Analyze lesson plan structure
        structure_analysis = pdf_processor.analyze_lesson_plan_structure(pdf_text)
        analysis.set_lesson_plan_structure(structure_analysis)
        db.session.commit()
        
        logging.info(f"Starting pedagogical feedback generation for {analysis.filename}")
        
        # Step 3: Generate pedagogical feedback with educational context
        educational_context = analysis.get_educational_context()
        pdf_summary = pdf_processor.get_analysis_summary(structure_analysis)
        
        combined_data = {
            'structure_analysis': structure_analysis,
            'educational_context': educational_context,
            'pdf_summary': pdf_summary,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        feedback = lesson_plan_agent.generate_pedagogical_feedback(combined_data)
        analysis.set_ric_feedback(feedback)
        
        # Mark as completed
        analysis.status = 'completed'
        analysis.analysis_timestamp = datetime.utcnow()
        db.session.commit()
        
        logging.info(f"PDF analysis completed for {analysis.filename}")
        
    except Exception as e:
        logging.error(f"PDF processing error for {analysis.filename}: {str(e)}")
        analysis.status = 'error'
        analysis.error_message = str(e)
        db.session.commit()
        raise e

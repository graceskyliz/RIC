import os
import json
import logging
from openai import OpenAI

class RICAgent:
    """RIC AI Agent - Educational feedback system using GPT-4 Turbo"""
    
    def __init__(self):
        # The newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # Do not change this unless explicitly requested by the user
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.model = "gpt-4o"
    
    def generate_educational_feedback(self, analysis_data):
        """
        Generate comprehensive educational feedback based on transcription and prosodic analysis
        
        Args:
            analysis_data: Dict containing transcription and prosody data
            
        Returns:
            Dict with structured educational feedback
        """
        try:
            # Prepare the analysis summary for the AI
            transcription = analysis_data.get('transcription', {})
            prosody = analysis_data.get('prosody', {})
            
            analysis_summary = self._prepare_analysis_summary(transcription, prosody)
            
            # Generate comprehensive feedback
            feedback_response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": f"Analyze this classroom teaching session and provide educational feedback:\n\n{analysis_summary}"
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
            feedback['ric_version'] = '1.0'
            
            return feedback
            
        except Exception as e:
            logging.error(f"RIC Agent error: {str(e)}")
            return self._get_error_feedback(str(e))
    
    def _prepare_analysis_summary(self, transcription, prosody):
        """Prepare a summary of the analysis data for the AI"""
        summary = []
        
        # Transcription summary
        if transcription:
            summary.append("=== TRANSCRIPTION ANALYSIS ===")
            summary.append(f"Text: {transcription.get('text', 'N/A')[:500]}...")
            summary.append(f"Speech Rate: {transcription.get('wpm', 0)} words per minute")
            summary.append(f"Total Pauses: {transcription.get('pauses', {}).get('count', 0)}")
            summary.append(f"Average Pause Duration: {transcription.get('pauses', {}).get('avg_ms', 0)}ms")
            
            fillers = transcription.get('fillers', {})
            if fillers:
                summary.append(f"Filler Words: {dict(list(fillers.items())[:5])}")
        
        # Prosodic summary
        if prosody:
            summary.append("\n=== PROSODIC ANALYSIS ===")
            summary.append(f"Average Pitch: {prosody.get('f0_mean_hz', 0):.1f} Hz")
            summary.append(f"Pitch Range: {prosody.get('f0_range_hz', 0):.1f} Hz")
            summary.append(f"Pitch Variability (Jitter): {prosody.get('jitter_local', 0):.2f}%")
            summary.append(f"Volume Stability (Shimmer): {prosody.get('shimmer_local', 0):.2f}%")
            summary.append(f"Average Volume: {prosody.get('intensity_mean_db', 0):.1f} dB")
            summary.append(f"Volume Range: {prosody.get('intensity_range_db', 0):.1f} dB")
        
        return "\n".join(summary)
    
    def _get_system_prompt(self):
        """Get the system prompt for RIC educational feedback"""
        return """
You are RIC (Reflective Instruction Coach), an expert AI educational consultant specializing in analyzing teaching delivery and providing actionable feedback to educators. Your role is to help teachers improve their classroom communication effectiveness.

ANALYSIS FOCUS AREAS:
1. Speech Delivery & Clarity
2. Engagement & Pace
3. Professional Communication
4. Classroom Management (verbal cues)

EVALUATION CRITERIA:
- Speech Rate: Optimal range 120-160 WPM for instruction
- Pause Usage: Effective use for emphasis and comprehension
- Vocal Variety: Pitch range and intonation patterns
- Clarity: Minimal filler words and clear articulation
- Volume Control: Appropriate intensity and consistency

OUTPUT FORMAT (JSON):
{
  "overall_score": 1-100,
  "summary": "Brief overall assessment",
  "strengths": ["List of 2-3 key strengths"],
  "areas_for_improvement": ["List of 2-3 specific improvement areas"],
  "detailed_analysis": {
    "speech_delivery": {
      "score": 1-100,
      "feedback": "Specific feedback on speech rate, clarity, articulation",
      "recommendations": ["Actionable suggestions"]
    },
    "engagement_pace": {
      "score": 1-100,
      "feedback": "Analysis of pacing and student engagement indicators",
      "recommendations": ["Actionable suggestions"]
    },
    "vocal_variety": {
      "score": 1-100,
      "feedback": "Assessment of pitch variation and intonation",
      "recommendations": ["Actionable suggestions"]
    },
    "professional_communication": {
      "score": 1-100,
      "feedback": "Evaluation of filler words, pauses, confidence",
      "recommendations": ["Actionable suggestions"]
    }
  },
  "key_metrics": {
    "speech_rate_assessment": "too_slow|optimal|too_fast",
    "pause_effectiveness": "poor|fair|good|excellent",
    "filler_word_frequency": "high|moderate|low",
    "vocal_confidence": "low|moderate|high"
  },
  "action_plan": ["3-5 prioritized, specific action items for improvement"]
}

TONE: Professional, supportive, constructive. Focus on growth and practical improvements. Acknowledge strengths while providing clear, actionable guidance for enhancement.
"""
    
    def _get_error_feedback(self, error_message):
        """Return error feedback structure"""
        return {
            "overall_score": 0,
            "summary": "Analysis could not be completed due to technical error.",
            "strengths": [],
            "areas_for_improvement": ["Technical issue prevented analysis"],
            "detailed_analysis": {
                "speech_delivery": {"score": 0, "feedback": "Error occurred", "recommendations": []},
                "engagement_pace": {"score": 0, "feedback": "Error occurred", "recommendations": []},
                "vocal_variety": {"score": 0, "feedback": "Error occurred", "recommendations": []},
                "professional_communication": {"score": 0, "feedback": "Error occurred", "recommendations": []}
            },
            "key_metrics": {
                "speech_rate_assessment": "unknown",
                "pause_effectiveness": "unknown",
                "filler_word_frequency": "unknown",
                "vocal_confidence": "unknown"
            },
            "action_plan": ["Please try uploading the audio file again"],
            "error": error_message,
            "ric_version": "1.0"
        }

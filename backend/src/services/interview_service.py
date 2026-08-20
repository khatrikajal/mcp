"""
Interview Service

AI-conducted interviews with:
- Dynamic question generation based on interview type
- Text-to-Speech (TTS) for AI speaking capability
- Transcript analysis and answer extraction
- Automated scoring and recommendation
- Comprehensive report generation
"""
import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import Session
from groq import Groq

from backend.src.db.models import (
    InterviewSession, InterviewQuestion, User,
    InterviewType, InterviewStatus, InterviewRecommendation
)
from backend.src.services.calendar_service import CalendarService
from backend.src.services.notetaker_service import NotetakerService

logger = logging.getLogger(__name__)


# =============================================================================
# Question Templates
# =============================================================================

TECHNICAL_QUESTIONS = {
    "coding": [
        "Can you walk me through your approach to solving a complex coding problem? Please describe your thought process.",
        "How do you ensure code quality in your projects? What practices do you follow?",
        "Describe a challenging bug you encountered and how you debugged it.",
        "How would you optimize a slow database query? Walk me through your approach.",
        "Explain how you would design a RESTful API for a user authentication system.",
    ],
    "system_design": [
        "How would you design a scalable real-time chat application?",
        "Walk me through how you would architect a URL shortening service.",
        "How would you design a system to handle millions of concurrent users?",
        "Describe how you would implement a caching strategy for a web application.",
    ],
    "technology": [
        "What's your experience with cloud platforms? Which do you prefer and why?",
        "How do you stay updated with new technologies and industry trends?",
        "Describe your experience with containerization and orchestration tools.",
        "What testing strategies do you employ in your development workflow?",
    ]
}

BEHAVIORAL_QUESTIONS = {
    "leadership": [
        "Tell me about a time when you had to lead a team through a difficult project.",
        "Describe a situation where you had to make a difficult decision with limited information.",
        "How do you handle conflicts within your team?",
    ],
    "problem_solving": [
        "Describe a time when you faced an unexpected challenge. How did you handle it?",
        "Tell me about a situation where you had to think creatively to solve a problem.",
        "Give an example of when you had to adapt quickly to a changing situation.",
    ],
    "communication": [
        "Tell me about a time when you had to explain a complex technical concept to a non-technical stakeholder.",
        "Describe a situation where effective communication was critical to the project's success.",
        "How do you handle disagreements with colleagues?",
    ],
    "teamwork": [
        "Describe your experience working in cross-functional teams.",
        "Tell me about a time when you helped a teammate who was struggling.",
        "How do you contribute to a positive team culture?",
    ]
}

HR_QUESTIONS = {
    "culture_fit": [
        "What type of work environment do you thrive in?",
        "How do you handle feedback and criticism?",
        "What motivates you in your work?",
        "Describe your ideal work-life balance.",
    ],
    "career_goals": [
        "Where do you see yourself in five years?",
        "What are your career aspirations?",
        "Why are you interested in this position?",
        "What would you like to achieve in your first 90 days?",
    ],
    "practical": [
        "What is your expected salary range?",
        "What is your availability to start?",
        "Are you open to occasional travel or overtime if needed?",
        "Do you have any questions for us about the company or role?",
    ]
}


@dataclass
class TTSConfig:
    """Text-to-Speech configuration"""
    provider: str = "gtts"  # gtts, elevenlabs, azure
    voice_id: str = "en-US-Standard-C"
    speaking_rate: float = 1.0
    pitch: float = 0.0


class InterviewService:
    """
    Comprehensive AI Interview Service

    Features:
    - Generate tailored interview questions
    - Text-to-Speech for AI voice
    - Conduct interviews via meeting integration
    - Analyze transcripts and extract answers
    - Score candidates automatically
    - Generate detailed reports
    """

    def __init__(self, db: Session):
        self.db = db
        self.llm = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")
        self.calendar_service = CalendarService()
        self.notetaker_service = NotetakerService()

    # =========================================================================
    # Question Generation
    # =========================================================================

    def generate_questions(
        self,
        interview_id: int,
        interview_type: InterviewType,
        position_title: str,
        required_skills: List[str],
        num_questions: int = 8
    ) -> List[InterviewQuestion]:
        """
        Generate interview questions based on type and position.

        Uses LLM to create personalized questions based on:
        - Interview type (technical, behavioral, HR)
        - Position requirements
        - Required skills
        """
        interview = self.db.query(InterviewSession).filter(
            InterviewSession.id == interview_id
        ).first()

        if not interview:
            raise ValueError(f"Interview {interview_id} not found")

        # Update status
        interview.status = InterviewStatus.PREPARING
        self.db.commit()

        questions = []

        try:
            if interview_type == InterviewType.TECHNICAL:
                questions = self._generate_technical_questions(
                    position_title, required_skills, num_questions
                )
            elif interview_type == InterviewType.BEHAVIORAL:
                questions = self._generate_behavioral_questions(
                    position_title, num_questions
                )
            elif interview_type == InterviewType.HR:
                questions = self._generate_hr_questions(
                    position_title, num_questions
                )
            else:  # MIXED
                # Distribute questions across types
                tech_count = num_questions // 3
                behavioral_count = num_questions // 3
                hr_count = num_questions - tech_count - behavioral_count

                questions.extend(self._generate_technical_questions(
                    position_title, required_skills, tech_count
                ))
                questions.extend(self._generate_behavioral_questions(
                    position_title, behavioral_count
                ))
                questions.extend(self._generate_hr_questions(
                    position_title, hr_count
                ))

            # Save questions to database
            db_questions = []
            for i, q in enumerate(questions, 1):
                db_question = InterviewQuestion(
                    interview_id=interview_id,
                    question_number=i,
                    question_text=q["text"],
                    question_type=InterviewType(q["type"]),
                    competency=q.get("competency", "general"),
                    difficulty=q.get("difficulty", "medium"),
                    weight=q.get("weight", 10),
                    expected_keywords=q.get("keywords", []),
                    ideal_answer_points=q.get("ideal_points", [])
                )
                self.db.add(db_question)
                db_questions.append(db_question)

            interview.status = InterviewStatus.READY
            self.db.commit()

            logger.info(f"Generated {len(db_questions)} questions for interview {interview_id}")
            return db_questions

        except Exception as e:
            logger.error(f"Error generating questions: {e}")
            interview.status = InterviewStatus.FAILED
            interview.error_message = str(e)
            self.db.commit()
            raise

    def _generate_technical_questions(
        self,
        position_title: str,
        required_skills: List[str],
        count: int
    ) -> List[Dict]:
        """Generate technical interview questions using LLM."""
        prompt = f"""Generate {count} technical interview questions for a {position_title} position.

Required skills: {', '.join(required_skills)}

Generate questions that test:
1. Coding ability and problem-solving
2. System design knowledge
3. Technical depth in required technologies

For each question, provide:
- The question text
- Key competency being tested
- Difficulty level (easy/medium/hard)
- Keywords to look for in a good answer
- Key points an ideal answer should include

Return as JSON array with format:
[
  {{
    "text": "question text",
    "type": "technical",
    "competency": "competency name",
    "difficulty": "medium",
    "keywords": ["keyword1", "keyword2"],
    "ideal_points": ["point1", "point2"],
    "weight": 10
  }}
]
"""
        return self._call_llm_for_questions(prompt, count, "technical")

    def _generate_behavioral_questions(
        self,
        position_title: str,
        count: int
    ) -> List[Dict]:
        """Generate behavioral interview questions using LLM."""
        prompt = f"""Generate {count} behavioral interview questions for a {position_title} position.

Use the STAR method (Situation, Task, Action, Result) format where appropriate.

Generate questions that assess:
1. Leadership and teamwork
2. Problem-solving under pressure
3. Communication skills
4. Adaptability and learning

For each question, provide:
- The question text
- Key competency being tested
- Keywords to look for in a good answer
- Key points an ideal answer should include

Return as JSON array with format:
[
  {{
    "text": "question text",
    "type": "behavioral",
    "competency": "competency name",
    "difficulty": "medium",
    "keywords": ["keyword1", "keyword2"],
    "ideal_points": ["point1", "point2"],
    "weight": 10
  }}
]
"""
        return self._call_llm_for_questions(prompt, count, "behavioral")

    def _generate_hr_questions(
        self,
        position_title: str,
        count: int
    ) -> List[Dict]:
        """Generate HR interview questions using LLM."""
        prompt = f"""Generate {count} HR interview questions for a {position_title} position.

Generate questions that assess:
1. Culture fit and values alignment
2. Career goals and motivation
3. Practical matters (availability, expectations)

For each question, provide:
- The question text
- Key area being assessed
- Keywords to look for in a good answer
- Key points an ideal answer should include

Return as JSON array with format:
[
  {{
    "text": "question text",
    "type": "hr",
    "competency": "competency name",
    "difficulty": "easy",
    "keywords": ["keyword1", "keyword2"],
    "ideal_points": ["point1", "point2"],
    "weight": 8
  }}
]
"""
        return self._call_llm_for_questions(prompt, count, "hr")

    def _call_llm_for_questions(
        self,
        prompt: str,
        count: int,
        default_type: str
    ) -> List[Dict]:
        """Call LLM to generate questions."""
        try:
            response = self.llm.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert interviewer. Generate professional interview questions. Always respond with valid JSON only."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )

            content = response.choices[0].message.content

            # Extract JSON from response
            try:
                # Try to find JSON array in response
                start = content.find('[')
                end = content.rfind(']') + 1
                if start >= 0 and end > start:
                    json_str = content[start:end]
                    questions = json.loads(json_str)
                    return questions[:count]
            except json.JSONDecodeError:
                pass

            # Fallback to template questions
            logger.warning("LLM response not valid JSON, using templates")
            return self._get_template_questions(default_type, count)

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return self._get_template_questions(default_type, count)

    def _get_template_questions(self, q_type: str, count: int) -> List[Dict]:
        """Get template questions as fallback."""
        templates = {
            "technical": TECHNICAL_QUESTIONS,
            "behavioral": BEHAVIORAL_QUESTIONS,
            "hr": HR_QUESTIONS
        }

        all_questions = []
        template_dict = templates.get(q_type, BEHAVIORAL_QUESTIONS)

        for category, questions in template_dict.items():
            for q in questions:
                all_questions.append({
                    "text": q,
                    "type": q_type,
                    "competency": category,
                    "difficulty": "medium",
                    "keywords": [],
                    "ideal_points": [],
                    "weight": 10
                })

        return all_questions[:count]

    # =========================================================================
    # Text-to-Speech (TTS) - AI Speaking Capability
    # =========================================================================

    async def generate_speech(
        self,
        text: str,
        voice_id: str = "en",
        speaking_rate: float = 1.0
    ) -> Tuple[bytes, int]:
        """
        Generate speech audio from text using TTS.

        Returns:
            Tuple of (audio_bytes, duration_seconds)
        """
        try:
            # Try ElevenLabs first if API key available
            elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")
            if elevenlabs_key:
                return await self._generate_speech_elevenlabs(text, voice_id)

            # Fallback to gTTS (Google Text-to-Speech)
            return await self._generate_speech_gtts(text, speaking_rate)

        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            raise

    async def _generate_speech_elevenlabs(
        self,
        text: str,
        voice_id: str
    ) -> Tuple[bytes, int]:
        """Generate speech using ElevenLabs API."""
        import httpx

        api_key = os.getenv("ELEVENLABS_API_KEY")
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key
        }

        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data, headers=headers)
            response.raise_for_status()
            audio_bytes = response.content

            # Estimate duration (rough: ~150 words per minute for speech)
            word_count = len(text.split())
            duration = int((word_count / 150) * 60)

            return audio_bytes, duration

    async def _generate_speech_gtts(
        self,
        text: str,
        speaking_rate: float
    ) -> Tuple[bytes, int]:
        """Generate speech using Google TTS (gTTS)."""
        from gtts import gTTS
        import io

        # Run in thread pool since gTTS is blocking
        loop = asyncio.get_event_loop()

        def generate():
            tts = gTTS(text=text, lang='en', slow=False)
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            return audio_buffer.read()

        audio_bytes = await loop.run_in_executor(None, generate)

        # Estimate duration
        word_count = len(text.split())
        duration = int((word_count / 150) * 60)

        return audio_bytes, duration

    async def generate_question_audio(
        self,
        question_id: int
    ) -> str:
        """
        Generate TTS audio for an interview question.

        Returns the audio file URL/path.
        """
        question = self.db.query(InterviewQuestion).filter(
            InterviewQuestion.id == question_id
        ).first()

        if not question:
            raise ValueError(f"Question {question_id} not found")

        # Generate introduction for first question
        if question.question_number == 1:
            intro = f"Hello! I'm your AI interviewer today. Let's begin with the first question. "
            text = intro + question.question_text
        else:
            text = f"Question {question.question_number}. {question.question_text}"

        audio_bytes, duration = await self.generate_speech(text)

        # Save audio file
        audio_dir = os.path.join(os.getcwd(), "audio_cache")
        os.makedirs(audio_dir, exist_ok=True)

        filename = f"question_{question.interview_id}_{question.question_number}.mp3"
        filepath = os.path.join(audio_dir, filename)

        with open(filepath, 'wb') as f:
            f.write(audio_bytes)

        # Update question record
        question.audio_generated = True
        question.audio_url = filepath
        question.audio_duration_seconds = duration
        self.db.commit()

        logger.info(f"Generated audio for question {question_id}: {duration}s")
        return filepath

    async def generate_all_question_audio(self, interview_id: int) -> List[str]:
        """Generate TTS audio for all questions in an interview."""
        questions = self.db.query(InterviewQuestion).filter(
            InterviewQuestion.interview_id == interview_id
        ).order_by(InterviewQuestion.question_number).all()

        audio_files = []
        for question in questions:
            filepath = await self.generate_question_audio(question.id)
            audio_files.append(filepath)

        return audio_files

    # =========================================================================
    # Interview Conducting
    # =========================================================================

    async def start_interview(self, interview_id: int) -> Dict[str, Any]:
        """
        Start an interview session.

        This will:
        1. Join the meeting via Notetaker
        2. Begin recording
        3. Generate intro speech
        """
        interview = self.db.query(InterviewSession).filter(
            InterviewSession.id == interview_id
        ).first()

        if not interview:
            raise ValueError(f"Interview {interview_id} not found")

        if interview.status not in [InterviewStatus.READY, InterviewStatus.SCHEDULED]:
            raise ValueError(f"Interview cannot be started in status: {interview.status}")

        try:
            interview.status = InterviewStatus.IN_PROGRESS
            interview.started_at = datetime.utcnow()
            self.db.commit()

            # Join meeting with notetaker if meeting URL exists
            if interview.meeting_url:
                notetaker_result = await self.notetaker_service.join_meeting(
                    interview.meeting_url,
                    participant_name="AI Interviewer"
                )
                interview.notetaker_id = notetaker_result.get("id")
                interview.notetaker_joined_at = datetime.utcnow()
                self.db.commit()

            # Generate intro audio
            intro_text = f"""
            Hello {interview.candidate_name}! Welcome to your interview for the {interview.position_title} position.
            I'm your AI interviewer today. This interview will last approximately {interview.duration_minutes} minutes.
            I'll be asking you {len(interview.questions)} questions. Please take your time to think through your answers.
            Let's begin!
            """

            intro_audio, duration = await self.generate_speech(intro_text.strip())

            # Generate audio for all questions
            question_audio_files = await self.generate_all_question_audio(interview_id)

            return {
                "status": "started",
                "interview_id": interview_id,
                "notetaker_id": interview.notetaker_id,
                "intro_audio_duration": duration,
                "question_audio_files": question_audio_files,
                "total_questions": len(interview.questions)
            }

        except Exception as e:
            logger.error(f"Failed to start interview {interview_id}: {e}")
            interview.status = InterviewStatus.FAILED
            interview.error_message = str(e)
            self.db.commit()
            raise

    async def end_interview(self, interview_id: int) -> Dict[str, Any]:
        """
        End an interview session and begin analysis.
        """
        interview = self.db.query(InterviewSession).filter(
            InterviewSession.id == interview_id
        ).first()

        if not interview:
            raise ValueError(f"Interview {interview_id} not found")

        try:
            interview.status = InterviewStatus.ANALYZING
            self.db.commit()

            # Stop notetaker and get transcript
            if interview.notetaker_id:
                transcript_data = await self.notetaker_service.get_transcript(
                    interview.notetaker_id
                )
                interview.transcript = transcript_data.get("transcript", "")
                interview.transcript_url = transcript_data.get("url")
                interview.recording_url = transcript_data.get("recording_url")
                interview.notetaker_left_at = datetime.utcnow()
                self.db.commit()

            # Analyze the interview
            analysis_result = await self.analyze_interview(interview_id)

            interview.status = InterviewStatus.COMPLETED
            interview.completed_at = datetime.utcnow()
            self.db.commit()

            return analysis_result

        except Exception as e:
            logger.error(f"Failed to end interview {interview_id}: {e}")
            interview.status = InterviewStatus.FAILED
            interview.error_message = str(e)
            self.db.commit()
            raise

    # =========================================================================
    # Transcript Analysis & Scoring
    # =========================================================================

    async def analyze_interview(self, interview_id: int) -> Dict[str, Any]:
        """
        Analyze interview transcript and score the candidate.

        This will:
        1. Extract answers for each question
        2. Score each answer
        3. Calculate overall score
        4. Generate recommendation
        5. Create detailed report
        """
        interview = self.db.query(InterviewSession).filter(
            InterviewSession.id == interview_id
        ).first()

        if not interview:
            raise ValueError(f"Interview {interview_id} not found")

        questions = self.db.query(InterviewQuestion).filter(
            InterviewQuestion.interview_id == interview_id
        ).order_by(InterviewQuestion.question_number).all()

        if not interview.transcript:
            logger.warning(f"No transcript available for interview {interview_id}")
            # Use mock transcript for testing
            interview.transcript = self._generate_mock_transcript(questions)
            self.db.commit()

        # Extract and score each answer
        total_score = 0
        total_weight = 0
        competency_scores = {}

        for question in questions:
            answer_data = await self._extract_and_score_answer(
                question,
                interview.transcript,
                interview.candidate_name
            )

            question.candidate_answer = answer_data["answer"]
            question.score = answer_data["score"]
            question.score_reasoning = answer_data["reasoning"]
            question.feedback = answer_data["feedback"]

            # Accumulate scores
            weighted_score = question.score * question.weight
            total_score += weighted_score
            total_weight += question.weight

            # Track competency scores
            competency = question.competency
            if competency not in competency_scores:
                competency_scores[competency] = {"total": 0, "count": 0}
            competency_scores[competency]["total"] += question.score
            competency_scores[competency]["count"] += 1

        # Calculate overall score (0-100)
        overall_score = int((total_score / total_weight) * 10) if total_weight > 0 else 0

        # Calculate competency averages
        competency_averages = {
            comp: round(data["total"] / data["count"], 1)
            for comp, data in competency_scores.items()
        }

        # Determine recommendation
        recommendation = self._calculate_recommendation(overall_score)

        # Extract strengths and weaknesses
        strengths, weaknesses = await self._identify_strengths_weaknesses(
            questions, interview.candidate_name
        )

        # Update interview record
        interview.overall_score = overall_score
        interview.recommendation = recommendation
        interview.strengths = strengths
        interview.weaknesses = weaknesses
        interview.competency_scores = competency_averages

        self.db.commit()

        # Generate report
        report = await self.generate_report(interview_id)

        return {
            "overall_score": overall_score,
            "recommendation": recommendation.value,
            "competency_scores": competency_averages,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "report_summary": interview.report_summary
        }

    async def _extract_and_score_answer(
        self,
        question: InterviewQuestion,
        transcript: str,
        candidate_name: str
    ) -> Dict[str, Any]:
        """Extract candidate's answer from transcript and score it."""
        prompt = f"""Analyze this interview transcript and extract the candidate's answer to the following question.

Question #{question.question_number}: {question.question_text}

Full Transcript:
{transcript}

Candidate Name: {candidate_name}

Instructions:
1. Find the candidate's response to this specific question
2. Score the answer from 0-10 based on:
   - Completeness and depth
   - Relevance to the question
   - Use of specific examples (for behavioral questions)
   - Technical accuracy (for technical questions)
   - Communication clarity

Expected keywords: {json.dumps(question.expected_keywords)}
Ideal answer points: {json.dumps(question.ideal_answer_points)}

Return a JSON object:
{{
  "answer": "The candidate's extracted answer",
  "score": 7,
  "reasoning": "Brief explanation of the score",
  "feedback": "Detailed constructive feedback"
}}
"""
        try:
            response = self.llm.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert interview evaluator. Extract and score interview answers objectively."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )

            content = response.choices[0].message.content

            # Parse JSON response
            try:
                start = content.find('{')
                end = content.rfind('}') + 1
                if start >= 0 and end > start:
                    return json.loads(content[start:end])
            except json.JSONDecodeError:
                pass

            # Fallback
            return {
                "answer": "Unable to extract answer",
                "score": 5,
                "reasoning": "Unable to analyze response",
                "feedback": "Please review manually"
            }

        except Exception as e:
            logger.error(f"Error scoring answer: {e}")
            return {
                "answer": "Error extracting answer",
                "score": 5,
                "reasoning": str(e),
                "feedback": "Error during analysis"
            }

    def _calculate_recommendation(self, score: int) -> InterviewRecommendation:
        """Calculate hiring recommendation based on score."""
        if score >= 85:
            return InterviewRecommendation.STRONG_HIRE
        elif score >= 70:
            return InterviewRecommendation.HIRE
        elif score >= 55:
            return InterviewRecommendation.MAYBE
        elif score >= 40:
            return InterviewRecommendation.NO_HIRE
        else:
            return InterviewRecommendation.STRONG_NO_HIRE

    async def _identify_strengths_weaknesses(
        self,
        questions: List[InterviewQuestion],
        candidate_name: str
    ) -> Tuple[List[str], List[str]]:
        """Identify candidate's strengths and areas for improvement."""
        # Find high and low scoring questions
        sorted_questions = sorted(questions, key=lambda q: q.score or 0, reverse=True)

        top_questions = sorted_questions[:3]
        bottom_questions = sorted_questions[-3:]

        strengths = []
        for q in top_questions:
            if q.score and q.score >= 7:
                strengths.append(f"{q.competency.replace('_', ' ').title()}: {q.feedback[:100]}...")

        weaknesses = []
        for q in bottom_questions:
            if q.score and q.score < 7:
                weaknesses.append(f"{q.competency.replace('_', ' ').title()}: Needs improvement in {q.competency}")

        return strengths[:5], weaknesses[:5]

    def _generate_mock_transcript(self, questions: List[InterviewQuestion]) -> str:
        """Generate a mock transcript for testing."""
        transcript_parts = []
        for q in questions:
            transcript_parts.append(f"Interviewer: {q.question_text}")
            transcript_parts.append(f"Candidate: Thank you for that question. Based on my experience...")
            transcript_parts.append("")
        return "\n".join(transcript_parts)

    # =========================================================================
    # Report Generation
    # =========================================================================

    async def generate_report(self, interview_id: int) -> str:
        """Generate comprehensive interview report."""
        interview = self.db.query(InterviewSession).filter(
            InterviewSession.id == interview_id
        ).first()

        if not interview:
            raise ValueError(f"Interview {interview_id} not found")

        questions = self.db.query(InterviewQuestion).filter(
            InterviewQuestion.interview_id == interview_id
        ).order_by(InterviewQuestion.question_number).all()

        # Build question details for report
        question_details = []
        for q in questions:
            question_details.append({
                "number": q.question_number,
                "question": q.question_text,
                "type": q.question_type.value,
                "answer": q.candidate_answer,
                "score": q.score,
                "feedback": q.feedback
            })

        prompt = f"""Generate a comprehensive interview evaluation report.

Candidate: {interview.candidate_name}
Position: {interview.position_title}
Interview Type: {interview.interview_type.value}
Date: {interview.scheduled_time.strftime('%Y-%m-%d %H:%M')}

Overall Score: {interview.overall_score}/100
Recommendation: {interview.recommendation.value if interview.recommendation else 'Pending'}

Competency Scores: {json.dumps(interview.competency_scores)}

Strengths:
{chr(10).join('- ' + s for s in (interview.strengths or []))}

Areas for Improvement:
{chr(10).join('- ' + w for w in (interview.weaknesses or []))}

Question Details:
{json.dumps(question_details, indent=2)}

Generate a professional report with:
1. Executive Summary (2-3 sentences)
2. Detailed Analysis of each competency area
3. Specific examples from responses
4. Final recommendation with justification
5. Suggested next steps

Format as Markdown.
"""
        try:
            response = self.llm.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert HR professional generating interview evaluation reports."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=2000
            )

            report = response.choices[0].message.content

            # Extract summary (first paragraph)
            lines = report.split('\n')
            summary_lines = []
            for line in lines:
                if line.strip() and not line.startswith('#'):
                    summary_lines.append(line.strip())
                    if len(summary_lines) >= 2:
                        break

            interview.report = report
            interview.report_summary = ' '.join(summary_lines)
            self.db.commit()

            return report

        except Exception as e:
            logger.error(f"Error generating report: {e}")
            interview.report = f"Error generating report: {e}"
            interview.report_summary = "Report generation failed"
            self.db.commit()
            raise

    # =========================================================================
    # CRUD Operations
    # =========================================================================

    def create_interview(
        self,
        user_id: int,
        organization_id: int,
        candidate_name: str,
        candidate_email: str,
        position_title: str,
        scheduled_time: datetime,
        interview_type: InterviewType = InterviewType.MIXED,
        duration_minutes: int = 45,
        required_skills: List[str] = None,
        position_description: str = None,
        meeting_url: str = None
    ) -> InterviewSession:
        """Create a new interview session."""
        interview = InterviewSession(
            user_id=user_id,
            organization_id=organization_id,
            candidate_name=candidate_name,
            candidate_email=candidate_email,
            position_title=position_title,
            position_description=position_description,
            required_skills=required_skills or [],
            interview_type=interview_type,
            duration_minutes=duration_minutes,
            scheduled_time=scheduled_time,
            meeting_url=meeting_url,
            status=InterviewStatus.SCHEDULED
        )

        self.db.add(interview)
        self.db.commit()
        self.db.refresh(interview)

        logger.info(f"Created interview {interview.id} for {candidate_name}")
        return interview

    def get_interview(self, interview_id: int) -> Optional[InterviewSession]:
        """Get interview by ID."""
        return self.db.query(InterviewSession).filter(
            InterviewSession.id == interview_id
        ).first()

    def list_interviews(
        self,
        user_id: int = None,
        organization_id: int = None,
        status: InterviewStatus = None,
        limit: int = 50
    ) -> List[InterviewSession]:
        """List interviews with optional filters."""
        query = self.db.query(InterviewSession)

        if user_id:
            query = query.filter(InterviewSession.user_id == user_id)
        if organization_id:
            query = query.filter(InterviewSession.organization_id == organization_id)
        if status:
            query = query.filter(InterviewSession.status == status)

        return query.order_by(InterviewSession.scheduled_time.desc()).limit(limit).all()

    def cancel_interview(self, interview_id: int) -> bool:
        """Cancel an interview."""
        interview = self.get_interview(interview_id)
        if not interview:
            return False

        if interview.status in [InterviewStatus.COMPLETED, InterviewStatus.IN_PROGRESS]:
            raise ValueError("Cannot cancel completed or in-progress interviews")

        interview.status = InterviewStatus.CANCELLED
        self.db.commit()

        logger.info(f"Cancelled interview {interview_id}")
        return True

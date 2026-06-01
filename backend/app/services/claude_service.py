import os
from groq import Groq
import json
import re
from typing import List, Dict
from app.core.config import get_settings

settings = get_settings()

# Initialize the Groq client for free inference
client = Groq(api_key=settings.GROQ_API_KEY)

# Using Llama 3 70B - highly capable, fast, and free on Groq
GROQ_MODEL = "llama-3.3-70b-versatile"

# ─── Q&A ──────────────────────────────────────────────────────────────────────

def answer_question(question: str, context_chunks: List[Dict]) -> str:
    """
    Use Groq to answer a student question given retrieved context chunks.
    """
    context_text = "\n\n---\n\n".join(
        f"[Chunk {c['chunk_index']+1}]\n{c['text']}" for c in context_chunks
    )

    prompt = f"""You are a helpful study assistant for students. Answer the student's question using ONLY the provided context from their lecture notes.

If the answer is not in the context, say: "I couldn't find this in your notes. Try asking your professor."

Be clear, concise, and student-friendly. Use bullet points or numbered lists when helpful.

Context from lecture notes:
{context_text}

Student's Question: {question}

Answer:"""

    # Swapped to Groq API call format
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model=GROQ_MODEL,
        max_tokens=1024,
    )
    return chat_completion.choices[0].message.content


# ─── Quiz Generation ──────────────────────────────────────────────────────────

QUIZ_SYSTEM_PROMPT = """You are an expert quiz generator for university students.
Generate multiple choice questions (MCQs) from provided lecture notes.
Each question must have exactly 4 options (A, B, C, D) with one correct answer.
Return ONLY valid JSON — no explanation, no markdown, no preamble.
"""

QUIZ_PROMPT_TEMPLATE = """Generate {num_questions} MCQ questions from the following lecture notes.

Rules:
- Questions must test understanding, not just memory
- Include the topic/concept each question tests
- Options should be plausible but clearly one correct answer
- Difficulty: mix of easy (30%), medium (50%), hard (20%)

Return this exact JSON structure:
{{
  "title": "Quiz title based on content",
  "questions": [
    {{
      "question": "Question text here?",
      "options": {{
        "A": "Option A text",
        "B": "Option B text",
        "C": "Option C text",
        "D": "Option D text"
      }},
      "correct_answer": "A",
      "explanation": "Why this is correct",
      "topic": "Topic this question covers"
    }}
  ]
}}

Lecture Notes:
{context}
"""


def generate_quiz(chunks: List[Dict], num_questions: int = 10) -> Dict:
    """
    Generate MCQ quiz from document chunks using Groq.
    """
    combined_text = "\n\n".join(c["text"] for c in chunks[:20])
    if len(combined_text) > 6000:
        combined_text = combined_text[:6000]

    prompt = QUIZ_PROMPT_TEMPLATE.format(
        num_questions=num_questions,
        context=combined_text,
    )

    # Swapped to Groq structure with JSON mode enforcement
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": QUIZ_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        max_tokens=2048,
        response_format={"type": "json_object"}  # Groq guarantees valid JSON output structure
    )

    raw = response.choices[0].message.content.strip()

    # Extra safety parsing string strip
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"```$", "", raw)

    quiz_data = json.loads(raw.strip())
    return quiz_data


# ─── Weak Topic Analysis ──────────────────────────────────────────────────────

def analyze_weak_topics(wrong_questions: List[Dict]) -> str:
    """
    Given a list of incorrectly answered questions, use Groq to
    summarize weak areas and give study recommendations.
    """
    if not wrong_questions:
        return "Great job! You answered everything correctly. Review the material to reinforce your knowledge."

    questions_text = "\n".join(
        f"- Q: {q['question']}\n  Topic: {q.get('topic', 'N/A')}\n  Explanation: {q.get('explanation', 'N/A')}"
        for q in wrong_questions
    )

    prompt = f"""A student got the following questions wrong in a quiz:

{questions_text}

Based on these mistakes:
1. Identify 2-3 key weak areas/topics
2. Give specific study tips for each weak area
3. Suggest what to focus on before the next quiz

Keep it encouraging and actionable. Use bullet points."""

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=512,
    )
    return response.choices[0].message.content
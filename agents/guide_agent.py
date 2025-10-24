# agents/guide_agent.py
from pathlib import Path
from typing import Dict, Any, List
import os
import re
import time
import random
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_guide_agent(lecture_metadata: Dict[str, Any], extracted_outline, style="detailed"):
    """
    Generates a concise lecturer guide PDF (4-5 pages max) using Gemini and fpdf.
    """
    # Get API key from environment
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables. Please check your .env file")
    
    try:
        from google import genai
    except ImportError:
        raise ImportError("Google GenAI library not installed. Run: pip install google-genai")
    
    lecture_title = lecture_metadata.get("title", "Lecture")
    client = genai.Client(api_key=api_key)

    # Get model from environment or use default
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    # Extract keypoints from outline
    keypoints = extract_keypoints_from_outline(extracted_outline)
    slides_text = "\n".join([f"- {k}" for i, k in enumerate(keypoints)])

    # Very specific prompt for concise, markdown-free content
    prompt = f"""
    Create a VERY CONCISE instructor guide for: "{lecture_title}"
    
    Topics covered: {slides_text}

    Create an ULTRA-CONCISE guide that fits in 4-5 pages maximum.

    Structure:

    LECTURE OVERVIEW
    - 2-3 main objectives
    - 3-4 key learning outcomes

    TEACHING NOTES
    For each topic, provide ONLY:
    - Core concept (1 sentence)
    - Key teaching points (2-3 bullet points)
    - 1 real-world example
    - 1 discussion question

    TEACHING STRATEGIES  
    - Timing breakdown
    - 1-2 interactive activities
    - Key teaching tips

    ASSESSMENT
    - 2-3 quick check questions
    - 1-2 discussion prompts
    - Key exam topics

    CRITICAL FORMATTING RULES:
    - ABSOLUTELY NO markdown symbols: no #, no *, no **, no brackets, no backticks
    - Use plain text only
    - Maximum 4-5 pages total content
    - Be extremely concise - use bullet points only
    - Each section should be brief and to the point
    - Focus only on essential teaching information

    Remember: This must be very short and fit in 4-5 pages. Cut all unnecessary content.
    """

    # Add retry logic with proper indentation
    max_retries = 3
    base_delay = 2
    guide_text = ""

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            guide_text = response.text.strip()
            break
        except Exception as e:
            if "503" in str(e) or "overload" in str(e) or "429" in str(e):
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    print(f"🔄 API overloaded. Retrying in {delay:.1f}s... (Attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                    continue
                else:
                    # Use fallback template
                    guide_text = generate_fallback_guide(lecture_title, keypoints)
                    break
            else:
                # For other errors, use fallback immediately
                guide_text = generate_fallback_guide(lecture_title, keypoints)
                break

    # Generate concise PDF
    output_path = generate_concise_pdf_guide(lecture_title, guide_text)
    return output_path

def extract_keypoints_from_outline(outline):
    """Extract keypoints from various outline formats"""
    keypoints = []
    
    if hasattr(outline, 'slides'):
        # Outline object with slides attribute
        for slide in outline.slides:
            if hasattr(slide, 'title'):
                keypoints.append(slide.title)
            elif hasattr(slide, 'content'):
                keypoints.append(slide.content[:100] + "..." if len(slide.content) > 100 else slide.content)
            else:
                keypoints.append(str(slide))
    elif isinstance(outline, list):
        # List of slides
        for slide in outline:
            if isinstance(slide, dict):
                if 'title' in slide:
                    keypoints.append(slide['title'])
                elif 'content' in slide:
                    keypoints.append(slide['content'][:100] + "..." if len(slide['content']) > 100 else slide['content'])
            else:
                keypoints.append(str(slide))
    elif hasattr(outline, '__dict__'):
        # Object with attributes
        for attr in ['title', 'content', 'keypoints']:
            if hasattr(outline, attr):
                value = getattr(outline, attr)
                if value:
                    keypoints.append(str(value))
    else:
        # Fallback: convert to string and split
        outline_str = str(outline)
        if len(outline_str) > 200:
            keypoints = [outline_str[i:i+100] for i in range(0, min(len(outline_str), 500), 100)]
        else:
            keypoints = [outline_str]
    
    # Ensure we have at least some content
    if not keypoints:
        keypoints = ["Key concepts from the lecture material"]
    
    return keypoints[:10]  # Limit to 10 keypoints

def generate_fallback_guide(lecture_title: str, keypoints: List[str]):
    """Generate a fallback guide when API fails"""
    fallback_content = f"""
LECTURE OVERVIEW
Main Objectives
- Understand core concepts of {lecture_title}
- Apply knowledge to practical scenarios
- Develop critical thinking skills

Key Learning Outcomes
- Master fundamental principles
- Solve related problems
- Connect concepts to real-world applications

TEACHING NOTES
Core Concepts
- Fundamental principles underlying {lecture_title}
- Key relationships and patterns
- Practical applications and implications

Key Teaching Points
- Focus on conceptual understanding
- Emphasize practical applications
- Connect to student experiences

Real-world Examples
- Industry applications
- Everyday scenarios
- Historical context

Discussion Questions
- How would you apply these concepts?
- What are the potential implications?
- How does this connect to previous topics?

TEACHING STRATEGIES
Timing Breakdown
- Introduction: 15%
- Core concepts: 50%
- Applications: 25%
- Review: 10%

Interactive Activities
- Think-pair-share exercises
- Case study analysis
- Quick polls or surveys

Teaching Tips
- Use visual aids when possible
- Encourage student participation
- Provide clear examples
- Check for understanding regularly

ASSESSMENT
Quick Check Questions
- What is the main concept?
- How would you explain this to someone else?
- What are the key applications?

Discussion Prompts
- Real-world implications
- Ethical considerations
- Future developments

Exam Topics
- Core concepts and definitions
- Application problems
- Critical analysis questions
"""
    return fallback_content

def generate_concise_pdf_guide(lecture_title: str, guide_text: str):
    """
    Generates a concise PDF guide (4-5 pages max) without any markdown symbols.
    """
    try:
        from fpdf import FPDF
    except ImportError:
        raise ImportError("fpdf library not installed. Run: pip install fpdf")
    
    # Create output directory
    output_dir = Path("outputs/guides")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create PDF with smaller fonts for conciseness
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    
    # Color scheme
    primary_color = (41, 128, 185)    # Blue
    secondary_color = (52, 152, 219)  # Light blue
    accent_color = (44, 62, 80)       # Dark blue
    text_color = (50, 50, 50)         # Dark gray
    
    # Title section - more compact
    pdf.set_fill_color(*primary_color)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "INSTRUCTOR GUIDE", 0, 1, "C", True)
    
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, lecture_title, 0, 1, "C", True)
    pdf.ln(8)
    
    # Clean the guide text aggressively
    clean_text = aggressive_clean_markdown(guide_text)
    
    # Process content with compact formatting
    pdf.set_text_color(*text_color)
    process_compact_content(pdf, clean_text, secondary_color, accent_color, text_color)
    
    # Compact footer
    pdf.set_y(-15)
    pdf.set_fill_color(*accent_color)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "I", 7)
    pdf.cell(0, 6, "SlideCraft - AI Lecture Processor", 0, 0, "C", True)
    
    # Save PDF
    safe_title = "".join(c for c in lecture_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    output_file = output_dir / f"{safe_title}_Instructor_Guide.pdf"
    pdf.output(str(output_file))
    
    print(f"✅ PDF guide generated: {output_file}")
    return str(output_file)

def aggressive_clean_markdown(text: str) -> str:
    """
    Aggressively removes all markdown symbols and trims content.
    """
    if not text:
        return "No content available for this guide."
    
    # Remove all markdown headers
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    
    # Remove all bold/italic markers
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    
    # Remove other markdown symbols
    text = re.sub(r'`(.*?)`', r'\1', text)
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
    
    # Convert various bullet styles to simple dashes
    text = re.sub(r'^\s*[•*+-]\s+', '- ', text, flags=re.MULTILINE)
    
    # Remove extra blank lines to save space
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
    
    return text.strip()

def process_compact_content(pdf, text: str, section_color: tuple, accent_color: tuple, text_color: tuple):
    """
    Process content with compact formatting to fit in 4-5 pages.
    """
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            pdf.ln(3)  # Smaller spacing
            continue
        
        # Check for major sections (uppercase and relatively short)
        line_upper = line.upper()
        is_major_section = any(keyword in line_upper for keyword in [
            'LECTURE OVERVIEW', 'TEACHING NOTES', 'TEACHING STRATEGIES', 'ASSESSMENT',
            'OVERVIEW', 'NOTES', 'STRATEGIES'
        ]) and len(line) < 50
        
        if is_major_section:
            pdf.ln(5)
            pdf.set_fill_color(*section_color)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("Arial", "B", 12)  # Smaller font for headers
            pdf.cell(0, 8, line.upper(), 0, 1, "L", True)
            pdf.set_text_color(*text_color)
            pdf.ln(2)
            
        # Check for sub-sections
        elif (line_upper == line and len(line) < 100 and 
              any(keyword in line_upper for keyword in [
                  'OBJECTIVES', 'OUTCOMES', 'KEY POINTS', 'EXAMPLES', 
                  'QUESTIONS', 'TIMING', 'ACTIVITIES', 'TIPS', 'MAIN',
                  'CORE', 'REAL-WORLD', 'DISCUSSION', 'QUICK', 'EXAM'
              ])):
            pdf.ln(3)
            pdf.set_text_color(*accent_color)
            pdf.set_font("Arial", "B", 10)
            pdf.cell(0, 6, line, 0, 1)
            pdf.set_text_color(*text_color)
            pdf.ln(1)
            
        else:
            # Regular content - use smaller font and tighter spacing
            pdf.set_font("Arial", size=10)  # Smaller font for content
            
            if line.startswith('-'):
                # Bullet points - compact
                pdf.cell(8)
                content = line[1:].strip()
                # Truncate very long lines
                if len(content) > 120:
                    content = content[:117] + '...'
                pdf.multi_cell(0, 5, content)
            else:
                # Regular text - more compact
                if len(line) > 120:
                    line = line[:117] + '...'
                pdf.multi_cell(0, 5, line)
            
            pdf.ln(1)  # Minimal spacing between lines
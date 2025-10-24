# utils/pdf_generator.py
from jinja2 import Environment, FileSystemLoader
import pdfkit
from pathlib import Path

TEMPLATE_DIR = Path("utils/templates")
OUTPUT_DIR = Path("outputs/guides")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def render_lecturer_guide_pdf(lecture_title: str, guide_text: str):
    """
    Renders the lecturer guide HTML and converts it into a clean, readable PDF.
    """
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template("lecturer_guide.html")
    html = template.render(title=lecture_title, guide_text=guide_text)

    output_file = OUTPUT_DIR / f"{lecture_title.replace(' ', '_')}_Instructor_Guide.pdf"
    pdfkit.from_string(html, str(output_file))
    return output_file

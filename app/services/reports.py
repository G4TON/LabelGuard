from fpdf import FPDF
from datetime import datetime
from app.config import config
import os

class CompetencyReport(FPDF):
    def header(self):
        self.set_font("helvetica", "B", 15)
        self.cell(0, 10, "RPL-Assist Competency Assessment Report", border=False, ln=1, align="C")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

def generate_pdf_report(assessment, worker, tasks, assessor):
    pdf = CompetencyReport()
    pdf.add_page()
    
    # 1. Worker Information
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, "1. Worker Information", ln=1)
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 8, f"Name: {worker.full_name}", ln=1)
    pdf.cell(0, 8, f"Phone: {worker.phone}", ln=1)
    pdf.cell(0, 8, f"Experience: {assessment.experience_years} years", ln=1)
    pdf.ln(5)
    
    # 2. Qualification Pack
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, "2. Qualification Pack", ln=1)
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 8, f"QP Name: {assessment.qp_name}", ln=1)
    pdf.cell(0, 8, f"QP ID: {assessment.qp_id}", ln=1)
    pdf.ln(5)
    
    # 3. Task-by-task results
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, "3. Task Results", ln=1)
    
    total_score = 0
    in_person_tasks = []
    
    for task in tasks:
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(0, 8, f"Task: {task.name}", ln=1)
        pdf.set_font("helvetica", "", 10)
        
        score = "N/A"
        if task.assessor_decision:
            score = str(task.assessor_decision.final_score)
            total_score += task.assessor_decision.final_score
            
        pdf.cell(0, 8, f"Score: {score}/4", ln=1)
        if task.requires_in_person:
            pdf.set_text_color(255, 0, 0)
            pdf.cell(0, 8, "REQUIRES IN-PERSON ASSESSMENT", ln=1)
            pdf.set_text_color(0, 0, 0)
            in_person_tasks.append(task.name)
            
        if task.assessor_decision and task.assessor_decision.override_reason:
            pdf.multi_cell(0, 8, f"Assessor Comment: {task.assessor_decision.override_reason}")
            
        pdf.ln(2)
        
    # 4. Summary & AI Disclosure
    pdf.add_page()
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, "4. Assessment Summary", ln=1)
    pdf.set_font("helvetica", "", 10)
    
    avg_score = total_score / len(tasks) if tasks else 0
    pdf.cell(0, 8, f"Average Score: {avg_score:.2f}/4", ln=1)
    
    if avg_score >= 3.0 and not in_person_tasks:
        competency_status = "Competent"
    elif in_person_tasks:
        competency_status = "Pending In-Person Verification"
    else:
        competency_status = "Not Competent"
        
    pdf.cell(0, 8, f"Competency Status: {competency_status}", ln=1)
    
    pdf.ln(10)
    pdf.set_font("helvetica", "I", 9)
    pdf.multi_cell(0, 6, "AI Assistance Disclosure: This assessment was assisted by AI for initial evidence review and qualification pack mapping. The final decisions and scores were verified and confirmed by a human assessor.")
    
    # 5. Sign-off
    pdf.ln(10)
    pdf.set_font("helvetica", "B", 10)
    assessor_name = assessor.username if assessor else "Pending"
    pdf.cell(0, 8, f"Assessor Sign-off: {assessor_name}", ln=1)
    pdf.cell(0, 8, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=1)
    pdf.cell(0, 8, f"Assessment Ref ID: {assessment.id}", ln=1)
    
    filename = f"report_assessment_{assessment.id}.pdf"
    filepath = config.REPORTS_DIR / filename
    pdf.output(str(filepath))
    return filepath

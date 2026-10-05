import streamlit as st
from app.database.models import Assessment, AISuggestion, AssessorDecision, Worker
from app.services.ai import ai_service
from app.services.assessment import load_qualification_pack, log_audit
from app.services.reports import generate_pdf_report
import os
import json

def render(db, current_user):
    st.title("Assessor Dashboard")
    
    st.write("### Pending Assessments")
    pending_assessments = db.query(Assessment).filter(Assessment.status.in_(['REVIEW', 'IN_PROGRESS'])).all()
    
    if not pending_assessments:
        st.info("No assessments currently require review.")
    
    for assessment in pending_assessments:
        worker = db.query(Worker).filter_by(id=assessment.worker_id).first()
        with st.expander(f"Assessment {assessment.id} - {worker.full_name} ({assessment.qp_name}) - Status: {assessment.status}"):
            st.write(f"**Trade:** {assessment.trade_selected}")
            st.write(f"**Experience:** {assessment.experience_years} years")
            st.write(f"**Self Declaration:** {assessment.self_declaration_text}")
            
            if st.button("Review Tasks", key=f"review_btn_{assessment.id}"):
                st.session_state['reviewing_assessment_id'] = assessment.id
                st.rerun()
                
    if 'reviewing_assessment_id' in st.session_state:
        st.markdown("---")
        render_assessment_review(db, st.session_state['reviewing_assessment_id'], current_user)

def render_assessment_review(db, assessment_id, current_user):
    assessment = db.query(Assessment).filter_by(id=assessment_id).first()
    worker = db.query(Worker).filter_by(id=assessment.worker_id).first()
    qp_data = load_qualification_pack(assessment.qp_id)
    
    st.header(f"Reviewing Assessment for {worker.full_name}")
    
    all_reviewed = True
    
    for task in assessment.tasks:
        st.subheader(f"Task: {task.name}")
        st.write(f"**Description:** {task.description}")
        
        task_qp = next((t for t in qp_data['tasks'] if t['id'] == task.task_id), None)
        if task_qp:
            st.markdown("**Rubric:**")
            for score, desc in task_qp['rubric'].items():
                st.write(f"- **{score}**: {desc}")
                
        # Show Evidence
        evidence_list = task.evidence
        evidence_text = ""
        for ev in evidence_list:
            if ev.evidence_type == 'text':
                st.write(f"**Worker Text Evidence:** {ev.text_content}")
                evidence_text += ev.text_content + " "
            elif ev.file_path:
                st.write(f"**Attached File:** {os.path.basename(ev.file_path)}")
                if ev.file_path.endswith(('.jpg', '.jpeg', '.png')):
                    try:
                        st.image(ev.file_path, width=300)
                        evidence_text += "[Image evidence provided] "
                    except:
                        st.write("Image not found locally (could be offline/syncing)")
                        
        # AI Review
        if task.status == 'EVIDENCE_SUBMITTED':
            if st.button("Generate AI Suggestion", key=f"ai_{task.id}"):
                with st.spinner("AI is reviewing evidence..."):
                    result = ai_service.review_evidence(task.description, task_qp['rubric'] if task_qp else {}, evidence_text)
                    
                    suggestion = AISuggestion(
                        task_id=task.id,
                        suggested_score=result.get('suggested_score'),
                        observation=result.get('observation'),
                        confidence=result.get('confidence', 0.0),
                        requires_human=result.get('requires_human', True)
                    )
                    db.add(suggestion)
                    task.status = 'AI_REVIEWED'
                    db.commit()
                    log_audit(db, 'AssessmentTask', task.id, 'AI_REVIEWED', current_user.id)
                    st.rerun()
                    
        if task.ai_suggestion:
            st.info("🤖 **AI Observation & Suggestion**")
            st.write(f"**Observation:** {task.ai_suggestion.observation}")
            st.write(f"**Suggested Score:** {task.ai_suggestion.suggested_score}/4 (Confidence: {task.ai_suggestion.confidence})")
            
        # Assessor Decision
        if task.status in ['EVIDENCE_SUBMITTED', 'AI_REVIEWED', 'ASSESSOR_REVIEWED']:
            with st.form(f"decision_form_{task.id}"):
                st.write("**Assessor Final Decision**")
                score_options = [1, 2, 3, 4]
                default_index = 0
                if task.assessor_decision:
                    default_index = score_options.index(task.assessor_decision.final_score)
                elif task.ai_suggestion and task.ai_suggestion.suggested_score in score_options:
                    default_index = score_options.index(task.ai_suggestion.suggested_score)
                    
                score = st.selectbox("Score", score_options, index=default_index)
                in_person = st.checkbox("Requires In-Person Assessment", value=task.requires_in_person)
                reason = st.text_area("Comments / Override Reason", value=task.assessor_decision.override_reason if task.assessor_decision else "")
                
                submitted = st.form_submit_button("Save Decision")
                if submitted:
                    if not task.assessor_decision:
                        decision = AssessorDecision(task_id=task.id, assessor_id=current_user.id)
                        db.add(decision)
                    else:
                        decision = task.assessor_decision
                        
                    decision.final_score = score
                    decision.override_reason = reason
                    task.requires_in_person = in_person
                    task.status = 'ASSESSOR_REVIEWED'
                    db.commit()
                    
                    log_audit(db, 'AssessmentTask', task.id, 'ASSESSOR_DECISION', current_user.id, 
                              new_value={"score": score, "in_person": in_person, "reason": reason})
                    st.success("Decision saved.")
                    st.rerun()
        
        if task.status != 'ASSESSOR_REVIEWED':
            all_reviewed = False
            
        st.markdown("---")

    if all_reviewed:
        st.success("All tasks have been reviewed.")
        if st.button("Sign Off & Generate Report"):
            assessment.status = 'COMPLETED'
            assessment.assessor_id = current_user.id
            db.commit()
            
            # Generate Report
            report_path = generate_pdf_report(assessment, worker, assessment.tasks, current_user)
            log_audit(db, 'Assessment', assessment.id, 'COMPLETED', current_user.id)
            
            st.success("Assessment Completed!")
            with open(report_path, "rb") as pdf_file:
                st.download_button(
                    label="Download Competency Report",
                    data=pdf_file,
                    file_name=os.path.basename(report_path),
                    mime="application/pdf"
                )
            del st.session_state['reviewing_assessment_id']

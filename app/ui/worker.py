import streamlit as st
import os
from app.database.models import Assessment, Evidence
from app.services.ai import ai_service
from app.services.assessment import load_qualification_pack, generate_assessment_tasks, log_audit
from app.config import config
from datetime import datetime

def render(db, current_user):
    st.title("Worker Self-Declaration")
    
    worker = current_user.worker_profile
    if not worker:
        st.error("Worker profile not found.")
        return
        
    st.header(f"Welcome, {worker.full_name}")
    
    # Check if active assessment exists
    assessment = db.query(Assessment).filter_by(worker_id=worker.id).order_by(Assessment.created_at.desc()).first()
    
    if not assessment or assessment.status == 'COMPLETED':
        if st.button("Start New Assessment"):
            new_assessment = Assessment(worker_id=worker.id)
            db.add(new_assessment)
            db.commit()
            log_audit(db, 'Assessment', new_assessment.id, 'CREATED', current_user.id)
            st.rerun()
        return

    st.subheader(f"Current Assessment Status: {assessment.status}")
    
    if assessment.status == 'CREATED':
        render_step_declaration(db, assessment, current_user)
    elif assessment.status == 'QP_MAPPED':
        render_step_qp_mapping(db, assessment, current_user)
    elif assessment.status == 'IN_PROGRESS':
        render_step_tasks(db, assessment, current_user)
    elif assessment.status == 'REVIEW':
        st.info("Assessment is currently under review by an assessor.")
    
def render_step_declaration(db, assessment, current_user):
    st.write("### Step 1: Self-Declaration")
    with st.form("declaration_form"):
        trade = st.selectbox("Select Trade", ["Plumbing", "Electrical", "Carpentry", "Masonry"])
        exp = st.number_input("Years of Experience", min_value=0, max_value=50)
        decl = st.text_area("Describe your past work experience and skills (You can type in your regional language)")
        
        submitted = st.form_submit_button("Submit Declaration")
        if submitted:
            assessment.trade_selected = trade
            assessment.experience_years = exp
            assessment.self_declaration_text = decl
            assessment.status = 'QP_MAPPED'
            db.commit()
            log_audit(db, 'Assessment', assessment.id, 'DECLARATION_SUBMITTED', current_user.id)
            st.rerun()

def render_step_qp_mapping(db, assessment, current_user):
    st.write("### Step 2: Qualification Pack Selection")
    
    worker_data = {
        "trade": assessment.trade_selected,
        "experience": assessment.experience_years,
        "declaration": assessment.self_declaration_text
    }
    
    available_qps = [{"id": "QP-DEMO-001", "title": "Demo Trade: General Plumber"}]
    
    with st.spinner("AI is analyzing your profile to suggest the best Qualification Pack..."):
        ai_suggestion = ai_service.suggest_qualification_pack(worker_data, available_qps)
    
    st.success(f"AI Suggested QP: **{ai_suggestion['suggested_qp_id']}**")
    st.info(f"Reasoning: {ai_suggestion['matching_reasons']}")
    
    qp_data = load_qualification_pack(ai_suggestion['suggested_qp_id'])
    
    if qp_data:
        st.write(f"**Title:** {qp_data['title']}")
        st.write(f"This pack has {len(qp_data['tasks'])} assessment tasks.")
        
        if st.button("Accept & Generate Tasks"):
            assessment.qp_id = qp_data['id']
            assessment.qp_name = qp_data['title']
            assessment.status = 'IN_PROGRESS'
            db.commit()
            
            generate_assessment_tasks(db, assessment.id, qp_data)
            log_audit(db, 'Assessment', assessment.id, 'QP_ACCEPTED', current_user.id, new_value={"qp_id": qp_data['id']})
            st.rerun()
    else:
        st.error("Failed to load suggested QP. Please contact admin.")

def render_step_tasks(db, assessment, current_user):
    st.write("### Step 3: Evidence Submission")
    
    tasks = assessment.tasks
    
    for idx, task in enumerate(tasks):
        with st.expander(f"Task {idx+1}: {task.name} ({task.status})", expanded=(task.status=='PENDING')):
            st.write(f"**Description:** {task.description}")
            
            qp_data = load_qualification_pack(assessment.qp_id)
            task_qp = next((t for t in qp_data['tasks'] if t['id'] == task.task_id), None)
            
            if task_qp:
                st.write(f"**Evidence Required:** {task_qp['evidence_requirements']}")
                st.write(f"**Assessability:** {task_qp['assessability']}")
            
            if task.status == 'PENDING':
                uploaded_file = st.file_uploader(f"Upload Evidence (Image/Video) for {task.name}", key=f"file_{task.id}")
                text_evidence = st.text_area("Or describe how you do this task (Text/Voice equivalent)", key=f"text_{task.id}")
                
                if st.button("Submit Evidence", key=f"submit_{task.id}"):
                    if uploaded_file or text_evidence:
                        file_path = None
                        if uploaded_file:
                            filename = f"{task.id}_{int(datetime.now().timestamp())}_{uploaded_file.name}"
                            file_path = os.path.join(config.EVIDENCE_DIR, filename)
                            with open(file_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                                
                        evidence = Evidence(
                            task_id=task.id,
                            evidence_type='image' if uploaded_file else 'text',
                            file_path=file_path,
                            text_content=text_evidence
                        )
                        db.add(evidence)
                        task.status = 'EVIDENCE_SUBMITTED'
                        db.commit()
                        log_audit(db, 'AssessmentTask', task.id, 'EVIDENCE_UPLOADED', current_user.id)
                        st.success("Evidence submitted.")
                        st.rerun()
                    else:
                        st.warning("Please provide evidence.")
            else:
                st.success("Evidence submitted for this task.")
    
    if all(task.status != 'PENDING' for task in tasks):
        if st.button("Complete Submission & Send to Assessor"):
            assessment.status = 'REVIEW'
            db.commit()
            log_audit(db, 'Assessment', assessment.id, 'SUBMITTED_FOR_REVIEW', current_user.id)
            st.success("Sent to Assessor!")
            st.rerun()

import sys
import os

# Ensure Python can find the 'app' module regardless of how the script is executed
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from app.database.connection import init_db, SessionLocal
from app.database.models import User, Worker
from app.ui import worker as worker_ui, assessor as assessor_ui, admin as admin_ui
from app.config import config

# Initialize DB safely to prevent race conditions on Streamlit Cloud
@st.cache_resource
def setup_db():
    init_db()
    db = SessionLocal()
    seed_demo_data(db)
    db.close()

setup_db()

st.set_page_config(page_title="RPL-Assist", layout="wide")

def seed_demo_data(db):
    if not db.query(User).filter_by(username="worker").first():
        worker_user = User(username="worker", password_hash="worker123", role="worker")
        db.add(worker_user)
        db.commit()
        worker = Worker(user_id=worker_user.id, full_name="Raju Plumber", phone="9876543210")
        db.add(worker)
        
        assessor_user1 = User(username="inspector1", password_hash="inspector123", role="assessor")
        assessor_user2 = User(username="inspector2", password_hash="inspector123", role="assessor")
        admin_user = User(username="admin", password_hash="admin123", role="admin")
        
        db.add_all([assessor_user1, assessor_user2, admin_user])
        db.commit()
        
        # Add mock assessment data for Cohen's Kappa analytics
        from app.database.models import AssessmentTask, AssessorDecision, Assessment
        
        # Create a dummy assessment just to host some tasks
        dummy_assessment = Assessment(worker_id=worker.id, status='COMPLETED')
        db.add(dummy_assessment)
        db.commit()
        
        tasks = []
        for i in range(5):
            t = AssessmentTask(assessment_id=dummy_assessment.id, name=f"Historical Task {i+1}", task_id=f"T{i+1}")
            db.add(t)
            tasks.append(t)
        db.commit()
        
        # Assessor 1 and 2 scoring the same tasks with some agreement and some disagreement
        scores_a1 = [4, 3, 2, 4, 3]
        scores_a2 = [4, 3, 1, 3, 3] # mostly agrees
        
        for i in range(5):
            d1 = AssessorDecision(task_id=tasks[i].id, assessor_id=assessor_user1.id, final_score=scores_a1[i])
            d2 = AssessorDecision(task_id=tasks[i].id, assessor_id=assessor_user2.id, final_score=scores_a2[i])
            db.add_all([d1, d2])
            
        db.commit()

def main():
    db = SessionLocal()
    
    if 'current_user_id' not in st.session_state:
        # Modern Centered Login Page
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("<h1 style='text-align: center;'>RPL-Assist</h1>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: gray;'>AI-Assisted Skill Assessment Platform</p>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            
            with st.form("login_form"):
                st.subheader("Sign In")
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                st.markdown("<br>", unsafe_allow_html=True)
                submit = st.form_submit_button("Login", use_container_width=True)
                
                if submit:
                    user = db.query(User).filter_by(username=username, password_hash=password).first()
                    if user:
                        st.session_state['current_user_id'] = user.id
                        st.session_state['current_user_role'] = user.role
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")
    else:
        # Logged in state
        current_user = db.query(User).filter_by(id=st.session_state['current_user_id']).first()
        
        # Sidebar for navigation / status
        st.sidebar.title("RPL-Assist")
        
        display_name = current_user.username
        if current_user.role == 'worker' and current_user.worker_profile:
            display_name = current_user.worker_profile.full_name
            
        st.sidebar.markdown(f"👤 **{display_name}**")
        st.sidebar.caption(f"Role: {current_user.role.capitalize()}")
        st.sidebar.markdown("---")
        st.sidebar.markdown("📶 **Status: ONLINE**")
        st.sidebar.markdown("<br>", unsafe_allow_html=True)
        
        if st.sidebar.button("Logout", use_container_width=True):
            del st.session_state['current_user_id']
            del st.session_state['current_user_role']
            st.rerun()
            
        # Render appropriate UI based on role
        if current_user.role == 'worker':
            worker_ui.render(db, current_user)
        elif current_user.role == 'assessor':
            assessor_ui.render(db, current_user)
        elif current_user.role == 'admin':
            admin_ui.render(db, current_user)

    db.close()

if __name__ == "__main__":
    main()

import streamlit as st
import pandas as pd
import plotly.express as px
from app.database.models import Assessment, AssessorDecision, AuditLog
from app.services.analytics import calculate_assessor_agreement

def render(db, current_user):
    st.title("Admin Dashboard & Analytics")
    
    st.write("### Overview")
    assessments = db.query(Assessment).all()
    
    total_assessments = len(assessments)
    completed_assessments = sum(1 for a in assessments if a.status == 'COMPLETED')
    pending_assessments = total_assessments - completed_assessments
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Assessments", total_assessments)
    col2.metric("Completed", completed_assessments)
    col3.metric("Pending", pending_assessments)
    
    if assessments:
        status_counts = {}
        for a in assessments:
            status_counts[a.status] = status_counts.get(a.status, 0) + 1
            
        df_status = pd.DataFrame(list(status_counts.items()), columns=['Status', 'Count'])
        fig = px.pie(df_status, values='Count', names='Status', title='Assessment Status Distribution')
        st.plotly_chart(fig)
    
    st.write("### Assessor Agreement (Cohen's Kappa)")
    # Fetch data for kappa
    decisions = db.query(AssessorDecision.task_id, AssessorDecision.assessor_id, AssessorDecision.final_score).all()
    if decisions:
        df = pd.DataFrame(decisions, columns=['task_id', 'assessor_id', 'score'])
        results = calculate_assessor_agreement(df)
        
        if "error" in results:
            st.warning(results["error"])
        else:
            for pair, data in results.items():
                st.write(f"**{pair}**")
                st.write(f"- Tasks Compared: {data['tasks_compared']}")
                st.write(f"- Kappa Score: {data['kappa']:.2f} ({data['interpretation']})")
    else:
        st.info("No assessor decisions available yet.")
        
    st.write("### Audit Logs")
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(20).all()
    if logs:
        log_data = []
        for log in logs:
            log_data.append({
                "Date": log.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                "Action": log.action,
                "Entity Type": log.entity_type,
                "Entity ID": log.entity_id,
                "User ID": log.user_id
            })
        st.dataframe(pd.DataFrame(log_data), use_container_width=True, hide_index=True)
    else:
        st.info("No audit logs available.")


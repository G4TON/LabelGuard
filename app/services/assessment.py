import yaml
from app.config import config
from app.database.models import AssessmentTask, AuditLog

def load_qualification_pack(qp_id):
    qp_file = config.QP_DIR / f"{qp_id.lower().replace('-', '_')}.yaml"
    # Try generic name if specific fails
    if not qp_file.exists():
        qp_file = config.QP_DIR / "demo_qp.yaml"
        
    if qp_file.exists():
        with open(qp_file, 'r') as f:
            return yaml.safe_load(f)
    return None

def generate_assessment_tasks(db, assessment_id, qp_data):
    tasks = []
    for t_data in qp_data.get('tasks', []):
        task = AssessmentTask(
            assessment_id=assessment_id,
            task_id=t_data['id'],
            name=t_data['name'],
            description=t_data['description']
        )
        db.add(task)
        tasks.append(task)
    db.commit()
    return tasks

def log_audit(db, entity_type, entity_id, action, user_id=None, previous_value=None, new_value=None, reason=None):
    log = AuditLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        user_id=user_id,
        previous_value=previous_value,
        new_value=new_value,
        reason=reason
    )
    db.add(log)
    db.commit()

from sklearn.metrics import cohen_kappa_score
import pandas as pd

def calculate_assessor_agreement(decisions_df):
    """
    Expects a DataFrame with columns: ['task_id', 'assessor_id', 'score']
    Returns a dictionary with kappa scores for pairs of assessors.
    """
    if decisions_df.empty:
        return {"error": "Insufficient data"}
        
    # Pivot so each assessor is a column, rows are tasks
    pivoted = decisions_df.pivot(index='task_id', columns='assessor_id', values='score').dropna()
    
    if len(pivoted.columns) < 2 or len(pivoted) < 2:
        return {"error": "Insufficient paired assessments to calculate Cohen's kappa."}
        
    assessors = pivoted.columns.tolist()
    results = {}
    
    for i in range(len(assessors)):
        for j in range(i + 1, len(assessors)):
            assessor1 = assessors[i]
            assessor2 = assessors[j]
            
            scores1 = pivoted[assessor1].tolist()
            scores2 = pivoted[assessor2].tolist()
            
            kappa = cohen_kappa_score(scores1, scores2)
            
            interpretation = "Poor"
            if kappa > 0.8: interpretation = "Almost Perfect"
            elif kappa > 0.6: interpretation = "Substantial"
            elif kappa > 0.4: interpretation = "Moderate"
            elif kappa > 0.2: interpretation = "Fair"
            elif kappa > 0: interpretation = "Slight"
            
            results[f"Assessor {assessor1} vs {assessor2}"] = {
                "kappa": kappa,
                "tasks_compared": len(pivoted),
                "interpretation": interpretation
            }
            
    return results

import requests

res = requests.post("http://localhost:8000/chat/start")
conv_id = res.json()["conversation_id"]

def submit_stage(stage, data):
    return requests.post("http://localhost:8000/chat/stage-submit", json={
        "conversation_id": conv_id,
        "stage": stage,
        "data": data,
        "selected_model": "medgemma"
    }).json()

submit_stage("chief_complaint", {"chief_complaint": "Severe headache and vomiting"})
submit_stage("symptom_detail", {"location": "Head", "character": "Throbbing", "severity": 8})
submit_stage("associated_symptoms", {"associated": ["Nausea", "Fatigue"]})
submit_stage("timeline", {"duration": "3 Days", "onset": "Sudden", "pattern": "Constant"})
submit_stage("history", {"history": "None"})
submit_stage("medications", {"medications": []})
submit_stage("reports", {"reports_skipped": True})
res = submit_stage("imaging", {"imaging_skipped": True})

print(res)

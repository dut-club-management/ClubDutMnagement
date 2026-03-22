from app import create_app
from models.analytics import Analytics

app = create_app()
with app.app_context():
    print("Existing analytics records:")
    records = Analytics.query.all()
    for record in records:
        print(f"  {record.metric_type} on {record.metric_date}: {record.metric_value}")

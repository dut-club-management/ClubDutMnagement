from app import create_app
from services.analytics_service import AnalyticsService

app = create_app()
with app.app_context():
    try:
        print("Testing analytics calculation...")
        result = AnalyticsService.calculate_participation_trends(30)
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

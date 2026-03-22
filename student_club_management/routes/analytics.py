from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from services.analytics_service import AnalyticsService, ReminderService
from models.analytics import Analytics
from app import db
from datetime import date, timedelta

analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')

@analytics_bp.route('/dashboard')
@login_required
def analytics_dashboard():
    """Analytics dashboard for admin"""
    if current_user.role != 'admin':
        return 'Unauthorized', 403
    
    # Get dashboard summary
    summary = AnalyticsService.get_dashboard_summary()
    
    # Get trend data
    membership_growth = AnalyticsService.get_analytics_data('membership_growth', 30)
    event_attendance = AnalyticsService.get_analytics_data('event_attendance', 30)
    participation_trends = AnalyticsService.get_analytics_data('participation', 30)
    
    return render_template('analytics/dashboard.html',
                         summary=summary,
                         membership_growth=membership_growth,
                         event_attendance=event_attendance,
                         participation_trends=participation_trends)

@analytics_bp.route('/api/refresh')
@login_required
def refresh_analytics():
    """Refresh analytics data"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        # Calculate fresh analytics
        AnalyticsService.calculate_membership_growth(30)
        AnalyticsService.calculate_event_attendance(30)
        AnalyticsService.calculate_participation_trends(30)
        
        return jsonify({'success': True, 'message': 'Analytics refreshed successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/api/send-reminders')
@login_required
def send_reminders():
    """Trigger manual reminder sending"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        ReminderService.send_event_reminders()
        ReminderService.send_club_reminders()
        
        return jsonify({'success': True, 'message': 'Reminders sent successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/api/data/<metric_type>')
@login_required
def get_analytics_data(metric_type):
    """Get analytics data for specific metric"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        days = request.args.get('days', 30, type=int)
        data = AnalyticsService.get_analytics_data(metric_type, days)
        
        # Convert to chart-friendly format
        chart_data = [{
            'date': record.metric_date.strftime('%Y-%m-%d'),
            'value': record.metric_value,
            'extra_data': record.extra_data or {}
        } for record in data]
        
        return jsonify({'data': chart_data, 'metric_type': metric_type})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

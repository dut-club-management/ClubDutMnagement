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
    
    try:
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
    
    except Exception as e:
        # Log the error for debugging
        import traceback
        error_details = traceback.format_exc()
        print(f"Analytics Dashboard Error: {e}")
        print(f"Full traceback: {error_details}")
        
        # Return a simple fallback dashboard
        try:
            fallback_summary = {
                'total_counts': {'users': 0, 'clubs': 0, 'events': 0, 'memberships': 0},
                'recent_activity': {'new_users': 0, 'new_clubs': 0, 'new_events': 0, 'new_memberships': 0, 'recent_attendance': 0, 'upcoming_events': 0},
                'club_status': {'active': 0, 'pending': 0},
                'recent_events_attendance': []
            }
            
            fallback_membership_growth = {'labels': [], 'data': []}
            fallback_event_attendance = {'labels': [], 'data': []}
            fallback_participation_trends = {'labels': [], 'data': []}
            
            return render_template('analytics/dashboard.html',
                                 summary=fallback_summary,
                                 membership_growth=fallback_membership_growth,
                                 event_attendance=fallback_event_attendance,
                                 participation_trends=fallback_participation_trends)
        except Exception as fallback_error:
            return f"Analytics Dashboard Error: {str(e)}<br>Fallback Error: {str(fallback_error)}", 500

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

@analytics_bp.route('/api/event-attendance/<int:event_id>')
@login_required
def get_event_attendance(event_id):
    """Get detailed attendance for a specific event"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        from models.event import Event
        from models.attendance import EventAttendance
        from models.user import User
        
        event = Event.query.get_or_404(event_id)
        
        # Get attendance details
        attendees = db.session.query(
            User.first_name,
            User.last_name,
            User.email,
            User.student_number,
            EventAttendance.checked_in_at,
            EventAttendance.is_attended
        ).join(EventAttendance, User.id == EventAttendance.user_id).filter(
            EventAttendance.event_id == event_id
        ).all()
        
        attendance_data = {
            'event': {
                'id': event.id,
                'name': event.event_name,
                'date': event.event_date.strftime('%Y-%m-%d %H:%M'),
                'location': event.location
            },
            'attendees': [
                {
                    'name': f"{att.first_name} {att.last_name}",
                    'email': att.email,
                    'student_number': att.student_number,
                    'checked_in_at': att.checked_in_at.strftime('%Y-%m-%d %H:%M') if att.checked_in_at else None,
                    'is_attended': att.is_attended
                } for att in attendees
            ],
            'total_attendees': len([att for att in attendees if att.is_attended]),
            'total_registered': len(attendees)
        }
        
        return jsonify({'success': True, 'data': attendance_data})
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

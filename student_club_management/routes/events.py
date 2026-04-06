from flask import Blueprint, render_template, request, redirect, flash, jsonify
from flask_login import login_required, current_user
from models.event import Event
from models.club import Club
from models.user import User
from models.membership import Membership
from models.attendance import EventAttendance
from models.notification import Notification
from datetime import datetime, timedelta
import json
import qrcode
from io import BytesIO
import base64

events_bp = Blueprint('events', __name__, url_prefix='/events')

def check_event_conflicts(event_date, end_date, location, event_id=None, club_id=None):
    """
    Check for conflicting events at the same location and time.
    Returns list of conflicting events.
    """
    from app import db
    
    # Define time window for conflict (1 hour before and after)
    window_start = event_date - timedelta(hours=1)
    window_end = end_date + timedelta(hours=1) if end_date else event_date + timedelta(hours=2)
    
    # Query for events at the same location within the time window
    query = Event.query.filter(
        Event.location.ilike(f'%{location}%'),
        Event.status.in_(['approved', 'pending', 'ongoing']),
        Event.event_date.between(window_start, window_end)
    )
    
    # Exclude current event if editing
    if event_id:
        query = query.filter(Event.id != event_id)
    
    conflicting_events = query.all()
    
    # Also check for any events at same time regardless of location
    time_conflicts = Event.query.filter(
        Event.status.in_(['approved', 'pending', 'ongoing']),
        Event.event_date.between(event_date - timedelta(minutes=30), event_date + timedelta(minutes=30))
    )
    if event_id:
        time_conflicts = time_conflicts.filter(Event.id != event_id)
    
    all_conflicts = list(conflicting_events)
    for e in time_conflicts:
        if e not in all_conflicts:
            all_conflicts.append(e)
    
    return all_conflicts


@events_bp.route('/')
@login_required
def index():
    """Main events listing page"""
    from app import db
    now = datetime.utcnow()
    
    # Get all approved events
    events = Event.query.filter_by(status='approved').order_by(Event.start_time.desc()).all()
    
    return render_template('events/index.html', events=events)


@events_bp.route('/calendar')
@login_required
def calendar():
    from app import db
    now = datetime.utcnow()
    
    # Auto-complete events that have passed their end date
    # An event is past if its event_date is in the past
    past_events = Event.query.filter(
        Event.status == 'approved',
        Event.event_date < now
    ).all()
    
    for event in past_events:
        event.status = 'completed'
    
    if past_events:
        db.session.commit()
    
    # Get all approved/ongoing events (not completed ones) for calendar display
    # Also include upcoming events that haven't started yet
    events = Event.query.filter(Event.status.in_(['approved', 'ongoing'])).all()
    
    # Format for FullCalendar
    events_data = []
    for e in events:
        event_type = 'Team Event' if e.requires_club else 'Open Event'
        # Color coding based on status
        color = '#10b981' if e.status == 'approved' else '#f59e0b'
        
        # Safely handle date serialization
        start_str = e.event_date.isoformat() if e.event_date else None
        end_str = e.end_date.isoformat() if e.end_date else None
        
        events_data.append({
            'id': e.id,
            'title': e.event_name,
            'start': start_str,
            'end': end_str,
            'url': f'/events/{e.id}',
            'color': color,
            'status': e.status,
            'extendedProps': {'type': event_type, 'location': e.location or ''}
        })
    return render_template('events/calendar.html', events=events_data)

@events_bp.route('/<int:event_id>')
def detail(event_id):
    event = Event.query.get_or_404(event_id)
    if event.status == 'pending':
        # Non-admin users can't see pending events
        if not current_user or current_user.role != 'admin':
            return 'Event not found', 404
    
    # Get attendance count
    attendance_count = EventAttendance.query.filter_by(event_id=event_id, is_attended=True).count()
    registered_count = EventAttendance.query.filter_by(event_id=event_id).count()
    
    return render_template('events/detail.html', event=event, 
                         attendance_count=attendance_count,
                         registered_count=registered_count)

@events_bp.route('/create', methods=['GET','POST'])
@login_required
def create():
    # Only leaders and admins can create events
    if current_user.role not in ['leader', 'admin']:
        flash('Only club leaders can create events', 'danger')
        return redirect('/events/calendar')
    
    # Show all active clubs to any leader (not just clubs they created)
    clubs = Club.query.filter_by(status='active').all()
    
    if request.method == 'POST':
        event_name = request.form.get('event_name')
        description = request.form.get('description')
        event_date = request.form.get('event_date')
        end_date = request.form.get('end_date')  # Optional end date
        location = request.form.get('location')
        max_attendees = request.form.get('max_attendees')
        requires_club = request.form.get('requires_club') == 'on'
        min_club_members = request.form.get('min_club_members') if requires_club else None
        max_club_members = request.form.get('max_club_members') if requires_club else None
        club_id = request.form.get('club_id') if request.form.get('club_id') else None
        
        try:
            event_dt = datetime.fromisoformat(event_date.replace('T', ' '))
            end_dt = datetime.fromisoformat(end_date.replace('T', ' ')) if end_date else None
        except:
            flash('Invalid date format', 'danger')
            return redirect('/events/create')
        
        # Check for conflicts
        end_dt_for_check = end_dt if end_dt else event_dt + timedelta(hours=2)
        conflicts = check_event_conflicts(event_dt, end_dt_for_check, location)
        
        if conflicts:
            conflict_names = ', '.join([c.event_name for c in conflicts[:3]])
            flash(f'⚠️ Warning: This event conflicts with existing events: {conflict_names}', 'warning')
            # Continue with creation but warn user
        
        # Verify club exists if specified (allow any leader to use any club)
        if club_id:
            club = Club.query.get(club_id)
            if not club:
                flash('Club not found', 'danger')
                return redirect('/events/create')
        
        new_event = Event(
            event_name=event_name,
            description=description,
            created_by=current_user.id,
            event_date=event_dt,
            end_date=end_dt,
            location=location,
            max_attendees=int(max_attendees) if max_attendees else None,
            requires_club=requires_club,
            min_club_members=int(min_club_members) if min_club_members else None,
            max_club_members=int(max_club_members) if max_club_members else None,
            club_id=int(club_id) if club_id else None,
            status='pending'  # Events need admin approval
        )
        from app import db
        db.session.add(new_event)
        db.session.commit()
        
        # Send notifications to relevant users
        try:
            from routes.notifications import send_event_notification
            # Notify all users about the new event
            all_users = User.query.all()
            user_ids = [u.id for u in all_users[:100]]  # Limit to 100
            send_event_notification(new_event, user_ids)
        except:
            pass  # Don't fail if notifications fail
        
        flash('Event submitted for admin approval!', 'success')
        return redirect(f'/events/calendar')
    
    return render_template('events/create.html', clubs=clubs)

@events_bp.route('/<int:event_id>/edit', methods=['GET','POST'])
@login_required
def edit(event_id):
    event = Event.query.get_or_404(event_id)
    if event.created_by != current_user.id:
        return 'Unauthorized', 403
    
    clubs = Club.query.filter_by(created_by=current_user.id).all()
    
    if request.method == 'POST':
        event.event_name = request.form.get('event_name')
        event.description = request.form.get('description')
        event.location = request.form.get('location')
        event_date = request.form.get('event_date')
        end_date = request.form.get('end_date')
        
        try:
            event.event_date = datetime.fromisoformat(event_date.replace('T', ' '))
            event.end_date = datetime.fromisoformat(end_date.replace('T', ' ')) if end_date else None
        except:
            flash('Invalid date format', 'danger')
            return redirect(f'/events/{event.id}/edit')
        
        # Check for conflicts when editing
        end_dt_for_check = event.end_date if event.end_date else event.event_date + timedelta(hours=2)
        conflicts = check_event_conflicts(event.event_date, end_dt_for_check, event.location, event_id=event.id)
        
        if conflicts:
            conflict_names = ', '.join([c.event_name for c in conflicts[:3]])
            flash(f'⚠️ Warning: This event conflicts with: {conflict_names}', 'warning')
        
        # Update event requirements
        event.requires_club = request.form.get('requires_club') == 'on'
        if event.requires_club:
            event.min_club_members = int(request.form.get('min_club_members')) if request.form.get('min_club_members') else None
            event.max_club_members = int(request.form.get('max_club_members')) if request.form.get('max_club_members') else None
        
        max_attendees = request.form.get('max_attendees')
        event.max_attendees = int(max_attendees) if max_attendees else None
        from app import db
        db.session.commit()
        flash('Event updated successfully!', 'success')
        return redirect(f'/events/{event.id}')
    
    return render_template('events/edit.html', event=event, clubs=clubs)

# API: Check conflicts - Checks if a new event conflicts with existing events at same location/time
@events_bp.route('/api/check-conflicts')
@login_required
def check_conflicts_api():
    """API endpoint to check for event conflicts in real-time"""
    event_date = request.args.get('event_date')
    location = request.args.get('location')
    event_id = request.args.get('event_id')
    
    if not event_date or not location:
        return jsonify({'conflicts': []})
    
    try:
        event_dt = datetime.fromisoformat(event_date.replace('T', ' '))
        end_dt = event_dt + timedelta(hours=2)
        
        conflicts = check_event_conflicts(
            event_dt, end_dt, location, 
            event_id=int(event_id) if event_id else None
        )
        
        return jsonify({
            'conflicts': [{
                'id': c.id,
                'name': c.event_name,
                'date': c.event_date.strftime('%B %d, %Y %I:%M %p'),
                'location': c.location
            } for c in conflicts]
        })
    except Exception as e:
        return jsonify({'error': str(e), 'conflicts': []})

@events_bp.route('/<int:event_id>/join', methods=['POST'])
@login_required
def join(event_id):
    """Join an event - individually or as a club team"""
    event = Event.query.get_or_404(event_id)
    
    if event.status != 'approved':
        flash('This event is not open for registration', 'danger')
        return redirect(f'/events/{event_id}')
    
    # Check attendee limit
    current_attendees = EventAttendance.query.filter_by(event_id=event_id).count()
    if event.max_attendees and current_attendees >= event.max_attendees:
        flash('Event is full', 'danger')
        return redirect(f'/events/{event_id}')
    
    if event.requires_club:
        # User is joining as part of a club
        club_id = request.form.get('club_id')
        if not club_id:
            flash('Please select a club', 'danger')
            return redirect(f'/events/{event_id}')
        
        club = Club.query.get_or_404(club_id)
        # Check user is member of this club
        membership = Membership.query.filter_by(user_id=current_user.id, club_id=club_id).first()
        if not membership:
            flash('You are not a member of this club', 'danger')
            return redirect(f'/events/{event_id}')
        
        # Get all club members
        club_members = User.query.join(Membership).filter(Membership.club_id == club_id).all()
        
        # Check min/max club members constraints
        if event.min_club_members and len(club_members) < event.min_club_members:
            flash(f'Club must have at least {event.min_club_members} members to participate', 'danger')
            return redirect(f'/events/{event_id}')
        
        if event.max_club_members and len(club_members) > event.max_club_members:
            flash(f'Club can have maximum {event.max_club_members} members for this event', 'danger')
            return redirect(f'/events/{event_id}')
        
        # Auto-add all club members to event
        from app import db
        added_count = 0
        for member in club_members:
            # Check if already attending
            existing = EventAttendance.query.filter_by(event_id=event_id, user_id=member.id).first()
            if not existing:
                event.attendees.append(member)
                # Create attendance record with QR code
                EventAttendance.create_for_registration(event_id, member.id)
                added_count += 1
                
                # Notify student
                try:
                    Notification.notify_student_joined_event(member, event)
                except:
                    pass
        
        db.session.commit()
        
        # Notify leader
        try:
            Notification.notify_leader_event_joined(event, current_user)
        except:
            pass
        
        flash(f'You and {added_count-1} club members joined the event!', 'success')
    else:
        # Individual registration
        existing = EventAttendance.query.filter_by(event_id=event_id, user_id=current_user.id).first()
        if not existing:
            from app import db
            event.attendees.append(current_user)
            # Create attendance record with QR code
            EventAttendance.create_for_registration(event_id, current_user.id)
            db.session.commit()
            
            # Notify student
            try:
                Notification.notify_student_joined_event(current_user, event)
            except:
                pass
            
            # Notify event leader
            try:
                Notification.notify_leader_event_joined(event, current_user)
            except:
                pass
            
            flash('Successfully joined event! QR code generated.', 'success')
        else:
            flash('You are already registered for this event', 'info')
    
    return redirect(f'/events/{event_id}')

@events_bp.route('/<int:event_id>/qr-code')
@login_required
def get_qr_code(event_id):
    """Display QR code for student registration"""
    event = Event.query.get_or_404(event_id)
    attendance = EventAttendance.query.filter_by(event_id=event_id, user_id=current_user.id).first()
    
    if not attendance:
        flash('You are not registered for this event', 'danger')
        return redirect(f'/events/{event_id}')
    
    # Generate QR code image
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(attendance.qr_code)
    qr.make(fit=True)
    
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64 for embedding in HTML
    buffer = BytesIO()
    qr_img.save(buffer, format='PNG')
    buffer.seek(0)
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return render_template('events/qr-code.html', 
                         event=event, 
                         attendance=attendance,
                         qr_image=qr_base64)

@events_bp.route('/<int:event_id>/attendance')
@login_required
def attendance(event_id):
    """Event attendance page for leaders to check in students"""
    event = Event.query.get_or_404(event_id)
    
    # Only event creator (leader) can access this
    if event.created_by != current_user.id and current_user.role != 'admin':
        flash('You do not have permission to view this page', 'danger')
        return redirect(f'/events/{event_id}')
    
    # Get all registered attendees
    attendances = EventAttendance.query.filter_by(event_id=event_id).all()
    
    # Calculate attendance rate
    total_registered = len(attendances)
    total_attended = sum(1 for a in attendances if a.is_attended)
    attendance_rate = (total_attended / total_registered * 100) if total_registered > 0 else 0
    
    return render_template('events/attendance.html', 
                         event=event, 
                         attendances=attendances,
                         total_registered=total_registered,
                         total_attended=total_attended,
                         attendance_rate=attendance_rate)

# API: Scan QR - Processes scanned QR code from event attendance and returns student info
@events_bp.route('/api/scan-qr', methods=['POST'])
@login_required
def scan_qr():
    """Process scanned QR code and return student info"""
    from app import db
    data = request.get_json()
    qr_data = data.get('qr_data', '')
    
    # Parse QR code data: event_id|user_id|token
    try:
        parts = qr_data.split('|')
        if len(parts) != 3:
            return jsonify({'success': False, 'error': 'Invalid QR code format'}), 400
        
        event_id, user_id, token = int(parts[0]), int(parts[1]), parts[2]
    except:
        return jsonify({'success': False, 'error': 'Invalid QR code data'}), 400
    
    # Verify event exists and current user is the leader
    event = Event.query.get(event_id)
    if not event:
        return jsonify({'success': False, 'error': 'Event not found'}), 404
    
    if event.created_by != current_user.id and current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    # Get attendance record
    attendance = EventAttendance.query.filter_by(
        event_id=event_id, 
        user_id=user_id, 
        qr_token=token
    ).first()
    
    if not attendance:
        return jsonify({'success': False, 'error': 'Invalid QR code'}), 404
    
    # Return student and event information
    return jsonify({
        'success': True,
        'student': {
            'id': attendance.user.id,
            'name': f"{attendance.user.first_name} {attendance.user.last_name}",
            'email': attendance.user.email,
            'student_number': attendance.user.student_number
        },
        'event': {
            'id': event.id,
            'name': event.event_name,
            'date': event.event_date.strftime('%b %d, %Y %I:%M %p'),
            'location': event.location
        },
        'attendance_id': attendance.id,
        'is_attended': attendance.is_attended
    })

# API: Mark attended - Marks a student as attended/check-in at an event
@events_bp.route('/api/mark-attended', methods=['POST'])
@login_required
def mark_attended():
    """Mark student as attended"""
    from app import db
    data = request.get_json()
    attendance_id = data.get('attendance_id')
    
    attendance = EventAttendance.query.get(attendance_id)
    if not attendance:
        return jsonify({'success': False, 'error': 'Attendance record not found'}), 404
    
    event = attendance.event
    if event.created_by != current_user.id and current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    attendance.is_attended = True
    attendance.checked_in_at = datetime.utcnow()
    from app import db
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f"{attendance.user.first_name} {attendance.user.last_name} marked as attended"
    })

# API: Attendance stats - Returns attendance statistics (registered, attended, rate) for an event
@events_bp.route('/api/attendance-stats/<int:event_id>')
@login_required
def attendance_stats(event_id):
    """Get attendance statistics for an event"""
    event = Event.query.get_or_404(event_id)
    
    if event.created_by != current_user.id and current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    attendances = EventAttendance.query.filter_by(event_id=event_id).all()
    
    total_registered = len(attendances)
    total_attended = sum(1 for a in attendances if a.is_attended)
    attendance_rate = (total_attended / total_registered * 100) if total_registered > 0 else 0
    
    return jsonify({
        'total_registered': total_registered,
        'total_attended': total_attended,
        'attendance_rate': round(attendance_rate, 1),
        'max_attendees': event.max_attendees,
        'spots_remaining': (event.max_attendees - total_registered) if event.max_attendees else None
    })


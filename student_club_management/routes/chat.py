from flask import Blueprint, render_template, request, redirect, flash, jsonify
from flask_login import login_required, current_user
from flask_wtf.csrf import CSRFError, CSRFProtect
from app import db
from models.chat import ChatConversation, ChatMessage, ChatRequest
from models.club import Club
from models.user import User
from models.membership import Membership
from models.notification import Notification

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')

# Get CSRF instance from app
def get_csrf():
    from flask import current_app
    return current_app.extensions['csrf']

@chat_bp.route('/')
@login_required
def index():
    """Show all conversations for current user"""
    # Get all conversations where user is participant
    conversations = ChatConversation.query.filter(
        (ChatConversation.participant_one == current_user.id) | 
        (ChatConversation.participant_two == current_user.id)
    ).order_by(ChatConversation.updated_at.desc()).all()
    
    # Get pending requests (for leaders)
    pending_requests = []
    if current_user.role == 'leader':
        # Get clubs where user is leader
        leader_clubs = Club.query.filter_by(created_by=current_user.id).all()
        club_ids = [c.id for c in leader_clubs]
        pending_requests = ChatRequest.query.filter(
            ChatRequest.club_id.in_(club_ids),
            ChatRequest.status == 'pending'
        ).all()
    
    return render_template('chat/index.html', 
                         conversations=conversations,
                         pending_requests=pending_requests)

@chat_bp.route('/conversations')
@login_required
def conversations():
    """Get all conversations as JSON"""
    conversations = ChatConversation.query.filter(
        (ChatConversation.participant_one == current_user.id) | 
        (ChatConversation.participant_two == current_user.id)
    ).order_by(ChatConversation.updated_at.desc()).all()
    
    return jsonify([{
        'id': c.id,
        'subject': c.subject,
        'other_user': c.get_other_participant(current_user.id).first_name + ' ' + c.get_other_participant(current_user.id).last_name,
        'other_user_id': c.get_other_participant(current_user.id).id,
        'unread_count': c.get_unread_count(current_user.id),
        'updated_at': c.updated_at.strftime('%b %d, %Y %I:%M %p'),
        'status': c.status
    } for c in conversations])

@chat_bp.route('/conversation/<int:conversation_id>')
@login_required
def view_conversation(conversation_id):
    """View a specific conversation"""
    conversation = ChatConversation.query.get_or_404(conversation_id)
    
    # Verify user is participant
    if conversation.participant_one != current_user.id and conversation.participant_two != current_user.id:
        flash('You do not have permission to view this conversation', 'danger')
        return redirect('/chat')
    
    # Mark messages as read
    ChatMessage.query.filter_by(
        conversation_id=conversation_id,
        recipient_id=current_user.id,
        is_read=False
    ).update({'is_read': True})
    db.session.commit()
    
    # Get other participant
    other_user = conversation.get_other_participant(current_user.id)
    
    return render_template('chat/conversation.html', 
                         conversation=conversation,
                         other_user=other_user)

# API: Get messages for a conversation - Returns all messages in a chat conversation as JSON
@chat_bp.route('/api/conversation/<int:conversation_id>/messages')
@login_required
def get_messages(conversation_id):
    """Get messages for a conversation as JSON"""
    conversation = ChatConversation.query.get_or_404(conversation_id)
    
    # Verify user is participant
    if conversation.participant_one != current_user.id and conversation.participant_two != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    messages = ChatMessage.query.filter_by(conversation_id=conversation_id).order_by(ChatMessage.created_at.asc()).all()
    
    # Mark messages as read
    ChatMessage.query.filter_by(
        conversation_id=conversation_id,
        recipient_id=current_user.id,
        is_read=False
    ).update({'is_read': True})
    db.session.commit()
    
    return jsonify([{
        'id': m.id,
        'sender_id': m.sender_id,
        'sender_name': m.sender.first_name + ' ' + m.sender.last_name,
        'message': m.message,
        'is_read': m.is_read,
        'is_mine': m.sender_id == current_user.id,
        'created_at': m.created_at.strftime('%b %d, %Y %I:%M %p')
    } for m in messages])

# API: Send message - Allows user to send a message in an existing conversation
@chat_bp.route('/api/conversation/<int:conversation_id>/send', methods=['POST'])
@login_required
def send_message(conversation_id):
    """Send a message in a conversation"""
    conversation = ChatConversation.query.get_or_404(conversation_id)
    
    # Verify user is participant
    if conversation.participant_one != current_user.id and conversation.participant_two != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    message_text = data.get('message', '').strip()
    
    if not message_text:
        return jsonify({'error': 'Message cannot be empty'}), 400
    
    # Determine recipient
    if conversation.participant_one == current_user.id:
        recipient_id = conversation.participant_two
    else:
        recipient_id = conversation.participant_one
    
    # Create message
    message = ChatMessage(
        conversation_id=conversation_id,
        sender_id=current_user.id,
        recipient_id=recipient_id,
        message=message_text
    )
    db.session.add(message)
    
    # Update conversation timestamp
    conversation.updated_at = db.func.now()
    
    # Send notification to recipient
    try:
        other_user = User.query.get(recipient_id)
        Notification.send_to_user(
            user_id=recipient_id,
            title=f"💬 New message from {current_user.first_name} {current_user.last_name}",
            message=message_text[:100] + "..." if len(message_text) > 100 else message_text,
            notification_type='chat',
            link=f'/chat/conversation/{conversation_id}'
        )
    except:
        pass
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': {
            'id': message.id,
            'sender_id': message.sender_id,
            'sender_name': current_user.first_name + ' ' + current_user.last_name,
            'message': message.message,
            'created_at': message.created_at.strftime('%b %d, %Y %I:%M %p')
        }
    })

@chat_bp.route('/start', methods=['GET', 'POST'])
@login_required
def start_conversation():
    """Start a new conversation with a user"""
    if request.method == 'POST':
        recipient_id = request.form.get('recipient_id')
        subject = request.form.get('subject', '')
        initial_message = request.form.get('message', '')
        
        if not recipient_id:
            flash('Please select a recipient', 'warning')
            return redirect('/chat/start')
        
        if int(recipient_id) == current_user.id:
            flash('You cannot start a conversation with yourself', 'warning')
            return redirect('/chat/start')
        
        # Always create a new conversation (allow multiple conversations with same user)
        conversation = ChatConversation(
            created_by=current_user.id,
            participant_one=current_user.id,
            participant_two=int(recipient_id),
            subject=subject
        )
        db.session.add(conversation)
        db.session.flush()  # Get the ID
        
        # Add initial message if provided
        if initial_message:
            message = ChatMessage(
                conversation_id=conversation.id,
                sender_id=current_user.id,
                recipient_id=int(recipient_id),
                message=initial_message
            )
            db.session.add(message)
            
            # Send notification
            try:
                recipient = User.query.get(int(recipient_id))
                Notification.send_to_user(
                    user_id=int(recipient_id),
                    title=f"💬 New message from {current_user.first_name} {current_user.last_name}",
                    message=initial_message[:100] + "..." if len(initial_message) > 100 else initial_message,
                    notification_type='chat',
                    link=f'/chat/conversation/{conversation.id}'
                )
            except:
                pass
        
        db.session.commit()
        flash('Conversation started!', 'success')
        return redirect(f'/chat/conversation/{conversation.id}')
    
    # Get potential recipients (leaders for students, students for leaders)
    if current_user.role == 'student':
        # Get all leaders
        recipients = User.query.filter_by(role='leader').all()
    elif current_user.role == 'leader':
        # Get members of user's clubs
        clubs = Club.query.filter_by(created_by=current_user.id).all()
        club_ids = [c.id for c in clubs]
        members = User.query.join(Membership).filter(
            Membership.club_id.in_(club_ids),
            Membership.status == 'active'
        ).all()
        recipients = members
    else:
        recipients = User.query.filter(User.id != current_user.id).all()
    
    return render_template('chat/start.html', recipients=recipients)

# ==================== Chat Requests (Leave/Move Club) ====================

@chat_bp.route('/request/leave/<int:club_id>', methods=['POST'])
@login_required
def request_leave(club_id):
    """Student requests to leave a club"""
    club = Club.query.get_or_404(club_id)
    message = request.form.get('message', '')
    
    # Check if already a member
    membership = Membership.query.filter_by(user_id=current_user.id, club_id=club_id).first()
    if not membership:
        flash('You are not a member of this club', 'warning')
        return redirect(f'/clubs/{club_id}')
    
    # Check if leader
    if club.created_by == current_user.id:
        flash('Club leader cannot leave their own club', 'warning')
        return redirect(f'/clubs/{club_id}')
    
    # Create request
    chat_request = ChatRequest(
        user_id=current_user.id,
        club_id=club_id,
        request_type='leave',
        message=message
    )
    db.session.add(chat_request)
    db.session.commit()
    
    # Notify leader
    try:
        Notification.notify_leader_student_request(
            club, current_user, 'leave club', 
            message if message else 'I would like to leave this club.'
        )
    except:
        pass
    
    flash('Your leave request has been sent to the club leader.', 'info')
    return redirect(f'/clubs/{club_id}')

@chat_bp.route('/request/move', methods=['POST'])
@login_required
def request_move():
    """Student requests to move to another club"""
    from_club_id = request.form.get('from_club_id')
    to_club_id = request.form.get('to_club_id')
    message = request.form.get('message', '')
    
    if not from_club_id or not to_club_id:
        flash('Please select both clubs', 'warning')
        return redirect('/clubs')
    
    if from_club_id == to_club_id:
        flash('Please select different clubs', 'warning')
        return redirect('/clubs')
    
    from_club = Club.query.get(from_club_id)
    to_club = Club.query.get(to_club_id)
    
    if not from_club or not to_club:
        flash('Invalid clubs selected', 'warning')
        return redirect('/clubs')
    
    # Check membership in source club
    membership = Membership.query.filter_by(user_id=current_user.id, club_id=from_club_id).first()
    if not membership:
        flash('You are not a member of the source club', 'warning')
        return redirect('/clubs')
    
    # Check if already member of target
    existing = Membership.query.filter_by(user_id=current_user.id, club_id=to_club_id).first()
    if existing:
        flash('You are already a member of the target club', 'warning')
        return redirect('/clubs')
    
    # Create request
    chat_request = ChatRequest(
        user_id=current_user.id,
        club_id=int(from_club_id),
        target_club_id=int(to_club_id),
        request_type='move',
        message=message if message else f'I would like to move to {to_club.club_name}.'
    )
    db.session.add(chat_request)
    db.session.commit()
    
    # Notify source club leader
    try:
        Notification.notify_leader_student_request(
            from_club, current_user, f'move to {to_club.club_name}',
            message if message else f'I would like to move to {to_club.club_name}.'
        )
    except:
        pass
    
    flash(f'Your move request has been sent to the {from_club.club_name} leader.', 'info')
    return redirect('/clubs')

# Leader: View requests
@chat_bp.route('/requests')
@login_required
def view_requests():
    """Leader views pending requests from students"""
    if current_user.role != 'leader':
        flash('Only club leaders can view requests', 'warning')
        return redirect('/dashboard')
    
    # Get clubs where user is leader
    clubs = Club.query.filter_by(created_by=current_user.id).all()
    club_ids = [c.id for c in clubs]
    
    pending_requests = ChatRequest.query.filter(
        ChatRequest.club_id.in_(club_ids),
        ChatRequest.status == 'pending'
    ).order_by(ChatRequest.created_at.desc()).all()
    
    processed_requests = ChatRequest.query.filter(
        ChatRequest.club_id.in_(club_ids),
        ChatRequest.status != 'pending'
    ).order_by(ChatRequest.created_at.desc()).limit(20).all()
    
    return render_template('chat/requests.html',
                         pending_requests=pending_requests,
                         processed_requests=processed_requests)

# Leader: Process request (approve/deny)
@chat_bp.route('/request/<int:request_id>/process', methods=['POST'])
@login_required
def process_request(request_id):
    """Leader approves or denies a request"""
    if current_user.role != 'leader':
        flash('Only club leaders can process requests', 'warning')
        return redirect('/dashboard')
    
    chat_request = ChatRequest.query.get_or_404(request_id)
    
    # Verify leader owns the club
    club = Club.query.get(chat_request.club_id)
    if club.created_by != current_user.id:
        flash('You do not have permission to process this request', 'danger')
        return redirect('/chat/requests')
    
    if chat_request.status != 'pending':
        flash('This request has already been processed', 'warning')
        return redirect('/chat/requests')
    
    action = request.form.get('action')  # approve or deny
    
    if action == 'approve':
        if chat_request.request_type == 'leave':
            # Remove member from club
            membership = Membership.query.filter_by(
                user_id=chat_request.user_id,
                club_id=chat_request.club_id
            ).first()
            if membership:
                db.session.delete(membership)
                
                # Notify student
                try:
                    Notification.notify_student_request_processed(
                        chat_request.user, club, 'leave', True
                    )
                except:
                    pass
                
                flash('Leave request approved', 'success')
        
        elif chat_request.request_type == 'move':
            # Remove from old club
            old_membership = Membership.query.filter_by(
                user_id=chat_request.user_id,
                club_id=chat_request.club_id
            ).first()
            
            if old_membership:
                db.session.delete(old_membership)
            
            # Add to new club
            target_club = Club.query.get(chat_request.target_club_id)
            if target_club and target_club.status == 'active':
                # Check capacity
                if not target_club.max_members or len(target_club.members) < target_club.max_members:
                    new_membership = Membership(
                        user_id=chat_request.user_id,
                        club_id=chat_request.target_club_id
                    )
                    db.session.add(new_membership)
                    
                    # Notify student
                    try:
                        Notification.notify_student_moved_to_club(
                            chat_request.user, club, target_club
                        )
                    except:
                        pass
                    
                    flash(f'Student moved to {target_club.club_name}', 'success')
                else:
                    flash('Target club is full', 'warning')
            else:
                flash('Target club not available', 'warning')
        
        chat_request.status = 'approved'
    
    elif action == 'deny':
        chat_request.status = 'denied'
        
        # Notify student
        try:
            Notification.notify_student_request_processed(
                chat_request.user, club, chat_request.request_type, False
            )
        except:
            pass
        
        flash('Request denied', 'info')
    
    chat_request.reviewed_by = current_user.id
    chat_request.reviewed_at = db.func.now()
    db.session.commit()
    
    return redirect('/chat/requests')

# API: Get unread count - Returns total number of unread chat messages for real-time badge
@chat_bp.route('/api/unread-count')
@login_required
def unread_count():
    """Get total unread message count"""
    try:
        count = ChatMessage.query.filter_by(
            recipient_id=current_user.id,
            is_read=False
        ).count()
        return jsonify({'count': count})
    except Exception as e:
        print(f"❌ Chat API error: {e}")
        return jsonify({'count': 0})

# API: Search users - Returns users matching search query for starting conversations
@chat_bp.route('/api/search-users')
@login_required
def search_users():
    """Search users by name or email"""
    query = request.args.get('q', '').strip()
    
    if not query or len(query) < 2:
        return jsonify([])
    
    # Search by name or email
    users = User.query.filter(
        (User.first_name.ilike(f'%{query}%')) |
        (User.last_name.ilike(f'%{query}%')) |
        (User.email.ilike(f'%{query}%'))
    ).filter(User.id != current_user.id).limit(20).all()
    
    return jsonify([{
        'id': u.id,
        'name': f"{u.first_name} {u.last_name}",
        'email': u.email,
        'role': u.role
    } for u in users])

# API: Get latest messages - Returns recent conversations for chat dropdown/preview
@chat_bp.route('/api/latest')
@login_required
def latest_messages():
    """Get latest messages for dropdown"""
    # Get conversations
    conversations = ChatConversation.query.filter(
        (ChatConversation.participant_one == current_user.id) | 
        (ChatConversation.participant_two == current_user.id)
    ).order_by(ChatConversation.updated_at.desc()).limit(5).all()
    
    result = []
    for c in conversations:
        other_user = c.get_other_participant(current_user.id)
        unread = c.get_unread_count(current_user.id)
        
        # Get last message
        last_msg = ChatMessage.query.filter_by(conversation_id=c.id).order_by(
            ChatMessage.created_at.desc()
        ).first()
        
        result.append({
            'conversation_id': c.id,
            'other_user_name': other_user.first_name + ' ' + other_user.last_name,
            'other_user_id': other_user.id,
            'last_message': last_msg.message[:50] + '...' if last_msg and len(last_msg.message) > 50 else (last_msg.message if last_msg else ''),
            'unread_count': unread,
            'updated_at': c.updated_at.strftime('%b %d, %I:%M %p')
        })
    
    return jsonify(result)


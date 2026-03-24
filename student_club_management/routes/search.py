from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import User, Club, Announcement, Event, Membership
from app import db
from sqlalchemy import or_, and_

search_bp = Blueprint('search', __name__, url_prefix='/search')

@search_bp.route('/')
@login_required
def search():
    """Global search functionality"""
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'all')
    
    if not query:
        return render_template('search/results.html', query='', results=[], search_type=search_type)
    
    results = []
    
    # Search announcements
    if search_type in ['all', 'announcements']:
        announcements = Announcement.query.filter(
            or_(
                Announcement.title.ilike(f'%{query}%'),
                Announcement.content.ilike(f'%{query}%')
            )
        ).limit(10).all()
        
        for announcement in announcements:
            results.append({
                'type': 'announcement',
                'title': announcement.title,
                'description': announcement.content[:200] + '...',
                'url': f"/announcements/{announcement.id}",
                'date': announcement.created_at,
                'icon': 'bullhorn'
            })
    
    # Search clubs
    if search_type in ['all', 'clubs']:
        clubs = Club.query.filter(
            or_(
                Club.club_name.ilike(f'%{query}%'),
                Club.description.ilike(f'%{query}%')
            )
        ).limit(10).all()
        
        for club in clubs:
            results.append({
                'type': 'club',
                'title': club.club_name,
                'description': club.description[:200] + '...',
                'url': f"/clubs/{club.id}",
                'date': club.created_at,
                'icon': 'users'
            })
    
    # Search users (admin/leader only)
    if search_type in ['all', 'users'] and current_user.role in ['admin', 'leader']:
        users = User.query.filter(
            or_(
                User.name.ilike(f'%{query}%'),
                User.email.ilike(f'%{query}%')
            )
        ).limit(10).all()
        
        for user in users:
            results.append({
                'type': 'user',
                'title': user.name,
                'description': user.email,
                'url': f"/users/{user.id}",
                'date': user.created_at,
                'icon': 'user'
            })
    
    # Sort by date
    results.sort(key=lambda x: x['date'], reverse=True)
    
    return render_template('search/results.html', query=query, results=results, search_type=search_type)

@search_bp.route('/api/suggestions')
@login_required
def search_suggestions():
    """Get search suggestions for autocomplete"""
    query = request.args.get('q', '').strip()
    
    if len(query) < 2:
        return jsonify([])
    
    suggestions = []
    
    # Club suggestions
    clubs = Club.query.filter(Club.club_name.ilike(f'%{query}%')).limit(5).all()
    for club in clubs:
        suggestions.append({
            'text': club.club_name,
            'type': 'club',
            'url': f"/clubs/{club.id}"
        })
    
    # Announcement suggestions
    announcements = Announcement.query.filter(Announcement.title.ilike(f'%{query}%')).limit(5).all()
    for announcement in announcements:
        suggestions.append({
            'text': announcement.title,
            'type': 'announcement',
            'url': f"/announcements/{announcement.id}"
        })
    
    return jsonify(suggestions)

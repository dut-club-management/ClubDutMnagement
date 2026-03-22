db = None


def init_db(app):
    from app import db
    with app.app_context():
        db.create_all()

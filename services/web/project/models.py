from . import db
from datetime import datetime, timedelta


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    platform_id = db.Column(db.String(120), unique=True, nullable=False)
    firstname = db.Column(db.String(120), nullable=False)
    lastname = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    pic = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    type = db.Column(db.String(50))  # For inheritance

    deepdive_results = db.relationship('DeepdiveResult', backref='user', lazy=True, cascade="all, delete-orphan")

    __mapper_args__ = {
        'polymorphic_identity': 'user',
        'polymorphic_on': type
    }


class DeepdiveResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Text, db.ForeignKey('user.id'))
    # store links
    twitter_links = db.Column(db.Text)
    linkedin_links = db.Column(db.Text)
    reddit_links = db.Column(db.Text)
    facebook_links = db.Column(db.Text)
    instagram_links = db.Column(db.Text)
    tiktok_links = db.Column(db.Text)
    other_links = db.Column(db.Text)
    # sherlocked accounts
    possible_accounts = db.Column(db.Text)


class GoogleUser(User):
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'google',
    }


class LinkedinUser(User):
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    headline = db.Column(db.String(120), nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': 'linkedin',
    }


class FacebookUser(User):
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'facebook',
    }


def delete_old_entries():
    cutoff_time = datetime.utcnow() - timedelta(hours=24)
    old_user = User.query.filter(User.created_at < cutoff_time).all()

    for user in old_user:
        db.session.delete(user)

    db.session.commit()


from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'user'

    username = db.Column(db.String(80), primary_key=True)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False)

    user_media = db.relationship('UserMedia', back_populates='user', lazy=True, overlaps="media")
    media = db.relationship('Media', secondary='user_media', back_populates='users', lazy='dynamic', overlaps="user_media")

    def get_id(self):
        return self.username

    def __repr__(self):
        return f"<User {self.username}>"

class Media(db.Model):
    __tablename__ = 'media'

    title = db.Column(db.String(255), primary_key=True)
    creator = db.Column(db.String(255), nullable=False)
    genre = db.Column(db.String(100), nullable=False)
    release_date = db.Column(db.Date, nullable=False)
    media_tags = db.Column(db.Text)

    user_media_links = db.relationship('UserMedia', back_populates='media', lazy=True, overlaps="users")
    users = db.relationship('User', secondary='user_media', back_populates='media', lazy='dynamic', overlaps="user_media_links")

    def get_metadata_list(self):
        return [tag.strip() for tag in self.media_tags.split(',')] if self.media_tags else []

    def set_metadata_list(self, tags):
        self.media_tags = ','.join([tag.strip() for tag in tags])

    def __repr__(self):
        return f"<Media {self.title} by {self.creator}>"

class UserMedia(db.Model):
    __tablename__ = 'user_media'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(80), db.ForeignKey('user.username'), nullable=False)
    media_title = db.Column(db.String(255), db.ForeignKey('media.title'), nullable=False)
    status = db.Column(db.String(50), nullable=False)

    user = db.relationship('User', back_populates='user_media', overlaps="media,users")
    media = db.relationship('Media', back_populates='user_media_links', overlaps="user_media,users")

    def __repr__(self):
        return f"<UserMedia {self.user_id} - {self.media_title} ({self.status})>"

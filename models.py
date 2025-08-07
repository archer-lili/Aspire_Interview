from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'user'

    username = db.Column(db.String(80), primary_key=True)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False)

    # Relationship to UserMedia (1-to-many)
    user_media = db.relationship(
        'UserMedia',
        back_populates='user',
        cascade='all, delete-orphan',
        lazy=True
    )

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

    # Relationship to UserMedia (1-to-many)
    user_media_links = db.relationship(
        'UserMedia',
        back_populates='media',
        cascade='all, delete-orphan',
        lazy=True
    )

    def get_metadata_list(self):
        return [tag.strip() for tag in self.media_tags.split(',')] if self.media_tags else []

    def set_metadata_list(self, tags):
        self.media_tags = ','.join([tag.strip() for tag in tags])

    def __repr__(self):
        return f"<Media {self.title} by {self.creator}>"


class UserMedia(db.Model):
    __tablename__ = 'user_media'

    # Option 1: Use surrogate primary key (id)
    id = db.Column(db.Integer, primary_key=True)

    # Foreign keys
    user_id = db.Column(db.String(80), db.ForeignKey('user.username', ondelete='CASCADE'), nullable=False)
    media_title = db.Column(db.String(255), db.ForeignKey('media.title', ondelete='CASCADE'), nullable=False)

    # Additional data in association table
    status = db.Column(db.String(50), nullable=False)  # "owned", "wishlist", etc.

    # Relationships
    user = db.relationship('User', back_populates='user_media')
    media = db.relationship('Media', back_populates='user_media_links')

    def __repr__(self):
        return f"<UserMedia {self.user_id} - {self.media_title} ({self.status})>"

    # --- Optional: If you want to enforce one user/media pair only ---
    # __table_args__ = (
    #     db.UniqueConstraint('user_id', 'media_title', name='uix_user_media'),
    # )

    # --- Optional: Use this instead of surrogate key for composite PK ---
    # user_id = db.Column(db.String(80), db.ForeignKey('user.username', ondelete='CASCADE'), primary_key=True)
    # media_title = db.Column(db.String(255), db.ForeignKey('media.title', ondelete='CASCADE'), primary_key=True)

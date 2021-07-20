from seal import db, login_manager
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


teams = db.Table(
    'teams',
    db.Column(
        'team_ID', db.Integer,
        db.ForeignKey('team.id'), primary_key=True
    ),
    db.Column(
        'user_ID', db.Integer,
        db.ForeignKey('user.id'), primary_key=True
    )
)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    image_file = db.Column(
        db.String(20), unique=True,
        nullable=False, default='default.jpg')
    password = db.Column(db.String(60), unique=True, nullable=False)
    teams = db.relationship(
        'Team', secondary=teams, lazy='subquery',
        backref=db.backref('members', lazy=True)
    )

    def __repr__(self):
        return f"User('{self.username}', '{self.image_file}')"


class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teamname = db.Column(db.String(20), unique=True, nullable=False)

    def __repr__(self):
        return f"Team('{self.teamname}')"

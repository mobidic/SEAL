from seal import db, login_manager
from flask_login import UserMixin


################################################################################
# Authentication


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


team2member = db.Table(
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
    mail = db.Column(db.String(40), unique=True, nullable=True)
    image_file = db.Column(
        db.String(20), unique=False,
        nullable=False, default='default.jpg')
    password = db.Column(db.String(60), unique=False, nullable=False)
    admin = db.Column(db.Boolean(), nullable=False, default=False)
    bioinfo = db.Column(db.Boolean(), nullable=False, default=False)
    technician = db.Column(db.Boolean(), nullable=False, default=False)
    biologist = db.Column(db.Boolean(), nullable=False, default=False)
    teams = db.relationship(
        'Team', secondary=team2member, lazy='subquery',
        backref=db.backref('members', lazy=True)
    )

    def __repr__(self):
        return f"User('{self.username}', '{self.image_file}')"


class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teamname = db.Column(db.String(20), unique=True, nullable=False)
    color = db.Column(db.String(7), unique=False, nullable=False, default="#95A5A6")

    def __repr__(self):
        return f"Team('{self.teamname}','{self.color}')"


################################################################################


################################################################################
# Patient

class Sample(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    samplename = db.Column(db.String(20), unique=False, nullable=False)
    analysed = db.Column(db.Boolean(), unique=False, nullable=False, default=False)

    def __repr__(self):
        return f"Sample('{self.samplename}','{self.analysed}')"


################################################################################

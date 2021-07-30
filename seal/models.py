from seal import db, login_manager
from flask_login import UserMixin


################################################################################
# Authentication


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


team2member = db.Table(
    'team2member',
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
# Analysis


var2sample = db.Table(
    'var2sample',
    db.Column(
        'variant_ID', db.Integer,
        db.ForeignKey('variant.id'), primary_key=True
    ),
    db.Column(
        'sample_ID', db.Integer,
        db.ForeignKey('sample.id'), primary_key=True
    ),
    db.Column(
        'depth', db.Integer, nullable=True, unique=False
    ),
    db.Column(
        'allelic_depth', db.Integer, nullable=True, unique=False
    ),
    db.Column(
        'analyse1', db.Boolean(), nullable=False, unique=False, default=False
    ),
    db.Column(
        'analyse2', db.Boolean(), nullable=False, unique=False, default=False
    ),
    db.Column(
        'reported', db.Boolean(), nullable=False, unique=False, default=False
    )
)


class Sample(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    samplename = db.Column(db.String(20), unique=False, nullable=False)
    analysed = db.Column(db.Boolean(), unique=False, nullable=False, default=False)
    variants = db.relationship(
        'Variant', secondary=var2sample, lazy='subquery',
        backref=db.backref('samples', lazy=True)
    )

    def __repr__(self):
        return f"Sample('{self.samplename}','{self.analysed}')"


class Variant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chr = db.Column(db.String(10), unique=False, nullable=False)
    pos = db.Column(db.Integer, unique=False, nullable=False)
    ref = db.Column(db.String(500), unique=False, nullable=False)
    alt = db.Column(db.String(500), unique=False, nullable=False)
    annotations = db.Column(db.JSON, nullable=True)

    __table_args__ = (
        db.UniqueConstraint('chr', 'pos', 'ref', 'alt', name='_varUC'),
    )

    def __repr__(self):
        return f"Variant('{self.chr}','{self.pos}','{self.ref}','{self.alt}')"


################################################################################

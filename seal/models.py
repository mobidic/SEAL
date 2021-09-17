from seal import db, login_manager
from flask_login import UserMixin
from sqlalchemy.orm import relationship

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
    filter_id = db.Column(db.Integer, db.ForeignKey('filter.id'), default=1)

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


class Sample(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    samplename = db.Column(db.String(20), unique=False, nullable=False)
    status = db.Column(db.Integer, unique=False, nullable=False, default=0)
    carrier = db.Column(db.Boolean(), default=False)
    index = db.Column(db.Boolean(), default=False)

    familyid = db.Column(db.Integer, db.ForeignKey('family.id'))
    family = relationship("Family", back_populates="samples")

    def __repr__(self):
        return f"Sample('{self.samplename}','{self.status}')"


class Family(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    family = db.Column(db.String(20), unique=True, nullable=False)
    samples = relationship("Sample")

    def __repr__(self):
        return f"Family('{self.family}')"


class Variant(db.Model):
    id = db.Column(db.Text, primary_key=True)
    chr = db.Column(db.String(10), unique=False, nullable=False)
    pos = db.Column(db.Integer, unique=False, nullable=False)
    ref = db.Column(db.String(500), unique=False, nullable=False)
    alt = db.Column(db.String(500), unique=False, nullable=False)
    annotations = db.Column(db.JSON, nullable=True)

    def __repr__(self):
        return f"Variant('{self.chr}','{self.pos}','{self.ref}','{self.alt}')"


class Var2Sample(db.Model):
    variant_ID = db.Column(db.Text, db.ForeignKey('variant.id'), primary_key=True)
    sample_ID = db.Column(db.Integer, db.ForeignKey('sample.id'), primary_key=True)
    depth = db.Column(db.Integer, nullable=True, unique=False)
    allelic_depth = db.Column(db.Integer, nullable=True, unique=False)
    analyse1 = db.Column(db.Boolean, nullable=False, unique=False)
    analyse2 = db.Column(db.Boolean, nullable=False, unique=False)
    reported = db.Column(db.Boolean, nullable=False, unique=False)

    sample = db.relationship(Sample, backref="variants")
    variant = db.relationship(Variant, backref="samples")

    def __repr__(self):
        return f"Var2Sample('{self.sample}','{self.variant}')"


class Filter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filtername = db.Column(db.String(20), unique=True, nullable=False)
    filter = db.Column(db.JSON, nullable=True)

    def __repr__(self):
        return f"{self.filtername}"


class Gene(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hgncname = db.Column(db.String(20), unique=True, nullable=False)
    hgncid = db.Column(db.String(20), unique=True, nullable=False)
    chromosome = db.Column(db.String(5))
    strand = db.Column(db.CHAR)
    transcripts = relationship("Transcript")

    def __repr__(self):
        return f"Gene('{self.hgncname}','{self.hgncid}')"


class Transcript(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    refSeq = db.Column(db.String(20), unique=True, nullable=False)
    canonical = db.Column(db.Boolean(), nullable=False, unique=False, default=False)
    refProt = db.Column(db.String(30))
    uniprot = db.Column(db.String(30))

    geneid = db.Column(db.Integer, db.ForeignKey('gene.id'))
    gene = relationship("Gene", back_populates="transcripts")

    def __repr__(self):
        return f"Transcript('{self.refSeq}','{self.canonical}')"


################################################################################

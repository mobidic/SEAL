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


var2sample = db.Table(
    'var2sample',
    db.Column(
        'variant_ID', db.Text,
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
    status = db.Column(db.Integer, unique=False, nullable=False, default=0)

    variants = db.relationship(
        'Variant', secondary=var2sample, lazy='subquery',
        backref=db.backref('samples', lazy=True)
    )

    def __repr__(self):
        return f"Sample('{self.samplename}','{self.status}')"


class Variant(db.Model):
    id = db.Column(db.Text, primary_key=True)
    chr = db.Column(db.String(10), unique=False, nullable=False)
    pos = db.Column(db.Integer, unique=False, nullable=False)
    ref = db.Column(db.String(500), unique=False, nullable=False)
    alt = db.Column(db.String(500), unique=False, nullable=False)
    annotations = db.Column(db.JSON, nullable=True)

    def __repr__(self):
        return f"Variant('{self.chr}','{self.pos}','{self.ref}','{self.alt}')"


class Filter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filtername = db.Column(db.String(20), unique=True, nullable=False)
    consequences = db.Column(db.ARRAY(db.String(40)), default=[
        "transcript_ablation",
        "splice_acceptor_variant",
        "splice_donor_variant",
        "stop_gained",
        "frameshift_variant",
        "stop_lost",
        "start_lost",
        "transcript_amplification",
        "inframe_insertion",
        "inframe_deletion",
        "missense_variant",
        "protein_altering_variant",
        "splice_region_variant",
        "incomplete_terminal_codon_variant",
        "start_retained_variant",
        "stop_retained_variant",
        "coding_sequence_variant",
        "regulatory_region_ablation",
        "regulatory_region_amplification",
        "feature_elongation",
        "regulatory_region_variant",
        "feature_truncation",
    ])
    impacts = db.Column(db.ARRAY(db.String(8)), default=["HIGH", "MODERATE", "MODIFIER"])
    gnomAD_AF = db.Column(db.Float(4), unique=False, nullable=True, default=0.01)
    clinsig = db.Column(db.ARRAY(db.String(40)), default=[
        "uncertain_significance",
        "conflicting_interpretations_of_pathogenicity",
        "pathogenic",
        "likely_pathogenic",
        "pathogenic_likely_pathogenic",
    ])

    def __repr__(self):
        return f"{self.filtername}"


class Gene(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hgnc = db.Column(db.String(20), unique=True, nullable=False)
    transcripts = relationship("Transcript")

    def __repr__(self):
        return f"Gene('{self.hgnc}')"


class Transcript(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transcriptname = db.Column(db.String(20), unique=True, nullable=False)
    gene_id = db.Column(db.Integer, db.ForeignKey('gene.id'))
    gene = relationship("Gene", back_populates="transcripts")

    def __repr__(self):
        return f"Transcript('{self.transcriptname}')"


################################################################################

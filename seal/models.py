from seal import db, login_manager, bcrypt
from flask_login import UserMixin
from sqlalchemy.orm import relationship
from sqlalchemy.ext.mutable import Mutable


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

sample2team = db.Table(
    'sample2team',
    db.Column(
        'team_ID', db.Integer,
        db.ForeignKey('team.id'), primary_key=True
    ),
    db.Column(
        'sample_ID', db.Integer,
        db.ForeignKey('sample.id'), primary_key=True
    )
)


class MutableList(Mutable, list):
    def append(self, value):
        list.append(self, value)
        self.changed()

    def remove(self, value):
        list.remove(self, value)
        self.changed()

    @classmethod
    def coerce(cls, key, value):
        if not isinstance(value, MutableList):
            if isinstance(value, list):
                return MutableList(value)
            return Mutable.coerce(key, value)
        else:
            return value


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    mail = db.Column(db.String(40), unique=True, nullable=True)
    image_file = db.Column(
        db.String(45), unique=False,
        nullable=False, default='default.jpg')
    password = db.Column(db.String(120), unique=False, nullable=False)
    logged = db.Column(db.Boolean(), nullable=False, default=False)
    admin = db.Column(db.Boolean(), nullable=False, default=False)
    bioinfo = db.Column(db.Boolean(), nullable=False, default=False)
    technician = db.Column(db.Boolean(), nullable=False, default=False)
    biologist = db.Column(db.Boolean(), nullable=False, default=False)

    sidebar = db.Column(db.Boolean(), nullable=False, default=False)

    filter_id = db.Column(db.Integer, db.ForeignKey('filter.id'), nullable=False, default=1)
    filter = relationship("Filter", backref=db.backref("users"))
    transcripts = db.Column(MutableList.as_mutable(db.ARRAY(db.String(30))), default=list())
    comments = relationship("Comment")

    teams = db.relationship(
        'Team', secondary=team2member, lazy='subquery',
        backref=db.backref('members', lazy=True)
    )

    def __repr__(self):
        return f"User('{self.username}', '{self.image_file}')"

    def verify_password(self, password):
        return bcrypt.check_password_hash(self.password, password)


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
    affected = db.Column(db.Boolean(), default=False)
    index = db.Column(db.Boolean(), default=False)

    familyid = db.Column(db.Integer, db.ForeignKey('family.id'))
    family = relationship("Family", back_populates="samples")

    runid = db.Column(db.Integer, db.ForeignKey('run.id'))
    run = relationship("Run", back_populates="samples")

    teams = db.relationship(
        'Team', secondary=sample2team, lazy='subquery',
        backref=db.backref('samples', lazy=True)
    )

    def __repr__(self):
        return f"Sample('{self.samplename}','{self.status}')"


class Family(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    family = db.Column(db.String(20), unique=True, nullable=False)
    samples = relationship("Sample")

    def __repr__(self):
        return f"Family('{self.family}')"


class Run(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    alias = db.Column(db.String(50), unique=False, nullable=True)

    samples = relationship("Sample")
    reads = relationship("Read")

    def __repr__(self):
        return f"Run('{self.name}')"


class Variant(db.Model):
    id = db.Column(db.Text, primary_key=True)
    chr = db.Column(db.String(10), unique=False, nullable=False)
    pos = db.Column(db.Integer, unique=False, nullable=False)
    ref = db.Column(db.String(500), unique=False, nullable=False)
    alt = db.Column(db.String(500), unique=False, nullable=False)
    class_variant = db.Column(db.Integer, unique=False, default=None)
    annotations = db.Column(db.JSON, nullable=True)
    comments = relationship("Comment")

    def __repr__(self):
        return f"Variant('{self.chr}','{self.pos}','{self.ref}','{self.alt}')"


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.Text, nullable=False)
    date = db.Column(db.TIMESTAMP(timezone=False), nullable=False)

    variantid = db.Column(db.Text, db.ForeignKey('variant.id'), nullable=False)
    variant = relationship("Variant", back_populates="comments")

    userid = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = relationship("User", back_populates="comments")

    def __repr__(self):
        return f"Comment('{self.comment}','{self.date}')"


class Var2Sample(db.Model):
    variant_ID = db.Column(db.Text, db.ForeignKey('variant.id'), primary_key=True)
    sample_ID = db.Column(db.Integer, db.ForeignKey('sample.id'), primary_key=True)
    depth = db.Column(db.Integer, nullable=True, unique=False)
    allelic_depth = db.Column(db.Integer, nullable=True, unique=False)
    filter = db.Column(MutableList.as_mutable(db.ARRAY(db.String(30))), default=list())
    reported = db.Column(db.Boolean, nullable=False, unique=False, default=False)

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


class Transcript(db.Model):
    # id = db.Column(db.Integer, primary_key=True)
    feature = db.Column(db.String(30), unique=True, nullable=False, primary_key=True)
    biotype = db.Column(db.String(50), unique=False, nullable=True)
    feature_type = db.Column(db.String(50), unique=False, nullable=True)
    symbol = db.Column(db.String(50), unique=False, nullable=True)
    symbol_source = db.Column(db.String(50), unique=False, nullable=True)
    gene = db.Column(db.String(30), unique=False, nullable=True)
    source = db.Column(db.String(30), unique=False, nullable=True)
    protein = db.Column(db.String(30), unique=False, nullable=True)
    canonical = db.Column(db.String(30), unique=False, nullable=True)
    hgnc = db.Column(db.String(30), unique=False, nullable=True)

    def __repr__(self):
        return f"Transcript('{self.feature}','{self.canonical}')"


region2bed = db.Table(
    'region2bed',
    db.Column(
        'region_ID', db.Integer,
        db.ForeignKey('region.id'), primary_key=True
    ),
    db.Column(
        'bed_ID', db.Integer,
        db.ForeignKey('bed.id'), primary_key=True
    )
)


class Region(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=False, nullable=False)
    chr = db.Column(db.String(50), unique=False, nullable=False)
    start = db.Column(db.Integer, unique=False, nullable=False)
    stop = db.Column(db.Integer, unique=False, nullable=False)

    def __repr__(self):
        return f"Region('{self.name}')"

    def varInRegion(self, variant):
        same_chr = (variant.chr == self.chr)
        pos = (variant.pos >= self.start and variant.pos <= self.stop)

        return (same_chr and pos)


class Bed(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True, nullable=False)

    regions = db.relationship(
        'Region', secondary=region2bed, lazy='subquery',
        backref=db.backref('beds', lazy=True)
    )

    def __repr__(self):
        return f"BED('{self.name}')"

    def varInBed(self, variant):
        for region in self.regions:
            if region.varInRegion(variant):
                return True
        return False


class Lane(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lane = db.Column(db.Integer)
    tiles = db.Column(db.Integer)
    density = db.Column(db.Integer)
    density_stddev = db.Column(db.Integer)
    cluster = db.Column(db.Float)
    cluster_stddev = db.Column(db.Float)

    phasing = db.Column(db.Float)
    phasing_stddev = db.Column(db.Float)
    phasingslope = db.Column(db.Float)
    phasingslope_stddev = db.Column(db.Float)
    phasingoffset = db.Column(db.Float)
    phasingoffset_stddev = db.Column(db.Float)

    prephasing = db.Column(db.Float)
    prephasing_stddev = db.Column(db.Float)
    prephasingslope = db.Column(db.Float)
    prephasingslope_stddev = db.Column(db.Float)
    prephasingoffset = db.Column(db.Float)
    prephasingoffset_stddev = db.Column(db.Float)

    cluster = db.Column(db.Float)
    cluster_pf = db.Column(db.Float)

    q30 = db.Column(db.Float)

    yield_g = db.Column(db.Float)
    projected_yield_g = db.Column(db.Float)

    cycles = db.Column(db.Integer)

    align = db.Column(db.Float)
    align_pf = db.Column(db.Float)

    error_rate = db.Column(db.Float)
    error_rate_stddev = db.Column(db.Float)
    error_rate_35 = db.Column(db.Float)
    error_rate_35_stddev = db.Column(db.Float)
    error_rate_75 = db.Column(db.Float)
    error_rate_75_stddev = db.Column(db.Float)
    error_rate_100 = db.Column(db.Float)
    error_rate_100_stddev = db.Column(db.Float)

    intensity = db.Column(db.Integer)
    intensity_stddev = db.Column(db.Integer)

    readid = db.Column(db.Integer, db.ForeignKey('read.id'))
    read = relationship("Read", back_populates="lanes")

    def __repr__(self):
        return f"Lane('{self.lane}')"


class Read(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    read = db.Column(db.Integer)
    is_index = db.Column(db.Boolean(), default=True)
    yield_g = db.Column(db.Float)
    projected_yield_g = db.Column(db.Float)
    aligned = db.Column(db.Float)
    error_rate = db.Column(db.Float)
    intensity = db.Column(db.Integer)
    percent_gt_q30 = db.Column(db.Float)

    runid = db.Column(db.Integer, db.ForeignKey('run.id'))
    run = relationship("Run", back_populates="reads")

    lanes = relationship("Lane")

    def __repr__(self):
        return f"Read('{self.read}')"


################################################################################

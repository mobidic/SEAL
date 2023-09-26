# (c) 2023, Charles VAN GOETHEM <c-vangoethem (at) chu-montpellier (dot) fr>
#
# This file is part of SEAL
# 
# SEAL db - Simple, Efficient And Lite database for NGS
# Copyright (C) 2023  Charles VAN GOETHEM - MoBiDiC - CHU Montpellier
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from datetime import datetime

from seal import db, login_manager, bcrypt

from flask_login import UserMixin

from sqlalchemy import select, func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.mutable import Mutable
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.dialects import postgresql

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
    api_key_md = db.Column(db.String(60), unique=False, nullable=True)
    logged = db.Column(db.Boolean(), nullable=False, default=False)
    admin = db.Column(db.Boolean(), nullable=False, default=False)
    bioinfo = db.Column(db.Boolean(), nullable=False, default=False)
    technician = db.Column(db.Boolean(), nullable=False, default=False)
    biologist = db.Column(db.Boolean(), nullable=False, default=False)

    sidebar = db.Column(db.Boolean(), nullable=False, default=False)

    filter_id = db.Column(db.Integer, db.ForeignKey('filter.id'), nullable=False, default=1)
    filter = relationship("Filter", backref=db.backref("users"))
    transcripts = db.Column(MutableList.as_mutable(db.ARRAY(db.String(30))), default=list())
    comments_variants = relationship("Comment_variant")
    comments_samples = relationship("Comment_sample")
    historics = relationship("History")

    teams = db.relationship(
        'Team', secondary=team2member, lazy='subquery',
        backref=db.backref('members', lazy=True)
    )

    def __repr__(self):
        return f"User('{self.username}', '{self.image_file}')"

    def __str__(self):
        return self.username

    def verify_password(self, password):
        return bcrypt.check_password_hash(self.password, password)


class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teamname = db.Column(db.String(20), unique=True, nullable=False)
    color = db.Column(db.String(7), unique=False, nullable=False, default="#95A5A6")

    def __repr__(self):
        return f"Team('{self.teamname}','{self.color}')"

    def __str__(self):
        return self.teamname


class Clinvar(db.Model):
    version = db.Column(db.Integer, primary_key=True)
    genome = db.Column(db.String(20), unique=False, nullable=False)
    date = db.Column(db.TIMESTAMP(timezone=False), nullable=False, default=datetime.now())
    current = db.Column(db.Boolean(), default=True, nullable=False)

    def __repr__(self):
        return f"Clinvar('{self.version}','{self.date}')"

    def __str__(self):
        return str(self.version)


################################################################################


################################################################################
# Analysis

class History(db.Model):
    user_ID = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True, default=1)
    user = relationship("User", back_populates="historics")
    sample_ID = db.Column(db.Integer, db.ForeignKey('sample.id'), primary_key=True)
    sample = relationship("Sample", back_populates="historics")
    date = db.Column(db.TIMESTAMP(timezone=False), nullable=False, primary_key=True, default=datetime.now())

    action = db.Column(db.Text, nullable=False)


class Sample(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    samplename = db.Column(db.String(120), unique=False, nullable=False)
    alias = db.Column(db.String(120), unique=False, nullable=False)
    status = db.Column(db.Integer, unique=False, nullable=False, default=0)
    affected = db.Column(db.Boolean(), default=False)
    index = db.Column(db.Boolean(), default=False)

    filter_id = db.Column(db.Integer, db.ForeignKey('filter.id'), nullable=True)
    filter = relationship("Filter", back_populates="samples")

    bed_id = db.Column(db.Integer, db.ForeignKey('bed.id'), nullable=True)
    bed = relationship("Bed", back_populates="samples")

    familyid = db.Column(db.Integer, db.ForeignKey('family.id'))
    family = relationship("Family", back_populates="samples")

    runid = db.Column(db.Integer, db.ForeignKey('run.id'))
    run = relationship("Run", back_populates="samples")

    historics = relationship("History")
    teams = db.relationship(
        'Team', secondary=sample2team, lazy='subquery',
        backref=db.backref('samples', lazy=True)
    )
    comments = relationship("Comment_sample")

    def __repr__(self):
        return f"Sample('{self.samplename}','{self.family}','{self.run}','{self.status}','{self.affected}','{self.index}')"

    def __str__(self):
        return self.samplename
    
    @hybrid_property
    def lastAction(self):
        return History.query.filter_by(sample_ID = self.id).order_by(History.date.desc()).first()
    
    @lastAction.expression
    def lastAction(cls):
        return select(func.max(History.date)).\
            where(History.sample_ID==cls.id).scalar_subquery()


class Family(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    family = db.Column(db.String(20), unique=True, nullable=False)
    samples = relationship("Sample")

    def __repr__(self):
        return f"Family('{self.family}')"

    def __str__(self):
        return self.family


class Run(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    alias = db.Column(db.String(50), unique=False, nullable=True)

    summary = db.Column(db.Text, unique=False, nullable=True)

    samples = relationship("Sample")
    reads = relationship("Read")

    def __repr__(self):
        return f"Run('{self.name}','{self.alias}')"

    def __str__(self):
        return self.name


class Variant(db.Model):
    id = db.Column(db.Text, primary_key=True)
    chr = db.Column(db.String(10), unique=False, nullable=False)
    pos = db.Column(db.Integer, unique=False, nullable=False)
    ref = db.Column(db.String(500), unique=False, nullable=False)
    alt = db.Column(db.String(500), unique=False, nullable=False)
    class_variant = db.Column(db.Integer, unique=False, default=None)
    annotations = db.Column(db.JSON, nullable=True)
    comments = relationship("Comment_variant")

    clinvar_VARID = db.Column(db.Integer, unique=False, nullable=True)
    clinvar_CLNSIG = db.Column(db.String(500), unique=False, nullable=True)
    clinvar_CLNSIGCONF = db.Column(MutableList.as_mutable(db.ARRAY(db.String(100))), default=list())
    clinvar_CLNREVSTAT = db.Column(MutableList.as_mutable(db.ARRAY(db.String(100))), default=list())

    def __repr__(self):
        return f"Variant('{self.chr}','{self.pos}','{self.ref}','{self.alt}')"

    def __str__(self):
        return self.id


class Comment_variant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.Text, nullable=False)
    date = db.Column(db.TIMESTAMP(timezone=False), nullable=False, default=datetime.now())

    variantid = db.Column(db.Text, db.ForeignKey('variant.id'), nullable=False)
    variant = relationship("Variant", back_populates="comments")

    userid = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = relationship("User", back_populates="comments_variants")

    def __repr__(self):
        return f"Comment('{self.comment}','{self.date}')"

    def __str__(self):
        return self.comment


class Comment_sample(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.Text, nullable=False)
    date = db.Column(db.TIMESTAMP(timezone=False), nullable=False, default=datetime.now())

    sampleid = db.Column(db.Integer, db.ForeignKey('sample.id'), nullable=False)
    sample = relationship("Sample", back_populates="comments")

    userid = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = relationship("User", back_populates="comments_samples")

    def __repr__(self):
        return f"Comment('{self.comment}','{self.date}')"

    def __str__(self):
        return self.comment


class Var2Sample(db.Model):
    variant_ID = db.Column(db.Text, db.ForeignKey('variant.id'), primary_key=True)
    sample_ID = db.Column(db.Integer, db.ForeignKey('sample.id'), primary_key=True)
    depth = db.Column(db.Integer, nullable=True, unique=False)
    allelic_depth = db.Column(db.Integer, nullable=True, unique=False)
    filter = db.Column(MutableList.as_mutable(db.ARRAY(db.String(30))), default=list())
    reported = db.Column(db.Boolean, nullable=False, unique=False, default=False)
    hide = db.Column(db.Boolean, nullable=False, unique=False, default=False)

    sample = db.relationship(Sample, backref="variants")
    variant = db.relationship(Variant, backref="samples")

    def __repr__(self):
        return f"Var2Sample('{self.sample}','{self.variant}')"

    def __str__(self):
        return f"{self.sample} - {self.variant}"

    def inBed(self):
        if self.sample.bed:
            return self.sample.bed.varInBed(self.variant) 
        else:
            return True


team2filter = db.Table(
    'team2filter',
    db.Column(
        'team_ID', db.Integer,
        db.ForeignKey('team.id'), primary_key=True
    ),
    db.Column(
        'filter_ID', db.Integer,
        db.ForeignKey('filter.id'), primary_key=True
    )
)


class Filter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filtername = db.Column(db.String(20), unique=True, nullable=False)
    filter = db.Column(db.JSON, nullable=True)
    samples = relationship("Sample")

    teams = db.relationship(
        'Team', secondary=team2filter, lazy='subquery',
        backref=db.backref('filters', lazy=True)
    )

    def __repr__(self):
        return f"Filter({self.filtername})"

    def __str__(self):
        return self.filtername


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

    def __str__(self):
        return self.feature


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

team2bed = db.Table(
    'team2bed',
    db.Column(
        'team_ID', db.Integer,
        db.ForeignKey('team.id'), primary_key=True
    ),
    db.Column(
        'bed_ID', db.Integer,
        db.ForeignKey('bed.id'), primary_key=True
    )
)


class Region(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=False, nullable=False)
    chr = db.Column(db.String(50), unique=False, nullable=False)
    start = db.Column(db.Integer, unique=False, nullable=False)
    stop = db.Column(db.Integer, unique=False, nullable=False)

    def __repr__(self):
        return f"Region('{self.name}','{self.chr}','{self.start}','{self.stop}')"

    def __str__(self):
        return self.name

    def varInRegion(self, variant):
        same_chr = (variant.chr == self.chr)
        pos = (variant.pos >= self.start and variant.pos <= self.stop)

        return (same_chr and pos)


class Bed(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(75), unique=True, nullable=False)
    samples = relationship("Sample")

    regions = db.relationship(
        'Region', secondary=region2bed, lazy='subquery',
        backref=db.backref('beds', lazy=True)
    )

    teams = db.relationship(
        'Team', secondary=team2bed, lazy='subquery',
        backref=db.backref('beds', lazy=True)
    )

    def __repr__(self):
        return f"BED('{self.name}')"

    def __str__(self):
        return self.name

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

    def __str__(self):
        return self.lane


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

    def __str__(self):
        return self.read


################################################################################
class Phenotype(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phenotypeMimNumber = db.Column(db.Integer)
    phenotype = db.Column(db.Text)
    inheritances = db.Column(MutableList.as_mutable(db.ARRAY(db.String(30))), default=list())
    phenotypeMappingKey = db.Column(db.Integer)

    def __repr__(self):
        return f"Phenotype('{self.phenotypeMimNumber}')"

    def __str__(self):
        return f"{self.phenotype} ({self.phenotypeMimNumber})"


phenotype2OMIM = db.Table(
    'phenotype2OMIM',
    db.Column(
        'phenotype_ID', db.Integer,
        db.ForeignKey('phenotype.id'), primary_key=True
    ),
    db.Column(
        'omim_ID', db.Integer,
        db.ForeignKey('omim.mimNumber'), primary_key=True
    )
)


class Omim(db.Model):
    mimNumber = db.Column(db.Integer, primary_key=True)
    approvedGeneSymbol = db.Column(db.String(50))
    comments = db.Column(db.Text)
    computedCytoLocation = db.Column(db.String(50))
    cytoLocation = db.Column(db.String(50))
    ensemblGeneID = db.Column(db.String(50))
    entrezGeneID = db.Column(db.String(50))
    geneSymbols = db.Column(postgresql.ARRAY(db.String(30)), default=list())

    phenotypes = db.relationship(
        'Phenotype', secondary=phenotype2OMIM, lazy='subquery',
        backref=db.backref('omims', lazy=True)
    )

    def __repr__(self):
        return f"Omim('{self.mimNumber}')"

    def __str__(self):
        return self.mimNumber

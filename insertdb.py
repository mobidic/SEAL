import os
from seal import db, app
from seal.models import User, Team, Sample, Variant, Filter, Gene, Transcript, Family


pathDB = os.path.join(app.root_path, 'site.db')
if os.path.exists(pathDB):
    os.remove(pathDB)

os.system('psql postgres -c "DROP DATABASE seal;"')
os.system('psql postgres -c "CREATE DATABASE seal;"')

db.create_all()

filterBasic = {
    "criteria": [
        {
            "criteria": [
                {
                    "condition": "<=",
                    "data": "GnomAD",
                    "value": [
                        "0.01"
                    ]
                }
            ],
            "logic": "AND"
        },
        {
            "criteria": [
                {
                    "condition": "contains",
                    "data": "Consequence",
                    "value": [
                        "transcript_ablation"
                    ]
                },
                {
                    "condition": "contains",
                    "data": "Consequence",
                    "value": [
                        "splice_acceptor_variant"
                    ]
                },
                {
                    "condition": "contains",
                    "data": "Consequence",
                    "value": [
                        "splice_donor_variant"
                    ]
                },
                {
                    "condition": "contains",
                    "data": "Consequence",
                    "value": [
                        "stop_gained"
                    ]
                },
                {
                    "condition": "contains",
                    "data": "Consequence",
                    "value": [
                        "frameshift_variant"
                    ]
                },
                {
                    "condition": "contains",
                    "data": "Consequence",
                    "value": [
                        "stop_lost"
                    ]
                },
                {
                    "condition": "contains",
                    "data": "Consequence",
                    "value": [
                        "start_lost"
                    ]
                },
                {
                    "condition": "contains",
                    "data": "Consequence",
                    "value": [
                        "transcript_amplification"
                    ]
                },
                {
                    "condition": "contains",
                    "data": "Consequence",
                    "value": [
                        "inframe_insertion"
                    ]
                },
                {
                    "condition": "contains",
                    "data": "Consequence",
                    "value": [
                        "inframe_deletion"
                    ]
                },
                {
                    "condition": "contains",
                    "data": "Consequence",
                    "value": [
                        "missense_variant"
                    ]
                },
                {
                    "condition": "contains",
                    "data": "Consequence",
                    "value": [
                        "protein_altering_variant"
                    ]
                },
                {
                    "condition": "contains",
                    "data": "Consequence",
                    "value": [
                        "splice_region_variant"
                    ]
                },
                {
                    "condition": "contains",
                    "data": "Consequence",
                    "value": [
                        "incomplete_terminal_codon_variant"
                    ]
                },
                {
                    "condition": "contains",
                    "data": "Consequence",
                    "value": [
                        "start_retained_variant"
                    ]
                },
                {
                    "condition": "contains",
                    "data": "Consequence",
                    "value": [
                        "stop_retained_variant"
                    ]
                }
            ],
            "logic": "OR"
        },
        {
            "criteria": [
                {
                    "condition": "contains",
                    "data": "ClinSig",
                    "value": [
                        "pathogenic"
                    ]
                },
                {
                    "condition": "contains",
                    "data": "ClinSig",
                    "value": [
                        "uncertain_significance"
                    ]
                },
                {
                    "condition": "null",
                    "data": "ClinSig",
                    "value": []
                }
            ],
            "logic": "OR"
        },
        {
            "criteria": [
                {
                    "criteria": [
                        {
                            "condition": ">=",
                            "data": "Missense",
                            "value": [
                                "0.35"
                            ]
                        },
                        {
                            "condition": "null",
                            "data": "Missense",
                            "value": []
                        }
                    ],
                    "logic": "OR"
                },
                {
                    "criteria": [
                        {
                            "condition": ">=",
                            "data": "SpliceAI DS",
                            "value": [
                                "0.5"
                            ]
                        },
                        {
                            "condition": "null",
                            "data": "SpliceAI DS",
                            "value": []
                        }
                    ],
                    "logic": "OR"
                }
            ],
            "logic": "OR"
        }
    ],
    "logic": "AND"
}

filter1 = Filter(filtername="No Filter", filter={"criteria": []})
filter2 = Filter(filtername="Default", filter=filterBasic)
db.session.add(filter1)
db.session.add(filter2)
db.session.commit()

user1 = User(username="admin", password="$2b$12$a41mGjwpAWjVNEJirzsbVOBVmn6dv2Cmj/xTye13j7qZg1nNMkUIS", admin=True, technician=True, bioinfo=True, biologist=True, filter_id=2)
user2 = User(username="user", mail="mail@mail.com", password="$2b$12$a41mGjwpAWjVNEJirzsbVOBVmn6dv2Cmj/xTye13j7qZg1nNMkUIS")
db.session.add(user1)
db.session.add(user2)
db.session.commit()

team1 = Team(teamname="team1")
team2 = Team(teamname="team2")
db.session.add(team2)
db.session.add(team1)
db.session.commit()

user = User.query.get(1)
user.teams.append(team2)
user.teams.append(team1)
db.session.commit()

family1 = Family(family="family1")
db.session.add(family1)
db.session.commit()

family2 = Family(family="family2")
db.session.add(family2)

sample1 = Sample(samplename="sample1", familyid=family1.id)
sample2 = Sample(samplename="sample2", status=-1)
sample3 = Sample(samplename="sample3", familyid=family2.id)
sample4 = Sample(samplename="sample4", status=2)
db.session.add(sample1)
db.session.add(sample2)
db.session.add(sample3)
db.session.add(sample4)
db.session.commit()

sample1 = Sample.query.get(1)
sample1.status = 1
db.session.commit()

variant1 = Variant(id="chr1-12-a-c", chr="chr1", pos=12, ref="a", alt="c")
variant2 = Variant(id="chr1-12-a-g", chr="chr1", pos=12, ref="a", alt="g")
db.session.add(variant1)
db.session.add(variant2)
db.session.commit()

sample = Sample.query.get(1)
sample.variants.append(variant2)
sample.variants.append(variant1)
db.session.commit()

variant = Variant.query.get("chr1-12-a-c")
variant.annotations = [{
    "date": "aaa",
    "ANN": {
        "feature1": {
            "Consequences": ["ConsequenceA"],
            "IMPACT": ["impact"],
            "SYMBOL": "GENE",

        },
        "feature2": {
            "annot1": "B"
        }
    }
}]
db.session.commit()

gene1 = Gene(hgncname="GENE_A", hgncid="IDA")
gene2 = Gene(hgncname="GENE_B", hgncid="IDB")
db.session.add(gene1)
db.session.add(gene2)
db.session.commit()


transcript1 = Transcript(refSeq="feature1", geneid=1)
transcript2 = Transcript(refSeq="feature2", geneid=1)
db.session.add(transcript1)
db.session.add(transcript2)
db.session.commit()

import os
from seal import db, app
from seal.models import User, Team, Sample, Variant, Filter, Gene, Transcript
from datetime import datetime
from sqlalchemy.orm.attributes import flag_modified
pathDB = os.path.join(app.root_path, 'site.db')
if os.path.exists(pathDB):
    os.remove(pathDB)

os.system('psql postgres -c "DROP DATABASE seal;"')
os.system('psql postgres -c "CREATE DATABASE seal;"')

db.create_all()


filter1 = Filter(filtername="Default")
filter2 = Filter(filtername="Other", gnomAD_AF=1)
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

sample1 = Sample(samplename="sample1")
sample2 = Sample(samplename="sample2", status=-1)
sample3 = Sample(samplename="sample3")
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
            "annot1": "A"
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

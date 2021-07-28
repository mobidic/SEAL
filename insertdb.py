import os
from seal import db, app
from seal.models import User, Team, Sample, Variant
from datetime import datetime
from sqlalchemy.orm.attributes import flag_modified

pathDB = os.path.join(app.root_path, 'site.db')
if os.path.exists(pathDB):
    os.remove(pathDB)

os.system('psql postgres -c "DROP DATABASE seal;"')
os.system('psql postgres -c "CREATE DATABASE seal;"')

db.create_all()


user1 = User(username="admin", password="$2b$12$a41mGjwpAWjVNEJirzsbVOBVmn6dv2Cmj/xTye13j7qZg1nNMkUIS", admin=True, technician=True, bioinfo=True, biologist=True)
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
sample2 = Sample(samplename="sample2", analysed=True)
sample3 = Sample(samplename="sample3")
db.session.add(sample1)
db.session.add(sample2)
db.session.add(sample3)
db.session.commit()

sample1 = Sample.query.get(1)
sample1.analysed = True
db.session.commit()

variant1 = Variant(chr="chr1", pos=12, ref="a", alt="c")
variant2 = Variant(chr="chr1", pos=12, ref="a", alt="g")
db.session.add(variant1)
db.session.add(variant2)
db.session.commit()

sample = Sample.query.get(1)
sample.variants.append(variant2)
sample.variants.append(variant1)
db.session.commit()

variant = Variant.query.get(1)
variant.annotations = [{
    "key1": "value1",
    "key2": ["value3", "value2"]
}, {
    "key1": "value1 - new",
    "key2": ["value3", "value2"]
}]
db.session.commit()

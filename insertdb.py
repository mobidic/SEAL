import os
from seal import db, app, bcrypt
from seal.models import User, Filter


pathDB = os.path.join(app.root_path, 'site.db')
if os.path.exists(pathDB):
    os.remove(pathDB)

os.system('psql postgres -c "DROP DATABASE seal;"')
os.system('psql postgres -c "CREATE DATABASE seal;"')

db.create_all()

filter1 = Filter(filtername="No Filter", filter={"criteria": []})
db.session.add(filter1)

user1 = User(username="admin", password=bcrypt.generate_password_hash("password").decode('utf-8'), admin=True, technician=True, bioinfo=True, biologist=True, logged=True)
db.session.add(user1)
db.session.commit()

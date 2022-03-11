import os

from pathlib import Path

from seal import db, app, bcrypt
from seal.models import User, Filter


pathDB = Path(app.root_path).joinpath('site.db')
try:
    pathDB.unlink()
except FileNotFoundError:
    pass

os.system('psql postgres -c "DROP DATABASE seal;"')
os.system('psql postgres -c "CREATE DATABASE seal;"')

db.create_all()

filter1 = Filter(filtername="No Filter", filter={"criteria": []})
db.session.add(filter1)

user1 = User(username="admin", password=bcrypt.generate_password_hash("password").decode('utf-8'), admin=True, technician=True, bioinfo=True, biologist=True, logged=True)
db.session.add(user1)
db.session.commit()

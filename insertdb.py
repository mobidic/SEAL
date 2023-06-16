import argparse

from seal import db, app, bcrypt
from seal.models import User, Filter


parser = argparse.ArgumentParser()
parser.add_argument('-p', '--password-admin', help='Password for admin user', default="password")
args = parser.parse_args()

db.create_all()

filter1 = Filter(filtername="No Filter", filter={"criteria": []})
db.session.add(filter1)

user1 = User(username="admin", password=bcrypt.generate_password_hash(args.password).decode('utf-8'), admin=True, technician=True, bioinfo=True, biologist=True, logged=True)
db.session.add(user1)
db.session.commit()

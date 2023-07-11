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

import argparse

from seal import db, app, bcrypt
from seal.models import User, Filter


parser = argparse.ArgumentParser()
parser.add_argument('-p', '--password', help='Password for admin user', default="password")
args = parser.parse_args()

db.create_all()

filter1 = Filter(filtername="No Filter", filter={"criteria": []})
db.session.add(filter1)

user1 = User(username="admin", password=bcrypt.generate_password_hash(args.password).decode('utf-8'), admin=True, technician=True, bioinfo=True, biologist=True, logged=True)
db.session.add(user1)
db.session.commit()

# (c) 2025, Charles VAN GOETHEM <c-vangoethem (at) chu-montpellier (dot) fr>
#
# This file is part of SEAL
# 
# SEAL db - Simple, Efficient And Lite database for NGS
# Copyright (C) 2025  Charles VAN GOETHEM - MoBiDiC - CHU Montpellier
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

import csv
from seal import db
from seal.models import Region

genes = dict()
with open("ncbiRefSeq.hg19.sorted.bed") as fd:
    rd = csv.reader(fd, delimiter="\t", quotechar='"')
    for row in rd:
        g = row[3]
        if g not in genes:
            genes[g] = dict()
        if row[0] not in genes[g]:
            genes[g].update({
                row[0]: {
                    "start": row[1],
                    "stop": row[2],
                }
            })
        else:
            genes[g][row[0]]["start"] = min(genes[g][row[0]]["start"], row[1])
            genes[g][row[0]]["stop"] = max(genes[g][row[0]]["stop"], row[2])

for b in genes:
    for c in genes[b]:
        region = Region(name=b, chr=c, start=genes[b][c]["start"], stop=genes[b][c]["stop"])
        db.session.add(region)
        db.session.commit()

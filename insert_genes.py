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

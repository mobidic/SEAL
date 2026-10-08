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

import re
from seal import db
from seal.models import Phenotype, Omim
import pprint


pp = pprint.PrettyPrinter(indent=4)


shorter_transmission = {
    "Autosomal dominant": "AD",
    "Autosomal recessive": "AR",
    "Digenic dominant": "DD",
    "Digenic recessive": "DR",
    "Isolated cases": "IC",
    "Mitochondrial": "Mito",
    "Multifactorial": "MF",
    "Pseudoautosomal dominant": "PAD",
    "Pseudoautosomal recessive": "PAR",
    "Somatic mosaicism": "SMos",
    "Somatic mutation": "SMut",
    "X-linked": "XL",
    "X-linked dominant": "XLD",
    "X-linked recessive": "XLR",
    "Y-linked": "YL",
    "?Autosomal dominant": "?AD",
    "?Autosomal recessive": "?AR",
    "?Digenic dominant": "?DD",
    "?Digenic recessive": "?DR",
    "?Isolated cases": "?IC",
    "?Mitochondrial": "?Mito",
    "?Multifactorial": "?MF",
    "?Pseudoautosomal dominant": "?PAD",
    "?Pseudoautosomal recessive": "?PAR",
    "?Somatic mosaicism": "?SMos",
    "?Somatic mutation": "?SMut",
    "?X-linked": "?XL",
    "?X-linked dominant": "?XLD",
    "?X-linked recessive": "?XLR",
    "?Y-linked": "?YL"
}
# Read from stdin
all_pheno = dict()
with open("genemap2.txt") as fd:
    for line in fd:

        # Skip comments
        if line.startswith('#'):
            continue

        # Strip trailing new line
        line = line.strip('\n')

        # Get the values
        valueList = line.split('\t')

        # Get the fields
        chromosome = valueList[0]
        genomicPositionStart = valueList[1]
        genomicPositionEnd = valueList[2]
        cytoLocation = valueList[3]
        computedCytoLocation = valueList[4]
        mimNumber = valueList[5]
        geneSymbols = valueList[6]
        geneName = valueList[7]
        approvedGeneSymbol = valueList[8]
        entrezGeneID = valueList[9]
        ensemblGeneID = valueList[10]
        comments = valueList[11]
        phenotypeString = valueList[12]
        mouse = valueList[13]

        # Skip empty phenotypes
        if not phenotypeString or not entrezGeneID or not approvedGeneSymbol:
            continue

        omim = Omim.query.get(mimNumber)
        if not omim:
            omim = Omim(
                mimNumber=mimNumber,
                approvedGeneSymbol=approvedGeneSymbol,
                comments=comments,
                cytoLocation=cytoLocation,
                computedCytoLocation=computedCytoLocation,
                entrezGeneID=entrezGeneID,
                ensemblGeneID=ensemblGeneID,
                geneSymbols=geneSymbols.split(",")
            )
            db.session.add(omim)
            db.session.commit()

        # Parse the phenotypes
        for phenotype in phenotypeString.split(';'):

            # Clean the phenotype
            phenotype = phenotype.strip()

            # Long phenotype
            matcher_long = re.match(r'^(.*),\s(\d{6})\s\((\d)\)(|, (.*))$', phenotype)
            matcher_short = re.match(r'^(.*)\((\d)\)(|, (.*))$', phenotype)
            if matcher_long:
                # Get the fields
                phenotype = matcher_long.group(1).strip('" ')
                phenotypeMimNumber = matcher_long.group(2).strip('" ')
                phenotypeMappingKey = matcher_long.group(3).strip('" ')
                inheritances = matcher_long.group(5)
            elif matcher_short:
                # Get the fields
                phenotype = matcher_short.group(1).strip('" ')
                phenotypeMappingKey = matcher_short.group(2).strip('" ')
                inheritances = matcher_short.group(3)
            if (matcher_long or matcher_short):
                if inheritances:
                    # Get the inheritances, may or may not be there
                    inheritances = [shorter_transmission[i.strip('" ')] for i in inheritances.split(',')]
                else:
                    inheritances = ['Unknown']
                pheno = Phenotype(
                    phenotypeMimNumber=phenotypeMimNumber if phenotypeMimNumber else None,
                    phenotype=phenotype,
                    inheritances=inheritances,
                    phenotypeMappingKey=phenotypeMappingKey
                )
                db.session.add(pheno)
                db.session.commit()
                omim.phenotypes.append(pheno)

import os
from seal import db, app
from seal.models import User, Team, Sample, Variant, Filter, Gene, Transcript, Family, Var2Sample


pathDB = os.path.join(app.root_path, 'site.db')
if os.path.exists(pathDB):
    os.remove(pathDB)

os.system('psql postgres -c "DROP DATABASE seal;"')
os.system('psql postgres -c "CREATE DATABASE seal;"')

db.create_all()

filterSlow = {
    "criteria": [
        {
            "criteria": [
                {
                    "condition": "<=",
                    "data": "GnomAD",
                    "type": "num",
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
                    "type": "html",
                    "value": [
                        "transcript_ablation"
                    ]
                },
                {
                    "condition": "contains",
                    "data": "Consequence",
                    "type": "html",
                    "value": [
                        "splice_acceptor_variant"
                    ]
                },
                {
                    "condition": "contains",
                    "data": "Consequence",
                    "type": "html",
                    "value": [
                        "splice_donor_variant"
                    ]
                },
                {
                    "condition": "contains",
                    "data": "Consequence",
                    "type": "html",
                    "value": [
                        "stop_gained"
                    ]
                },
                {
                    "condition": "contains",
                    "data": "Consequence",
                    "type": "html",
                    "value": [
                        "frameshift_variant"
                    ]
                },
                {
                    "condition": "contains",
                    "data": "Consequence",
                    "type": "html",
                    "value": [
                        "stop_lost"
                    ]
                },
                {
                    "condition": "contains",
                    "data": "Consequence",
                    "type": "html",
                    "value": [
                        "start_lost"
                    ]
                },
                {
                    "condition": "contains",
                    "data": "Consequence",
                    "type": "html",
                    "value": [
                        "transcript_amplification"
                    ]
                },
                {
                    "condition": "contains",
                    "data": "Consequence",
                    "type": "html",
                    "value": [
                        "inframe_insertion"
                    ]
                },
                {
                    "condition": "contains",
                    "data": "Consequence",
                    "type": "html",
                    "value": [
                        "inframe_deletion"
                    ]
                },
                {
                    "condition": "contains",
                    "data": "Consequence",
                    "type": "html",
                    "value": [
                        "missense_variant"
                    ]
                },
                {
                    "condition": "contains",
                    "data": "Consequence",
                    "type": "html",
                    "value": [
                        "protein_altering_variant"
                    ]
                },
                {
                    "condition": "contains",
                    "data": "Consequence",
                    "type": "html",
                    "value": [
                        "splice_region_variant"
                    ]
                },
                {
                    "condition": "contains",
                    "data": "Consequence",
                    "type": "html",
                    "value": [
                        "incomplete_terminal_codon_variant"
                    ]
                },
                {
                    "condition": "contains",
                    "data": "Consequence",
                    "type": "html",
                    "value": [
                        "start_retained_variant"
                    ]
                },
                {
                    "condition": "contains",
                    "data": "Consequence",
                    "type": "html",
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
                    "type": "html",
                    "value": [
                        "pathogenic"
                    ]
                },
                {
                    "condition": "contains",
                    "data": "ClinSig",
                    "type": "html",
                    "value": [
                        "uncertain_significance"
                    ]
                },
                {
                    "condition": "null",
                    "data": "ClinSig",
                    "type": "html",
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
                            "type": "num",
                            "value": [
                                "0.35"
                            ]
                        },
                        {
                            "condition": "null",
                            "data": "Missense",
                            "type": "num",
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
                            "type": "num",
                            "value": [
                                "0.5"
                            ]
                        },
                        {
                            "condition": "null",
                            "data": "SpliceAI DS",
                            "type": "num",
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

filterDefault = {
    "criteria": [
        {
            "criteria": [
                {
                    "condition": "<=",
                    "data": "GnomAD",
                    "type": "num",
                    "value": [
                        "0.01"
                    ]
                },
                {
                    "criteria": [
                        {
                            "condition": "<=",
                            "data": "SEAL (pct)",
                            "type": "num",
                            "value": [
                                "0.1"
                            ]
                        },
                        {
                            "condition": "<=",
                            "data": "SEAL (cnt)",
                            "type": "num",
                            "value": [
                                "10"
                            ]
                        }
                    ],
                    "logic": "OR"
                }
            ],
            "logic": "AND"
        },
        {
            "criteria": [
                {
                    "condition": ">=",
                    "data": "Missense",
                    "type": "num",
                    "value": [
                        "0.35"
                    ]
                },
                {
                    "condition": "null",
                    "data": "Missense",
                    "type": "num",
                    "value": []
                }
            ],
            "logic": "OR"
        },
        {
            "criteria": [
                {
                    "condition": "!=",
                    "data": "Impact",
                    "type": "html",
                    "value": [
                        "LOW"
                    ]
                },
                {
                    "condition": "!=",
                    "data": "Impact",
                    "type": "html",
                    "value": [
                        "MODIFIER"
                    ]
                }
            ],
            "logic": "AND"
        },
        {
            "criteria": [
                {
                    "condition": "contains",
                    "data": "ClinSig",
                    "type": "html",
                    "value": [
                        "pathogenicity"
                    ]
                },
                {
                    "condition": "contains",
                    "data": "ClinSig",
                    "type": "html",
                    "value": [
                        "uncertain"
                    ]
                },
                {
                    "condition": "null",
                    "data": "ClinSig",
                    "type": "html",
                    "value": []
                }
            ],
            "logic": "OR"
        }
    ],
    "logic": "AND"
}

filter1 = Filter(filtername="No Filter", filter={"criteria": []})
filter2 = Filter(filtername="Slow", filter=filterSlow)
filter3 = Filter(filtername="Default", filter=filterDefault)
db.session.add(filter1)
db.session.add(filter2)
db.session.add(filter3)
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

sample1.status = 1

variant1 = Variant(id="chr1-12-a-c", chr="chr1", pos=12, ref="a", alt="c")
variant2 = Variant(id="chr1-12-a-g", chr="chr1", pos=12, ref="a", alt="g")
db.session.add(variant1)
db.session.add(variant2)

v2s1 = Var2Sample(variant_ID=variant1.id, sample_ID=sample1.id, depth=20, allelic_depth=10, analyse1=False, analyse2=False, reported=False)
v2s2 = Var2Sample(variant_ID=variant2.id, sample_ID=sample1.id, depth=30, allelic_depth=20, analyse1=True, analyse2=True, reported=True)
v2s3 = Var2Sample(variant_ID=variant1.id, sample_ID=sample2.id, depth=45, allelic_depth=10, analyse1=True, analyse2=True, reported=False)
db.session.add(v2s1)
db.session.add(v2s2)
db.session.add(v2s3)
db.session.commit()

variant = Variant.query.get("chr1-12-a-c")
variant.annotations = [{
    "date": "aaa",
    "ANN": {
      "NM_0001": {
        "BIOTYPE": "protein_coding",
        "BayesDel_addAF_rankscore": "0.89972",
        "BayesDel_noAF_rankscore": "0.94997",
        "CADD_raw_rankscore": "0.80838",
        "CADD_raw_rankscore_hg19": "0.76535",
        "CDS_position": "797/2448",
        "CLIN_SIG": "uncertain_significance",
        "ClinPred_rankscore": "0.55954",
        "Consequence": "missense_variant",
        "DANN_rankscore": "0.68440",
        "DEOGEN2_rankscore": "0.87174",
        "EI": "Exon 5/23",
        "ENSP": "ENSP00000326281",
        "EXON": "5/23",
        "Eigen-PC-raw_coding_rankscore": "0.84383",
        "Eigen-raw_coding_rankscore": "0.82115",
        "Existing_variation": "rs761142449",
        "FATHMM_converted_rankscore": "0.96982",
        "Feature": "NM_0001.7",
        "Feature_type": "Transcript",
        "GERP++_RS_rankscore": "0.76297",
        "GM12878_fitCons_rankscore": "0.11191",
        "Gene": "ENSG00000092529",
        "GenoCanyon_rankscore": "0.74766",
        "H1-hESC_fitCons_rankscore": "0.34648",
        "HGVSc": "NM_0001.7:c.797A>C",
        "HGVSg": "chr1:g.12A>C",
        "HGVSp": "ENSP00000326281.7:p.Ile266Thr",
        "HUVEC_fitCons_rankscore": "0.14980",
        "IMPACT": "MODERATE",
        "INTRON": None,
        "LINSIGHT_rankscore": None,
        "LIST-S2_rankscore": "0.79272",
        "LRT_converted_rankscore": "0.84330",
        "M-CAP_rankscore": "0.94614",
        "MPC_rankscore": "0.60511",
        "MVP_rankscore": "0.98737",
        "MaxEntScan_alt": None,
        "MaxEntScan_diff": None,
        "MaxEntScan_ref": None,
        "MetaLR_rankscore": "0.97893",
        "MetaSVM_rankscore": "0.99004",
        "MutPred_rankscore": "0.79267",
        "MutationAssessor_rankscore": "0.52218",
        "MutationTaster_converted_rankscore": "0.81001",
        "PROVEAN_converted_rankscore": "0.80943",
        "PolyPhen": "probably_damaging(0.958)",
        "Polyphen2_HDIV_rankscore": "0.56202",
        "Polyphen2_HVAR_rankscore": "0.67449",
        "PrimateAI_rankscore": "0.74568",
        "Protein_position": "266/815",
        "REVEL_rankscore": "0.98869",
        "SIFT4G_converted_rankscore": "0.63918",
        "SIFT_converted_rankscore": "0.91255",
        "SYMBOL": "CAPN3",
        "SiPhy_29way_logOdds_rankscore": "0.75351",
        "SpliceAI_pred_DP_AG": "4",
        "SpliceAI_pred_DP_AL": "10",
        "SpliceAI_pred_DP_DG": "8",
        "SpliceAI_pred_DP_DL": "4",
        "SpliceAI_pred_DS_AG": "0.00",
        "SpliceAI_pred_DS_AL": "0.00",
        "SpliceAI_pred_DS_DG": "0.00",
        "SpliceAI_pred_DS_DL": "0.00",
        "SpliceAI_pred_SYMBOL": "CAPN3",
        "VARIANT_CLASS": "SNV",
        "VEST4_rankscore": "0.93135",
        "bStatistic_converted_rankscore": "0.80015",
        "fathmm-MKL_coding_rankscore": "0.97318",
        "fathmm-XF_coding_rankscore": "0.82512",
        "gnomADg": None,
        "gnomADg_AF_AFR": None,
        "gnomADg_AF_AMR": None,
        "gnomADg_AF_ASJ": None,
        "gnomADg_AF_EAS": None,
        "gnomADg_AF_FIN": None,
        "gnomADg_AF_NFE": None,
        "gnomADg_AF_OTH": None,
        "integrated_fitCons_rankscore": "0.35715",
        "phastCons100way_vertebrate_rankscore": "0.71638",
        "phastCons17way_primate_rankscore": "0.91618",
        "phastCons30way_mammalian_rankscore": "0.86279",
        "phyloP100way_vertebrate_rankscore": "0.87040",
        "phyloP17way_primate_rankscore": "0.52053",
        "phyloP30way_mammalian_rankscore": "0.56520",
        "SOMATIC":"r",
        "PHENO":"",
        "PUBMED":""
      }
    }
}]

variant = Variant.query.get("chr1-12-a-g")
variant.annotations = [{
    "date": "aaa",
    "ANN": {
      "NM_0001": {
        "BIOTYPE": "protein_coding",
        "BayesDel_addAF_rankscore": "0.89972",
        "BayesDel_noAF_rankscore": "0.94997",
        "CADD_raw_rankscore": "0.80838",
        "CADD_raw_rankscore_hg19": "0.76535",
        "CDS_position": "797/2448",
        "CLIN_SIG": "uncertain_significance",
        "ClinPred_rankscore": "0.55954",
        "Consequence": "missense_variant",
        "DANN_rankscore": "0.68440",
        "DEOGEN2_rankscore": "0.87174",
        "EI": "Exon 5/23",
        "ENSP": "ENSP00000326281",
        "EXON": "5/23",
        "Eigen-PC-raw_coding_rankscore": "0.84383",
        "Eigen-raw_coding_rankscore": "0.82115",
        "Existing_variation": "rs761142449",
        "FATHMM_converted_rankscore": "0.96982",
        "Feature": "NM_0001.7",
        "Feature_type": "Transcript",
        "GERP++_RS_rankscore": "0.76297",
        "GM12878_fitCons_rankscore": "0.11191",
        "Gene": "ENSG00000092529",
        "GenoCanyon_rankscore": "0.74766",
        "H1-hESC_fitCons_rankscore": "0.34648",
        "HGVSc": "NM_0001.7:c.797A>G",
        "HGVSg": "chr1:g.12A>G",
        "HGVSp": "ENSP00000326281.7:p.Ile266Thr",
        "HUVEC_fitCons_rankscore": "0.14980",
        "IMPACT": "MODERATE",
        "INTRON": None,
        "LINSIGHT_rankscore": None,
        "LIST-S2_rankscore": "0.79272",
        "LRT_converted_rankscore": "0.84330",
        "M-CAP_rankscore": "0.94614",
        "MPC_rankscore": "0.60511",
        "MVP_rankscore": "0.98737",
        "MaxEntScan_alt": None,
        "MaxEntScan_diff": None,
        "MaxEntScan_ref": None,
        "MetaLR_rankscore": "0.97893",
        "MetaSVM_rankscore": "0.99004",
        "MutPred_rankscore": "0.79267",
        "MutationAssessor_rankscore": "0.52218",
        "MutationTaster_converted_rankscore": "0.81001",
        "PROVEAN_converted_rankscore": "0.80943",
        "PolyPhen": "probably_damaging(0.958)",
        "Polyphen2_HDIV_rankscore": "0.56202",
        "Polyphen2_HVAR_rankscore": "0.67449",
        "PrimateAI_rankscore": "0.74568",
        "Protein_position": "266/815",
        "REVEL_rankscore": "0.98869",
        "SIFT4G_converted_rankscore": "0.63918",
        "SIFT_converted_rankscore": "0.91255",
        "SYMBOL": "CAPN3",
        "SiPhy_29way_logOdds_rankscore": "0.75351",
        "SpliceAI_pred_DP_AG": "4",
        "SpliceAI_pred_DP_AL": "10",
        "SpliceAI_pred_DP_DG": "8",
        "SpliceAI_pred_DP_DL": "4",
        "SpliceAI_pred_DS_AG": "0.00",
        "SpliceAI_pred_DS_AL": "0.00",
        "SpliceAI_pred_DS_DG": "0.00",
        "SpliceAI_pred_DS_DL": "0.00",
        "SpliceAI_pred_SYMBOL": "CAPN3",
        "VARIANT_CLASS": "SNV",
        "VEST4_rankscore": "0.93135",
        "bStatistic_converted_rankscore": "0.80015",
        "fathmm-MKL_coding_rankscore": "0.97318",
        "fathmm-XF_coding_rankscore": "0.82512",
        "gnomADg": None,
        "gnomADg_AF_AFR": None,
        "gnomADg_AF_AMR": None,
        "gnomADg_AF_ASJ": None,
        "gnomADg_AF_EAS": None,
        "gnomADg_AF_FIN": None,
        "gnomADg_AF_NFE": None,
        "gnomADg_AF_OTH": None,
        "integrated_fitCons_rankscore": "0.35715",
        "phastCons100way_vertebrate_rankscore": "0.71638",
        "phastCons17way_primate_rankscore": "0.91618",
        "phastCons30way_mammalian_rankscore": "0.86279",
        "phyloP100way_vertebrate_rankscore": "0.87040",
        "phyloP17way_primate_rankscore": "0.52053",
        "phyloP30way_mammalian_rankscore": "0.56520",
        "SOMATIC":"r",
        "PHENO":"",
        "PUBMED":""
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

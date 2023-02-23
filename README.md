# SEAL db - Simple, Efficient And Lite database for NGS

## Installation

First of all clone the repo :
```bash
git clone https://github.com/mobidic/seal.git
```

### Install dependencies

#### With Conda

Please install conda ([documentation here](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html))

`conda env create -f environment.yml`

#### VEP

> __If you have install all dependencies from conda you need to activate your
environment by launching this command :__ `conda activate seal`

You need to complete VEP installation (https://www.ensembl.org/info/docs/tools/vep/script/vep_download.html#installer) :
`vep_install -a cf -s homo_sapiens -y GRCh37 -c /output/path/to/GRCh37/vep --CONVERT`

##### Plugins

Install VEP plugins (https://www.ensembl.org/info/docs/tools/vep/script/vep_plugins.html) :
  - dbNSFP
  - MaxEntScan
  - SpliceAI
  - dbscSNV
  - GnomAD

*__A more complete guide will be written soon__*

### Configuration of the app

- Please edit file `seal/static/vep.config.json` and replace those variable:
  - `{dir_vep}` => `/path/to/vep`
  - `{dir_vep_plugins}` => `/path/to/vep/plugins`
  - `{GnomAD_vcf}` => `/path/to/gnomad.vcf`
  - `{fasta}` => `/path/to/genome.fa.gz`

- Please edit file `seal/config.yaml` :
  - create your secret app key.
  - you can edit following what you need

### Initialise Database

> If you install all dependencies with conda make sure to activate the
> environment :
> ```bash
> conda activate seal
> ```

> __This section is a bit tricky. We work on it to simplify the process.__

- Start database server
```bash
initdb -D ${PWD}/seal/seal.db
pg_ctl -D ${PWD}/seal/seal.db -l ${PWD}/seal/seal.db.log start
```
- Issue [#26](https://github.com/mobidic/SEAL/issues/26)
  - comment line on `seal/__init__.py`
  ```python
  # from seal import routes
  # from seal import schedulers
  # from seal import admin
  ```
- Initialize database

The database will be intialise with an admin user :
  - username : `admin`
  - password : `password`
```bash
python insertdb.py
flask db init
flask db migrate -m "Init DataBase"
```
- __[Optional]__ Add Gene as Region (usefull to create _in-silico_ panels)
```bash
wget -qO- http://hgdownload.cse.ucsc.edu/goldenpath/hg19/database/ncbiRefSeq.txt.gz   | gunzip -c - | awk -v OFS="\t" '{ if (!match($13, /.*-[0-9]+/)) { print $3, $5-2000, $6+2000, $13; } }' -  | sort -u > ncbiRefSeq.hg19.sorted.bed
python insert_genes.py
```
- __[Optional]__ Add OMIM (for transmission and relative diseases) __/!\ YOU NEED AN OMIM ACCESS TO DOWNLOAD FILE__
```bash
wget -qO- https://data.omim.org/downloads/{{YOUR API KEY}}/genemap2.txt
python insert_OMIM.py
```
- Issue [#26](https://github.com/mobidic/SEAL/issues/26)
  - uncomment line on `seal/__init__.py`
  ```python
  from seal import routes
  from seal import schedulers
  from seal import admin
  ```

### Launch the app

Now you can launch the app :
```
flask --app seal --debug run
```

__Please report any issue [here](https://github.com/mobidic/SEAL/issues/new)__

## Tips & Tricks

Here are listed some usefull *Tips & Tricks*.

- Update database
```bash
flask db migrate -m "message"
flask db upgrade
```
- Start/Stop the datatabase server
```bash
pg_ctl -D ${PWD}/seal/seal.db -l ${PWD}/seal/seal.db.log start
pg_ctl -D ${PWD}/seal/seal.db -l ${PWD}/seal/seal.db.log stop
```

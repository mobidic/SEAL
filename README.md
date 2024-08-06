
# SEAL db - Simple, Efficient And Lite database for NGS

![seal.gif](docs/img/seal.gif)

SEAL db is a Python project that provides a simple, efficient, and lightweight
database for Next Generation Sequencing (NGS) data. SEAL db is built with the
Flask framework and uses PostgreSQL as the backend database. It includes a web
interface that allows users to upload and query NGS data.

__Please report any issue [here](https://github.com/mobidic/SEAL/issues/new)__

## Installation

To install SEAL db, first clone the repository from GitHub:

```bash
git clone https://github.com/mobidic/seal.git
```

SEAL db requires several dependencies to be installed, which can be done either
with Conda or manually.

### Install dependencies

#### With Conda

To install dependencies with Conda, first install Conda if it is not already installed. Conda installation instructions can be found ([here](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html))

After installing Conda, create a new environment using the environment.yml file
provided with SEAL db:

`conda env create -f environment.yml`

#### Installing VEP

> __If you have install all dependencies from conda you need to activate your
environment by launching this command:__ `conda activate seal`

After installing dependencies, you need to install VEP (Variant Effect
Predictor), which is used by SEAL db to annotate variants. The installation
instructions for VEP can be found
[here](https://www.ensembl.org/info/docs/tools/vep/script/vep_download.html#installer).

For conda environment:

`vep_install -a cf -s homo_sapiens -y GRCh37 -c /output/path/to/GRCh37/vep --CONVERT`

After installing VEP, you need to install several VEP plugins that are used by
SEAL db:
  - dbNSFP
  - MaxEntScan
  - SpliceAI
  - dbscSNV
  - GnomAD

The installation instructions for VEP plugins can be found ([here](https://www.ensembl.org/info/docs/tools/vep/script/vep_plugins.html)).

*__A more complete guide will be written soon__*

### Configuration

After installing dependencies and VEP, you need to configure the app by editing
two files:
- `seal/static/vep.config.json`
- `seal/config.yaml`

In `seal/static/vep.config.json`, replace the following variables with the appropriate paths:
- `{dir_vep}` => `/path/to/vep`
- `{dir_vep_plugins}` => `/path/to/vep/plugins`
- `{GnomAD_vcf}` => `/path/to/gnomad.vcf`
- `{fasta}` => `/path/to/genome.fa.gz`

In `seal/config.yaml`, create your secret app key and edit other settings as
needed.

### Initialization of the database

> If you install all dependencies with conda make sure to activate the
> environment :
> ```bash
> conda activate seal
> ```

> comment line on `seal/__init__.py` (see [#26](https://github.com/mobidic/SEAL/issues/26))
> ```python
> # from seal import routes
> # from seal import schedulers
> # from seal import admin
> ```

To initialise the database, start the database server and run the following
commands:

```bash
initdb -D ${PWD}/seal/seal.db
pg_ctl -D ${PWD}/seal/seal.db -l ${PWD}/seal/seal.db.log start
psql postgres -c "CREATE DATABASE seal;"
python insertdb.py -p password
```

> uncomment line on `seal/__init__.py` (see [#26](https://github.com/mobidic/SEAL/issues/26))
> ```python
> from seal import routes
> from seal import schedulers
> from seal import admin
> ```

```bash
flask --app seal --debug db init
flask --app seal --debug db migrate -m "Init DataBase"
```

The database will be intialise with an admin user :
- username : `admin`
- password : `password`

Optionally, you can also add gene regions and OMIM data to the database.

```bash
wget -qO- http://hgdownload.cse.ucsc.edu/goldenpath/hg19/database/ncbiRefSeq.txt.gz   | gunzip -c - | awk -v OFS="\t" '{ if (!match($13, /.*-[0-9]+/)) { print $3, $5-2000, $6+2000, $13; } }' -  | sort -u > ncbiRefSeq.hg19.sorted.bed
python insert_genes.py
```
```bash
wget -qO- https://data.omim.org/downloads/{{YOUR API KEY}}/genemap2.txt
python insert_OMIM.py
```

### Launching the App

Finally, to launch the app, run the following command:
```bash
flask --app seal --debug run
```

## Tips & Tricks

Here are some useful *Tips & Tricks* working with SEAL:

- Update database
```bash
flask --app seal --debug db migrate -m "message"
flask --app seal --debug db upgrade
```

- Start/Stop the datatabase server
```bash
pg_ctl -D ${PWD}/seal/seal.db -l ${PWD}/seal/seal.db.log start
pg_ctl -D ${PWD}/seal/seal.db -l ${PWD}/seal/seal.db.log stop
```

- Dump/Restore the database
```bash
pg_dump -O -C --if-exists --clean --inserts -d seal -x -F t -f seal.tar
pg_restore -x -f seal.tar
```

- Multiple instances of SEAL (maybe usefull for differents projects, teams, tests, stages...)

*Edit the config.yaml*
```yaml
  SQLALCHEMY_DATABASE_URI: 'postgresql:///seal-bis'
```
*Follow the [initialization steps](#initialization-of-the-database) with this new database (edit this ommand)*
```bash
psql postgres -c "CREATE DATABASE seal-bis;"
```


# License

GNU General Public License v3.0 or later

See [COPYING](COPYING) to see the full text.

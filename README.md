# SEAL - System of Experiments & Analysis for the Lab

## Installation

First of all clone the repo :
https://github.com/Char-Al/seal.git

### Install dependencies
#### Conda
Please install conda (see : https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html)

`conda env create -f environment.yml`

#### Launch the app

```bash
conda activate seal
export FLASK_APP=seal
export FLASK_ENV=development
export PYTHONPATH=${PWD}
initdb -D ${PWD}/seal/seal.db
pg_ctl -D ${PWD}/seal/seal.db -l ${PWD}/seal/seal.db.log start
flask run
pg_ctl -D ${PWD}/seal/seal.db -l ${PWD}/seal/seal.db.log stop
```

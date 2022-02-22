# SEAL - System of Experiments & Analysis for the Lab

## Installation

First of all clone the repo :
```bash
git clone https://github.com/mobidic/seal.git
```

### Install dependencies

#### Conda

Please install conda ([documentation here](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html))

`conda env create -f environment.yml`

### Execution

This is an example of a typical execution of this Flask application on :
- __Operating System__: Debian GNU/Linux 10 (buster)
- __Kernel__: Linux 4.19.0-17-amd64
- __Architecture__: x86-64

It can be slightly different depending on your Operating System, Kernel, Architecture, Environment...

#### Step by step

- Activate your virtual environment :
```bash
conda activate seal
````
- Export the environment variables
```bash
export FLASK_APP=seal
export FLASK_ENV=development
export PYTHONPATH=${PWD}
```
  - __[Optional]__ If you use [MobiDetails](https://mobidetails.iurc.montp.inserm.fr/MD/), add your API key
```bash
export API_KEY_MD="YOUR_MOBIDETAILS_API_KEY"
```
- Start database server
```bash
initdb -D ${PWD}/seal/seal.db
pg_ctl -D ${PWD}/seal/seal.db -l ${PWD}/seal/seal.db.log start
```
  - __[Optional]__ Initialize database
  ```bash
  python insertdb.py
  flask db init
  flask db migrate -m "Init DataBase"
  ```
- Launch the flask app
```bash
flask run
```

### Miscellaneous

- Update database
```bash
flask db migrate -m "message"
flask db upgrade
```
- Stop the server
```bash
pg_ctl -D ${PWD}/seal/seal.db -l ${PWD}/seal/seal.db.log stop
```

#### All commands

```bash
conda activate seal
export FLASK_APP=seal
export FLASK_ENV=development
export PYTHONPATH=${PWD}
# export API_KEY_MD="YOUR_MOBIDETAILS_API_KEY"
initdb -D ${PWD}/seal/seal.db
pg_ctl -D ${PWD}/seal/seal.db -l ${PWD}/seal/seal.db.log start
# python insertdb.py
# flask db init
# flask db migrate -m "Init DataBase"
flask run
# flask db migrate -m "message"
# flask db upgrade
# pg_ctl -D ${PWD}/seal/seal.db -l ${PWD}/seal/seal.db.log stop
```

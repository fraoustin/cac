# CAC 85

## Development

todo


### prerequis

> pip install -r REQUIREMENTS.txt

for run quality

> pip install flake8

### run quality

> flake8

### run test

> python -m unittest discover tests

### build image

> docker build -t edit .

### run image

> docker run --rm --name cac cac

> docker run --rm --name cac -p 5000:5000 -v C:/Users/faoustin/Workspaces/cac/files/uploads:/cac/files/uploads edit

> docker run --rm --name cac cac python -m unittest discover tests




export APP_BASE_URL=https://ide.fraoustin.fr/proxy/5000
export APP_DEBUG=true
export PYTHONPATH=:/config/project/dbml-to-sqlalchemy/
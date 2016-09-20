VIRTUAL_ENV = $(PWD)/.env

export

develop:
	virtualenv -p python2 .env
	.env/bin/pip install -r requirements.txt

deploy:
	./virtualenv-lambda-push.sh update

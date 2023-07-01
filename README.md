# My Personal Web Page [Web Site](https://cihatertem.dev)

The portfolio web site based on **Django** framework. It is ready to go & **dockerized** for **swarm cluster** on **AWS EC2 nodes**.

Staticfiles are served from **AWS S3 Bucket**.

The project uses **Traefik** for reverse proxy and **SSL cert** process.

Database requirement was met with Postgres image in swarm cluster.

The Github action is just to build and push docker image to docker hub repository.

## environtment example

Environment settings inside **environments/cihatdev_environment.txt"

* Email for website contact form's endpoint.
* DEBUG 1 (True) or 0 (False)
* DB_HOST willnot need to change if docker-compose-postgres' definition.

```shell
ADMIN_ADDRESS=CHANGE/WITH/YOUR/ADMIN/ENDPOINT
AlLOWED_HOSTS=example.com,www.example.com
EMAIL=CHANGE_WITH_EMAIL
DEBUG=1
POSTGRES_DB_CIHAT=CHANGE_WITH_DATABASE_NAME
DB_HOST=db
CIHAT_BUCKET_NAME=CHANGE_WITH_S3_BUCKET_NAME
AWS_S3_REGION_NAME=CHANGE_WITH_AWS_REGION_NAME
```

## docker-compose files

3 Docker compose files are setted up for swarm cluster and there are several **CHANGE_WITH** sections in the files.

## aws_user_data.sh

This file is for AWS EC2 instance creation page's **USER DATA** section. This scipt targets swarm worker instance. And it contains server harden & network optimization settings. There are several **CHANGE_WITH** sections.
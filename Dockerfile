# syntax=docker/dockerfile:experimental

FROM 482956169056.dkr.ecr.us-east-1.amazonaws.com/uw/python-postgres-build:v0.4 as build
COPY canvas_account_admin_tools/requirements/*.txt /code/
RUN --mount=type=ssh,id=build_ssh_key ./python_venv/bin/pip3 install gunicorn && ./python_venv/bin/pip3 install -r aws.txt
COPY . /code/
RUN chmod a+x /code/docker-entrypoint.sh

FROM 482956169056.dkr.ecr.us-east-1.amazonaws.com/uw/python-postgres-base:v0.3
COPY --from=build /code /code/
ENV PYTHONUNBUFFERED 1
WORKDIR /code
ENTRYPOINT ["/code/docker-entrypoint.sh"]
EXPOSE 8000
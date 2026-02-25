FROM python:3.10.5

EXPOSE 8000
WORKDIR /usr/src/app

ADD requirements.txt /usr/src/app
RUN pip install -r requirements.txt

ADD . /usr/src/app

# Start Gunicorn with 3 workers (processes), based on the formula 2 * CPU + 1 for a t2.micro (1 vCPU) instance
CMD gunicorn --bind 0.0.0.0:8000 project.wsgi:application --workers 3 --timeout 1200



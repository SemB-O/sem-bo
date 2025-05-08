FROM python:3.10.5

EXPOSE 8000
WORKDIR /project

ADD requirements.txt /project
RUN pip install -r requirements.txt

ADD ./project /project

# Start Gunicorn with 3 workers (processes), based on the formula 2 * CPU + 1 for a t2.micro (1 vCPU) instance
CMD gunicorn --bind 0.0.0.0:8000 project.wsgi:application --workers 3



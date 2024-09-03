# define base image
FROM python:3.6

# set working directory
WORKDIR /app

COPY /app/backend .

# copy 'app' subfolder content to current directory, i.e. '/app'
COPY ./app/dockerfile_requirements .

ENV TZ="America/Sao_Paulo"

# run command at build time
RUN apt-get update \
	&& apt-get install -y zbar-tools -y \
	&& apt-get install -y poppler-utils -y \
	&& apt-get install build-essential cmake -y \	
    && pip install -r requirements.txt \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
	&& echo $TZ > /etc/timezone	

EXPOSE 8000
CMD ["gunicorn", "--worker-tmp-dir", "/dev/shm", "--workers=1", "--threads=4", "--log-level=debug", "--access-logfile=/app/assets/log/gunicorn-facial_ac.log", "--log-file=/app/assets/log/gunicorn-facial.log", "--capture-output", "--timeout", "1000", "--bind=0.0.0.0:8000", "--chdir", "/app", "api_facial:app"] #gunicorn Rec-Facial

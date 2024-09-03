# define base image
FROM python:3.6

# set working directory
WORKDIR /app

COPY /app/backend .

# copy 'app' subfolder content to current directory, i.e. '/app'
COPY ./app/dockerfile_requirements .

# run command at build time
RUN apt-get update \
    && apt-get install tesseract-ocr -y \
	&& apt-get install -y zbar-tools -y \
	&& apt-get install -y poppler-utils -y \
	&& apt-get install build-essential cmake -y \
	&& cp -r por.traineddata /usr/share/tesseract-ocr/4.00/tessdata/ \
	&& cp -r osd.traineddata /usr/share/tesseract-ocr/4.00/tessdata/ \
	&& cp -r eng.traineddata /usr/share/tesseract-ocr/4.00/tessdata/ \
    && pip install -r requirements.txt \
	&& rm eng.traineddata \
	&& rm osd.traineddata \
    && rm por.traineddata \
    && rm requirements.txt 	

EXPOSE 8000
CMD ["uwsgi", "api_renach_uwsgi.ini"]


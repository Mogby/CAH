FROM python

RUN mkdir /cah

COPY . /cah/

WORKDIR /cah/rest_api

RUN pip install -r requirements.txt

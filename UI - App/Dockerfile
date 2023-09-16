FROM python:3.10.9

WORKDIR /app

ADD . /app

RUN pip install --upgrade pip

RUN pip install -r requirements.txt

EXPOSE 8501

ENTRYPOINT [ "streamlit","run"]

CMD ["app.py"]
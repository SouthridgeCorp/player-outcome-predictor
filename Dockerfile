FROM python:3.9
WORKDIR /docker_app
COPY . /docker_app
RUN rm -rf venv
RUN sh installation.sh
RUN . venv/bin/activate
EXPOSE 8501
ENTRYPOINT ["streamlit", "run"]
CMD ["app.py"]
FROM python:latest

ENV VIRTUAL_ENV=/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"


COPY requirements.txt .
RUN pip install -r requirements.txt


COPY . .
CMD ["python", "app/__main__.py"]
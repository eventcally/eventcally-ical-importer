FROM python:3.10

# Add rsync
RUN apt update -qq && apt upgrade -y && apt autoremove -y
RUN apt install -y rsync redis-tools curl && apt autoremove -y

EXPOSE 5000

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install pip requirements
COPY requirements.txt .
RUN python -m pip install --upgrade pip
RUN python -m pip install -r requirements.txt

WORKDIR /app
COPY . /app

RUN chmod u+x ./entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]

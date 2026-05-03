FROM apache/airflow:2.8.1
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt && \
    pip install --no-cache-dir --force-reinstall \
        "flask-session==0.5.0" \
        "flask==2.2.5" \
        "werkzeug==2.3.7"

# Patch flask-session datetime timezone comparison bug
RUN sed -i 's/saved_session.expiry <= datetime.utcnow()/saved_session.expiry.replace(tzinfo=None) <= datetime.utcnow()/' \
    /home/airflow/.local/lib/python3.8/site-packages/flask_session/sessions.py

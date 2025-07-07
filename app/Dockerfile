FROM llm_small_deps:v1 as base_deps

# Final Stage:
FROM python:3.10.11-slim-buster as final

WORKDIR /app

# Install any system packages you still need
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libaio1 \
        wget \
        unzip \
        nginx && \
    rm -rf /var/lib/apt/lists/*

RUN pip install gunicorn

RUN pip install --upgrade pip \
    && pip install protobuf sentencepiece \
    pip install flask opentelemetry-api \
            opentelemetry-sdk \
            opentelemetry-instrumentation \
            opentelemetry-exporter-otlp \
            opentelemetry-instrumentation-flask \
            opentelemetry-instrumentation-logging


RUN bash -c 'mkdir -p /var/log/containers'

# Copy dependencies, oracle, java, models, etc. from your llm_deps:v1 base
COPY --from=base_deps /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=base_deps /opt/oracle /opt/oracle
COPY --from=base_deps /etc/ld.so.conf.d/oracle-instantclient.conf /etc/ld.so.conf.d/oracle-instantclient.conf
COPY --from=base_deps /mnt/models/Deepseek /mnt/models/Deepseek
COPY --from=base_deps /root/nltk_data /root/nltk_data
COPY --from=base_deps /usr/lib/jvm/java-17-openjdk-amd64 /usr/lib/jvm/java-17-openjdk-amd64

# Set all environment variables required
ENV LD_LIBRARY_PATH=/opt/oracle/instantclient_19_18:$LD_LIBRARY_PATH
ENV PATH=/opt/oracle/instantclient_19_18:$PATH
ENV PYTHONPATH=/usr/local/lib/python3.10/site-packages
ENV NLTK_DATA=/root/nltk_data
ENV MODEL_PATH=/mnt/models/Deepseek
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH

# Copy your actual application code
COPY . .

COPY flask.conf /etc/nginx/nginx.conf

EXPOSE 1999

ENTRYPOINT ["sh", "/app/run.sh"]

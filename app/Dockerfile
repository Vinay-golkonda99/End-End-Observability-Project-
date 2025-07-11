# Stage 1: Prebuilt base with model + deps
FROM vinaygolkonda99/llm_deps:otel AS base_deps

# Stage 2: Final container
FROM python:3.10.11-slim-buster AS final

WORKDIR /app

# System packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libaio1 \
        wget \
        unzip \
        nginx \
    && rm -rf /var/lib/apt/lists/*

# Required for Promtail/Loki logging
RUN mkdir -p /var/log/containers

# Copy ML + Oracle deps from base
COPY --from=base_deps /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=base_deps /opt/oracle /opt/oracle
COPY --from=base_deps /etc/ld.so.conf.d/oracle-instantclient.conf /etc/ld.so.conf.d/oracle-instantclient.conf
COPY --from=base_deps /mnt/models/Deepseek /mnt/models/Deepseek
COPY --from=base_deps /root/nltk_data /root/nltk_data
COPY --from=base_deps /usr/lib/jvm/java-17-openjdk-amd64 /usr/lib/jvm/java-17-openjdk-amd64

# 🔥 NOW install Python deps AFTER base COPY (important!)
RUN pip install --upgrade pip && \
    pip install --no-cache-dir gunicorn
    

# Environment variables
ENV LD_LIBRARY_PATH=/opt/oracle/instantclient_19_18:$LD_LIBRARY_PATH
ENV PATH=/opt/oracle/instantclient_19_18:$PATH
ENV PYTHONPATH=/usr/local/lib/python3.10/site-packages
ENV NLTK_DATA=/root/nltk_data
ENV MODEL_PATH=/mnt/models/Deepseek
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH
ENV PATH="/root/.local/bin:${PATH}"

# Copy app source + Nginx config
COPY . .
COPY flask.conf /etc/nginx/nginx.conf

# Expose port used in Nginx config
EXPOSE 80

# Entrypoint to run Gunicorn + Nginx
ENTRYPOINT ["sh", "/app/run.sh"]

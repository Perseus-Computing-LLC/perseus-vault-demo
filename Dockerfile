FROM local/perseus-vault:2.22.0-embedded-20260730

USER 0:0
WORKDIR /app
COPY app.py index.html ./
RUN mkdir -p /data && chown -R 10001:10001 /app /data

ENV PERSEUS_VAULT_BIN=/usr/local/bin/perseus-vault \
    DEMO_DB=/data/demo.db \
    PORT=8092
EXPOSE 8092

USER 10001:10001
CMD ["python3", "/app/app.py"]

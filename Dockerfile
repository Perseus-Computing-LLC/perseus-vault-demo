FROM local/perseus-vault:2.23.2-aar-1205-7b4b42b6

USER 0:0
WORKDIR /app
COPY app.py index.html ./
RUN mkdir -p /data && chown -R 10001:10001 /app /data

ENV PERSEUS_VAULT_BIN=/usr/local/bin/perseus-vault \
    DEMO_DB=/data/demo.db \
    PORT=8092 \
    VAULT_VERSION=2.23.2 \
    SOURCE_REPOSITORY=https://github.com/Perseus-Computing-LLC/perseus-vault-demo \
    SOURCE_REVISION=main \
    LEDGER_URL=https://ledger.perseus.observer

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD ["python3", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8092/healthz', timeout=3).read()"]
EXPOSE 8092

USER 10001:10001
ENTRYPOINT []
CMD ["python3", "/app/app.py"]

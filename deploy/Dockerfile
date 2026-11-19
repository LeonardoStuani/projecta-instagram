# Painel da agência (Instagram) · só Python da biblioteca padrão + Pillow e qrcode.
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir pillow==11.0.0 qrcode==8.0
# O repositório inteiro entra como volume em /app (assim git pull atualiza o painel sem rebuild).
WORKDIR /app
ENV PYTHONUTF8=1 PYTHONUNBUFFERED=1 PAINEL_PORTA=8765 PAINEL_BIND=0.0.0.0
RUN useradd -m -u 1000 painel && git config --system --add safe.directory /app
USER painel
EXPOSE 8765
CMD ["python", "scripts/painel.py", "--sem-navegador"]


FROM python:3.12.11-slim

ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin/:$PATH"

WORKDIR /app

COPY pyproject.toml uv.lock* ./
RUN uv venv --python 3.12.11 && uv sync

RUN echo '#!/bin/bash\nuv run streamlit run app.py --server.headless=true --server.port 8085 --server.address 0.0.0.0 --server.fileWatcherType none' > /app/start.sh && chmod +x /app/start.sh

COPY . .

EXPOSE 8085

CMD ["/app/start.sh"]
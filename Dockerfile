# Python 3.10を使用
FROM python:3.10-slim

WORKDIR /app

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

# 必要なシステムパッケージをインストール
RUN apt-get update && apt-get install -y \
    git \
    gcc \
    build-essential \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Rustツールチェーンをインストール
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y --no-modify-path
ENV PATH="/root/.cargo/bin:${PATH}"

# pipのアップグレードとNumPyのインストール
RUN pip install --no-cache-dir -U pip setuptools wheel

# requirements.txtをコピー
COPY requirements.txt ./

# パッケージをインストール
RUN pip install --no-cache-dir -r requirements.txt
RUN python -c "from transformers import AutoModel; AutoModel.from_pretrained('megagonlabs/transformers-ud-japanese-electra-base-ginza-510')"

# アプリケーションコードをコピー
COPY anonymization_basic.py ./

# エントリーポイントを設定
ENTRYPOINT ["python", "anonymization_basic.py"]

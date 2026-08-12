# Code Ocean capsule environment for "Same Transactions, Different Alarms".
# Offline reproduction only: no network, no API keys. Base image served from
# Code Ocean's registry; pinned pip packages match code/requirements.txt.
FROM registry.codeocean.com/codeocean/py-r:python3.12.8-R4.4.2-JupyterLab4.3.5-RStudiorstudio-server-2024.12.1-563-ubuntu22.04

ARG DEBIAN_FRONTEND=noninteractive

RUN pip install -U --no-cache-dir \
    numpy==2.2.6 \
    scikit-learn==1.7.2 \
    pyyaml==6.0.3 \
    pydantic==2.13.4

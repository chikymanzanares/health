FROM python:3.12-slim

WORKDIR /app

COPY frontend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt grpcio-tools==1.68.1

COPY proto /app/proto
COPY frontend /app/frontend

WORKDIR /app/frontend
RUN python -m grpc_tools.protoc \
    -I../proto \
    --python_out=. \
    --grpc_python_out=. \
    ../proto/enums.proto \
    ../proto/eligibility.proto \
    ../proto/authorization.proto \
    ../proto/claim.proto \
    ../proto/insurance_service.proto

ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py
ENV GRPC_HOST=backend
ENV GRPC_PORT=50051
ENV DATABASE_PATH=/data/health.db

EXPOSE 5000
CMD ["python", "app.py"]

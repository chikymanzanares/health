FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY proto /app/proto
COPY backend /app/backend

WORKDIR /app/backend
RUN python -m grpc_tools.protoc \
    -I../proto \
    --python_out=infrastructure/grpc/generated \
    --grpc_python_out=infrastructure/grpc/generated \
    ../proto/enums.proto \
    ../proto/eligibility.proto \
    ../proto/authorization.proto \
    ../proto/claim.proto \
    ../proto/insurance_service.proto

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/backend:/app/backend/infrastructure/grpc/generated
EXPOSE 50051
CMD ["python", "main.py"]

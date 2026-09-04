.PHONY: help up down build logs proto proto-clean shell-front shell-back

PROTO_DIR := proto
PROTOS := \
	$(PROTO_DIR)/enums.proto \
	$(PROTO_DIR)/eligibility.proto \
	$(PROTO_DIR)/authorization.proto \
	$(PROTO_DIR)/claim.proto \
	$(PROTO_DIR)/insurance_service.proto
BACKEND_OUT := backend/infrastructure/grpc/generated
FRONTEND_OUT := frontend
GENERATED := \
	enums_pb2.py \
	enums_pb2_grpc.py \
	eligibility_pb2.py \
	eligibility_pb2_grpc.py \
	authorization_pb2.py \
	authorization_pb2_grpc.py \
	claim_pb2.py \
	claim_pb2_grpc.py \
	insurance_service_pb2.py \
	insurance_service_pb2_grpc.py

help:
	@echo "Targets:"
	@echo "  make up          - build and start frontend + gRPC backend (docker compose)"
	@echo "  make down        - stop containers"
	@echo "  make build       - build images (recompiles .proto inside Dockerfiles)"
	@echo "  make logs        - follow container logs"
	@echo "  make proto       - compile .proto → Python stubs (local, for IDE / host runs)"
	@echo "  make proto-clean - remove generated *_pb2*.py files"

up:
	docker compose up --build -d
	@echo ""
	@echo "Web UI:  http://127.0.0.1:5000"
	@echo "gRPC:    localhost:50051"
	@echo "Login:   juanjo / juanjo01  or  tom / tom01"
	@echo ""
	@echo "Note: changing a .proto requires rebuild (make up / make build)."
	@echo "      Optional host stubs: make proto"

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

proto:
	@mkdir -p $(BACKEND_OUT)
	@if python3 -c "import grpc_tools.protoc" 2>/dev/null; then \
	  python3 -m grpc_tools.protoc -I $(PROTO_DIR) --python_out=$(BACKEND_OUT) --grpc_python_out=$(BACKEND_OUT) $(PROTOS); \
	  python3 -m grpc_tools.protoc -I $(PROTO_DIR) --python_out=$(FRONTEND_OUT) --grpc_python_out=$(FRONTEND_OUT) $(PROTOS); \
	else \
	  docker run --rm -v "$(CURDIR):/work" -w /work python:3.12-slim \
	    bash -c 'pip install -q grpcio-tools==1.68.1 protobuf==5.29.2 && \
	      mkdir -p $(BACKEND_OUT) && \
	      python -m grpc_tools.protoc -I $(PROTO_DIR) --python_out=$(BACKEND_OUT) --grpc_python_out=$(BACKEND_OUT) $(PROTOS) && \
	      python -m grpc_tools.protoc -I $(PROTO_DIR) --python_out=$(FRONTEND_OUT) --grpc_python_out=$(FRONTEND_OUT) $(PROTOS)'; \
	fi
	@echo "Generated stubs in $(BACKEND_OUT)/ and $(FRONTEND_OUT)/"

proto-clean:
	@for f in $(GENERATED); do rm -f $(BACKEND_OUT)/$$f $(FRONTEND_OUT)/$$f; done
	rm -f backend/insurance_pb2.py backend/insurance_pb2_grpc.py
	rm -f frontend/insurance_pb2.py frontend/insurance_pb2_grpc.py

shell-front:
	docker compose exec frontend bash

shell-back:
	docker compose exec backend bash

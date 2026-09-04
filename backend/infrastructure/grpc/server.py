"""gRPC server bootstrap."""

from __future__ import annotations

import logging
from concurrent import futures

import grpc
from infrastructure.grpc.generated import insurance_service_pb2_grpc
from infrastructure.grpc.servicer import InsuranceGrpcServicer

log = logging.getLogger("insurance-grpc")


def serve(
    servicer: InsuranceGrpcServicer,
    host: str = "0.0.0.0",
    port: int = 50051,
) -> None:
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=8))
    insurance_service_pb2_grpc.add_InsuranceServiceServicer_to_server(servicer, server)
    addr = f"{host}:{port}"
    server.add_insecure_port(addr)
    server.start()
    log.info("Insurance gRPC listening on %s", addr)
    server.wait_for_termination()

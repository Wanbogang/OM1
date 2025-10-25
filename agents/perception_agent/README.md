# PerceptionAgent (stub)
Purpose: inference wrapper for edge perception models (ONNX).
API (example):
- gRPC service: Perception.Detect(stream Image) -> DetectionList
- Output: [{bbox, polygon, class, score, timestamp}]
Notes: add proto files and example inference wrapper in next PR.

# Production Deployment Guide

## Prerequisites

- Kubernetes cluster (1.28+) with GPU nodes (NVIDIA)
- `kubectl` and `helm` configured
- Container registry (GCR, ECR, or Docker Hub)
- Domain name with TLS certificate

## 1. Build & Push Container Images

```bash
# API
docker build -f infra/Dockerfile.api -t your-registry/veridian-api:latest .
docker push your-registry/veridian-api:latest

# Workers
docker build -f infra/Dockerfile.worker -t your-registry/veridian-worker:latest .
docker push your-registry/veridian-worker:latest

# Dashboard
docker build -f infra/Dockerfile.dashboard -t your-registry/veridian-dashboard:latest dashboard/
docker push your-registry/veridian-dashboard:latest
```

## 2. Create Kubernetes Secrets

```bash
kubectl create secret generic veridian-secrets \
  --from-literal=ANTHROPIC_API_KEY=<key> \
  --from-literal=TAVILY_API_KEY=<key> \
  --from-literal=DATABASE_URL=<url> \
  --from-literal=REDIS_URL=<url> \
  --from-literal=JWT_SECRET_KEY=$(openssl rand -hex 32)
```

## 3. Create ConfigMap

```bash
kubectl create configmap veridian-config \
  --from-literal=QDRANT_URL=http://qdrant:6333 \
  --from-literal=NEO4J_URI=bolt://neo4j:7687 \
  --from-literal=MINIO_ENDPOINT=minio:9000
```

## 4. Deploy Infrastructure

```bash
# PostgreSQL (using Helm)
helm install postgres bitnami/postgresql --set auth.postgresPassword=<password>

# Redis
helm install redis bitnami/redis --set auth.enabled=false

# Qdrant
kubectl apply -f infra/k8s/qdrant-deployment.yaml

# Neo4j
helm install neo4j neo4j/neo4j --set neo4j.password=<password>
```

## 5. Deploy Application

```bash
kubectl apply -f infra/k8s/api-deployment.yaml
kubectl apply -f infra/k8s/workers-deployment.yaml
kubectl apply -f infra/k8s/ml-serving/torchserve-deployment.yaml
kubectl apply -f infra/k8s/keda-scalers.yaml
```

## 6. Run Migrations

```bash
kubectl exec -it deploy/veridian-api -- alembic upgrade head
```

## Scaling Recommendations

| Component      | Min Replicas | Max Replicas | Scaling Metric        |
| -------------- | ------------ | ------------ | --------------------- |
| API            | 2            | 10           | CPU 70%               |
| Worker (text)  | 1            | 8            | CPU 75%               |
| Worker (image) | 1            | 6            | CPU 70%               |
| Worker (audio) | 0            | 4            | Redis queue depth > 5 |
| Worker (video) | 0            | 3            | Redis queue depth > 3 |
| TorchServe     | 1            | 2            | GPU utilization 80%   |

## Monitoring Setup

### Prometheus + Grafana

```bash
helm install prometheus prometheus-community/kube-prometheus-stack
```

Key metrics to monitor:
- `veridian_analyses_total` — total analyses processed
- `veridian_avg_processing_ms` — average latency
- `celery_task_duration_seconds` — per-task duration
- GPU memory utilization on ML worker nodes
- Redis queue depth per worker type

### Alerting Rules

- **P1**: API latency > 5s for > 5 minutes
- **P1**: Worker dead-letter queue > 10 messages
- **P2**: GPU OOM events on ML workers
- **P2**: Database connection pool exhaustion
- **P3**: Cache hit rate < 50%

## Zero-Downtime Deploys

PodDisruptionBudgets ensure at least 1 replica of each component stays running during rolling updates:

```bash
kubectl rollout restart deployment veridian-api
kubectl rollout status deployment veridian-api
```

## Backup Strategy

- **PostgreSQL**: Automated daily backups via `pg_dump` CronJob
- **Qdrant**: Snapshot API on weekly schedule
- **Neo4j**: `neo4j-admin dump` daily
- **MinIO**: Cross-region replication enabled

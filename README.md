
---

# Flask Listener Application Deployment

This repository contains a simple Flask application that receives GET and POST requests, along with Kubernetes manifests for deployment, Docker configuration, and integration with ArgoCD for GitOps-based automated deployments. It also includes steps to enable HPA, monitoring with Prometheus/Grafana, and logging with EFK stack.

---



# Design Proposal

**Q1: Would you choose Knative or a Kubernetes Deployment + HPA for autoscaling? Why?**
**A1:** I would go with a **Kubernetes Deployment combined with Horizontal Pod Autoscaler (HPA)**. HPA integrates natively with Kubernetes, providing predictable and controlled scaling based on CPU or memory usage. While Knative is great for serverless workloads, HPA gives more control and stability for a persistent web service like Flask.

**Q2: How would you expose the service securely (Ingress Controller, ALB/NLB, TLS)?**
**A2:** I would use an **Ingress Controller** (e.g., NGINX) along with **TLS certificates** to encrypt all traffic. In production, an **ALB/NLB** could be placed in front for load balancing and TLS termination. Additionally, **NetworkPolicies** would restrict traffic between pods or from external sources to enhance security.

**Q3: What observability stack would you use (Prometheus/Grafana/Kibana)?**
**A3:** I would implement a full observability stack:

* **Prometheus**: for metrics collection (CPU, memory, custom metrics)
* **Grafana**: for dashboards, visualization, and alerting
* **EFK (Elasticsearch, Fluentd, Kibana)**: for centralized logging and troubleshooting
  This setup enables monitoring, troubleshooting, and alerting efficiently.

**Q4: How would you enforce RBAC and security policies?**
**A4:** Security would be enforced using **Kubernetes RBAC** for least-privilege access to service accounts, users, and CI/CD pipelines. **NetworkPolicies** would control pod-to-pod communication. I would also use **Pod Security Admission** to enforce safe container practices and integrate image scanning to avoid deploying vulnerable images.

**Q5: How would your design handle a 10x traffic spike while keeping costs under control?**
**A5:** I would rely on HPA along with **Cluster Autoscaler** to dynamically scale nodes. Efficient resource allocation and container sizing would prevent over-provisioning and manage costs. Caching and load balancing strategies would help handle sudden traffic spikes without impacting performance or infrastructure expenses.




**Q6: How would you ensure zero-downtime deployments in this setup?**

**A6:** Zero-downtime deployments can be achieved using **rolling updates** with Kubernetes Deployments. By gradually updating pods while keeping existing ones running, traffic continues uninterrupted. Readiness and liveness probes ensure only healthy pods receive traffic. For critical updates, **canary deployments** can be used to release changes to a subset of users before rolling out fully.

**Q7: How should secrets (DB credentials, API keys) be managed in Kubernetes?**

**A7:** Secrets should be stored using **Kubernetes Secrets** rather than in plaintext. Access should be granted via **service accounts with least privilege**, and sensitive data should be mounted as environment variables or volumes inside pods. For additional security, secrets can be encrypted at rest, and external secret managers (like **HashiCorp Vault** or cloud KMS) can be integrated.

**Q8: How would you design for multi-cluster or disaster recovery (DR) readiness if required by the client?**

**A8:** Multi-cluster or DR readiness can be achieved by replicating workloads across clusters in different regions. **Cluster Federation** or GitOps-driven deployments ensure consistent configuration. Backups for persistent volumes and databases, along with automated failover, allow quick recovery. Traffic can be routed intelligently via **DNS failover** or **global load balancers**.

**Q9: What would your incident response plan look like for a regional outage?**

**A9:** The incident response plan would include automated monitoring and alerting through **Prometheus/Grafana** for rapid detection. The plan involves failing over traffic to secondary clusters, restoring services from backups, and performing root cause analysis. Communication channels would be pre-defined for stakeholders, and post-incident review would update procedures to prevent recurrence.

---




## Table of Contents

1. [Flask Application](#flask-application)
2. [Docker Build and Run](#docker-build-and-run)
3. [Kubernetes Deployment](#kubernetes-deployment)
4. [Ingress and TLS](#ingress-and-tls)
5. [ArgoCD Integration](#argocd-integration)
6. [Horizontal Pod Autoscaler (HPA)](#horizontal-pod-autoscaler-hpa)
7. [Monitoring and Alerts](#monitoring-and-alerts)
8. [Logging with Kibana](#logging-with-kibana)


```
project/
├── ArgoCD
│   └── flask-app-argo.yaml
├── EFK
│   ├── elasticsearch/
│   │   ├── es-sts.yaml
│   │   └── es-svc.yaml
│   ├── fluentd/
│   │   ├── fluentd-ds.yaml
│   │   ├── fluentd-late.yaml
│   │   ├── fluentd-rb.yaml
│   │   ├── fluentd-role.yaml
│   │   └── fluentd-sa.yaml
│   ├── kibana/
│   │   ├── kibana-deployment.yaml
│   │   └── kibana-svc.yaml
│   └── README.md
├── flask-app/
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
├── flask-k8s/
│   ├── deploy.yaml
│   └── service.yaml
├── HPA/
│   └── Hpa.yaml
├── Keys/
│   ├── flask-ingress.yaml
│   ├── flask-tls.crt
│   └── flask-tls.key
└── Prometheus-Grafana/
    └── README.md
```

* **flask-app/**: Application code and Dockerfile.
* **flask-k8s/**: Kubernetes deployment and service manifests.
* **Keys/**: TLS certificate and ingress YAML.
* **EFK/**: Elasticsearch, Fluentd, Kibana manifests for logging.
* **HPA/**: Horizontal Pod Autoscaler manifests.
* **ArgoCD/**: Optional ArgoCD application manifests.
* **Prometheus-Grafana/**: Monitoring and alerting configurations.



---

## Flask Application

**File:** `flask-app/app.py`

```python
from flask import Flask, request
import logging

app = Flask(__name__)

# Configure logging to stdout
logging.basicConfig(level=logging.INFO)

@app.route("/", methods=["GET", "POST"])
def home():
    logging.info("Incoming request: %s %s", request.method, request.path)
    logging.info("Headers: %s", dict(request.headers))
    if request.method == "POST":
        logging.info("Payload: %s", request.get_data(as_text=True))
    return {"message": "Hello from Flask!"}, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

* Application listens on **port 5000**.
* Supports **GET** and **POST** requests.
* Logs requests and payloads to stdout.

---

## Docker Build and Run

**Dockerfile** (`flask-app/Dockerfile`):

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000
CMD ["python", "app.py"]
```

### Build Docker Image

```bash
docker build -t flask-listener:1.1 ./flask-app
```

### Run Docker Container

```bash
docker run -d -p 5000:5000 --name flask-listener flask-listener:1.1
```

### Test API

**GET Request**

```bash
curl http://localhost:5000/
```

**POST Request**

```bash
curl -X POST http://localhost:5000/ -H "Content-Type: application/json" -d '{"test":"data"}'
```

**Check Logs**

```bash
docker logs -f flask-listener
```

Expected logs include incoming request info and payloads.

---

## Kubernetes Deployment

**Namespace**

```bash
kubectl create ns test
```

**Deployment Manifest** (`flask-k8s/deploy.yaml`):

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: flask-app
  labels:
    app: flask
spec:
  replicas: 2
  selector:
    matchLabels:
      app: flask
  template:
    metadata:
      labels:
        app: flask
    spec:
      containers:
      - name: flask-app
        image: 10.10.20.47:8082/flask-listener:1.0
        imagePullPolicy: Always
        ports:
        - containerPort: 5000
```

**Service Manifest** (`flask-k8s/service.yaml`):

```yaml
apiVersion: v1
kind: Service
metadata:
  name: flask-service
spec:
  selector:
    app: flask
  ports:
    - protocol: TCP
      port: 80
      targetPort: 5000
  type: ClusterIP
```

**Deploy to Cluster**

```bash
kubectl apply -f flask-k8s/ -n test
```

---

## Ingress and TLS

**Generate Self-Signed Certificate**

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -out flask-tls.crt -keyout flask-tls.key \
  -subj "/CN=flask.local/O=flask.local"
```

**Create Kubernetes Secret**

```bash
kubectl create secret tls flask-tls --cert=flask-tls.crt --key=flask-tls.key -n test
```

**Ingress Manifest** (`Keys/flask-ingress.yaml`):

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: flask-app-ingress
  namespace: test
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  tls:
  - hosts:
      - flask.local
    secretName: flask-tls
  rules:
  - host: flask.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: flask-service
            port:
              number: 80
```

**Patch Nginx Service to NodePort (Optional)**

```bash
kubectl patch svc ingress-nginx-controller -n ingress-nginx \
  -p '{"spec": {"type": "NodePort"}}'
```

Access the app at:

```
http://<NodeIP>:<NodePort>
https://flask.local:<HTTPS NodePort>
```

Add `flask.local` to `/etc/hosts` for local testing.

---

## ArgoCD Integration

**Create Namespace**

```bash
kubectl create namespace argocd
```

**Install ArgoCD**

```bash
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

**Expose API Server (Optional)**

```bash
kubectl patch svc argocd-server -n argocd -p '{"spec": {"type": "NodePort"}}'
```

**Get Admin Password**

```bash
kubectl get secret argocd-initial-admin-secret -n argocd -o jsonpath="{.data.password}" | base64 -d
```

**ArgoCD Application Manifest**

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: flask-app
  namespace: argocd
spec:
Absolutely! I’ve organized everything you provided into a **professional, clean, step-by-step README.md** suitable for your GitHub repo. I removed any GitHub Actions references and kept it focused on **Flask app, Docker, Kubernetes, ArgoCD, HPA, Grafana, and Kibana**.

Here’s a polished version:

---

# Flask Listener Application Deployment

This repository contains a simple Flask application that receives GET and POST requests, along with Kubernetes manifests for deployment, Docker configuration, and integration with ArgoCD for GitOps-based automated deployments. It also includes steps to enable HPA, monitoring with Prometheus/Grafana, and logging with EFK stack.

---

## Table of Contents

1. [Flask Application](#flask-application)
2. [Docker Build and Run](#docker-build-and-run)
3. [Kubernetes Deployment](#kubernetes-deployment)
4. [Ingress and TLS](#ingress-and-tls)
5. [ArgoCD Integration](#argocd-integration)
6. [Horizontal Pod Autoscaler (HPA)](#horizontal-pod-autoscaler-hpa)
7. [Monitoring and Alerts](#monitoring-and-alerts)
8. [Logging with Kibana](#logging-with-kibana)

---

## Flask Application

**File:** `flask-app/app.py`

```python
from flask import Flask, request
import logging

app = Flask(__name__)

# Configure logging to stdout
logging.basicConfig(level=logging.INFO)

@app.route("/", methods=["GET", "POST"])
def home():
    logging.info("Incoming request: %s %s", request.method, request.path)
    logging.info("Headers: %s", dict(request.headers))
    if request.method == "POST":
        logging.info("Payload: %s", request.get_data(as_text=True))
    return {"message": "Hello from Flask!"}, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

* Application listens on **port 5000**.
* Supports **GET** and **POST** requests.
* Logs requests and payloads to stdout.

---

## Docker Build and Run

**Dockerfile** (`flask-app/Dockerfile`):

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000
CMD ["python", "app.py"]
```

### Build Docker Image

```bash
docker build -t flask-listener:1.1 ./flask-app
```

### Run Docker Container

```bash
docker run -d -p 5000:5000 --name flask-listener flask-listener:1.1
```

### Test API

**GET Request**

```bash
curl http://localhost:5000/
```

**POST Request**

```bash
curl -X POST http://localhost:5000/ -H "Content-Type: application/json" -d '{"test":"data"}'
```

**Check Logs**

```bash
docker logs -f flask-listener
```

Expected logs include incoming request info and payloads.

---

## Kubernetes Deployment

**Namespace**

```bash
kubectl create ns test
```

**Deployment Manifest** (`flask-k8s/deploy.yaml`):

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: flask-app
  labels:
    app: flask
spec:
  replicas: 2
  selector:
    matchLabels:
      app: flask
  template:
    metadata:
      labels:
        app: flask
    spec:
      containers:
      - name: flask-app
        image: 10.10.20.47:8082/flask-listener:1.0
        imagePullPolicy: Always
        ports:
        - containerPort: 5000
```

**Service Manifest** (`flask-k8s/service.yaml`):

```yaml
apiVersion: v1
kind: Service
metadata:
  name: flask-service
spec:
  selector:
    app: flask
  ports:
    - protocol: TCP
      port: 80
      targetPort: 5000
  type: ClusterIP
```

**Deploy to Cluster**

```bash
kubectl apply -f flask-k8s/ -n test
```

---

## Ingress and TLS

**Generate Self-Signed Certificate**

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -out flask-tls.crt -keyout flask-tls.key \
  -subj "/CN=flask.local/O=flask.local"
```

**Create Kubernetes Secret**

```bash
kubectl create secret tls flask-tls --cert=flask-tls.crt --key=flask-tls.key -n test
```

**Ingress Manifest** (`Keys/flask-ingress.yaml`):

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: flask-app-ingress
  namespace: test
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  tls:
  - hosts:
      - flask.local
    secretName: flask-tls
  rules:
  - host: flask.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: flask-service
            port:
              number: 80
```

**Patch Nginx Service to NodePort (Optional)**

```bash
kubectl patch svc ingress-nginx-controller -n ingress-nginx \
  -p '{"spec": {"type": "NodePort"}}'
```

Access the app at:

```
http://<NodeIP>:<NodePort>
https://flask.local:<HTTPS NodePort>
```

Add `flask.local` to `/etc/hosts` for local testing.

---

## ArgoCD Integration

**Create Namespace**

```bash
kubectl create namespace argocd
```

**Install ArgoCD**

```bash
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

**Expose API Server (Optional)**

```bash
kubectl patch svc argocd-server -n argocd -p '{"spec": {"type": "NodePort"}}'
```

**Get Admin Password**

```bash
kubectl get secret argocd-initial-admin-secret -n argocd -o jsonpath="{.data.password}" | base64 -d
```

**ArgoCD Application Manifest**

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: flask-app
  namespace: argocd
spec:
  project: default
  source:
    repoURL: 'https://github.com/dushyant25398/Persistent-Systems.git'
    targetRevision: main
    path: flask-k8s
  destination:
    server: 'https://kubernetes.default.svc'
    namespace: test
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

* ArgoCD automatically syncs changes to the cluster when the deployment manifest is updated.

---

## Horizontal Pod Autoscaler (HPA)

**Install Metrics Server**

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

**Validate Metrics Server**

```bash
kubectl get pods -n kube-system | grep metrics-server
kubectl get apiservices | grep metrics.k8s.io
kubectl top nodes
kubectl top pods -n test
```

**Patch Metrics Server (if needed)**

```bash
kubectl -n kube-system patch deployment metrics-server --type='json' -p='
[
  {
    "op": "add",
    "path": "/spec/template/spec/containers/0/args/-",
    "value": "--kubelet-insecure-tls"
  }
]'
```

**Create HPA**

```bash
kubectl autoscale deployment flask-app --cpu-percent=50 --min=1 --max=5 -n test
```

**Generate Load (Optional)**

```bash
kubectl run -i --tty load-generator --rm --image=busybox --restart=Never -- \
  /bin/sh -c "while true; do wget -q -O- http://flask-service.test.svc.cluster.local; done"
```

**Monitor HPA**

```bash
kubectl get hpa -n test --watch
```

---

## Monitoring and Alerts (Grafana & Prometheus)

* Create alert for **High CPU Usage (>80%)**.
* Metric query:

```
(rate(container_cpu_usage_seconds_total{namespace="test"}[5m])) * 100
```

* Configure **Folder**: Kubernetes Alerts
* **Label**: severity=critical
* Attach **Contact Points** (Slack, Email, Webhook).

Grafana evaluates alerts every 1 minute by default.

---

## Logging with Kibana

* Create **Index Pattern**: `logstash-*`
* Configure **@timestamp** as the time field.
* Logs from Fluentd are visible in Kibana dashboards.

---

This README provides a **complete guide from Flask application creation to GitOps deployment with ArgoCD**, HPA autoscaling, and monitoring/logging.

---

If you want, I can also **add a nice folder/file structure diagram at the top** so the README looks even more professional and easy to follow. This is especially helpful for new developers or operators looking at the repo.

Do you want me to add that?
  project: default
  source:
    repoURL: 'https://github.com/dushyant25398/Persistent-Systems.git'
    targetRevision: main
    path: flask-k8s
  destination:
    server: 'https://kubernetes.default.svc'
    namespace: test
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

* ArgoCD automatically syncs changes to the cluster when the deployment manifest is updated.

---

## Horizontal Pod Autoscaler (HPA)

**Install Metrics Server**

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

**Validate Metrics Server**

```bash
kubectl get pods -n kube-system | grep metrics-server
kubectl get apiservices | grep metrics.k8s.io
kubectl top nodes
kubectl top pods -n test
```

**Patch Metrics Server (if needed)**

```bash
kubectl -n kube-system patch deployment metrics-server --type='json' -p='
[
  {
    "op": "add",
    "path": "/spec/template/spec/containers/0/args/-",
    "value": "--kubelet-insecure-tls"
  }
]'
```

**Create HPA**

```bash
kubectl autoscale deployment flask-app --cpu-percent=50 --min=1 --max=5 -n test
```

**Generate Load (Optional)**

```bash
kubectl run -i --tty load-generator --rm --image=busybox --restart=Never -- \
  /bin/sh -c "while true; do wget -q -O- http://flask-service.test.svc.cluster.local; done"
```

**Monitor HPA**

```bash
kubectl get hpa -n test --watch
```

---

## Monitoring and Alerts (Grafana & Prometheus)

* Create alert for **High CPU Usage (>80%)**.
* Metric query:

```
(rate(container_cpu_usage_seconds_total{namespace="test"}[5m])) * 100
```

* Configure **Folder**: Kubernetes Alerts
* **Label**: severity=critical
* Attach **Contact Points** (Slack, Email, Webhook).

Grafana evaluates alerts every 1 minute by default.

---

## Logging with Kibana

* Create **Index Pattern**: `logstash-*`
* Configure **@timestamp** as the time field.
* Logs from Fluentd are visible in Kibana dashboards.

---

Jenkins Pipeline for CI/CD


pipeline {
    agent any

    environment {
        DOCKER_IMAGE_BASE = "10.10.20.47:8082/flask-listener"
        DOCKER_TAG = "${BUILD_NUMBER}"
        REGISTRY = "10.10.20.47:8082"
    }

    stages {

        stage('Checkout Code') {
            steps {
                git branch: 'main', url: 'https://github.com/dushyant25398/Persistent-Systems.git'
            }
        }

        stage('Remove Old Docker Images') {
            steps {
                sh """
                    docker images --filter=reference='${DOCKER_IMAGE_BASE}:*' --format '{{.ID}}' | tail -n +2 | xargs -r docker rmi -f || true
                """
            }
        }

        stage('Docker Login to Nexus') {
            steps {
                sh "docker login ${REGISTRY} -u admin -p 'Amantya@2025'"
            }
        }

        stage('Build Docker Image') {
            steps {
                sh "docker build -t ${DOCKER_IMAGE_BASE}:${DOCKER_TAG} -f flask-app/Dockerfile ./flask-app"
            }
        }

        stage('Push Docker Image to Nexus') {
            steps {
                sh "docker push ${DOCKER_IMAGE_BASE}:${DOCKER_TAG}"
            }
        }

        stage('Update K8s Deployment Manifest') {
            steps {
                withCredentials([string(credentialsId: 'github-pat', variable: 'GH_PAT')]) {
                    sh """
                        sed -i "s|image:.*|image: ${DOCKER_IMAGE_BASE}:${DOCKER_TAG}|" flask-k8s/deploy.yaml
                        git config --global user.email "ci-bot@org.com"
                        git config --global user.name "ci-bot"
                        git add flask-k8s/deploy.yaml
                        git commit -m "Update image to ${DOCKER_IMAGE_BASE}:${DOCKER_TAG}"
                        git push https://$GH_PAT@github.com/dushyant25398/Persistent-Systems.git main
                    """
                }
            }
        }
    }

    post {
        success {
            echo "Pipeline executed successfully! Image tagged as ${DOCKER_IMAGE_BASE}:${DOCKER_TAG}"
            echo "ArgoCD will automatically deploy the updated image to the 'test' namespace."
        }
        failure {
            echo "Pipeline failed!"
        }
    }
}



### Jenkins pipeline used here 
---

### GitOps Pipeline 




name: Build & Deploy Flask App (GitOps)

on:
  push:
    branches: [ "main" ]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Docker Login to Docker Hub
        run: |
          echo "${{ secrets.DOCKERHUB_PAT }}" | docker login -u "${{ secrets.DOCKERHUB_USERNAME }}" --password-stdin
      - name: Build Docker Image
        run: |
          IMAGE_HUB=lucky2821/flask-listener:${{ github.sha }}
          docker build -t $IMAGE_HUB ./flask-app
      - name: Push Docker Image
        run: |
          IMAGE_HUB=lucky2821/flask-listener:${{ github.sha }}
          docker push $IMAGE_HUB
      - name: Update Deployment Manifest
        env:
          GH_PAT: ${{ secrets.GH_PAT }}
        run: |
          IMAGE_HUB=lucky2821/flask-listener:${{ github.sha }}
          sed -i "s|image:.*|image: $IMAGE_HUB|" flask-k8s/deploy.yaml
          git config --global user.email "dushyant25398@gmail.com"
          git config --global user.name "Dushyant"
          git add flask-k8s/deploy.yaml
          git commit -m "Update image to $IMAGE_HUB"
          git push https://$GH_PAT@github.com/dushyant25398/Persistent-Systems.git main



Stored Credentials in GitHub Secrets.

Giving the Permissions only for the test namespace.
---

**`flask-rbac.yaml`**

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: flask-app-role
  namespace: test
rules:
  # Allow reading and listing pods and services in the namespace
  - apiGroups: [""]
    resources: ["pods", "services"]
    verbs: ["get", "list", "watch"]
  
  # Allow reading configmaps and secrets if the app needs them
  - apiGroups: [""]
    resources: ["configmaps", "secrets"]
    verbs: ["get", "list"]
  
  # Allow updating deployments (optional, only if app updates itself)
  - apiGroups: ["apps"]
    resources: ["deployments"]
    verbs: ["get", "list", "watch"]
```

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: flask-app-rolebinding
  namespace: test
subjects:
  - kind: ServiceAccount
    name: flask-sa  # You can create this service account and assign to your pods
    namespace: test
roleRef:
  kind: Role
  name: flask-app-role
  apiGroup: rbac.authorization.k8s.io
```

---

**How to use it:**

1. Create a service account for your Flask app pods:

```bash
kubectl create serviceaccount flask-sa -n test
```

2. Apply the RBAC manifest:

```bash
kubectl apply -f flask-rbac.yaml
```

3. Update your Deployment to use the service account:

```yaml
spec:
  serviceAccountName: flask-sa
```

---

 **This ensures:**

* The app can only list/get pods, services, configmaps, and secrets in its own namespace.
* No cluster-wide privileges are given.
* Easy to extend if new resources are needed later.





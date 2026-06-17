#!/bin/sh
set -e

# Patch kubeconfig so the container can reach the host's Kubernetes API server.
# Rewrites loopback addresses → host.docker.internal and skips TLS verification
# (kind certs don't include host.docker.internal in their SANs).
if [ -f /root/.kube/config ]; then
    mkdir -p /tmp/kube
    python3 - <<'EOF'
import sys, yaml

with open("/root/.kube/config") as f:
    cfg = yaml.safe_load(f)

for cluster in cfg.get("clusters", []):
    c = cluster.get("cluster", {})
    server = c.get("server", "")
    server = server.replace("https://127.0.0.1", "https://host.docker.internal")
    server = server.replace("https://localhost", "https://host.docker.internal")
    c["server"] = server
    c["insecure-skip-tls-verify"] = True
    c.pop("certificate-authority-data", None)
    c.pop("certificate-authority", None)

with open("/tmp/kube/config", "w") as f:
    yaml.dump(cfg, f)
EOF
    export KUBECONFIG=/tmp/kube/config
fi

exec "$@"

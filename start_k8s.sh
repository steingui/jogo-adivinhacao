#!/bin/bash
set -e

CLUSTER_NAME="guess-game-cluster"
NAMESPACE="default"

echo "=== 1. Criando Cluster k3d ==="
if k3d cluster list | grep -q "$CLUSTER_NAME"; then
    echo "Cluster '$CLUSTER_NAME' já existe. Continuando..."
else
    # Mapeia a porta NodePort 30080 do cluster para a porta 30080 da máquina host
    k3d cluster create "$CLUSTER_NAME" -p "30080:30080@server:0" --agents 1
fi

echo "=== 2. Importando Imagens locais para o k3d ==="
docker tag jogo-adivinhacao-backend:latest steingui/jogo-adivinhacao-backend:latest
docker tag jogo-adivinhacao-frontend:latest steingui/jogo-adivinhacao-frontend:latest
k3d image import steingui/jogo-adivinhacao-backend:latest steingui/jogo-adivinhacao-frontend:latest -c "$CLUSTER_NAME"

echo "=== 3. Instalando o Metrics Server para o HPA ==="
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

echo "Aguardando inicialização do Metrics Server..."
kubectl rollout status deployment metrics-server -n kube-system --timeout=60s || true

echo "Aplicando patch de segurança no Metrics Server (insecure TLS para ambiente local)..."
kubectl patch deployment metrics-server -n kube-system --type='json' -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"}]' || true

echo "Reiniciando Metrics Server para aplicar configurações..."
kubectl rollout restart deployment metrics-server -n kube-system

echo "=== 4. Instalando a Aplicação via Helm Chart ==="
helm upgrade --install guess-game k8s/guess-game

echo "=== 5. Aguardando Pods ficarem Prontos ==="
kubectl wait --for=condition=ready pod -l app=db --timeout=90s
kubectl wait --for=condition=ready pod -l app=backend --timeout=90s
kubectl wait --for=condition=ready pod -l app=frontend --timeout=90s

echo "=== Implantação Concluída com Sucesso! ==="
echo "Acesse a aplicação no navegador em: http://localhost:30080"
echo "Para testar o HPA executando stress test no backend:"
echo "  kubectl run -i --tty load-generator --rm --image=busybox:1.28 --restart=Never -- /bin/sh -c 'while true; do wget -q -O- http://backend:5000/api/health; done'"

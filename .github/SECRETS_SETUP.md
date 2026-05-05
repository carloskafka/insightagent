# GitHub Actions Secrets Setup

## Secrets Required in GitHub Repository

Configure estes secrets em **Settings > Secrets and variables > Actions**:

### Docker Hub
- `DOCKER_USERNAME`: Seu usuário do Docker Hub
- `DOCKER_PASSWORD`: Token de acesso do Docker Hub (ou senha)

### Kubernetes
- `KUBECONFIG`: Arquivo kubeconfig em base64
  ```bash
  cat ~/.kube/config | base64 -w 0
  ```

### Application Secrets
- `OPENROUTER_API_KEY`: Chave da API OpenRouter
- `JWT_SECRET`: Segredo para JWT (ex: `super-secret-jwt-key-production`)
- `POSTGRES_PASSWORD`: Senha do PostgreSQL no cluster K8s

## Como Funciona o CI/CD

### 1. Job `test` (roda em push e PR)
- Sobe serviços via `services:` do GitHub Actions:
  - Redis (porta 6379)
  - PostgreSQL (porta 5432)
  - Qdrant (porta 6333)
- Roda testes com pytest conectando nos serviços locais

### 2. Job `build-and-push` (só em main)
- Build da imagem Docker
- Push para Docker Hub

### 3. Job `deploy` (só em main)
- Configura kubectl com kubeconfig secreto
- Cria secrets no cluster K8s
- Aplica deployments do Kubernetes
- Atualiza imagem e faz rollout

## Notas Importantes

✅ **docker-compose.yml** é apenas para desenvolvimento local  
✅ **GitHub Actions** usa `services:` para subir dependências nos testes  
✅ **Kubernetes** tem seus próprios deployments de Redis, Postgres, Qdrant  
✅ Os serviços do docker-compose NÃO são usados no CI/CD  

## Desenvolvimento Local

```bash
# Subir todos os serviços
docker-compose up -d

# Rodar testes localmente (precisa dos serviços rodando)
pytest tests/ -v
```

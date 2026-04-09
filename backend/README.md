# Biblioteca Marxista — Back-end API

API REST construída com **FastAPI + SQLAlchemy + PostgreSQL**.

---

## Requisitos

- Python 3.11+
- PostgreSQL 14+

---

## Instalação

```bash
# 1. Clonar / descomprimir o projecto
cd biblioteca

# 2. Criar ambiente virtual
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com as suas credenciais PostgreSQL e SECRET_KEY
```

---

## Base de dados

```bash
# Criar a base de dados no PostgreSQL (uma vez)
psql -U postgres -c "CREATE DATABASE biblioteca_marxista;"

# As tabelas são criadas automaticamente ao arrancar a aplicação
```

---

## Seed — Criar os administradores

```bash
python -m app.scripts.seed_admins
```

Cria os utilizadores:

| Email | Password |
|---|---|
| anneheschkel@admin.com | Fr@nkFr@nk!!! |
| filipaheschkel@admin.com | Ann€Ann€??? |

> As passwords são guardadas como hash bcrypt. Nunca em texto simples.

---

## Arrancar o servidor

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Documentação interactiva

- Swagger UI: http://localhost:8000/docs
- ReDoc:       http://localhost:8000/redoc
- Health:      http://localhost:8000/health

---

## Estrutura de endpoints

### Autenticação
| Método | Rota | Descrição |
|---|---|---|
| POST | /api/v1/auth/login | Login (retorna JWT) |
| GET  | /api/v1/auth/me    | Utilizador autenticado |

### API Pública (sem autenticação)
| Método | Rota | Descrição |
|---|---|---|
| GET | /api/v1/public/contents | Listar conteúdos publicados |
| GET | /api/v1/public/contents/featured | Destaques (carousel) |
| GET | /api/v1/public/contents/{slug} | Detalhe de conteúdo |
| GET | /api/v1/public/categories | Listar categorias |
| GET | /api/v1/public/verbetes | Listar verbetes |
| GET | /api/v1/public/verbetes/featured | Verbetes em destaque |
| GET | /api/v1/public/verbetes/{slug} | Detalhe de verbete |
| GET | /api/v1/public/search/contents?q= | Full-text search em conteúdos |
| GET | /api/v1/public/search/verbetes?q= | Full-text search em verbetes |

### Admin — Conteúdos (requer JWT de admin)
| Método | Rota | Descrição |
|---|---|---|
| POST   | /api/v1/admin/contents | Criar conteúdo |
| GET    | /api/v1/admin/contents | Listar todos |
| GET    | /api/v1/admin/contents/{id} | Detalhe |
| PUT    | /api/v1/admin/contents/{id} | Editar |
| DELETE | /api/v1/admin/contents/{id} | Soft delete |
| PATCH  | /api/v1/admin/contents/{id}/publish | Publicar |
| PATCH  | /api/v1/admin/contents/{id}/unpublish | Despublicar |
| PATCH  | /api/v1/admin/contents/{id}/feature?featured=true | Marcar destaque |

### Admin — Categorias e Tags
| POST/GET/PUT/DELETE | /api/v1/admin/categories | CRUD categorias |
| POST/GET/PUT/DELETE | /api/v1/admin/tags | CRUD tags |

### Admin — Verbetes
| POST/GET/PUT/DELETE | /api/v1/admin/verbetes | CRUD verbetes |
| PATCH | /api/v1/admin/verbetes/{id}/feature?featured=true | Destaque |

### Admin — Dashboard e Logs
| GET | /api/v1/admin/dashboard/stats | Estatísticas gerais |
| GET | /api/v1/admin/logs | Logs de actividade |

---

## Variáveis de ambiente (.env)

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/biblioteca_marxista
SECRET_KEY=chave-secreta-muito-longa-e-aleatoria
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
ENVIRONMENT=development
```

> Em produção, definir `ENVIRONMENT=production` desactiva o echo SQL e restringe o CORS.

---

## Autenticação nas rotas protegidas

```http
Authorization: Bearer <access_token>
```

---

## Paginação — Formato de resposta

```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "total_pages": 5
}
```

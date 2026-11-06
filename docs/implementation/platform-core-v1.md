# Platform Core v1 — identidade, autenticação e auditoria

## Objetivo

Fornecer identidade persistente, autenticação por sessão de servidor, autorização RBAC e auditoria para os módulos Learning Center, Internship Center, Laboratory Engine e Portfolio.

## Modelo de segurança

- Password hashing com Argon2id através de `pwdlib[argon2]`.
- Tokens de sessão opacos, gerados por CSPRNG, enviados apenas num cookie `HttpOnly`.
- A base de dados guarda apenas SHA-256 do token de sessão, nunca o token bruto.
- Sessões expiram após 12 horas por omissão e podem ser revogadas.
- Cookie usa `SameSite=Lax`, `Path=/`, sem atributo `Domain`; `Secure` deve ser ativado fora do ambiente local HTTP.
- CSRF: token aleatório independente por sessão, guardado como hash no servidor e também num cookie `SameSite=Lax` legível pelo frontend; o frontend envia o mesmo valor em `X-CSRF-Token` e o backend compara cookie, cabeçalho e hash da sessão.
- Login limitado através de Redis; falha de Redis bloqueia novas autenticações em vez de desativar silenciosamente o rate limiting.
- RBAC no backend; esconder elementos na UI não é controlo de autorização.
- Eventos de autenticação e gestão de sessão são registados em `audit_events`. Segredos, passwords e tokens nunca devem ser registados.

## Roles iniciais

- `owner`: administração global.
- `learner`: utilização dos recursos de aprendizagem, laboratórios permitidos, submissões e portfólio próprio.
- `reviewer`: revisão de tickets, avaliações e evidências.

As roles e permissões de sistema são criadas pela migração `0003_platform_core`. Nenhum utilizador ou password é criado automaticamente.

## Criar a primeira conta Owner

Depois de aplicar as migrações, executar no container API:

```bash
docker compose exec api python -m app.scripts.create_owner \
  --email owner@example.local \
  --name "Platform Owner"
```

A password é solicitada interativamente (duas vezes), deve ter pelo menos 15 caracteres e não deve ser passada como argumento, guardada no shell history ou colocada no `.env`.

A criação inicial é bloqueada se já existir uma conta com role `owner`. Criar utilizadores adicionais e gestão de roles será uma entrega posterior, protegida pela permissão `users:manage`.

## Endpoints

- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/sessions`
- `DELETE /api/v1/auth/sessions/{session_id}`

## Limitações desta entrega

- Não há registo público.
- Não há recuperação de password nem MFA ainda.
- A gestão de utilizadores/roles por interface ainda não está implementada.
- A limitação de tentativas depende de Redis disponível.
- O ambiente local usa HTTP e, por isso, o cookie `Secure` fica desativado apenas em `APP_ENV=development`. Em produção é obrigatório HTTPS e `SESSION_COOKIE_SECURE=true`.
- O frontend Next.js e a API são servidos em `localhost` com portas diferentes; a origem exata deve permanecer na allowlist CORS.

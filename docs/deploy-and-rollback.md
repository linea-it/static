# Deploy automático, agente de automação e rollback

Nomes de hosts neste documento são **exemplos** (`webproxy01`, `automation01`), não os hostnames reais do inventário.

## Como o agente self-hosted continua só no `ops`

O runner self-hosted (ex.: host `automation01`) está registrado no repositório **`linea-it/ops`**. Ele só executa jobs com `runs-on: self-hosted` **nesse** repo.

```text
Dev merge em static (main)
        │
        ▼
static: workflow "Trigger static deploy on ops"
        runs-on: ubuntu-latest   ← runners da GitHub, NÃO automation01
        só envia repository_dispatch para ops
        │
        ▼
ops: workflow "Nginx - Static Files Deploy"
        ├─ metadata-lint     → ubuntu-latest (GitHub)
        └─ deploy-static     → self-hosted (automation01)
                │
                ▼
           ansible-playbook nginx-static-deploy.yml
                │
                ▼
           webproxy01 / webproxy02  (document root público /static)
```

Pontos importantes:

- O agente em `automation01` **não** é vinculado ao `static`.
- O YAML no `static` não roda Ansible nem toca nos proxies; só dispara o `ops`.
- Lint de metadados roda em `ubuntu-latest` (GitHub).
- Só o job de deploy no `ops` usa o self-hosted.

### Segredo necessário no `static`

No repo `linea-it/static` → Settings → Secrets → Actions:

| Secret | Uso |
|--------|-----|
| `OPS_DISPATCH_TOKEN` | PAT (classic `repo` + permissão de Actions, ou fine-grained com acesso a `linea-it/ops` para disparar workflows / `repository_dispatch`) |

Sem esse secret, o merge em `main` falha no job de disparo (o código já está no Git, mas o deploy automático não parte).

Deploy manual continua disponível: no `ops`, Actions → **Nginx - Static Files Deploy** → `workflow_dispatch` (útil para rollback ou republish).

---

## CODEOWNERS (autonomia vs proteção)

| Caminho | Review de Code Owners |
|---------|------------------------|
| `metadata/satosa-prod-sps-*.xml` | `@linea-it/infra` obrigatório |
| `docs/rnp-cafe-notify-template.md`, `docs/deploy-and-rollback.md`, `scripts/lint_satosa_sps.py` | infra |
| `.github/workflows/` (disparo automático para o `ops`) | infra — evita abuso do `OPS_DISPATCH_TOKEN` |
| Demais (`logos/`, `eds/`, `satosa-dev-*`, `satosa-sing-*`, …) | PR normal; **sem** code owner de infra |

Branch protection em `main` deve exigir PR + “Require review from Code Owners” (só aplica onde há owners).

---

## Rollback (voltar ao commit anterior)

Há **duas** formas. Prefira a 1 (via Git/ref); use a 2 se o GitHub/Actions estiver indisponível e o backup no disco ainda existir.

### 1. Republicar um SHA anterior do `static` (recomendado)

1. No clone do `static`, descubra o commit bom:

   ```bash
   git log --oneline -10
   # anote o SHA anterior ao deploy ruim, ex.: abcdef1
   ```

2. No GitHub do **`ops`**: Actions → **Nginx - Static Files Deploy** → Run workflow  
   - `static_ref` = o SHA bom (`abcdef1`)  
   - `check_mode` = `false` (ou `true` primeiro, para dry-run)

3. Confirme em `webproxy01` e `webproxy02` (ou abrindo a URL afetada) que o conteúdo voltou.

4. Opcional: no `static`, abra um PR que reverte o commit ruim (`git revert`) para o Git ficar alinhado com o que está em produção. Se só republicar o SHA antigo sem reverter no Git, o **próximo merge em main** pode publicar de novo o conteúdo ruim.

### 2. Restaurar backup local feito pelo playbook

Cada deploy bem-sucedido (antes de trocar os arquivos) tenta copiar o diretório atual para algo como:

`/root/static-backup-YYYYMMDD-HHMMSS`

nos hosts do grupo Ansible de proxies web (ex.: `webproxy01`, `webproxy02`).

Em `automation01` (ou com acesso root aos proxies), em **cada** `webproxy`:

```bash
# listar backups
ls -lt /root/static-backup-*

# escolher o backup imediatamente anterior à falha
BACKUP=/root/static-backup-20260904153000   # exemplo

# restaurar (atenção: substitui o conteúdo público)
# DOCROOT = document root onde /static é publicado (confira no inventário)
rm -rf "$DOCROOT"
cp -a "$BACKUP" "$DOCROOT"
```

Repita no segundo proxy (failover). Depois alinhe o Git com a opção 1 ou um `git revert`.

### Se o lint bloquear o deploy

O job `metadata-lint` no `ops` impede publicar XML SPS inválido. Para rollback de **só assets** (logo etc.) isso não atrapalha: o SHA antigo também passa no lint. Se o lint falhar no SHA que você quer republicar, corrija o XML nesse SHA ou escolha um SHA anterior em que o lint passe.

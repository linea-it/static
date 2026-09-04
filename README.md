# STATIC

Repositório de arquivos auxiliares estáticos servidos pelos proxies web do LIneA (failover).

Conteúdo publicado em [www.linea.org.br/static/](https://www.linea.org.br/static/) e metadados SAML em caminhos sob `metadata/` (incluindo SATOSA).

## Onde roda o quê

| O quê | Onde |
|-------|------|
| PR, CODEOWNERS, template RNP, script de lint | este repo (`static`) |
| Sinal de “houve merge na main” | workflow mínimo neste repo em **ubuntu-latest** (GitHub) — **não** usa o self-hosted |
| Lint SPS + Ansible de publish | [linea-it/ops](https://github.com/linea-it/ops) |
| Agente self-hosted (ex.: `automation01`) | **somente** jobs `self-hosted` no `ops` |

Detalhes, secret `OPS_DISPATCH_TOKEN` e **rollback**: [docs/deploy-and-rollback.md](docs/deploy-and-rollback.md).

## Metadados SATOSA (SPs)

Os agregados `metadata/satosa-{dev,prod,sing}-sps-*.xml` listam os Service Providers que confiam no SATOSA daquele ambiente.

### Modelo CAFe / RNP

Perante a federação **CAFe**, o SP do LIneA é o **satosa-prod**. Apps de produção entram em `satosa-prod-sps-linea.xml`. Nova app em **prod** → aviso **manual** à RNP:

- [docs/rnp-cafe-notify-template.md](docs/rnp-cafe-notify-template.md)

### Quem precisa aprovar o PR

- **`satosa-prod-sps-*.xml`**: Code Owners `@linea-it/infra`
- **`.github/workflows/`**, **`docs/deploy-and-rollback.md`**: Code Owners `@linea-it/infra`
- **dev / sing / logos / eds / etc.**: PR normal (sem code owner de infra)

## Fluxo do dia a dia

1. Abra um PR em `main` com a alteração.
2. Valide XML localmente se mexeu em SPS: `python scripts/lint_satosa_sps.py --metadata-dir metadata`
3. Se **prod** e SP **novo**: envie o aviso RNP com o template.
4. Após approve + merge em `main`, o `static` dispara automaticamente o deploy no `ops` (self-hosted → webproxies).
5. Deploy manual / rollback: ver [docs/deploy-and-rollback.md](docs/deploy-and-rollback.md).

### Lint local / no ops

```bash
python scripts/lint_satosa_sps.py --metadata-dir metadata
```

No `ops`: Actions → **Static - Metadata Lint** (opcional, para validar uma ref antes do merge).

## Proteção de branch (`main`)

Settings → Branches → `main`:

1. Require a pull request before merging  
2. Require review from Code Owners  
3. Configure o secret `OPS_DISPATCH_TOKEN` (ver doc de deploy)

Ajuste o team em [`.github/CODEOWNERS`](.github/CODEOWNERS) se o slug não for `@linea-it/infra`.

# STATIC

Repositório de arquivos auxiliares estáticos servidos pelos proxies web do LIneA (failover).

Conteúdo publicado em [www.linea.org.br/static/](https://www.linea.org.br/static/) e metadados SAML em caminhos sob `metadata/` (incluindo SATOSA).

**GitHub Actions não rodam neste repositório.** Workflows (lint, deploy) ficam no [linea-it/ops](https://github.com/linea-it/ops), no agente único da máquina play (Ansible contra os hosts).

## Metadados SATOSA (SPs)

Os agregados `metadata/satosa-{dev,prod,sing}-sps-*.xml` listam os Service Providers que confiam no SATOSA daquele ambiente. Incluir ou remover um SP nesses arquivos estabelece ou revoga a relação de confiança local.

### Modelo CAFe / RNP

Perante a federação **CAFe**, o SP do LIneA é o **satosa-prod** — não cada aplicação interna. Apps de produção entram no agregado local `satosa-prod-sps-linea.xml`. Quando uma **nova** aplicação de produção é adicionada, alguém do time deve **enviar manualmente** um aviso à RNP usando o template:

- [docs/rnp-cafe-notify-template.md](docs/rnp-cafe-notify-template.md)

Não há e-mail automático.

## Fluxo para adicionar ou remover um SP

1. Abra um PR em `main` alterando o agregado do ambiente correto (`satosa-dev-sps-*.xml`, `satosa-prod-sps-*.xml` ou `satosa-sing-sps-*.xml`).
2. Insira o XML do SP **antes** do fechamento de `EntitiesDescriptor`, com comentários de início/fim como nos exemplos existentes.
3. Valide o XML localmente (abaixo) e/ou dispare o workflow **Static - Metadata Lint** no repo `ops`.
4. Se o PR **adicionar** entityIDs em **prod**, envie o aviso à RNP com o template acima.
5. Code owners de `metadata/` revisam e aprovam.
6. Após o merge em `main`, a infra publica com **Nginx - Static Files Deploy** no `ops` (Ansible nos lbproxies).

### Lint local

```bash
python scripts/lint_satosa_sps.py --metadata-dir metadata
```

Com diff contra outro checkout:

```bash
python scripts/lint_satosa_sps.py --metadata-dir metadata --base-dir /path/to/base/checkout
```

No `ops`: Actions → **Static - Metadata Lint** (`workflow_dispatch`), informando a ref do `static` (branch/SHA) e, se quiser diff, a `base_ref`.

## Proteção de branch (`main`) — configuração manual

No GitHub: **Settings → Branches → Branch protection rules** para `main`:

1. Require a pull request before merging
2. Require review from Code Owners

(Não há status check de Actions neste repo — o lint vive no `ops`.)

Ajuste o time em [`.github/CODEOWNERS`](.github/CODEOWNERS) se `@linea-it/infra` não for o slug correto.

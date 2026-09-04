## Summary

<!-- What changed and why -->

## Environments

- [ ] `satosa-dev-sps-*.xml`
- [ ] `satosa-prod-sps-*.xml`
- [ ] `satosa-sing-sps-*.xml`
- [ ] Other files under `metadata/` / static assets

## Checklist

- [ ] XML validated locally (`python scripts/lint_satosa_sps.py`) and/or via **Static - Metadata Lint** in `linea-it/ops`
- [ ] New SP metadata placed before the closing `EntitiesDescriptor`, with begin/end comments
- [ ] If **production** and this PR **adds** a new service behind satosa-prod: I sent (or will send) the RNP notice using [docs/rnp-cafe-notify-template.md](docs/rnp-cafe-notify-template.md)
- [ ] I know rollback is documented in [docs/deploy-and-rollback.md](docs/deploy-and-rollback.md)

## Notes

The production SATOSA (`satosa-prod`) is the SP registered with the CAFe federation. Local apps are trusted via `satosa-prod-sps-linea.xml`; RNP still needs a human notice when a new production app starts using it.

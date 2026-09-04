# Aviso à RNP — nova aplicação atrás do satosa-prod (CAFe)

Use este template quando um PR **adicionar** um Service Provider em `metadata/satosa-prod-sps-*.xml`.

**Contexto:** o LIneA não registra cada aplicação como SP separado na federação CAFe. O SP federado é o **satosa-prod**. A aplicação abaixo passa a consumir autenticação através desse SP; a RNP precisa ser informada manualmente (envie este texto por e-mail ou canal habitual — não há envio automático).

---

**Para:** `[CONTATO_RNP_OU_CAFE]`  
**Assunto:** LIneA — nova aplicação em produção atrás do satosa-prod (CAFe)

```
Prezados,

Informamos que uma nova aplicação do LIneA passou a utilizar o SATOSA de produção
como provedor de autenticação/autorização. Lembramos que o satosa-prod é o SP
do LIneA perante a federação CAFe.

Dados da aplicação:

- Nome do serviço: [NOME_DO_SERVICO]
- URL pública: [https://exemplo.linea.org.br]
- entityID (metadado SAML local): [https://exemplo.linea.org.br/...]
- Ambiente: produção
- Data prevista / efetiva: [AAAA-MM-DD]
- Responsável técnico (LIneA): [NOME] <[email@linea.org.br]>

A relação de confiança local entre o satosa-prod e a aplicação foi (ou será)
estabelecida via metadados em:
https://github.com/linea-it/static (arquivo satosa-prod-sps-linea.xml).

Permanecemos à disposição para qualquer ajuste necessário do lado da federação.

Atenciosamente,
[NOME]
[TIME / LIneA]
```

Substitua os placeholders entre colchetes antes de enviar. Atualize `[CONTATO_RNP_OU_CAFE]` com o endereço ou canal usado pelo time de infraestrutura.

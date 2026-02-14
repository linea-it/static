# LIneA Embedded Discovery Service

Página de Login com botões referente aos provedores de autenticação configurados no SATOSA do LIneA e que podem ser utilizados pelos serviços LIneA que possuem integração SAML com Shibboleth SP.

## Configuração

### Requisitos

1. Serviço integrado e configurado com Shibboleth SP e Apache HTTP;
2. Relação de confiança estabelecida entre o serviço e o SATOSA do LIneA.

### Passos

1. Acesse o diretório `/var/www` do ambiente com Shibboleth SP e Apache; 
2. Faça download deste repositório e acesse o diretório `eds`; 
3. Configure as variáveis `edsPageTitle`, `shibLoginURL` e `targetURL` no arquivo `config.js`;
4. Edite o arquivo `/etc/shibboleth/shibboleth2.xml` e faça as seguintes alterações:
   1. Substitua o elemento `SSO` existente por:
        ```xml
        <SSO discoveryProtocol="SAMLDS" discoveryURL="https://FQDN-Service/eds">
        SAML2
        </SSO>
        ```
        **Obs.:** Substitua `FQDN-Service` pelo FQDN do serviço em questão, ex. `register.linea.org.br`.
    2. Revise se o arquivo possui um elemento `MetadataProvider` para cada mecanismo de autenticação utilizado nos botões da página de EDS. Caso não exista, adicione o elemento conforme exemplo:
        ```xml
        <MetadataProvider type="XML" validate="true"
                url="https://identity.linea.org.br/metadata/satosa-prod-frontend-cilogon.xml"
                backingFilePath="cilogon-metadata.xml"
                maxRefreshDelay="7200"/>
        ```
        **Obs.:** Altere o valor das propriedades `url` e `backingFilePath` pelos valores dos mecanismos em questão.
5. Adicione no arquivo de configuração do apache, exemplo `/opt/rh/httpd24/root/etc/httpd/conf.d/shib.conf`, o seguinte conteúdo:
    ```apache
    Alias "/eds" "/var/www/eds"
    <Directory "/var/www/eds">
        Options FollowSymLinks
        AllowOverride None
        Require all granted
    </Directory>
    ```
6. Reinicie o Apache
   ```bash
   systemctl restart httpd24-httpd.service
   ```

### Observações gerais

1. Esta página só funcionará com um Serviço integrado com SAML por meio do Shibboleth SP. Para outras implementações de SAML serão necessárias alterações no código deste repositório e nas configurações;
2. Para o funcionamento correto dos redirecionamento para os provedores de autenticação presentes na página de login, é importante que seja estabelecida, previamente, a relação de confiança entre o serviço e o SATOSA do LIneA. Isso deve ser feito entre o serviço e cada um dos frontends do SATOSA. Os metadados do SATOSA e SPs estão acessíveis no link [https://identity.linea.org.br/metadata](https://identity.linea.org.br/metadata);
3. Para o desempenho correto da página de erro, o link de redirecionamento "sign out and connect with another login" deve ser modificado para a aplicação correspondente.

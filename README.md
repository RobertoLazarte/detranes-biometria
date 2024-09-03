# Detran API docker

Repositorio com o protótipo de estrutura das APIs do Renach e do Rec Facial em containers. Neste exemplo, a estrutura de containers para cada uma das APIs é gerado via docker compose, criando a seguinte estrutura:
- 1 container para o NGNIX (conecta no network frontend)
- 1 container para a aplicação em Flask + uWSGI (conecta nos networks frontend e backend)
- 1 container para o banco de dados Postgre (conecta no network backend)
- 1 container para o PgAdmin apenas para acompanhamento e acesso ao banco (conecta no network backend)
- 1 docker volume que conecta com o container do Postgre para armazenamento dos dados

Existem dois arquivos compose yml para gerar a estrutura listada acima para cada uma das APIs, que já estão separadas. O arquivo _docker-compose.yml_ gera a estruta acima para a API do Renach ( _api_renach.py_ ), que uma vez rodando poderá ter sua documentação (SWAGGER) acessada no caminho http://localhost:8000/ (porta 8000 definida tanto para o _proxy_ reverso NGNIX como no deploy do uWSGI). Já o arquivo _docker-compose_facial.yml_ gera a estruta acima para a API do Rec Facial ( _api_facial.py_ ), que uma vez rodando poderá ser acessada no caminho http://localhost:8000/ (porta 8000 definida tanto para o _proxy_ reverso NGNIX como no deploy do uWSGI).

Na raíz do repositório estão os arquivos __yml_, o Dockerfile para gerar a imagem do container para a aplicação em Flask + uWSGI e os arquivos de configuração do NGNIX para cada um dos casos. Os arquivos de deploy para o uWSGI estão no cmainho _app/backend_, identificados pelo nome.
  
## Launch
Para rodar a estrura na primeira vez, na raiz do repositorio rodar o docker compose para criar a imagem do container do flask com suas dependências:
```
docker-compose build
```
Na sequência, carregar/atualizar as imagens dos demais containers:
```
docker-compose pull
```
Na primeira inicialização, subir primeiramente apenas o container do Postgre, para criar o docker volume e configurar o banco de dados:
```
docker-compose up -d db
```
Na sequência, subir os demais containers:
```
docker-compose up -d api_renach proxy pgadmin
```
Para parar os containers:
```
docker-compose down
```
adicionar a opção `-v` no comando anterior caso se deseje apagar o docker volume. Na seguinte vez, para subir a estrutura de containers, rodar apenas:
```
docker-compose up -d

```
Para subir a estrutura de containers para a API do recfacial, dado que as imagens dos containers já foram criadas/atualizadas e docker volume já foi criado, rodar:
```
docker-compose -f docker-compose_facial.yml up -d
```
caso contráriom seguir a sequência de passos acima com a inclusão da  opção `-f docker-compose_facial.yml` em todos eles.

Para acessar o PgAdmin, entrar em http://localhost:8080/ (login e senha criados no compose file) e criar nova conexão de servidor colocando as informações do container do Postgre (host igual ao nome do container, db_user e db_password criados no compose file e port padrão 5432). No primeiro deploy de cada uma das APIs as tabelas serão criadas automaticamente pelas aplicações Flask e poderão ser acessadas via PgAdmin.

## Importante

Alguns pontos importantes a serem considerados: a API do Rec Facil não está funcional pois é necessário ajustar a questão da conexão com o CAS, que ocorre nos arquivos: _app/backend/scripts/api_facial/functions/recfacial.py_, _app/backend/scripts/api_facial/resources/batchcred.py_ e _app/backend/scripts/api_facial/resources/creds.py_ através do comando:
```
conn = swat.CAS('a-dtes-pvx05.sas.detran.es.gov.br',
                            5570,
                            'rodrigo.ferrari',
                            '{SAS002}23B6882C31A5DBF51C3F913F51CEA44B3C126085')
```
Também é necessário levar manualmente os modelos usados no processo de reconhicimento facial para a pasta _app/backend/assets/models_facial_. São 21 arquivos que serão disponibilizados via drive.


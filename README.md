# Monitoramento de Luminosidade de Plantações 🌱

## Sobre o projeto

Este projeto desenvolveu um sistema IoT para monitorar a luminosidade recebida por plantas. A proposta foi acompanhar as variações de luz no ambiente e armazenar essas informações para que pudessem ser consultadas posteriormente.

O sistema utilizou um ESP32 em um circuito simulado no Wokwi. As leituras foram enviadas por MQTT ao EMQX Cloud e encaminhadas para uma API REST integrada ao Supabase, onde foram armazenadas. O frontend web foi utilizado para apresentar as informações ao usuário.

O monitoramento foi direcionado a três culturas: batata, soja e amendoim.

## Objetivo

Desenvolver uma solução que permitisse acompanhar a luminosidade do ambiente, registrar os valores recebidos e possibilitar sua visualização por meio de uma página web.

## Arquitetura do projeto

O sistema foi organizado em três blocos principais:

- **Sensor simulado:** ESP32 no Wokwi, responsável por gerar e transmitir as leituras de luminosidade.
- **API REST:** recebe os dados encaminhados pelo EMQX, valida as informações e realiza a gravação no Supabase.
- **Frontend web:** consulta e apresenta as informações armazenadas.

A comunicação entre os componentes utilizou MQTT e requisições HTTP.

### Fluxo de funcionamento

```text
ESP32 (Wokwi)
     |
     | MQTT
     v
EMQX Cloud
     |
     | Regra + ação HTTP
     v
Supabase Edge Function
     |
     v
Banco de dados Supabase
     |
     v
Frontend Web
```

## Tecnologias utilizadas

- **Wokwi:** simulação do circuito com ESP32.
- **MQTT:** protocolo utilizado para transmitir as leituras.
- **EMQX Cloud:** broker responsável por receber as mensagens MQTT e encaminhar os dados.
- **Supabase:** serviço utilizado para disponibilizar a API, executar a Edge Function e armazenar os registros no banco de dados.
- **Cloudflare:** hospedagem utilizada para disponibilizar o frontend web.

## Estrutura do projeto

O projeto foi organizado em componentes responsáveis por cada etapa do funcionamento:

- Código do ESP32 e configuração da simulação no Wokwi.
- Configuração do tópico, da regra e da ação HTTP no EMQX.
- Código da função `hyper-action`, responsável pelo recebimento e validação das requisições.
- Script SQL responsável pela criação da tabela e das permissões do banco de dados.
- Arquivos do frontend web.
- Pasta com os dois certificados utilizados na configuração da conexão segura com o EMQX.

## Comunicação MQTT

O dispositivo utilizado no projeto foi identificado como:

```text
esp32_02
```

O tópico utilizado para publicação das leituras foi:

```text
esp32_02/luminosidade
```

As mensagens foram organizadas no formato JSON, contendo a identificação do dispositivo, o identificador único da mensagem, a cultura monitorada e o valor de luminosidade.

Exemplo de mensagem:

```json
{
  "device_id": "esp32_02",
  "message_id": "leitura_001",
  "sensor_id": "soja",
  "luminosity": 72.5
}
```

O campo `sensor_id` identifica a cultura relacionada à leitura e aceita os seguintes valores:

- `batata`
- `soja`
- `amendoim`

Cada leitura possui um identificador próprio, utilizado para diferenciar os registros e evitar duplicidade para o mesmo dispositivo.

### Certificados da conexão MQTT

Para estabelecer a conexão segura com o broker EMQX Cloud, foram utilizados dois certificados: um certificado base e outro gerado pelo próprio EMQX.

Os dois arquivos foram organizados em uma pasta específica dentro do repositório, facilitando sua localização e utilização na configuração da comunicação MQTT.

Durante a configuração da conexão, os certificados devem ser indicados conforme os parâmetros de segurança exigidos pelo broker e pela implementação do ESP32.

**Atenção:** os certificados públicos podem ser disponibilizados conforme sua finalidade, mas chaves privadas, senhas e outras credenciais de acesso não devem ser publicadas no GitHub.

## API REST

A API foi implementada por meio de uma Supabase Edge Function chamada `hyper-action`.

**Endpoint:**

```text
https://bzjjnpjaxamnvynuijae.supabase.co/functions/v1/hyper-action
```

A função recebe requisições HTTP pelo método POST, verifica a chave de acesso, valida o formato dos dados recebidos e realiza a gravação no banco de dados.

O encaminhamento das mensagens foi configurado no EMQX Cloud por meio de uma regra e de uma ação HTTP.

## Banco de dados

O banco de dados foi desenvolvido no Supabase e utilizou a tabela:

```text
public.readings
```

A estrutura da tabela contém os seguintes campos:

| Campo | Tipo | Descrição |
|---|---|---|
| device_id | text | Identificação do dispositivo |
| message_id | text | Identificação única da leitura |
| sensor_id | text | Cultura relacionada à leitura |
| luminosity | double precision | Valor da luminosidade em lux |
| received_at | timestamptz | Data e hora do recebimento |

O campo `sensor_id` aceita os valores `batata`, `soja` e `amendoim`. O banco também possui restrições para validar os identificadores e limitar os valores de luminosidade entre 0 e 100.000.

A chave primária é composta pelos campos `device_id` e `message_id`, permitindo identificar cada mensagem recebida.

O banco utiliza Row Level Security (RLS) para controlar as permissões de acesso. As consultas públicas e autenticadas foram permitidas pela política configurada, enquanto as operações de gravação ficaram destinadas ao serviço responsável pelo recebimento das leituras.

### Criação do banco de dados

Para reproduzir a estrutura do banco em um novo projeto Supabase:

1. Criar uma conta no Supabase e iniciar um novo projeto.
2. Acessar o SQL Editor no painel do Supabase.
3. Executar o script SQL de criação da tabela `public.readings`.
4. Conferir se a tabela foi criada com os campos e as restrições descritos anteriormente.
5. Verificar se a política de consulta e as permissões foram configuradas corretamente.

O script completo de criação do banco está disponível no repositório, sem informações secretas.

## Instruções para reprodução do projeto

### 1. Simulação do sensor no Wokwi

1. Acessar o projeto pelo link disponibilizado nesta documentação.
2. Abrir a simulação do ESP32.
3. Conferir as configurações de conexão MQTT e os dados necessários para comunicação.
4. Executar a simulação para iniciar a geração e o envio das leituras de luminosidade.

O dispositivo utilizado foi identificado como `esp32_02`, e o tópico de publicação foi `esp32_02/luminosidade`.

### 2. Configuração do EMQX Cloud

1. Criar ou acessar um ambiente no EMQX Cloud.
2. Configurar o acesso do dispositivo ao broker MQTT.
3. Utilizar os certificados disponibilizados na pasta específica do repositório para configurar a conexão segura.
4. Conferir o tópico utilizado para receber as mensagens.
5. Criar a regra responsável por receber e interpretar o conteúdo JSON.
6. Configurar a ação HTTP para encaminhar os dados à Edge Function do Supabase.
7. Verificar os registros de recebimento e as respostas da ação HTTP.

A regra utilizou a função `json_decode` para interpretar a mensagem recebida. A ação HTTP utilizou o método POST e o endpoint da função `hyper-action`.

### 3. Configuração do Supabase

1. Criar um projeto no Supabase.
2. Executar o script SQL disponibilizado no repositório para criar a tabela `public.readings`.
3. Configurar a Edge Function `hyper-action`.
4. Configurar as variáveis e os segredos necessários para a autenticação.
5. Conferir se a função consegue receber uma requisição válida e registrar uma leitura no banco.

A chave de acesso utilizada pela função deve ser armazenada como segredo no Supabase. Nenhuma credencial deve ser publicada no GitHub.

### 4. Configuração do frontend

1. Obter os arquivos do frontend no repositório.
2. Configurar o endereço do projeto Supabase e os dados públicos necessários para a consulta, conforme a implementação.
3. Verificar se as consultas estão direcionadas à tabela e aos campos corretos.
4. Publicar a aplicação na plataforma de hospedagem utilizada.
5. Acessar o endereço publicado e verificar a apresentação das leituras.

As chaves públicas utilizadas pelo frontend devem respeitar as permissões configuradas no Supabase. Chaves secretas de serviço não devem ser incluídas nos arquivos públicos.

### 5. Verificação do funcionamento

Após a configuração dos serviços, o funcionamento deverá ser verificado por meio das seguintes etapas:

1. Executar a simulação do ESP32 no Wokwi.
2. Alterar o valor de luminosidade na simulação.
3. Verificar se a mensagem foi publicada no tópico MQTT.
4. Conferir se o EMQX recebeu e encaminhou a mensagem.
5. Verificar se a API recebeu os dados e registrou a leitura no Supabase.
6. Consultar o frontend e conferir se a leitura correspondente foi apresentada.

Também devem ser verificados o comportamento do sistema diante de uma interrupção da transmissão, a retomada do envio de mensagens e o armazenamento dos dados mesmo quando o painel estiver fechado.

## Testes realizados

Durante o desenvolvimento, foram realizados testes diretamente na função do Supabase para verificar o recebimento e a gravação dos dados. A função retornou sucesso quando recebeu uma requisição no formato esperado.

Também foram configurados o acesso MQTT, o tópico e a regra de encaminhamento no EMQX Cloud. O envio manual pelo cliente MQTT foi utilizado para testar a comunicação com os serviços seguintes.

Durante a integração, foi identificada uma resposta HTTP 400 com o erro `invalid_contract`. Por esse motivo, ainda ficou necessária a validação do formato dos dados encaminhados pela regra e a confirmação do envio automático das leituras pelo circuito.

## Limitações e melhorias

O projeto utilizou um ambiente simulado, portanto os valores não representaram necessariamente medições de um sensor físico instalado junto a uma planta.

Também foi necessária a validação da integração automática entre o ESP32 e o Supabase, além da verificação do funcionamento completo do frontend. Entre as melhorias previstas estavam a apresentação da luminosidade atual, do histórico das leituras e do horário da última atualização, além da indicação de dados desatualizados.

## Links do projeto

- **Circuito no Wokwi:** https://wokwi.com/projects/480982649599772673
- **Supabase:** https://bzjjnpjaxamnvynuijae.supabase.co
- **API REST — hyper-action:** https://bzjjnpjaxamnvynuijae.supabase.co/functions/v1/hyper-action
- **Frontend publicado:** https://patient-sun-9224.santosmariad16.workers.dev/
- **Repositório GitHub:** https://github.com/MariaLu28/Projeto-integrador-de-monitoramento-IoT.git
- **Vídeo de demonstração:** https://youtu.be/X3qp3pKRoR8

## Integrantes

- Luca Casari Veloso de Almeida
- Maria Luiza dos Santos

Projeto desenvolvido como atividade acadêmica do curso de Bacharelado em Inteligência Artificial da Unimar.

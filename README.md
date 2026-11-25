# Monitoramento de Luminosidade Vegetal 🌱

## Sobre o projeto

Este projeto tem como objetivo desenvolver um sistema IoT para monitorar a luminosidade recebida por uma planta. A proposta é acompanhar as variações de luz no ambiente e armazenar essas informações para que possam ser consultadas posteriormente.

O sistema utiliza um ESP32 em um circuito simulado no Wokwi. As leituras são enviadas por MQTT ao EMQX Cloud e encaminhadas para uma API REST integrada ao Supabase, onde ficam armazenadas.

## Objetivo

Criar uma solução que permita acompanhar a luminosidade do ambiente de uma planta, registrando os valores recebidos e possibilitando sua visualização em uma página web.

## Arquitetura do projeto

O sistema é dividido em três partes principais:

- **Sensor simulado:** ESP32 no Wokwi, responsável por gerar as leituras de luminosidade.
- **API REST:** recebe os dados encaminhados pelo EMQX e realiza a gravação no Supabase.
- **Frontend web:** apresenta as informações armazenadas para consulta.

A comunicação entre essas partes utiliza MQTT e requisições HTTP.

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
- **MQTT:** protocolo utilizado para enviar as leituras.
- **EMQX Cloud:** recebe as mensagens MQTT e encaminha os dados.
- **Supabase:** disponibiliza a API REST, a função Edge Function e o banco de dados.
- **Cloudflare Pages:** hospedagem prevista para o frontend web.

## Comunicação MQTT

O dispositivo utilizado no projeto possui o identificador:

```text
esp32_02
```

O tópico utilizado para publicação das leituras é:

```text
esp32_02/luminosidade
```

As mensagens seguem o formato JSON:

```json
{
  "device_id": "esp32_02",
  "message_id": "leitura_001",
  "luminosity": 72.5
}
```

Cada leitura possui um identificador próprio para facilitar o armazenamento e a diferenciação dos registros.

## API e banco de dados

A API foi desenvolvida utilizando uma Supabase Edge Function chamada `hyper-action`.

**Endpoint:**

```text
https://bzjjnpjaxamnvynuijae.supabase.co/functions/v1/hyper-action
```

A função recebe requisições HTTP pelo método POST, valida os dados recebidos e realiza a gravação no banco de dados.

A tabela utilizada é:

```text
public.readings
```

Ela possui os seguintes campos:

| Campo | Descrição |
|---|---|
| device_id | Identificação do dispositivo |
| message_id | Identificação da leitura |
| luminosity | Valor da luminosidade |
| received_at | Data e hora do recebimento |

## Testes realizados

Durante o desenvolvimento, foram realizados testes diretamente na função do Supabase para verificar o recebimento e a gravação dos dados. A função retornou sucesso quando recebeu uma requisição no formato esperado.

Também foram configurados o acesso MQTT, o tópico e a regra de encaminhamento no EMQX Cloud. O envio manual pelo cliente MQTT foi utilizado para testar a comunicação com os serviços seguintes.

Durante a integração, foi identificada uma resposta HTTP 400 com o erro `invalid_contract`. Por isso, ainda é necessário validar o formato dos dados encaminhados pela regra e confirmar o envio automático das leituras pelo circuito.

## Limitações e melhorias

Atualmente, o projeto utiliza um ambiente simulado, portanto os valores não representam necessariamente medições de um sensor físico.

Também é necessário concluir a integração automática entre o ESP32 e o Supabase e finalizar o frontend. Como melhorias, pretende-se apresentar a luminosidade atual, o histórico das leituras e a última atualização recebida, além de indicar quando os dados estiverem desatualizados.

## Links do projeto

- **Circuito no Wokwi:** https://wokwi.com/projects/480982649599772673
- **Supabase:** https://bzjjnpjaxamnvynuijae.supabase.co
- **Site:** https://patient-sun-9224.santosmariad16.workers.dev/

## Integrantes

- Luca Casari Veloso de Almeida ;
- Maria Luiza dos Santos

---

Projeto desenvolvido como atividade acadêmica do curso de Bacharelado em Inteligência Artificial da Unimar.

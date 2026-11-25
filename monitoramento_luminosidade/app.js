
import { buscarLeituras } from "./config.js";

const app = document.getElementById("app");

const plantacoes = {
  batata: {
    nome: "Batata",
    emoji: "🥔",
    luxMinimo: 26950,
    luxMaximo: 43120,
    descricao: "A luz fornece energia para a fotossíntese e contribui para o desenvolvimento das folhas e dos tubérculos."
  },

  soja: {
    nome: "Soja",
    emoji: "🌱",
    luxMinimo: 26950,
    luxMaximo: 43120,
    descricao: "A luz é essencial para a fotossíntese, o crescimento da planta e o desenvolvimento das flores e dos grãos."
  },

  amendoim: {
    nome: "Amendoim",
    emoji: "🥜",
    luxMinimo: 26950,
    luxMaximo: 40425,
    descricao: "A luz fornece energia para a fotossíntese e auxilia no desenvolvimento das folhas, flores e vagens."
  }
};

let grafico = null;
let intervaloAtualizacao = null;

function formatarNumero(valor) {
  return Number(valor).toLocaleString("pt-BR", {
    maximumFractionDigits: 2
  });
}

function formatarData(data) {
  return new Date(data).toLocaleString("pt-BR");
}

function avaliarLuminosidade(valorLux, plantacao) {
  if (valorLux < plantacao.luxMinimo) {
    return {
      emoji: "😟",
      texto: "Luminosidade baixa",
      mensagem: `Abaixo da faixa de referência (${formatarNumero(plantacao.luxMinimo)} a ${formatarNumero(plantacao.luxMaximo)} lux).`
    };
  }

  if (valorLux > plantacao.luxMaximo) {
    return {
      emoji: "🥵",
      texto: "Luminosidade alta",
      mensagem: `Acima da faixa de referência (${formatarNumero(plantacao.luxMinimo)} a ${formatarNumero(plantacao.luxMaximo)} lux).`
    };
  }

  return {
    emoji: "😊",
    texto: "Luminosidade adequada",
    mensagem: `Dentro da faixa de referência (${formatarNumero(plantacao.luxMinimo)} a ${formatarNumero(plantacao.luxMaximo)} lux).`
  };
}

function legendaEmojis() {
  return `
    <div class="legenda">
      <h3>Legenda dos indicadores</h3>

      <div class="legenda-itens">
        <div class="legenda-item">
          <span>😟</span>
          <p>Abaixo da faixa de referência</p>
        </div>

        <div class="legenda-item">
          <span>😊</span>
          <p>Dentro da faixa de referência</p>
        </div>

        <div class="legenda-item">
          <span>🥵</span>
          <p>Acima da faixa de referência</p>
        </div>
      </div>
    </div>
  `;
}

function mostrarInicio() {
  clearInterval(intervaloAtualizacao);

  app.innerHTML = `
    <h1>🌱 Monitor de Luminosidade</h1>

    <p class="subtitle">
      Acompanhe a luminosidade das suas plantações!
    </p>

    <div class="plantacoes" id="plantacoes">
      ${Object.entries(plantacoes).map(([id, plantacao]) => `
        <a href="?plantacao=${id}" class="plantacao">
          <span class="plantacao-emoji">${plantacao.emoji}</span>

          <h2>${plantacao.nome}</h2>

          <p>
            Referência: ${formatarNumero(plantacao.luxMinimo)} a ${formatarNumero(plantacao.luxMaximo)} lux
          </p>

          <div class="resumo-leitura" id="resumo-${id}">
            Carregando leitura...
          </div>

          <span class="acessar">Ver detalhes →</span>
        </a>
      `).join("")}
    </div>

    ${legendaEmojis()}

    <p class="footer">
      Sistema de monitoramento de luminosidade
    </p>
  `;

  carregarResumo();

  intervaloAtualizacao = setInterval(carregarResumo, 10000);
}

async function carregarResumo() {
  for (const [id, plantacao] of Object.entries(plantacoes)) {
    const elemento = document.getElementById(`resumo-${id}`);

    if (!elemento) {
      continue;
    }

    try {
      const leituras = await buscarLeituras(id, 1);

      if (leituras.length === 0) {
        elemento.innerHTML = `
          <span class="status-resumo">😐 Sem leituras</span>
        `;
        continue;
      }

      const ultimaLeitura = leituras[0];

      const status = avaliarLuminosidade(
        Number(ultimaLeitura.luminosity),
        plantacao
      );

      elemento.innerHTML = `
        <span class="status-resumo">
          ${status.emoji} ${status.texto}
        </span>

        <span class="valor-resumo">
          ${formatarNumero(ultimaLeitura.luminosity)}
        </span>

        <span class="unidade-resumo">lux</span>
      `;
    } catch (erro) {
      elemento.innerHTML = `
        <span class="erro-resumo">Erro ao carregar</span>
      `;

      console.error(`Erro ao carregar ${plantacao.nome}:`, erro);
    }
  }
}

function mostrarPlantacao(id) {
  clearInterval(intervaloAtualizacao);

  const plantacao = plantacoes[id];

  if (!plantacao) {
    mostrarInicio();
    return;
  }

  app.innerHTML = `
    <a href="index.html" class="voltar">
      ← Voltar às plantações
    </a>

    <div class="cabecalho-plantacao">
      <span class="emoji">${plantacao.emoji}</span>

      <h1>${plantacao.nome}</h1>

      <div class="status" id="status-atual">
        Carregando status...
      </div>
    </div>

    <div class="painel referencia">
      <h2>Referência de luminosidade</h2>

      <p class="descricao-referencia">
        ${plantacao.descricao}
      </p>

      <div class="referencia-dados">
        <div class="referencia-item">
          <span class="referencia-titulo">
            Faixa de luminosidade de referência
          </span>

          <strong>
            ${formatarNumero(plantacao.luxMinimo)} –
            ${formatarNumero(plantacao.luxMaximo)} lux
          </strong>
        </div>
      </div>
    </div>

    <div class="painel leitura-atual">
      <h2>Leitura atual do sensor</h2>

      <div class="lux" id="valor">--</div>

      <span class="unit">lux</span>

      <div class="message" id="mensagem">
        Aguardando leitura do sensor...
      </div>
    </div>

    ${legendaEmojis()}

    <div class="painel">
      <h2>Histórico de luminosidade</h2>

      <div class="grafico">
        <canvas id="grafico"></canvas>
      </div>
    </div>

    <div class="painel">
      <h2>Histórico de leituras</h2>

      <div class="tabela-container">
        <table>
          <thead>
            <tr>
              <th>Data e horário</th>
              <th>Luminosidade (lux)</th>
              <th>Status</th>
            </tr>
          </thead>

          <tbody id="tabela">
            <tr>
              <td colspan="3">Carregando leituras...</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <p class="footer">
      Atualização automática a cada 10 segundos
    </p>
  `;

  carregarDados(id);

  intervaloAtualizacao = setInterval(() => {
    carregarDados(id);
  }, 10000);
}

async function carregarDados(id) {
  try {
    const leituras = await buscarLeituras(id, 100);

    const valor = document.getElementById("valor");
    const mensagem = document.getElementById("mensagem");
    const tabela = document.getElementById("tabela");

    if (!valor || !mensagem || !tabela) {
      return;
    }

    if (leituras.length === 0) {
      valor.textContent = "--";

      mensagem.textContent =
        "Nenhuma leitura recebida para esta plantação.";

      tabela.innerHTML = `
        <tr>
          <td colspan="3">Nenhuma leitura encontrada.</td>
        </tr>
      `;

      atualizarGrafico([], id);
      return;
    }

    const plantacao = plantacoes[id];

    const ultimaLeitura = leituras[0];

    const status = avaliarLuminosidade(
      Number(ultimaLeitura.luminosity),
      plantacao
    );

    const statusAtual = document.getElementById("status-atual");

    valor.textContent = formatarNumero(ultimaLeitura.luminosity);

    if (statusAtual) {
      statusAtual.textContent =
        `${status.emoji} ${status.texto}`;
    }

    mensagem.innerHTML = `
      <strong>${status.emoji} ${status.texto}</strong>
      <p>${status.mensagem}</p>
    `;

    tabela.innerHTML = leituras.map(leitura => {
      const statusLeitura = avaliarLuminosidade(
        Number(leitura.luminosity),
        plantacao
      );

      return `
        <tr>
          <td>${formatarData(leitura.received_at)}</td>

          <td>${formatarNumero(leitura.luminosity)} lux</td>

          <td>
            ${statusLeitura.emoji} ${statusLeitura.texto}
          </td>
        </tr>
      `;
    }).join("");

    atualizarGrafico(leituras, id);

  } catch (erro) {
    console.error("Erro ao carregar leituras:", erro);

    const mensagem = document.getElementById("mensagem");

    if (mensagem) {
      mensagem.textContent =
        "Não foi possível carregar as leituras.";
    }
  }
}

function atualizarGrafico(leituras, id) {
  const canvas = document.getElementById("grafico");

  if (!canvas) {
    return;
  }

  const dados = [...leituras].reverse();

  const labels = dados.map(leitura => {
    return new Date(leitura.received_at).toLocaleTimeString("pt-BR");
  });

  const valores = dados.map(leitura => leitura.luminosity);

  if (grafico) {
    grafico.destroy();
  }

  grafico = new Chart(canvas, {
    type: "line",

    data: {
      labels: labels,

      datasets: [{
        label: "Luminosidade (lux)",
        data: valores,
        borderColor: "#38965c",
        backgroundColor: "rgba(56, 150, 92, 0.15)",
        borderWidth: 3,
        pointRadius: 4,
        pointHoverRadius: 7,
        fill: true,
        tension: 0.3
      }]
    },

    options: {
      responsive: true,
      maintainAspectRatio: false,

      interaction: {
        intersect: false,
        mode: "index"
      },

      plugins: {
        legend: {
          display: true
        },

        tooltip: {
          callbacks: {
            label: function(context) {
              return `Luminosidade: ${formatarNumero(context.parsed.y)} lux`;
            }
          }
        }
      },

      scales: {
        x: {
          title: {
            display: true,
            text: "Horário da leitura"
          }
        },

        y: {
          beginAtZero: true,

          title: {
            display: true,
            text: "Luminosidade (lux)"
          }
        }
      }
    }
  });
}

const parametros = new URLSearchParams(window.location.search);

const identificador = parametros.get("plantacao");

if (identificador && plantacoes[identificador]) {
  mostrarPlantacao(identificador);
} else {
  mostrarInicio();
}

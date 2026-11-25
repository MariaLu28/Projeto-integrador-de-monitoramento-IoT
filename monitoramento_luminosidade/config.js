
export const SUPABASE_URL =
  "https://bzjjnpjaxamnvynuijae.supabase.co";

export const SUPABASE_KEY =
  "sb_publishable_GhyX8vemh0Ft8-gOr1qt9A_B8lv4bBD";

const TABELA = "readings";
const DEVICE_ID = "esp32_02";

export async function buscarLeituras(plantacao, limite = 100) {
  const url =
    `${SUPABASE_URL}/rest/v1/${TABELA}` +
    `?select=device_id,message_id,sensor_id,luminosity,received_at` +
    `&device_id=eq.${encodeURIComponent(DEVICE_ID)}` +
    `&sensor_id=eq.${encodeURIComponent(plantacao)}` +
    `&order=received_at.desc` +
    `&limit=${limite}`;

  const resposta = await fetch(url, {
    method: "GET",
    headers: {
      "apikey": SUPABASE_KEY,
      "Authorization": `Bearer ${SUPABASE_KEY}`,
      "Content-Type": "application/json"
    }
  });

  if (!resposta.ok) {
    const erro = await resposta.text();

    throw new Error(
      "Erro ao consultar Supabase: " + erro
    );
  }

  return await resposta.json();
}

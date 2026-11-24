
from machine import ADC, Pin
import time
import network
import ntptime
import ssl
import json
import os
import binascii
import _thread
import sys
import select

from mqtt_client import MQTTClient
from ca_cert import ca_der
from config import (
    MQTT_HOST, MQTT_PORT, MQTT_USER, MQTT_PASSWORD,
    DEVICE_ID, TOPIC, SEND_INTERVAL_MS
)

# ==========================================
# CONFIGURACAO GERAL
# ==========================================

BOOT_ID = binascii.hexlify(os.urandom(8)).decode()
CLIENT_ID = (DEVICE_ID + "-" + BOOT_ID).encode()

lock = _thread.allocate_lock()

estado = {
    "leituras": [],
    "pausa": False,
    "confirmada": False
}

contador = 0


# ==========================================
# SENSORES LDR
# ==========================================

sensores = [
    {
        "id": "batata",
        "adc": ADC(Pin(32))
    },
    {
        "id": "soja",
        "adc": ADC(Pin(33))
    },
    {
        "id": "amendoim",
        "adc": ADC(Pin(34))
    }
]

for sensor in sensores:
    sensor["adc"].atten(ADC.ATTN_11DB)


VIN = 3.3
R_FIXED = 10000.0
RL10 = 50000.0
GAMMA = 0.7


def read_lux(adc):
    raw = adc.read_u16()

    # Evita divisao por zero e valores infinitos.
    voltage = (raw / 65535.0) * VIN

    if voltage < 0.0001:
        voltage = 0.0001

    if voltage > VIN - 0.0001:
        voltage = VIN - 0.0001

    r_ldr = R_FIXED * (voltage / (VIN - voltage))

    lux = 10.0 * ((RL10 / r_ldr) ** (1.0 / GAMMA))

    return round(lux)


# ==========================================
# IDENTIFICACAO DAS MENSAGENS
# ==========================================

def novo_id():
    global contador

    contador += 1

    return "%s-%s-%d" % (
        DEVICE_ID,
        BOOT_ID,
        contador
    )


# ==========================================
# CONTROLE DE PAUSA
# ==========================================

def pausado():
    with lock:
        return estado["pausa"]


def esperar(ms):
    inicio = time.ticks_ms()

    while time.ticks_diff(time.ticks_ms(), inicio) < ms:
        if pausado():
            return

        time.sleep_ms(100)


# ==========================================
# CONEXAO WIFI E MQTT
# ==========================================

def fechar(cliente):
    if cliente is not None:
        try:
            cliente.sock.close()
        except Exception:
            pass


def conectar(wifi):
    wifi.active(True)

    if not wifi.isconnected():
        wifi.disconnect()
        time.sleep_ms(500)

        wifi.connect("Wokwi-GUEST", "")

    inicio = time.ticks_ms()

    while not wifi.isconnected():
        if pausado():
            raise OSError("Pausa solicitada")

        if time.ticks_diff(time.ticks_ms(), inicio) > 30000:
            wifi.disconnect()
            raise OSError("Tempo de Wi-Fi excedido")

        time.sleep_ms(100)

    print("IP", wifi.ifconfig()[0])

    ntptime.timeout = 3
    ntptime.settime()

    print("RELOGIO SINCRONIZADO", time.gmtime()[:6])

    if pausado():
        raise OSError("Pausa solicitada")

    ssl_params = {
        "cert_reqs": ssl.CERT_REQUIRED,
        "cadata": ca_der(),
        "server_hostname": MQTT_HOST
    }

    cliente = MQTTClient(
        client_id=CLIENT_ID,
        server=MQTT_HOST,
        port=MQTT_PORT,
        user=MQTT_USER.encode(),
        password=MQTT_PASSWORD.encode(),
        keepalive=60,
        ssl=True,
        ssl_params=ssl_params
    )

    try:
        cliente.connect(timeout=5)
    except Exception:
        fechar(cliente)
        raise

    print("MQTT CONECTADO")

    return cliente


# ==========================================
# TAREFA DE REDE
# ==========================================

def tarefa_rede():
    wifi = network.WLAN(network.STA_IF)

    cliente = None
    ultimo_envio = None

    while True:
        try:
            if pausado():
                fechar(cliente)
                cliente = None

                if wifi.active():
                    wifi.active(False)

                with lock:
                    primeira = not estado["confirmada"]
                    estado["confirmada"] = True

                if primeira:
                    print("REDE PAUSADA: aquisicao local continua")

                time.sleep_ms(100)
                continue

            with lock:
                estado["confirmada"] = False

            if cliente is None or not wifi.isconnected():
                fechar(cliente)
                cliente = None

                cliente = conectar(wifi)

                ultimo_envio = None

            agora = time.ticks_ms()

            venceu = (
                ultimo_envio is None or
                time.ticks_diff(agora, ultimo_envio) >= SEND_INTERVAL_MS
            )

            if venceu and not pausado():

                # Copia as leituras sem manter o lock durante a rede.
                with lock:
                    leituras = [
                        dict(leitura)
                        for leitura in estado["leituras"]
                    ]

                if leituras and not pausado():

                    for leitura in leituras:
                        payload = json.dumps(leitura).encode()

                        cliente.publish(
                            TOPIC.encode(),
                            payload,
                            retain=False,
                            qos=0
                        )

                        print(
                            "PUBLICADO",
                            leitura["sensor_id"],
                            leitura["message_id"],
                            "(nao comprova gravacao)"
                        )

                    ultimo_envio = time.ticks_ms()

            time.sleep_ms(100)

        except Exception as erro:
            print(
                "FALHA REDE",
                type(erro).__name__,
                str(erro)
            )

            fechar(cliente)
            cliente = None

            esperar(3000)


# ==========================================
# LEITURA DOS SENSORES
# ==========================================

poll = select.poll()
poll.register(sys.stdin, select.POLLIN)

print("Envie x + Enter para alternar pausa/retomada da rede")

_thread.start_new_thread(tarefa_rede, ())

ultimo = time.ticks_ms()

while True:

    # Controle de pausa pelo monitor serial.
    if poll.poll(0):
        tecla = sys.stdin.read(1)

        if tecla.lower() == "x":
            with lock:
                estado["pausa"] = not estado["pausa"]
                pedido = estado["pausa"]

            print(
                "PEDIDO",
                "PAUSA" if pedido else "RETOMADA"
            )

    agora = time.ticks_ms()

    if time.ticks_diff(agora, ultimo) >= 2000:

        intervalo = time.ticks_diff(agora, ultimo)
        ultimo = agora

        novas_leituras = []

        # Le cada sensor individualmente.
        for sensor in sensores:
            try:
                lux_value = read_lux(sensor["adc"])

                leitura = {
                    "device_id": DEVICE_ID,
                    "message_id": novo_id(),
                    "sensor_id": sensor["id"],
                    "luminosity": lux_value
                }

                novas_leituras.append(leitura)

                print(
                    "LOCAL",
                    sensor["id"],
                    "Lum:",
                    lux_value
                )

            except OSError as erro:
                print(
                    "FALHA SENSOR",
                    sensor["id"],
                    erro
                )

        # Atualiza as tres leituras de uma vez.
        with lock:
            estado["leituras"] = novas_leituras

        print("INTERVALO_MS", intervalo)

    time.sleep_ms(50)

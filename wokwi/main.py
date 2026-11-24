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
from config import (MQTT_HOST, MQTT_PORT, MQTT_USER, MQTT_PASSWORD,
                    DEVICE_ID, TOPIC, SEND_INTERVAL_MS)

BOOT_ID = binascii.hexlify(os.urandom(8)).decode()
CLIENT_ID = (DEVICE_ID + "-" + BOOT_ID).encode()
lock = _thread.allocate_lock()
estado = {"leitura": None, "pausa": False, "confirmada": False}
contador = 0


def novo_id():
    global contador
    contador += 1
    return "%s-%s-%d" % (DEVICE_ID, BOOT_ID, contador)


def pausado():
    with lock:
        return estado["pausa"]


def esperar(ms):
    inicio = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), inicio) < ms:
        if pausado():
            return
        time.sleep_ms(100)


def fechar(cliente):
    if cliente is not None:
        try:
            cliente.sock.close()
        except Exception:
            pass



def conectar(wifi):
    wifi.active(True)

    if not wifi.isconnected():
        # Cancela uma tentativa anterior, caso exista.
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
            venceu = (ultimo_envio is None or
                      time.ticks_diff(agora, ultimo_envio) >= SEND_INTERVAL_MS)
            if venceu and not pausado():
                # Copiar rapidamente. Nenhuma operação de rede dentro do lock.
                with lock:
                    leitura = (dict(estado["leitura"])
                               if estado["leitura"] else None)
                if leitura is not None and not pausado():
                    payload = json.dumps(leitura).encode()
                    cliente.publish(TOPIC.encode(), payload,
                                    retain=False, qos=0)
                    print("PUBLICADO", leitura["message_id"],
                          "(nao comprova gravacao)")
                    ultimo_envio = time.ticks_ms()
            time.sleep_ms(100)
        except Exception as erro:
            print("FALHA REDE", type(erro).__name__, str(erro))
            fechar(cliente)
            cliente = None
            # Não conservar payload para reenvio. Só a leitura atual permanece.
            esperar(3000)

ldr_pin = ADC(Pin(32))
ldr_pin.atten(ADC.ATTN_11DB)
VIN = 3.3
R_FIXED = 10000.0
RL10 = 50000.0
GAMMA = 0.7

def read_lux():
    raw = ldr_pin.read_u16()
    if raw <= 0:
        return float('inf')
    if raw >= 65535:
        return 0.0
        
    voltage = (raw / 65535.0) * VIN
    
    r_ldr = R_FIXED * (voltage / (VIN - voltage))
    
    
    lux = 10.0 * ((RL10 / r_ldr) ** (1.0 / GAMMA))
    return lux

poll = select.poll()
poll.register(sys.stdin, select.POLLIN)
print("Envie x + Enter para alternar pausa/retomada da rede")
_thread.start_new_thread(tarefa_rede, ())
ultimo = time.ticks_ms()
while True:
    if poll.poll(0):
        tecla = sys.stdin.read(1)
        if tecla.lower() == "x":
            with lock:
                estado["pausa"] = not estado["pausa"]
                pedido = estado["pausa"]
            print("PEDIDO", "PAUSA" if pedido else "RETOMADA")
    agora = time.ticks_ms()
    if time.ticks_diff(agora, ultimo) >= 2000:
        intervalo = time.ticks_diff(agora, ultimo)
        ultimo = agora
        try:
            lux_value = read_lux()
            leitura = {"device_id": DEVICE_ID, "message_id": novo_id(),
                       "luminosity": lux_value}
            with lock:
                estado["leitura"] = leitura
            print("LOCAL Lum", lux_value,
                  "intervalo_ms", intervalo)
        except OSError as erro:
            # Política didática de falha: apagar indicador e invalidar a leitura.
            with lock:
                estado["leitura"]=None
            print("FALHA SENSOR",erro)
    time.sleep_ms(50)

#!/usr/bin/env python3

# Componentes Basico
# EP - PUCPR
# Prof. Luiz Lima Jr.

from pika import BlockingConnection
from sys import argv
from enum import Enum

if len(argv) < 2:
    print(f"USO: {argv[0]} <id> [<v1> <v2> ...]")
    exit(1)

Estado = Enum('Estado', ['OCIOSO', 'INICIADOR'])

idx = argv[1]
Nx = argv[2:]
estado = Estado.OCIOSO

print("meu id =", idx)
print("meus vizinhos =", Nx)

from pika import ConnectionParameters

conexao = BlockingConnection(ConnectionParameters('localhost'))
canal = conexao.channel()

canal.queue_declare(queue=idx, auto_delete=True)

# envia mensagem para dest
def envia(msg, dests, canal):
    for dest in dests:
        canal.basic_publish(exchange="",
                            routing_key=dest,
                            body=idx + ":" + msg)

def recebendo(msg, origem, canal):
    # implemente aqui o algoritmo distribuido
    print(f"{msg} recebida de {origem}")

def espontaneamente(msg, canal):
    # implemente aqui o algoritmo distribuido
    global estado
    estado = Estado.INICIADOR
def callback(ch, method, properties, body):
    m = body.decode().split(":")
    if len(m) < 2:
        # nao tem origem
        msg = m[0]
        origem = "STARTER"
    else:
        msg = m[1]
        origem = m[0]

    if origem.upper() == "STARTER":
        espontaneamente(msg, ch)
    else:
        recebendo(msg, origem, ch)
    else:
        recebendo(msg, origem, canal)


canal.basic_consume(queue=idx,
                    on_message_callback=callback,
                    auto_ack=True)

try:
    print(f"{idx}: aguardando mensagens...")
    canal.start_consuming()
except KeyboardInterrupt:
    canal.stop_consuming()

conexao.close()
print("Terminando")


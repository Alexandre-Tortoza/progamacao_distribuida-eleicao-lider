#!/usr/bin/env python3

from pika import BlockingConnection
from sys import argv
from enum import Enum

if len(argv) < 4:
    print(f"USO: {argv[0]} <id> <vizinho> <valor>")
    exit(1)

Estado = Enum('Estado', ['OCIOSO', 'INICIADOR'])

idx = argv[1]
vizinho = argv[2]
valor = argv[3]
estado = Estado.OCIOSO

print("meu id =", idx)
print("meu vizinho =", vizinho)
print("meu valor =", valor)

conexao = BlockingConnection()
canal = conexao.channel()

canal.queue_declare(queue=idx, auto_delete=True)

# envia mensagem para dest
def envia(msg, dests, canal):
    for dest in dests:
        canal.basic_publish(exchange="",
                            routing_key=dest,
                            body=idx + ":" + msg)

def recebendo(msg, origem, canal):
    print(f"{msg} recebida de {origem}")
    if (int(msg) == int(valor)):
        print(f"Eu sou o lider com o valor: {valor}")
    else:
        if (int(msg) < int(valor)):
            envia(msg, vizinho, canal)
            print(f"Enviando {msg} para {vizinho}")
        else:
            envia(valor, vizinho, canal)
            print(f"Enviando {valor} para {vizinho}")

def espontaneamente(msg, canal):
    global estado
    estado = Estado.INICIADOR
    envia(valor, vizinho, canal)

def callback(canal, metodo,  props, msg):
    m = msg.decode().split(":")
    if len(m) < 2:
        # nao tem origem
        msg = m[0]
        origem = "STARTER"
    else:
        msg = m[1]
        origem = m[0]

    if origem.upper()=="STARTER":
        espontaneamente(msg, canal)
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


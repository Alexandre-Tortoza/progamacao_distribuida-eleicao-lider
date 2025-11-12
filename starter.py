#!/usr/bin/env python3

from pika import BlockingConnection
from sys import argv

if len(argv) < 2:
	print(f"Uso: {argv[0]} <mensagem> <dest1> ")
	exit(1)

mensagem = argv[1]
destinos = argv[2]

def envia(msg, dest, canal):
	canal.basic_publish(exchange="",
						routing_key=dest,
						body="STARTER:" + msg)

conexao = BlockingConnection()
canal = conexao.channel()

for d in destinos:
	canal.queue_declare(queue=d, auto_delete=True)
	envia(mensagem, d, canal)
	print(f'Mensagem "{mensagem}" enviada para {d}')

conexao.close()

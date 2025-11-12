#!/usr/bin/env python3

from pika import BlockingConnection, ConnectionParameters
from sys import argv

if len(argv) < 3:
    print(f"Uso: {argv[0]} <mensagem> <dest1> [<dest2> ...] (onde <dest1>, <dest2>, ... são nomes de filas)")
    exit(1)

mensagem = argv[1]  
destinos = argv[2:]  

def envia(msg, dest, canal):
    canal.basic_publish(
        exchange="",              
        routing_key=dest,         
        body=f"STARTER:{msg}"     
    )

conexao = BlockingConnection(ConnectionParameters('localhost'))
canal = conexao.channel()

for d in destinos:    
    canal.queue_declare(queue=d)

    envia(mensagem, d, canal)
    
    print(f'Mensagem "{mensagem}" enviada para {d}')


conexao.close()
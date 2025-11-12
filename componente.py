#!/usr/bin/env python3

from pika import BlockingConnection, ConnectionParameters
from sys import argv
from enum import Enum

if len(argv) < 2:
    print(f"USO: {argv[0]} <id> [<v1> <v2> ...]")
    exit(1)

Estado = Enum('Estado', ['OCIOSO', 'INICIADOR', 'PARTICIPANTE', 'LIDER', 'LIDERADO'])

idx = argv[1]           
Nx = argv[2:]           
estado = Estado.OCIOSO  
lider = None            
participando = False    

print("meu id =", idx)
print("meus vizinhos =", Nx)

conexao = BlockingConnection(ConnectionParameters('localhost'))
canal = conexao.channel()

canal.queue_declare(queue=idx, auto_delete=True)

def envia(msg, dests, canal):
    for dest in dests:
        canal.basic_publish(
            exchange="",                    
            routing_key=dest,               
            body=idx + ":" + msg            
        )

def recebendo(msg, origem, canal):
    global estado, lider, participando

    partes = msg.split(":")
    tipo_msg = partes[0]

    if tipo_msg == "ELECTION":
        id_recebido = partes[1] if len(partes) > 1 else origem
        print(f"[ELECTION] Recebi ID {id_recebido} de {origem} (meu ID: {idx})")
        if id_recebido == idx:
            estado = Estado.LIDER
            lider = idx
            print(f"{idx}: SOU O LÍDER!")
            
            if len(Nx) > 0:
                envia(f"LEADER:{idx}", [Nx[0]], canal)
                print(f"[LEADER] Anunciando liderança para {Nx[0]}")

        elif id_recebido < idx:
            
            print(f"[ELECTION] ID {id_recebido} < {idx}, repassando {id_recebido}")
            if len(Nx) > 0:
                envia(f"ELECTION:{id_recebido}", [Nx[0]], canal)

            if estado == Estado.OCIOSO:
                estado = Estado.PARTICIPANTE
                participando = True

        else:
            
            if not participando:
                print(f"[ELECTION] ID {id_recebido} > {idx}, enviando meu ID {idx}")
                if len(Nx) > 0:
                    envia(f"ELECTION:{idx}", [Nx[0]], canal)
                estado = Estado.PARTICIPANTE
                participando = True
                
            else:
                
                print(f"[ELECTION] ID {id_recebido} > {idx}, mas já participei, ignorando")

    elif tipo_msg == "LEADER":
        id_lider = partes[1] if len(partes) > 1 else origem

        if estado != Estado.LIDER:
            estado = Estado.LIDERADO
            lider = id_lider
            print(f"{idx}: Reconheço {id_lider} como LÍDER")
            
            if len(Nx) > 0:
                envia(f"LEADER:{id_lider}", [Nx[0]], canal)
        else:
            
            print(f"[LEADER] Anúncio completou o anel, eleição finalizada!")
            print(f"★ Sistema estabilizado: {idx} é o LÍDER ★")

def espontaneamente(msg, canal):
    global estado, participando

    estado = Estado.INICIADOR
    participando = True

    print(f"\n{'='*60}")
    print(f"{idx}: INICIANDO ELEIÇÃO ESPONTANEAMENTE")
    print(f"{'='*60}")

    if len(Nx) > 0:
        envia(f"ELECTION:{idx}", [Nx[0]], canal)
        print(f"[ELECTION] Enviando meu ID {idx} para {Nx[0]}")
    else:
        
        print(f"{idx}: Não há vizinhos, SOU O ÚNICO E PORTANTO O LÍDER! ")
        estado = Estado.LIDER
        lider = idx

def callback(ch, method, properties, body):
    m = body.decode().split(":")

    if len(m) < 2:
        msg = m[0]
        origem = "STARTER"
    else:        
        origem = m[0]
        msg = m[1]

    if origem.upper() == "STARTER":
        espontaneamente(msg, ch)
    else:       
        recebendo(msg, origem, ch)

canal.basic_consume(
    queue=idx,                      
    on_message_callback=callback,   
    auto_ack=True                   
)

try:
    print(f"{idx}: aguardando mensagens...")
    canal.start_consuming()
except KeyboardInterrupt:
    
    canal.stop_consuming()

conexao.close()
print("Terminando")
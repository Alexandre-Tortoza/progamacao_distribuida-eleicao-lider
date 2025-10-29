# Especificação Formal: Eleição de Líder em Anel

## 1. Visão Geral

Sistema distribuído que implementa algoritmo de eleição de líder em topologia de anel usando RabbitMQ.

**Objetivo**: Garantir que exatamente um nó seja eleito líder em um anel de N nós com IDs únicos.

**Tecnologias**:

- Python 3.13
- RabbitMQ Server
- Biblioteca `pika`
- Exchange tipo DIRECT

---

## 2. Especificação do Algoritmo

### 2.1. Propriedades Obrigatórias

**P1 - Terminação**: O algoritmo deve terminar em tempo finito.

**P2 - Unicidade**: Ao final, exatamente um nó deve estar no estado LEADER.

**P3 - Correção**: O líder eleito deve ter o menor ID entre todos os nós participantes.

### 2.2. Estados Possíveis

```python
ASLEEP     # Estado inicial, aguardando eleição
CANDIDATE  # Participando ativamente da eleição
LEADER     # Eleito como líder
FOLLOWER   # Reconheceu outro nó como líder
```

### 2.3. Tipos de Mensagens

```python
ELECTION(candidate_id)  # Propaga ID candidato
ELECTED(leader_id)      # Anuncia líder eleito
```

### 2.4. Regras do Algoritmo

**REGRA 1: Iniciar Eleição**

```
QUANDO: Espontaneamente ∧ state = ASLEEP
FAZER:
  state := CANDIDATE
  ENVIAR ELECTION(meu_id) para sucessor
```

**REGRA 2: Receber ELECTION com ID menor**

```
QUANDO: RECEBER ELECTION(id) ∧ id < meu_id
FAZER:
  state := CANDIDATE
  ENVIAR ELECTION(id) para sucessor
```

**REGRA 3: Receber ELECTION com ID maior**

```
QUANDO: RECEBER ELECTION(id) ∧ id > meu_id
FAZER:
  state := CANDIDATE
  ENVIAR ELECTION(meu_id) para sucessor
```

**REGRA 4: Receber próprio ID de volta**

```
QUANDO: RECEBER ELECTION(id) ∧ id = meu_id
FAZER:
  state := LEADER
  ENVIAR ELECTED(meu_id) para sucessor
```

**REGRA 5: Receber ELECTED de outro nó**

```
QUANDO: RECEBER ELECTED(id) ∧ id ≠ meu_id
FAZER:
  state := FOLLOWER
  ENVIAR ELECTED(id) para sucessor
```

**REGRA 6: ELECTED volta ao líder**

```
QUANDO: RECEBER ELECTED(id) ∧ id = meu_id
FAZER:
  # Eleição completa - parar propagação
```

### 2.5. Complexidade

- **Mensagens**: O(n²) no pior caso
  - n mensagens ELECTION no pior caso (cada nó pode propagar)
  - n mensagens ELECTED (uma volta completa no anel)
- **Tempo**: O(n) no pior caso
  - Proporcional ao diâmetro do anel (n nós)

---

## 3. Arquitetura AMQP

### 3.1. Topologia RabbitMQ

```
Exchange: "leader.election.ring"
Tipo: DIRECT
Durable: false

Queues: "node.1", "node.2", ..., "node.N"
Bindings: queue "node.X" com routing_key "node.X"
```

### 3.2. Roteamento em Anel

```
Node 1 → publica com routing_key="node.2"
Node 2 → publica com routing_key="node.3"
...
Node N → publica com routing_key="node.1"
```

### 3.3. Formato de Mensagem (JSON)

```json
{
  "type": "ELECTION" | "ELECTED",
  "candidate_id": <int>,
  "sender_id": <int>,
  "timestamp": "<ISO-8601>"
}
```

---

## 4. Estrutura de Código

### 4.1. Estrutura de Diretórios

```
leader-election-ring/
├── src/
│   ├── core/
│   │   ├── entity.py          # Classe Entity
│   │   ├── states.py          # Enum EntityState
│   │   └── message.py         # Dataclasses Message
│   │
│   ├── messaging/
│   │   └── pika_client.py     # Wrapper pika
│   │
│   ├── algorithm/
│   │   └── leader_election.py # Implementação algoritmo
│   │
│   └── node/
│       └── node.py             # Classe Node principal
│
├── scripts/
│   ├── setup_rabbitmq.py      # Setup exchange/queues
│   ├── start_node.py          # Iniciar um nó
│   └── simulate_ring.py       # Simulação completa
│
├── tests/
│   ├── test_entity.py
│   ├── test_algorithm.py
│   └── test_integration.py
│
├── config/
│   └── default.yaml
│
├── requirements.txt
└── README.md
```

### 4.2. Classes Principais

**Entity** (`src/core/entity.py`)

```python
@dataclass
class Entity:
    entity_id: int
    node_index: int
    state: EntityState = EntityState.ASLEEP
    successor_index: int = 0
```

**Node** (`src/node/node.py`)

```python
class Node:
    def __init__(self, node_index: int, entity_id: int, ring_size: int)
    def send_to_successor(self, message: Message)
    def on_message_received(self, ch, method, properties, body)
    def start_election(self)
    def start(self)
    def stop(self)
```

**LeaderElection** (`src/algorithm/leader_election.py`)

```python
class LeaderElection:
    def handle_election(self, entity: Entity, candidate_id: int) -> Action
    def handle_elected(self, entity: Entity, leader_id: int) -> Action
```

---

## 5. Exemplo de Execução

### 5.1. Setup Inicial

```bash
# 1. Instalar RabbitMQ
docker run -d --name rabbitmq -p 5672:5672 rabbitmq:3-management

# 2. Instalar dependências
pip install pika pydantic PyYAML

# 3. Configurar topology
python scripts/setup_rabbitmq.py --nodes 5
```

### 5.2. Configuração (config/default.yaml)

```yaml
rabbitmq:
  host: localhost
  port: 5672

ring:
  size: 5
  node_ids: [5, 3, 7, 1, 4] # IDs únicos

election:
  initiator_index: 1
```

### 5.3. Simulação

```bash
# Simula anel completo
python scripts/simulate_ring.py
```

**Saída Esperada:**

```
[Node 1] ID=5 iniciando eleição
[Node 1] Enviou ELECTION(5) para Node 2
[Node 2] ID=3 recebeu ELECTION(5)
[Node 2] Enviou ELECTION(3) para Node 3
[Node 3] ID=7 recebeu ELECTION(3)
[Node 3] Enviou ELECTION(3) para Node 4
[Node 4] ID=1 recebeu ELECTION(3)
[Node 4] Enviou ELECTION(1) para Node 5
[Node 5] ID=4 recebeu ELECTION(1)
[Node 5] Enviou ELECTION(1) para Node 1
[Node 1] ID=5 recebeu ELECTION(1)
[Node 1] Enviou ELECTION(1) para Node 2
[Node 2] ID=3 recebeu ELECTION(1)
[Node 2] Enviou ELECTION(1) para Node 3
[Node 3] ID=7 recebeu ELECTION(1)
[Node 3] Enviou ELECTION(1) para Node 4
[Node 4] ID=1 recebeu ELECTION(1) - próprio ID!
[Node 4] SOU O LÍDER! Enviando ELECTED(1)
[Node 5] Reconheço líder ID=1
[Node 1] Reconheço líder ID=1
[Node 2] Reconheço líder ID=1
[Node 3] Reconheço líder ID=1
[Node 4] Eleição completa!

✓ Líder eleito: Node 4 (ID=1)
✓ Terminação garantida
✓ Unicidade garantida
✓ Correção garantida (menor ID)
```

---

## 6. Casos de Teste Obrigatórios

### 6.1. Teste Básico: 3 Nós

```python
# Anel: [5, 3, 7]
# Esperado: Node com ID=3 seja eleito líder
```

### 6.2. Teste Completo: 5 Nós

```python
# Anel: [5, 3, 7, 1, 4]
# Esperado: Node com ID=1 seja eleito líder
```

### 6.3. Teste Pior Caso

```python
# Anel: [5, 4, 3, 2, 1]
# Iniciador: Node com ID=5
# Esperado: Node com ID=1 seja eleito líder
# Complexidade: O(n²) mensagens
```

### 6.4. Teste com IDs Não Sequenciais

```python
# Anel: [100, 42, 7, 999, 13]
# Esperado: Node com ID=7 seja eleito líder
```

---

## 7. Validação das Propriedades

### 7.1. Terminação

**Critério**: Algoritmo deve terminar em no máximo 2n passos.

**Validação**:

- Contar total de mensagens enviadas
- Verificar que processo para após ELECTED completar volta

### 7.2. Unicidade

**Critério**: Apenas um nó deve estar em estado LEADER ao final.

**Validação**:

```python
assert sum(1 for node in nodes if node.state == LEADER) == 1
```

### 7.3. Correção

**Critério**: Líder eleito deve ter o menor ID.

**Validação**:

```python
leader_id = [n.entity_id for n in nodes if n.state == LEADER][0]
min_id = min(n.entity_id for n in nodes)
assert leader_id == min_id
```

---

## 8. Dependências (requirements.txt)

```txt
pika==1.3.2
pydantic==2.5.3
PyYAML==6.0.1
pytest==7.4.3
```

---

## 9. Critérios de Aceite

- [ ] Implementa todas as 6 regras do algoritmo
- [ ] Usa AMQP/RabbitMQ com exchange DIRECT
- [ ] Biblioteca pika para comunicação
- [ ] Passa em todos os 4 casos de teste
- [ ] Valida as 3 propriedades (terminação, unicidade, correção)
- [ ] Código segue PEP 8
- [ ] Type hints em todas as funções
- [ ] Documentação clara (docstrings)
- [ ] README com instruções de uso

---

## 10. Referências

- **Slides do Professor**: PD_11-AMQP.pdf (páginas 31-36)
- **RabbitMQ Docs**: https://www.rabbitmq.com/tutorials/tutorial-four-python.html
- **Pika Docs**: https://pika.readthedocs.io/
- **AMQP Spec**: https://www.amqp.org/

---

**Última atualização**: 2025-10-29

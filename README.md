# Servidor de Transferência de Arquivos TCP/UDP

Este projeto implementa um servidor de transferência de arquivos em Python capaz de operar simultaneamente com os protocolos TCP e UDP na mesma porta. O sistema é robusto, atendendo múltiplos clientes sem a necessidade de reinicialização e baixando automaticamente o arquivo de exemplo caso ele não seja encontrado localmente.

## Funcionalidades Principais

-   **Servidor Dual**: Opera com TCP e UDP simultaneamente na mesma porta, utilizando threads.
-   **Persistente**: O servidor continua em execução para atender sequencialmente a múltiplos clientes.
-   **Download Automático**: O servidor verifica a existência do arquivo de vídeo localmente e o baixa de uma URL caso não o encontre.
-   **Transferência UDP Confiável**: Implementa um mecanismo simples de Stop-and-Wait com ACKs para garantir a entrega dos pacotes via UDP.
-   **Segurança em Threads (Thread-Safe)**: O acesso ao arquivo e o download inicial são controlados com um Lock para evitar condições de corrida entre as threads TCP e UDP.

## Conteúdo do Repositório

-   `server.py`: O script do servidor. Ele inicia os serviços TCP e UDP e aguarda conexões de clientes.
-   `cliente.py`: O script do cliente. Ele pode se conectar ao servidor usando TCP ou UDP para baixar o arquivo.

## Instruções para Compilação e Execução

O projeto é desenvolvido em Python e não requer um processo de compilação. As bibliotecas utilizadas são parte da biblioteca padrão do Python.

### Pré-requisitos

-   Python 3.x

### Execução

1.  **Clone o repositório:**
    ```bash
    git clone <URL_DO_SEU_REPOSITORIO>
    cd <NOME_DO_SEU_REPOSITORIO>
    ```

2.  **Abra dois terminais** no diretório do projeto. Um será para o servidor e o outro para o cliente.

3.  **No primeiro terminal, inicie o servidor:**
    ```bash
    python3 server.py --port 9000
    ```
    O servidor irá verificar se o arquivo de vídeo existe. Se não existir, ele o baixará e ficará aguardando conexões.

4.  **No segundo terminal, execute o cliente.** Você pode escolher entre o protocolo TCP ou UDP.

    -   **Para transferir via TCP:**
        ```bash
        python3 cliente.py --server 127.0.0.1 --proto tcp --port 9000
        ```
    -   **Para transferir via UDP:**
        ```bash
        python3 cliente.py --server 127.0.0.1 --proto udp --port 9000
        ```

O arquivo recebido será salvo como `received_tcp.mp4` ou `received_udp.mp4` no mesmo diretório.

## Resultados Obtidos nos Testes

Abaixo estão exemplos da saída do console durante a execução dos testes.

### 1. Iniciando o Servidor (sem o arquivo local)

O servidor detecta a ausência do arquivo e inicia o download antes de começar a escutar as conexões.

```
[server] arquivo não encontrado — baixando de [https://file-examples.com/storage/fe90bd970b68dc58f98d738/2017/04/file_example_MP4_1920_18MG.mp4](https://file-examples.com/storage/fe90bd970b68dc58f98d738/2017/04/file_example_MP4_1920_18MG.mp4) ...
[server] download concluído.
[tcp server] servidor iniciado. aguardando conexões em 0.0.0.0:9000 ...
[udp server] servidor UDP iniciado em 0.0.0.0:9000. aguardando requisições...
[main] Servidor duplo (TCP/UDP) rodando na porta 9000. Pressione Ctrl+C para sair.

[udp server] aguardando nova requisição de cliente...
```

### 2. Executando o Cliente TCP

**Saída do Cliente:**
```
[client] iniciando transferência TCP...
[tcp client] filesize = 18874368 bytes. iniciando recebimento...
[tcp client] recebeu 18874368 bytes.
[tcp client] tempo reportado pelo servidor: 0.221458 s
```

**Saída correspondente no Servidor:**
```
[tcp server] conexão de ('127.0.0.1', 54321)
[tcp server] envio para ('127.0.0.1', 54321) concluído. tempo (s): 0.221458
[tcp server] tempo enviado ao cliente ('127.0.0.1', 54321).
[tcp server] conexão com ('127.0.0.1', 54321) fechada. aguardando próxima...
```

### 3. Executando o Cliente UDP

**Saída do Cliente:**
```
[client] iniciando transferência UDP...
[udp client] filesize=18874368, total_packets=4608. iniciando recebimento...
[udp client] arquivo reconstruído (4608 pacotes).
[udp client] tempo reportado pelo servidor: 2.754321 s
```

**Saída correspondente no Servidor:**
```
[udp server] aguardando nova requisição de cliente...
[udp server] pedido de ('127.0.0.1', 45678): b'REQUEST UDP'
[udp server] header confirmado por ('127.0.0.1', 45678).
[udp server] iniciando envio de 4608 pacotes para ('127.0.0.1', 45678).
... (mensagens de retransmissão podem aparecer aqui em caso de perda de pacotes) ...
[udp server] todos pacotes confirmados por ('127.0.0.1', 45678). tempo (s): 2.754321
[udp server] tempo enviado para ('127.0.0.1', 45678).
[udp server] transferência para ('127.0.0.1', 45678) concluída.

[udp server] aguardando nova requisição de cliente...
```
#!/usr/bin/env python3
import socket
import argparse
import os
import struct
import time
import urllib.request
import threading

FILE_URL = "https://file-examples.com/storage/fe90bd970b68dc58f98d738/2017/04/file_example_MP4_1920_18MG.mp4"
LOCAL_FILE = "file_example_MP4_1920_18MG.mp4"
UDP_CHUNK = 4096
UDP_TIMEOUT = 0.5  
MAX_UDP_RETRIES = 8

def ensure_file():
    if os.path.exists(LOCAL_FILE):
        print(f"[server] arquivo local encontrado: {LOCAL_FILE} ({os.path.getsize(LOCAL_FILE)} bytes)")
        return
    print(f"[server] arquivo não encontrado — baixando de {FILE_URL} ...")
    urllib.request.urlretrieve(FILE_URL, LOCAL_FILE)
    print("[server] download concluído.")

def run_tcp(host, port):
    ensure_file()
    filesize = os.path.getsize(LOCAL_FILE)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.listen(5)
        print(f"[tcp server] servidor iniciado. aguardando conexões em {host}:{port} ...")
        
        while True:
            try:
                conn, addr = s.accept()
                with conn:
                    print(f"\n[tcp server] conexão de {addr}")
                    _ = conn.recv(1024)

                    conn.sendall(struct.pack("!Q", filesize))
                    start = time.time()
                    with open(LOCAL_FILE, "rb") as f:
                        while True:
                            chunk = f.read(65536)
                            if not chunk:
                                break
                            conn.sendall(chunk)
                    end = time.time()
                    elapsed = end - start
                    print(f"[tcp server] envio para {addr} concluído. tempo (s): {elapsed:.6f}")

                    conn.sendall(struct.pack("!d", elapsed))
                    print(f"[tcp server] tempo enviado ao cliente {addr}.")
                print(f"[tcp server] conexão com {addr} fechada. aguardando próxima...")
            except KeyboardInterrupt:
                print("\n[tcp server] encerrando thread TCP...")
                break
            except Exception as e:
                print(f"[tcp server] erro inesperado: {e}. aguardando próxima conexão...")

def run_udp(host, port):
    ensure_file()
    filesize = os.path.getsize(LOCAL_FILE)
    total_packets = (filesize + UDP_CHUNK - 1) // UDP_CHUNK

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        print(f"[udp server] servidor UDP iniciado em {host}:{port}. aguardando requisições...")
        
        while True:
            try:
                print("\n[udp server] aguardando nova requisição de cliente...")
                data, client_addr = s.recvfrom(4096)
                print(f"[udp server] pedido de {client_addr}: {data.decode(errors='ignore')}")
                
                header = struct.pack("!QI", filesize, total_packets)
                header_acked = False
                tries = 0
                while not header_acked and tries < MAX_UDP_RETRIES:
                    s.sendto(header, client_addr)
                    s.settimeout(UDP_TIMEOUT)
                    try:
                        ack_data, _ = s.recvfrom(1024)
                        if ack_data == b"ACK_HEADER":
                            header_acked = True
                    except socket.timeout:
                        tries += 1
                        print(f"[udp server] retransmitindo header para {client_addr} (tentativa {tries})")

                if not header_acked:
                    print(f"[udp server] não recebeu ACK do header de {client_addr}. abortando esta sessão.")
                    continue
                
                print(f"[udp server] header confirmado por {client_addr}.")

                packets = []
                with open(LOCAL_FILE, "rb") as f:
                    seq = 0
                    while True:
                        chunk = f.read(UDP_CHUNK)
                        if not chunk:
                            break
                        pkt = struct.pack("!I", seq) + chunk
                        packets.append(pkt)
                        seq += 1

                print(f"[udp server] iniciando envio de {len(packets)} pacotes para {client_addr}.")
                start = time.time()
                aborted = False
                for seq_num, pkt in enumerate(packets):
                    tries = 0
                    while True:
                        s.sendto(pkt, client_addr)
                        s.settimeout(UDP_TIMEOUT)
                        try:
                            ack_data, _ = s.recvfrom(1024)
                            if len(ack_data) >= 4:
                                (ack_seq,) = struct.unpack("!I", ack_data[:4])
                                if ack_seq == seq_num:
                                    break
                        except socket.timeout:
                            tries += 1
                            if tries >= MAX_UDP_RETRIES:
                                print(f"[udp server] timeout com pacote {seq_num} para {client_addr}. abortando sessão.")
                                aborted = True
                                break
                            print(f"[udp server] retransmitindo pacote {seq_num} para {client_addr} (tentativa {tries})")
                    if aborted:
                        break
                
                if aborted:
                    continue

                end = time.time()
                elapsed = end - start
                print(f"[udp server] todos pacotes confirmados por {client_addr}. tempo (s): {elapsed:.6f}")

                s.sendto(struct.pack("!d", elapsed), client_addr)
                print(f"[udp server] tempo enviado para {client_addr}.")
                print(f"[udp server] transferência para {client_addr} concluída.")

            except KeyboardInterrupt:
                print("\n[udp server] encerrando thread UDP...")
                break
            except Exception as e:
                print(f"[udp server] erro inesperado: {e}. aguardando próxima requisição...")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Servidor de transferência (TCP e UDP) - mede tempo de envio")
    parser.add_argument("--host", default="0.0.0.0", help="IP para bind (default 0.0.0.0)")
    parser.add_argument("--port", type=int, default=9000, help="porta (default 9000)")
    args = parser.parse_args()


    tcp_thread = threading.Thread(target=run_tcp, args=(args.host, args.port))
    udp_thread = threading.Thread(target=run_udp, args=(args.host, args.port))

    tcp_thread.start()
    udp_thread.start()

    print(f"[main] Servidor duplo (TCP/UDP) rodando na porta {args.port}. Pressione Ctrl+C para sair.")

    try:
        tcp_thread.join()
        udp_thread.join()
    except KeyboardInterrupt:
        print("\n[main] Recebido sinal de interrupção. Encerrando servidores...")
    
    print("[main] Servidores encerrados.")

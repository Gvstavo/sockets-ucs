#!/usr/bin/env python3
import socket
import struct
import argparse
import os

def run_tcp(server_ip, server_port, out_file="received_tcp.mp4"):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((server_ip, server_port))
        s.sendall(b"REQUEST TCP")
        raw = s.recv(8)
        if len(raw) < 8:
            print("[tcp client] não recebeu cabeçalho de tamanho.")
            return
        (filesize,) = struct.unpack("!Q", raw)
        print(f"[tcp client] filesize = {filesize} bytes. iniciando recebimento...")
        received = 0
        with open(out_file, "wb") as f:
            while received < filesize:
                chunk = s.recv(65536)
                if not chunk:
                    break
                f.write(chunk)
                received += len(chunk)
        print(f"[tcp client] recebeu {received} bytes.")
        raw = b""
        while len(raw) < 8:
            more = s.recv(8 - len(raw))
            if not more:
                break
            raw += more
        if len(raw) == 8:
            (elapsed,) = struct.unpack("!d", raw)
            print(f"[tcp client] tempo reportado pelo servidor: {elapsed:.6f} s")
        else:
            print("[tcp client] não recebeu tempo do servidor.")

def run_udp(server_ip, server_port, out_file="received_udp.mp4"):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(5.0)
        server = (server_ip, server_port)
        
        s.sendto(b"REQUEST UDP", server)
        
        try:
            header, _ = s.recvfrom(4096)
            s.sendto(b"ACK_HEADER", server) 
        except socket.timeout:
            print("[udp client] timeout esperando pelo header do servidor. abortando.")
            return
            
        filesize, total_packets = struct.unpack("!QI", header[:12])
        print(f"[udp client] filesize={filesize}, total_packets={total_packets}. iniciando recebimento...")

        received_packets = {}
        
        while len(received_packets) < total_packets:
            try:
                data, _ = s.recvfrom(4096 + 4) 
            except socket.timeout:
                print(f"[udp client] timeout esperando pacote... recebidos {len(received_packets)}/{total_packets}")
                continue
                
            if len(data) >= 4:
                seq = struct.unpack("!I", data[:4])[0]
                payload = data[4:]
                if seq not in received_packets:
                    received_packets[seq] = payload
                s.sendto(struct.pack("!I", seq), server)

        with open(out_file, "wb") as f:
            for i in range(total_packets):
                f.write(received_packets.get(i, b''))
        print(f"[udp client] arquivo reconstruído ({len(received_packets)} pacotes).")

        try:
            s.settimeout(2.0)
            data, _ = s.recvfrom(1024)
            if len(data) >= 8:
                (elapsed,) = struct.unpack("!d", data[:8])
                print(f"[udp client] tempo reportado pelo servidor: {elapsed:.6f} s")
            else:
                print("[udp client] não recebeu tempo do servidor.")
        except socket.timeout:
            print("[udp client] não recebeu confirmação final com o tempo (timeout).")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cliente para teste de transferência TCP/UDP")
    parser.add_argument("--server", required=True, help="IP do servidor")
    parser.add_argument("--port", type=int, default=9000, help="porta do servidor (default 9000)")
    parser.add_argument("--proto", choices=["tcp", "udp"], required=True, help="protocolo a usar (tcp ou udp)")
    args = parser.parse_args()

    if args.proto == "tcp":
        run_tcp(args.server, args.port)
    elif args.proto == "udp":
        run_udp(args.server, args.port)
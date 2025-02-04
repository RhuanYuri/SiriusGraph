import serial
import serial.tools.list_ports
import time

# Função para listar as portas seriais disponíveis
def listar_portas_seriais():
    portas = serial.tools.list_ports.comports()
    return [porta.device for porta in portas]

# Função para conectar a uma porta serial específica
def conectar_porta_serial(porta, baudrate=115200):
    try:
        conexao = serial.Serial(porta, baudrate, timeout=1)
        if conexao.is_open:
            print(f"Conectado à porta {porta} com baudrate {baudrate}.")
            return conexao
        else:
            print(f"Falha ao conectar à porta {porta}.")
            return None
    except serial.SerialException as e:
        print(f"Erro ao conectar à porta {porta}: {e}")
        return None

# Função para ler dados da porta serial
def ler_dados_serial(conexao, tempo_leitura=5):
    start_time = time.time()
    while time.time() - start_time < tempo_leitura:
        if conexao.in_waiting > 0:
            dados = conexao.readline().decode().strip()
            return dados
        time.sleep(0.1)
    return None

# Função principal para testar todas as portas seriais e exibir apenas a que está transmitindo dados
def testar_portas_seriais():
    portas = listar_portas_seriais()
    print(f"Portas seriais disponíveis: {portas}")
    for porta in portas:
        conexao = conectar_porta_serial(porta)
        if conexao:
            dados = ler_dados_serial(conexao)
            if dados:
                print(f"Porta {porta} está transmitindo dados: {dados}")
                conexao.close()
                return
            else:
                print(f"Nenhum dado recebido na porta {porta}.")
                conexao.close()

if __name__ == "__main__":
    testar_portas_seriais()

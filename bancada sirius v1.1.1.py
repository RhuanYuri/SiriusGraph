import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import serial
import serial.tools.list_ports
import time
import cv2
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from PIL import Image, ImageTk, ImageOps
from sklearn.linear_model import LinearRegression
import os

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
            # Verificação adicional para garantir que há comunicação na porta serial
            conexao.write(b'\n')  # Enviar um byte para verificar a comunicação
            time.sleep(1)  # Esperar um momento para receber a resposta
            if conexao.in_waiting > 0:
                print("Comunicação estabelecida com sucesso.")
                return conexao
            else:
                print("Nenhuma resposta do dispositivo na porta serial.")
                conexao.close()
                return None
        else:
            print(f"Falha ao conectar à porta {porta}.")
            return None
    except serial.SerialException as e:
        print(f"Erro ao conectar à porta {porta}: {e}")
        return
# Função para desenhar o gráfico de linha como uma imagem
def gerar_imagem_grafico(df, largura, altura):
    fig, ax = plt.subplots(figsize((largura / 100), (altura / 100)), dpi=100)

    # Gráfico de linha para tempo vs. força
    ax.plot(df['tempo'], df['forca'], color='purple', label='Força (N)')  # Linha roxa
    
    # Configurações do gráfico
    ax.set_title('Força vs. Tempo')
    ax.set_xlabel('Tempo (s)')
    ax.set_ylabel('Força (N)')
    ax.grid(True)

    # Ajustar os limites do eixo y para manter os dados centralizados
    ax.set_ylim(0, df['forca'].max() * 1.2)

    # Tornar o gráfico transparente
    ax.set_facecolor((0, 0, 0, 0))  # Fundo do gráfico transparente
    fig.patch.set_alpha(0)  # Fundo da figura transparente

    # Converter o gráfico para uma imagem numpy
    canvas = FigureCanvas(fig)
    canvas.draw()

    # Transformar a figura em uma imagem numpy
    img = np.frombuffer(canvas.tostring_rgb(), dtype='uint8')
    img = img.reshape(fig.canvas.get_width_height()[::-1] + (3,))
    
    plt.close(fig)  # Fechar a figura para liberar memória
    return img
class CalibrationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Calibração da Célula de Carga")

        # Definir cores
        btn_color = "#4CAF50"
        btn_fg_color = "#ffffff"
        label_color = "#333333"
        
        # Atributos para gravação
        self.gravando = False
        self.dados = []  # Lista para armazenar os dados
        self.arquivo = None  # Caminho do arquivo de saída
        self.serial_connection = None  # Conexão serial
        self.model = LinearRegression()  # Modelo de regressão linear

        # Carregar a imagem de fundo
        # coloque o caminho do arquivo fundo.png presente na pasta(lembre de colocar barras duplas)
        self.background_image = Image.open("C:\\Users\\neide\\Downloads\\abviewer\\Projeto bancada sirius v1\\fundo.png")
        self.background_photo = ImageTk.PhotoImage(self.background_image)
        self.canvas = tk.Canvas(root)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.update_background_image()

        # Vincular o evento de redimensionamento da janela à função de redimensionamento da imagem de fundo
        self.root.bind("<Configure>", self.on_resize)

        # Definir a variável known_weight
        self.known_weight = tk.DoubleVar()

        # Interface
        self.port_label = tk.Label(root, text="Selecione a porta serial:", fg=label_color, font=('Arial', 12))
        self.port_label.place(x=20, y=20)
        
        self.port_combobox = ttk.Combobox(root, values=listar_portas_seriais())
        self.port_combobox.place(x=220, y=20)
        
        self.refresh_button = tk.Button(root, text="Atualizar Portas", command=self.atualizar_portas, bg=btn_color, fg=btn_fg_color, font=('Arial', 10))
        self.refresh_button.place(x=400, y=20)

        self.label = tk.Label(root, text="Peso conhecido (kg):", fg=btn_color, font=('Arial', 12))
        self.label.place(x=20, y=60)
        
        self.entry = tk.Entry(root, textvariable=self.known_weight)
        self.entry.place(x=220, y=60)

        self.calibrate_button = tk.Button(root, text="Calibrar", command=self.calibrate, font=('Arial', 10))
        self.calibrate_button.place(x=20, y=100)

        self.start_recording_button = tk.Button(root, text="Iniciar Gravação", command=self.iniciar_gravacao, font=('Arial', 10))
        self.start_recording_button.place(x=120, y=100)

        self.save_data_button = tk.Button(root, text="Salvar Dados", command=self.salvar_dados, font=('Arial', 10))
        self.save_data_button.place(x=220, y=100)

        self.marca_dagua_button = tk.Button(root, text="Selecionar Marca d'Água", command=self.selecionar_marca_dagua, font=('Arial', 10))
        self.marca_dagua_button.place(x=320, y=100)

        self.show_graph_button = tk.Button(root, text="Mostrar Gráfico com Webcam", command=self.mostrar_webcam_com_grafico, font=('Arial', 10))
        self.show_graph_button.place(x=20, y=140)

        self.connect_button = tk.Button(root, text="Conectar", command=self.conectar_porta, font=('Arial', 10))
        self.connect_button.place(x=220, y=140)

        # Animação
        self.animate_widgets()

    def animate_widgets(self):
        # Animação para o botão calibrar
        self.calibrate_button.config(bg="red")
        self.root.after(500, lambda: self.calibrate_button.config(bg="blue"))
        self.root.after(1000, lambda: self.animate_widgets())

    def atualizar_portas(self):
        self.port_combobox['values'] = listar_portas_seriais()
    
    def update_background_image(self):
        # Obtenha o tamanho atual da janela
        width, height = self.root.winfo_width(), self.root.winfo_height()
        resized_image = self.background_image.resize((width, height), Image.Resampling.LANCZOS)
        self.background_photo = ImageTk.PhotoImage(resized_image)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.background_photo)
        self.canvas.lower("all")

    def on_resize(self, event):
        # Atualiza a imagem de fundo quando a janela é redimensionada
        self.update_background_image()
    def conectar_porta(self):
        port = self.port_combobox.get()
        try:
            self.serial_connection = serial.Serial(port, 115200, timeout=1)
            messagebox.showinfo("Conexão", f"Conectado à porta {port}")
        except serial.SerialException as e:
            messagebox.showerror("Erro de Conexão", f"Não foi possível abrir a porta {port}: {e}")

    def testar_conexao(self):
        try:
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.write(b'g\n')
                response = self.serial_connection.readline().decode().strip()
                if response.startswith("<2,"):
                    messagebox.showinfo("Teste de Conexão", "Conexão estabelecida e resposta recebida.")
                else:
                    messagebox.showerror("Teste de Conexão", "Resposta inválida recebida.")
        except (serial.SerialException, ValueError) as e:
            messagebox.showerror("Erro de Conexão", f"Erro ao testar a conexão: {e}")
    def selecionar_marca_dagua(self):
        self.marca_dagua_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp;*.tiff")])
        if self.marca_dagua_path:
            self.marca_dagua = cv2.imread(self.marca_dagua_path, cv2.IMREAD_UNCHANGED)  # Carregar com canal alfa para transparência
            if self.marca_dagua is None:
                messagebox.showerror("Erro", "Não foi possível carregar a imagem da marca d'água.")
            else:
                messagebox.showinfo("Informação", f"Marca d'água carregada: {self.marca_dagua_path}")
        else:
            messagebox.showinfo("Informação", "Nenhuma imagem selecionada.")

    def get_load_cell_reading(self):
        try:
            if self.serial_connection and self.serial_connection.is_open:
                line = self.serial_connection.readline().decode().strip()
                if line:
                    _, time_value, weight_value = line.strip('<>').split(',')
                    return float(weight_value)
        except (serial.SerialException, ValueError) as e:
            messagebox.showerror("Erro de Conexão", f"Erro na leitura dos dados: {e}")
        return None

    def set_conversion_factor(self, factor):
        if self.serial_connection and self.serial_connection.is_open:
            command = f's{factor}\n'
            self.serial_connection.write(command.encode())
            response = self.serial_connection.read_until().decode().strip()
            messagebox.showinfo("Resposta", f"Fator de conversão atualizado: {response}")
    def calibrate(self):
        # Aviso ao usuário para obter leituras sem carga
        messagebox.showinfo("Aviso", "Vamos obter os valores sem carga.")
        if not messagebox.askokcancel("Confirmação", "Clique em OK para continuar."):
            return  # Se o usuário cancelar, interrompa o processo

        # Obtenha a leitura sem carga
        no_load_value = self.get_load_cell_reading()
        messagebox.showinfo("Informação", "Adicione a carga conhecida e clique em OK")
        
        # Obtenha a leitura com carga conhecida
        known_load_value = self.get_load_cell_reading()
        known_weight = self.known_weight.get()
        
        # Calcular o fator de conversão
        conversion_factor = (known_load_value - no_load_value) / known_weight
        print(f'Novo fator de conversão: {conversion_factor}')
        
        # Atualizar dados de calibração para aprendizado de máquina
        self.update_calibration_data(no_load_value, known_load_value, known_weight)

        # Configurar novo fator de conversão no ESP32
        self.set_conversion_factor(conversion_factor)
    
    def update_calibration_data(self, no_load_value, known_load_value, known_weight):
        # Atualizar o modelo de regressão linear com novos dados
        X = np.array([[no_load_value], [known_load_value]])
        y = np.array([0, known_weight])
        self.model.fit(X, y)
        print("Modelo de regressão atualizado.")
    def iniciar_gravacao(self):
        """Inicia a gravação dos dados."""
        if not self.gravando:
            self.gravando = True
            self.dados.clear()  # Limpa os dados antes de começar a gravar
            self.start_recording_button.config(text="Parar Gravação")  # Atualiza o texto do botão

            # Criar a pasta para salvar os dados
            self.folder_name = f"calibration_data_{time.strftime('%Y%m%d_%H%M%S')}"
            os.makedirs(self.folder_name, exist_ok=True)

            # Iniciar o VideoWriter para gravação de tela
            self.video_writer = cv2.VideoWriter(
                os.path.join(self.folder_name, 'calibration_video.avi'),
                cv2.VideoWriter_fourcc(*'XVID'),
                #taxa de quadros
                30.0,
                (1280, 720)  # Tamanho do frame
            )
        else:
            self.gravando = False
            self.start_recording_button.config(text="Iniciar Gravação")  # Atualiza o texto do botão

            # Finalizar o VideoWriter
            self.video_writer.release()
    def salvar_dados(self):
        """Salva os dados gravados em um arquivo .txt."""
        if not self.dados:
            messagebox.showwarning("Aviso", "Não há dados para salvar.")
            return

        # Salvar os dados na pasta criada
        caminho_arquivo = os.path.join(self.folder_name, 'calibration_data.txt')
        with open(caminho_arquivo, 'w') as f:
            for dado in self.dados:
                f.write(f"{dado}\n")
        messagebox.showinfo("Sucesso", f"Dados salvos em {caminho_arquivo}")
    def mostrar_webcam_com_grafico(self):
        port = self.port_combobox.get()
        cap = cv2.VideoCapture(0)

        # Definir a janela para tela cheia
        cv2.namedWindow('Webcam com Gráfico Transparente', cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty('Webcam com Gráfico Transparente', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        # Carregar a imagem da marca d'água de sua equipe
        marca_dagua_path = self.marca_dagua_path
        marca_dagua = cv2.imread(marca_dagua_path, cv2.IMREAD_UNCHANGED)  # Carregar com canal alfa para transparência

        if marca_dagua is None:
            messagebox.showerror("Erro", "Não foi possível carregar a imagem da marca d'água.")
            return

        # Redimensionar a marca d'água para um tamanho menor
        altura_marca, largura_marca = marca_dagua.shape[:2]
        nova_largura = int(largura_marca * 0.20)  # Largura 20% do original
        nova_altura = int(altura_marca * 0.25)    # Altura 25% do original
        marca_dagua = cv2.resize(marca_dagua, (nova_largura, nova_altura), interpolation=cv2.INTER_AREA)

        try:
            ser = serial.Serial(port, 115200, timeout=1)  # Tentar conectar à porta serial
        except serial.SerialException as e:
            ser = None
            messagebox.showerror("Erro de Conexão", f"Não foi possível abrir a porta {port}: {e}")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            altura, largura, _ = frame.shape  # Dimensões do frame da webcam

            # Posição da marca d'água no canto inferior direito
            y_offset = altura - nova_altura - 3
            x_offset = largura - nova_largura - 3

            # Processamento dos dados se disponíveis
            if ser:
                line = ser.readline().decode().strip()
                if line:
                    data = line.strip('<>').split(',')
                    if len(data) == 3:
                        tempo, forca, pressao = map(float, data)

                        # Criar um DataFrame temporário para o gráfico
                        df = pd.DataFrame({
                            'tempo': [tempo],
                            'forca': [forca],
                            'pressao': [pressao]
                        })

                        # Calcular impulso e total de impulso
                        df['impulso'] = df['forca'] * df['tempo']  # Impulso = Força * Tempo
                        df['impulso_total'] = df['impulso'].cumsum()  # Impulso total é a soma cumulativa dos impulsos

                        # Gerar o gráfico de linha (tempo vs força)
                        grafico_img = gerar_imagem_grafico(df, largura, altura)

                        # Redimensionar o gráfico para cobrir toda a tela
                        grafico_img_resized = cv2.resize(grafico_img, (largura, altura))

                        # Aplicar transparência ao gráfico (0.7 para o frame e 0.3 para o gráfico)
                        combined_frame = cv2.addWeighted(frame, 0.7, grafico_img_resized, 0.3, 0)

                        # Pegar os últimos valores (mais recentes) do dataset
                        ultimo_dado = df.iloc[-1]
                        tempo = ultimo_dado['tempo']
                        forca = ultimo_dado['forca']
                        impulso = ultimo_dado['impulso']
                        impulso_total = df['impulso_total'].iloc[-1]  # Impulso total

                        # Exibir o texto na tela
                        cv2.putText(combined_frame, "Tempo", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
                        cv2.putText(combined_frame, "{:.2f} s".format(tempo), (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)

                        cv2.putText(combined_frame, "Força", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
                        cv2.putText(combined_frame, "{:.2f} N".format(forca), (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)

                        cv2.putText(combined_frame, "Impulso", (10, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
                        cv2.putText(combined_frame, "{:.2f} N.s".format(impulso), (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)

                        cv2.putText(combined_frame, "Impulso Total", (10, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
                        cv2.putText(combined_frame, "{:.2f} N.s".format(impulso_total), (10, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)

                        # Adicionar os dados à lista se a gravação estiver ativa
                        if self.gravando:
                            self.dados.append(f"{tempo},{forca},{impulso},{impulso_total}")

                            # Gravar o frame no vídeo
                            self.video_writer.write(combined_frame)
                else:
                    combined_frame = frame.copy()
            else:
                combined_frame = frame.copy()

            # Sobrepor a marca d'água no canto inferior direito
            if marca_dagua.shape[2] == 4:
                alpha_channel = marca_dagua[:, :, 3] / 255.0
                marca_dagua_rgb = marca_dagua[:, :, :3]
                # Combinando a marca d'água com o frame
                for c in range(0, 3):
                    combined_frame[y_offset:y_offset+nova_altura, x_offset:x_offset+nova_largura, c] = \
                        (1. - alpha_channel) * combined_frame[y_offset:y_offset+nova_altura, x_offset:x_offset+nova_largura, c] + \
                        alpha_channel * marca_dagua_rgb[:, :, c]
            else:
                # Caso a marca d'água não tenha transparência, simplesmente sobrepor
                combined_frame[y_offset:y_offset+nova_altura, x_offset:x_offset+nova_largura] = marca_dagua

            # Mostrar o frame com o gráfico transparente e os dados
            cv2.imshow('Webcam com Gráfico Transparente', combined_frame)

            # Gravar o frame no vídeo, se gravação estiver ativa
            if self.gravando:
                self.video_writer.write(combined_frame)

            # Pressione 'q' para sair
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        if ser:
            ser.close()
        cap.release()
        cv2.destroyAllWindows()

# Função principal
def main():
    root = tk.Tk()
    app = CalibrationApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()

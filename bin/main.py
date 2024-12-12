import cv2
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

# Função para ler os dados do arquivo e gerar o dataset
def ler_dados_arquivo(caminho_arquivo):
    try:
        df = pd.read_csv(caminho_arquivo, delim_whitespace=True, header=None, skiprows=1, encoding='latin1',  names=['tempo', 'forca'])
        return df
    except Exception as e:
        print(f"Erro ao ler o arquivo: {e}")
        return None

# Função para calcular impulso e total de impulso
def calcular_impulso(df):
    df['impulso'] = df['forca'] * df['tempo']  # Impulso = Força * Tempo
    df['impulso_total'] = df['impulso'].cumsum()  # Impulso total é a soma cumulativa dos impulsos
    return df

# Função para desenhar o gráfico de linha como uma imagem
def gerar_imagem_grafico(df, largura, altura):
    # Dimensões do gráfico
    fig, ax = plt.subplots(figsize=(5, 3), dpi=100)  # Ajustar o tamanho do gráfico

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

def mostrar_webcam_com_grafico(caminho_arquivo):
    cap = cv2.VideoCapture(0)

    # Definir a janela para tela cheia
    cv2.namedWindow('Webcam com Gráfico Transparente', cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty('Webcam com Gráfico Transparente', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        altura, largura, _ = frame.shape  # Dimensões do frame da webcam

        # Carregar os dados e gerar a imagem do gráfico
        df = ler_dados_arquivo(caminho_arquivo)
        if df is not None:
            # Calcular impulso e total de impulso
            df = calcular_impulso(df)

            # Gerar o gráfico de linha (tempo vs força)
            grafico_img = gerar_imagem_grafico(df, largura, altura)

            # Definir posição do gráfico no canto inferior esquerdo
            posicao_x = 10
            posicao_y = altura - 200  # Ajuste a altura para posicionar corretamente

            # Redimensionar o gráfico para caber na área designada
            grafico_img_resized = cv2.resize(grafico_img, (300, 170))  # Tamanho do gráfico

            # Criar uma região do frame para colocar o gráfico
            frame_copia = frame.copy()
            frame_copia[posicao_y:posicao_y+170, posicao_x:posicao_x+300] = grafico_img_resized

            # Aplicar transparência ao gráfico (0.7 = 70% do frame + 30% do gráfico)
            combined_frame = cv2.addWeighted(frame, 0.6, frame_copia, 0.4, 0)

            # Pegar os últimos valores (mais recentes) do dataset
            ultimo_dado = df.iloc[-1]
            tempo = ultimo_dado['tempo']
            forca = ultimo_dado['forca']
            impulso = ultimo_dado['impulso']
            impulso_total = df['impulso_total'].iloc[-1]  # Impulso total

            # Ajustar o texto para ficar em múltiplas linhas
            texto1 = f"Tempo:{tempo:.2f} s"
            texto2 = f"Forca:{forca:.2f} N"
            texto3 = f"Impulso:{impulso:.2f} N.s"
            texto4 = f"Impulso Total:{impulso_total:.2f} N.s"

            # Definir as coordenadas para o texto na tela (canto superior esquerdo)
            posicao_x_texto = 10
            posicao_y_inicial = 30
            espaçamento = 50  # Espaçamento entre linhas

            # Exibir o texto na tela
            cv2.putText(combined_frame, texto1.split(':')[0], (posicao_x_texto, posicao_y_inicial), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(combined_frame, texto1.split(':')[1], (posicao_x_texto, posicao_y_inicial + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(combined_frame, texto2.split(':')[0], (posicao_x_texto, posicao_y_inicial + espaçamento), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(combined_frame, texto2.split(':')[1], (posicao_x_texto, posicao_y_inicial + 20 + espaçamento), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(combined_frame, texto3.split(':')[0], (posicao_x_texto, posicao_y_inicial + 2 * espaçamento), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(combined_frame, texto3.split(':')[1], (posicao_x_texto, posicao_y_inicial + 20 + 2 * espaçamento), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(combined_frame, texto4.split(':')[0], (posicao_x_texto, posicao_y_inicial + 3 * espaçamento), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(combined_frame, texto4.split(':')[1], (posicao_x_texto, posicao_y_inicial + 20 + 3 * espaçamento), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
           
            # Mostrar o frame com o gráfico transparente e os dados
            cv2.imshow('Webcam com Gráfico Transparente', combined_frame)

        # Pressione 'q' para sair
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# Função principal
def main(caminho_arquivo):
    mostrar_webcam_com_grafico(caminho_arquivo)

if __name__ == "__main__":
    caminho_arquivo = input('Digite o caminho do arquivo: ') #"C:\\Users\\rhuan\\Downloads\\log_2024_12_12__16h_25min_42s.txt" # Substitua pelo caminho do seu arquivo de dados
    main(caminho_arquivo) 

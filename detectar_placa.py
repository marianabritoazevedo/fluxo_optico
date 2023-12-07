import os
import sys
import cv2
import numpy as np

def select_points(event, x, y, flags, param):
    '''
    Seleciona os 4 pontos referentes aos vértices da placa.
    Devem ser selecionados com o botão esquerdo do mouse
    '''
    global points, select_points_flag
    if event == cv2.EVENT_LBUTTONDOWN:
        if len(points) < 4:
            points.append((x, y))
            if len(points) == 4:
                select_points_flag = True

# Função para calcular o fluxo óptico usando o algoritmo Lucas-Kanade
def calculate_optical_flow(prev_gray, current_gray, points):
    '''
    Cálculo do fluxo óptico a partir do algoritmo de 
    Lucas-Kanade
    '''
    p0 = np.array(points, dtype=np.float32)
    p1, _, _ = cv2.calcOpticalFlowPyrLK(prev_gray, current_gray, p0, None)
    return p1

def initialize():
    '''
    Realiza a inicialização do algoritmo, com alguns parâmetros do vídeo
    e do diretório que irá armazenar as imagens finais
    '''
    # Inicializar o leitor de vídeo de acordo com o caminho do
    # vídeo informado pelo usuário
    video_path = 0 if len(sys.argv) == 1 else sys.argv[1]
    cap = cv2.VideoCapture(video_path)

    # Ler o primeiro frame
    ret, first_frame = cap.read()
    if not ret:
        print("Erro ao ler o vídeo")
        exit()

    # Criar diretório personalizado para os frames ampliados
    name_path = video_path.split('.')
    output_directory = f'frames_{name_path[0]}'
    os.makedirs(output_directory, exist_ok=True)

    return cap, first_frame, output_directory

if __name__ == '__main__':
    '''
    Função principal do código
    '''

    # Inicializar variáveis
    cap, first_frame, output_directory = initialize()
    points = []
    select_points_flag = False
    window_name = 'Rastreamento Óptico'
    frame_count = 0

    # Criar uma janela para o vídeo
    cv2.namedWindow(window_name)
    cv2.setMouseCallback(window_name, select_points)

    while True:
        # Congelar o vídeo até que o usuário selecione quatro pontos
        while not select_points_flag:
            cv2.putText(first_frame, 'Selecione os 4 pontos das extremidades da placa!', (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.imshow(window_name, first_frame)
            if cv2.waitKey(30) & 0xFF == 27:
                break

        # Converter para escala de cinza
        first_frame_gray = cv2.cvtColor(first_frame, cv2.COLOR_BGR2GRAY)

        # Inicializar a janela ampliada
        placa_window = 'Placa do Carro'
        cv2.namedWindow(placa_window)

        while True:
            # Ler o próximo frame
            ret, frame = cap.read()
            if not ret:
                break

            # Converter para escala de cinza
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Rastrear os quatro pontos selecionados usando o fluxo óptico
            new_points = calculate_optical_flow(first_frame_gray, gray, points)

            # Encontrar os pontos para desenho da janela ampliada
            rect = cv2.boundingRect(np.array(new_points, dtype=np.int32))
            x, y, w, h = rect

            # Encontrar retângulo (inclinado ou não) que delimita a região da placa
            placa = cv2.minAreaRect(np.array(new_points, dtype=np.float32))
            box_placa = cv2.boxPoints(placa)
            box_placa = np.int0(box_placa)

            # Exibir a janela ampliada focada na placa do carro (sem retângulo)
            enlarged_frame = frame[y:y + h, x:x + w]
            cv2.imshow(placa_window, enlarged_frame)

            # Salvar o frame ampliado em um arquivo PNG
            frame_filename = os.path.join(output_directory, f'frame_{frame_count:04d}.png')
            cv2.imwrite(frame_filename, enlarged_frame)
            frame_count += 1

            # Exibir o vídeo com os quatro pontos selecionados congelados e retângulo
            # com delimitação da região
            cv2.polylines(frame, [box_placa], isClosed=True, color=(0, 255, 0), thickness=1)
            cv2.imshow(window_name, frame)

            # Atualizar o primeiro frame e pontos
            first_frame_gray = gray
            points = new_points.tolist()

            # Aguardar o pressionamento da tecla 'Esc' para sair
            if cv2.waitKey(30) & 0xFF == 27:
                break

        # Liberar recursos
        cap.release()
        cv2.destroyAllWindows()

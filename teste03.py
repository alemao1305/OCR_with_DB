import cv2 as cv
import numpy as np
from color import *
from vehicle import VehicleCounter
import datetime 
import sqlite3

class VehicleCounter:


    def __init__(self, shape, line_position):
        self.shape = shape
        self.line_position = line_position
        self.vehicle_count = 0 # Inicializar o contador como zero
        self.matched_vehicles = set() # Conjunto para armazenar veículos já contados
    
    def update_count(self, matches,frame_number):
        # Verificar se cada veículo na detecção é novo
        frame_number.draw_frame
        new_vehicles = 0
        for match in matches:
            centroid = match[1]
            centroid_tuple = tuple(centroid)  # Converter para tupla
            if centroid_tuple not in self.matched_vehicles:
                self.matched_vehicles.add(centroid_tuple)
                new_vehicles += 1
        
        # Incrementar a contagem apenas para novos veículos
        self.vehicle_count += new_vehicles

    def reset_count(self):
        # Resetar a contagem de veículos e o conjunto de veículos já contados
        self.vehicle_count = 0
        self.matched_vehicles.clear()

# Iniciar a captura de vídeo
capture = cv.VideoCapture("Recursos/video.mp4")
cars = cv.CascadeClassifier("Recursos/cars.xml")

# Coordenadas das regiões de interesse
coordF   = [(170,448), (214,372), (480,372), (522,448)]
coordROI = [(  0,500), (245,245), (460,245), (645,500)]

# Variáveis para o contador de veículos e arquivo de saída
car_counter = None
output_file_path = "contagem_veiculos.txt"
output_file = open(output_file_path, "w")

# Variáveis para controle do envio de dados para o banco
last_db_update_time = datetime.datetime.now()

# Função para enviar informações para o banco de dados
def enviar_informacoes_para_banco():
    global last_db_update_time
    global car_counter
    data_atual = datetime.datetime.now()#.strftime("%Y-%m-%d %H:%M:%S")
    comando_sql = f"INSERT INTO Contador_De_Veiculos ('QUANTIDADE', 'DATA_INICIO', 'DATA_FIM') VALUES ({car_counter.vehicle_count}, '{last_db_update_time}', '{data_atual}');"
    cur.execute(comando_sql)
    con.commit()
    last_db_update_time = data_atual
    print("Informações enviadas para o banco de dados.")

# Função para desenhar FPS na tela
def draw_fps():
    fps = cv.getTickFrequency() / (cv.getTickCount() - start_time)
    cv.putText(frame, "FPS: {:.1f}".format(fps), (10, 30), cv.FONT_HERSHEY_SIMPLEX, 0.75, (50,170,50), 2)

# Função para desenhar contador na tela
def draw_counter():
    cv.putText(frame, "COUNT: {:.0f}".format(car_counter.vehicle_count), (340, 30), cv.FONT_HERSHEY_SIMPLEX, 0.75, (50,170,50), 2)

# Função para desenhar número do frame na tela
def draw_frame(frame_number):
    cv.putText(frame, "FRAME: {:.0f}".format(frame_number), (635, 30), cv.FONT_HERSHEY_SIMPLEX, 0.75, (50,170,50), 2)

# Função para desenhar polígono na tela
def draw_polygon(coord, color):
    pts = np.array([coord], np.int32)
    pts = pts.reshape((-1, 1, 2))
    cv.polylines(frame, [pts], True, color, 2)

# Função para calcular o centróide
def get_centroid(x, y, largura, altura):
    x1 = largura // 2
    y1 = altura // 2
    cx = x + x1
    cy = y + y1
    return tuple([int(round(cx)), int(round(cy))])

# Função para definir a região de interesse
def region_of_interest(coord, image):
    polygons = np.array([coord])
    mask = np.zeros_like(image)
    cv.fillPoly(mask, polygons, 255)
    masked_image = cv.bitwise_and(gray, mask)
    return masked_image

# Função para lidar com a detecção de veículos
def handle_vehicle_detection(detections, frame_number):
    global car_counter  # Definir a variável car_counter como global

    matches = []
    if car_counter is None:
        car_counter = VehicleCounter(frame.shape[:2], frame.shape[0] / 2)

    for (i, (x, y, w, h)) in enumerate(detections):
        centroid = get_centroid(x, y, w, h)
        cv.rectangle(frame, (x,y), (x+w,y+h), GREEN, 2)
        cv.circle(frame, centroid, 4, RED, -1)
        matches.append(((x, y, w, h), centroid))
        car_counter.update_count(matches, frame)

    update_output_file(car_counter, frame_number)  # Atualizar o arquivo de texto
    draw_counter()
    
# Função para atualizar o arquivo de saída
def update_output_file(counter, frame_number):
    current_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    output_file.write("Data {}: Frame {}: Contagem de veiculos: {}\n".format(current_datetime, frame_number, counter.vehicle_count))

# Loop principal
data_incio = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
con = sqlite3.connect("recursos/Contador.db")
cur = con.cursor()

frame_number = -1
while True:
    start_time = cv.getTickCount()
    frame_number += 1

    ret, frame = capture.read()
    if not ret:
        break
    
    frame = cv.resize(frame, (800, 600))
    gray  = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)

    croppedF   = region_of_interest(coordF, gray)
    croppedROI = region_of_interest(coordROI, gray)

    # Desenhar polígono na tela
    draw_polygon(coordROI, RED)
    cv.line(frame, (0, 300), (800, 300), RED, 1)

    # Detectar veículos
    detections = cars.detectMultiScale(croppedROI, 1.1, 6)
    handle_vehicle_detection(detections, frame_number)

    # Verificar se é hora de enviar dados para o banco de dados
    if (datetime.datetime.now() - last_db_update_time).total_seconds() >= 20:  # Verificar se passaram 20 segundos
        enviar_informacoes_para_banco()  # Enviar informações para o banco de dados
        last_db_update_time = datetime.datetime.now()  # Atualizar o tempo do último envio
        car_counter.reset_count()  # Resetar o contador de veículos para zero

    draw_frame(frame_number)    
    draw_fps()
    
    cv.imshow('Output', frame)

    if cv.waitKey(1) == 27:
        data_final = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        comando_sql = f"INSERT INTO Contador_De_Veiculos ('QUANTIDADE', 'DATA_INICIO', 'DATA_FIM') VALUES ( {car_counter.vehicle_count}, '{data_incio}', '{data_final}');"
        cur.execute(comando_sql)
        con.commit()
        break

# Fechar o arquivo de texto ao encerrar o programa
output_file.close()

# Fechar a conexão com o banco de dados e liberar a captura de vídeo
con.close()
capture.release()
cv.destroyAllWindows()

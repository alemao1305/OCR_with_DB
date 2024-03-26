import cv2 as cv
import numpy as np
from color import *
from vehicle import VehicleCounter
import datetime 
import sqlite3

#capture = cv.VideoCapture(0)
#capture = cv.VideoCapture('rtsp://admin:123456@10.3.0.122:554/play1.sdp', cv.CAP_FFMPEG)
capture = cv.VideoCapture("Recursos/video.mp4")
cars = cv.CascadeClassifier("Recursos/cars.xml")
#moto = cv.CascadeClassifier("Recursos/moto.xml")
#bikes = cv.CascadeClassifier("Recurso/bikes.xml")
#Bus = cv.CascadeClassifier("Recurso/Bus_Front.xml")

coordF   = [(170,448), (214,372), (480,372), (522,448)]
coordROI = [(  0,500), (245,245), (460,245), (645,500)]

#count_temp = 0
car_counter = None
#moto_counter = None
#Bus_front_counter = None

# Criar ou abrir o arquivo de texto para gravação
output_file_path = "contagem_veiculos.txt"
output_file = open(output_file_path, "w")

# ... (código existente)

def update_output_file(counter, frame_number):
    global count_temp
      
    current_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

     
    if counter.vehicle_count > count_temp:
        
        count_temp = counter.vehicle_count
    # Gravar a contagem no arquivo de texto
        output_file.write("Data {}: Frame {}: Contagem de veiculos: {}\n".format(current_datetime, frame_number, counter.vehicle_count))
    while True :
        if counter.vehicle_count >= 1:
            break
    
# ============================================================================

def draw_fps():
    fps = cv.getTickFrequency() / (cv.getTickCount() - start_time)
    cv.putText(frame, "FPS: {:.1f}".format(fps), (10, 30), cv.FONT_HERSHEY_SIMPLEX, 0.75, (50,170,50), 2)

# ============================================================================

def draw_counter():
    cv.putText(frame, "COUNT: {:.0f}".format(car_counter.vehicle_count), (340, 30), cv.FONT_HERSHEY_SIMPLEX, 0.75, (50,170,50), 2)
    #cv.putText(frame, "COUNT: {:.0f}".format(moto_counter.vehicle_count), (340, 60), cv.FONT_HERSHEY_SIMPLEX, 0.75, (50,170,50), 2)
    #cv.putText(frame, "COUNT: {:.0f}".format(Bus_front_counter.vehicle_count), (340, 90), cv.FONT_HERSHEY_SIMPLEX, 0.75, (50,170,50), 2)

# ============================================================================

def draw_frame(frame_number):
    cv.putText(frame, "FRAME: {:.0f}".format(frame_number), (635, 30), cv.FONT_HERSHEY_SIMPLEX, 0.75, (50,170,50), 2)

# ============================================================================

def draw_polygon(coord, color):
    pts = np.array([coord], np.int32)
    pts = pts.reshape((-1, 1, 2))
    cv.polylines(frame, [pts], True, color, 2)

# ============================================================================

def get_centroid(x, y, largura, altura):
    x1 = largura // 2
    y1 = altura // 2
    cx = x + x1
    cy = y + y1
    return tuple([int(round(cx)), int(round(cy))])

# ============================================================================

def region_of_interest(coord, image):
    polygons = np.array([coord])
    mask = np.zeros_like(image)
    cv.fillPoly(mask, polygons, 255)
    masked_image = cv.bitwise_and(gray, mask)
    return masked_image

# ============================================================================

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

    # draw_polygon(coordF, GREEN)
    draw_polygon(coordROI, RED)
    cv.line(frame, (0, 300), (800, 300), RED, 1)

    detections = cars.detectMultiScale(croppedROI, 1.1, 6)

    detections = cars.detectMultiScale(croppedROI, 1.1, 6)

    matches = []
    if car_counter is None:
        car_counter = VehicleCounter(frame.shape[:2], frame.shape[0] / 2)

    for (i, (x, y, w, h)) in enumerate(detections):
        centroid = get_centroid(x, y, w, h)
        cv.rectangle(frame, (x,y), (x+w,y+h), GREEN, 2)
        cv.circle(frame, centroid, 4, RED, -1)
        matches.append(((x, y, w, h), centroid))
        car_counter.update_count(matches, frame)

    # ... (código existente)

    #update_output_file(car_counter, frame_number,)  # Atualizar o arquivo de texto

    draw_frame(frame_number)    
    draw_counter()
    draw_fps()
    
    cv.imshow('Output', frame)

    if cv.waitKey(1) == 27:
        data_final = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        comando_sql = f"INSERT INTO Contador_De_Veiculos ('QUANTIDADE', 'DATA_INICIO', 'DATA_FIM') VALUES ( {car_counter.vehicle_count}, '{data_incio}', '{data_final}');"
        #print(comando_sql)
        cur.execute(comando_sql)
        con.commit()
        con.close()
        break




# Fechar o arquivo de texto ao encerrar o programa
output_file.close()

capture.release()
cv.destroyAllWindows()



import qrcode
from tkinter import messagebox, Tk, Label, Entry, Button
import cv2 as cv
import numpy as np
import datetime
import sqlite3
import psycopg2
import schedule
from vehicle import VehicleCounter
import time
from diretorio_db import caminho2
from diretorio_xml import caminho

class VehicleCounter:
    def __init__(self, frame_size, line_position):
        self.vehicle_count = 0
        self.frame_size = frame_size
        self.line_position = line_position
        self.detected_vehicles = []

    def update_count(self, matches, frame):
        new_vehicles = []
        for (rect, centroid) in matches:
            if self._is_new_vehicle(centroid):
                new_vehicles.append((centroid, datetime.datetime.now()))
        self.detected_vehicles.extend(new_vehicles)
        self.vehicle_count += len(new_vehicles)

    time.sleep(2)
    def reset_count(self):
        time.sleep(0)
        self.vehicle_count = 0
        self.detected_vehicles = []

    def _is_new_vehicle(self, centroid):
        for detected, _ in self.detected_vehicles:
            if self._is_same_vehicle(detected, centroid):
                return False
        return True

    def _is_same_vehicle(self, detected, centroid):
        return (detected[-1] - centroid[-1]) ** 1 + (detected[0] - centroid[0]) ** 2 < 100

url1 = ""
dados = {}

def gera_qr_code():
    global url1

    url = website_entry.get()

    if len(url) == 0:
        messagebox.showinfo(
            title="Erro!",
            message="Favor insira uma URL válida")
    else:
        opcao_escolhida = messagebox.askokcancel(
            title=url,
            message=f"O endereço URL é: \n "
                    f"Endereço: {url} \n "
                    f"Pronto para salvar?")

        if opcao_escolhida:
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(url)
            qr.make(fit=True)
            img = qr.make_image(fill_color='black', back_color='white')
            img.save('qrExport.png')
            url1 = url

if __name__ == '__main__':
    window = Tk()
    window.title("Gerador de Código QR")
    window.config(padx=10, pady=100)

    website_label = Label(text="URL:")
    website_label.grid(row=2, column=0)

    website_entry = Entry(width=35)
    website_entry.grid(row=2, column=1, columnspan=2)
    website_entry.focus()
    add_button = Button(text="IP da Câmera", width=36, command=gera_qr_code)
    add_button.grid(row=4, column=1, columnspan=2)

    window.mainloop()

if caminho:
    cars = cv.CascadeClassifier(caminho)

if url1:
    '''capture = cv.VideoCapture(url1, cv.CAP_FFMPEG)
else:'''
    capture = cv.VideoCapture('recursos/videoeditado.mp4')

if cars.empty():
    print("Erro ao carregar o classificador em cascata!")
else:
    print("Classificador em cascata carregado com sucesso!")

coordF = [(170, 448), (214, 372), (480, 372), (522, 448)]
coordROI = [(0, 500), (245, 245), (460, 245), (645, 500)]

car_counter = VehicleCounter((800, 600), 300)

last_db_update_time = datetime.datetime.now()

host = "10.3.0.151"
port = "5433"
database = "TesteOlinto"
user = "Olinto"
password = "olinto1"


def enviar_para_postgresql():
    global last_db_update_time
    try:
        con = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        cur = con.cursor()
        data_inicio = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data_fim = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        comando_sql = "INSERT INTO Contador_De_Veiculos (QUANTIDADE, DATA_INICIO, DATA_FIM) VALUES (%s, %s, %s);"
        cur.execute(comando_sql, (car_counter.vehicle_count, data_inicio, data_fim))
        con.commit()
        last_db_update_time = data_inicio
        cur.close()
        con.close()
        time.sleep(0)
        #car_counter.reset_count()
        print("Dados enviados para o banco de dados PostgreSQL.")
    except psycopg2.Error as e:
        print("Erro ao conectar ao PostgreSQL:", e)
#time.sleep(3)
def enviar_informacoes_para_banco():
    global last_db_update_time
    global car_counter
    data_atual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    comando_sql = "INSERT INTO Contador_De_Veiculos (QUANTIDADE, DATA_INICIO, DATA_FIM) VALUES (?, ?, ?);"
    cur.execute(comando_sql, (car_counter.vehicle_count, last_db_update_time, data_atual))
    con.commit()
    last_db_update_time = data_atual
    #car_counter.reset_count()
    print("Informações enviadas para o banco de dados SQLite.")


def agendar_envio_dados():
    enviar_para_postgresql()
    enviar_informacoes_para_banco()
    car_counter.reset_count()

schedule.every(0.30).minutes.do(agendar_envio_dados)

output_file_path = "contagem_veiculos.txt"
output_file = open(output_file_path, "w")

def update_output_file(counter, frame_number):
    current_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    output_file.write("Data {}: Frame {}: Contagem de veiculos: {}\n".format(current_datetime, frame_number, counter.vehicle_count))

def draw_fps():
    fps = cv.getTickFrequency() / (cv.getTickCount() - start_time)
    cv.putText(frame, "FPS: {:.1f}".format(fps), (10, 30), cv.FONT_HERSHEY_SIMPLEX, 0.75, (50, 170, 50), 2)

def draw_counter():
    cv.putText(frame, "COUNT: {:.0f}".format(car_counter.vehicle_count), (340, 30), cv.FONT_HERSHEY_SIMPLEX, 0.75, (50, 170, 50), 2)

def draw_frame(frame_number):
    cv.putText(frame, "FRAME: {:.0f}".format(frame_number), (635, 30), cv.FONT_HERSHEY_SIMPLEX, 0.75, (50, 170, 50), 2)

def draw_polygon(coord, color):
    pts = np.array([coord], np.int32)
    pts = pts.reshape((-1, 1, 2))
    cv.polylines(frame, [pts], True, color, 2)

def get_centroid(x, y, largura, altura):
    x1 = largura // 2
    y1 = altura // 2
    cx = x + x1
    cy = y + y1
    return tuple([int(round(cx)), int(round(cy))])

def region_of_interest(coord, image):
    polygons = np.array([coord])
    mask = np.zeros_like(image)
    cv.fillPoly(mask, polygons, 255)
    masked_image = cv.bitwise_and(image, mask)
    return masked_image

data_inicio = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
con = sqlite3.connect(caminho2)
cur = con.cursor()

frame_number = -1
while True:
    start_time = cv.getTickCount()
    frame_number += 1

    ret, frame = capture.read()
    if not ret:
        break
    
    frame = cv.resize(frame, (800, 600))
    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)

    croppedF = region_of_interest(coordF, gray)
    croppedROI = region_of_interest(coordROI, gray)

    draw_polygon(coordROI, (0, 0, 255))
    cv.line(frame, (0, 300), (800, 300), (0, 0, 255), 1)

    detections = cars.detectMultiScale(croppedROI, 1.1, 6)
    matches = []

    for (x, y, w, h) in detections:
        centroid = get_centroid(x, y, w, h)
        cv.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv.circle(frame, centroid, 4, (0, 0, 255), -1)
        matches.append(((x, y, w, h), centroid))

    car_counter.update_count(matches, frame)
    update_output_file(car_counter, frame_number)

    schedule.run_pending()

    draw_frame(frame_number)    
    draw_counter()
    draw_fps()
    
    cv.imshow('Output', frame)

    if cv.waitKey(1) == 27:
        data_final = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        comando_sql = "INSERT INTO Contador_De_Veiculos (QUANTIDADE, DATA_INICIO, DATA_FIM) VALUES (?, ?, ?);"
        cur.execute(comando_sql, (car_counter.vehicle_count, data_inicio, data_final))
        con.commit()

        dados = {'QUANTIDADE': car_counter.vehicle_count}
        enviar_para_postgresql()
        break

output_file.close()
capture.release()
cv.destroyAllWindows()
cur.close()
con.close()

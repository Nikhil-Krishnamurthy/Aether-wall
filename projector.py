import cv2
import time as counter
import threading
import queue
import pygame
import pygame_gui
import socket
from ultralytics import YOLO
from datetime import time
import tinytuya
import asyncio
import python_weather
import datetime
from datetime import date
from typing import Optional, Dict, Any
import requests
import random
import holidays
import os
import html
import math

hud = True #controls if the code will create a window for pycharm.
wifi = False #controls wifi usage for external commands (this needs to be false to run properly)

morning_items = []
afternoon_items = []
evening_items = []
scan_again = True

last_weather_update_min = -1
temp_image = pygame.image.load("assets/sunny.png")

current_quote = ""
break_point = False

write_string = ""
to_write = False
to_remove = False
erase_line = ""

bulb_on_red = 255
bulb_on_green = 255
bulb_on_blue = 255

us_holidays = holidays.US(years=[date.today().year, date.today().year + 1])
today_var = date.today()

upcoming = sorted([(d, name) for d, name in us_holidays.items() if d >= today_var])

string_upcoming = ""
for holiday_date, name in upcoming[:3]:
    string_upcoming += f"{holiday_date.strftime('%b %d')}: {name}\n"

html_safe = html.escape(string_upcoming)
html_holiday = html_safe.replace("\n", "<br>")

#lookup table for all the images for the weather
WEATHER_PHOTOS = {
    python_weather.Kind.SUNNY: "assets/sunny.png",
    python_weather.Kind.CLOUDY: "assets/cloudy.png",
    python_weather.Kind.FOG: "assets/fog.png",
    python_weather.Kind.HEAVY_RAIN: "assets/heavy_rain.png",
    python_weather.Kind.HEAVY_SNOW: "assets/heavy_snow.png",
    python_weather.Kind.HEAVY_SNOW_SHOWERS: "assets/heavy_snow.png",
    python_weather.Kind.HEAVY_SHOWERS: "assets/heavy_showers.png",
    python_weather.Kind.LIGHT_RAIN: "assets/light_rain.png",
    python_weather.Kind.LIGHT_SNOW: "assets/light_snow.png",
    python_weather.Kind.LIGHT_SNOW_SHOWERS: "assets/sleet.png",
    python_weather.Kind.LIGHT_SHOWERS: "assets/light_showers.png",
    python_weather.Kind.LIGHT_SLEET: "assets/sleet.png",
    python_weather.Kind.LIGHT_SLEET_SHOWERS: "assets/sleet.png",
    python_weather.Kind.PARTLY_CLOUDY: "assets/partly_cloudy.png",
    python_weather.Kind.SMOKY_HAZE: "assets/smoky_haze.png",
    python_weather.Kind.THUNDERY_HEAVY_RAIN: "assets/thundery_heavy_rain.png",
    python_weather.Kind.THUNDERY_SHOWERS: "assets/thundery_showers.png",
    python_weather.Kind.THUNDERY_SNOW_SHOWERS: "assets/thundery_showers.png",
    python_weather.Kind.VERY_CLOUDY: "assets/cloudy.png",

}

QUOTE_API = [
    {
        "url": "https://api.kanye.rest",
        "parse": lambda data: f"\"{data['quote']}\" - Kanye"
    },
    {
        "url": "https://api.adviceslip.com/advice",
        "parse": lambda data: f"{data['slip']["advice"]}"
    },
    {
        "url": "https://ron-swanson-quotes.herokuapp.com/v2/quotes",
        "parse": lambda data: f"\"{data[0]}\" - Ron Swanson"
    }
]

#weather storage system, stores temperature, type of weather, and rain amount and chance
current_weather = {
    "temp" : -1,
    "kind" : "",
    "precipitation" : -1.0,
    "term": None,
    "feels": -1,
    "speed": -1,
    "direction": ""
}

morning_weather = {
    "temp" : -1,
    "kind" : "",
    "precipitation" : -1.0,
    "chance" : 0.0,
    "emoji": "",
    "term": None
}

afternoon_weather = {
    "temp" : -1.0,
    "kind" : "",
    "precipitation" : -1.0,
    "chance" : 0.0,
    "emoji": "",
    "term": None
}

evening_weather = {
    "temp" : -1,
    "kind" : "",
    "precipitation" : -1.0,
    "chance" : 0.0,
    "emoji": "",
    "term": None
}

#initializes the ui on the screen, only if enabled, if disabled, turns off time tracking and weather too

if hud:
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    clock = pygame.time.Clock()

    background = pygame.Surface(screen.get_size())
    background.fill((pygame.Color('#000000')))

    manager = pygame_gui.UIManager((1280, 720))


    def create_analog_clock_image(size=100):
        """Draws an analog clock onto a Pygame Surface."""
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        center = (size // 2, size // 2)
        radius = (size // 2) - 4

        pygame.draw.circle(surface, (200, 200, 200), center, radius, 2)

       
        now = datetime.datetime.now()
        hour = now.hour % 12
        minute = now.minute
        second = now.second

      
        hour_angle = math.radians((hour + minute / 60.0) * 30 - 90)
        minute_angle = math.radians((minute + second / 60.0) * 6 - 90)
        second_angle = math.radians(second * 6 - 90)

        h_x = center[0] + (radius * 0.5) * math.cos(hour_angle)
        h_y = center[1] + (radius * 0.5) * math.sin(hour_angle)
        pygame.draw.line(surface, (255, 255, 255), center, (h_x, h_y), 4)

   
        m_x = center[0] + (radius * 0.75) * math.cos(minute_angle)
        m_y = center[1] + (radius * 0.75) * math.sin(minute_angle)
        pygame.draw.line(surface, (220, 220, 220), center, (m_x, m_y), 2)


        s_x = center[0] + (radius * 0.85) * math.cos(second_angle)
        s_y = center[1] + (radius * 0.85) * math.sin(second_angle)
        pygame.draw.line(surface, (220, 50, 50), center, (s_x, s_y), 1)


        pygame.draw.circle(surface, (255, 255, 255), center, 3)

        return surface

    morning_box = pygame_gui.elements.UITextBox( #holds to do for morning
        relative_rect=pygame.Rect((15, 20), (260, 550)),
        html_text="Todo Not Loaded",
        manager=manager
    )

    afternoon_box = pygame_gui.elements.UITextBox( #holds to do for afternoon
        relative_rect=pygame.Rect((285, 20), (260, 550)),
        html_text="Todo Not Loaded",
        manager=manager
    )

    evening_box = pygame_gui.elements.UITextBox( #holds to do for evening
        relative_rect=pygame.Rect((555, 20), (260, 550)),
        html_text="Todo Not Loaded",
        manager=manager
    )

    weather_box = pygame_gui.elements.UITextBox( #current conditions (holds time and weather)
        relative_rect=pygame.Rect((825, 160), (440, 410)),
        html_text="Temperature Not Loaded",
        manager=manager
    )

    morning_weather_box = pygame_gui.elements.UITextBox(
        relative_rect=pygame.Rect((15, 580), (260, 120)),
        html_text="Temperature Not Loaded",
        manager=manager
    )

    afternoon_weather_box = pygame_gui.elements.UITextBox(
        relative_rect=pygame.Rect((285, 580), (260, 120)),
        html_text="Temperature Not Loaded",
        manager=manager
    )

    evening_weather_box = pygame_gui.elements.UITextBox(
        relative_rect=pygame.Rect((555, 580), (260, 120)),
        html_text="Temperature Not Loaded",
        manager=manager
    )

    time_box = pygame_gui.elements.UITextBox(
        relative_rect=pygame.Rect((825,20), (440, 130)),
        html_text="Time",
        manager=manager
    )

    morning_image = pygame_gui.elements.UIImage(
        relative_rect=pygame.Rect((185, 600), (80, 80)),
        image_surface=temp_image,
        manager=manager
    )

    afternoon_image = pygame_gui.elements.UIImage(
        relative_rect=pygame.Rect((455, 600), (80, 80)),
        image_surface=temp_image,
        manager=manager
    )

    evening_image = pygame_gui.elements.UIImage(
        relative_rect=pygame.Rect((725, 600), (80, 80)),
        image_surface=temp_image,
        manager=manager
    )

    weather_image = pygame_gui.elements.UIImage(
        relative_rect=pygame.Rect((1050, 170), (200, 200)),
        image_surface=temp_image,
        manager=manager
    )

    stupid_quote = pygame_gui.elements.UITextBox(
        relative_rect=pygame.Rect((825, 580), (440, 120)),
        html_text="No quote loaded",
        manager=manager
    )

    clock_ui = pygame_gui.elements.UIImage(
        relative_rect=pygame.Rect((1100, 35), (100, 100)),
        image_surface=create_analog_clock_image(100),
        manager=manager
    )

    font_dict = manager.get_theme().get_font_dictionary()

    
    gui_path = os.path.dirname(pygame_gui.__file__)
    regular_path = os.path.join(gui_path, 'core', 'data', 'NotoSans-Regular.ttf')
    bold_path = os.path.join(gui_path, 'core', 'data', 'NotoSans-Bold.ttf')

   
    font_dict.add_font_path('noto_sans', regular_path, bold_path=bold_path)

    font_dict.preload_font(
        font_name='noto_sans',
        font_size=14,
        bold=True
    )

   
    font_dict.preload_font(
        font_name='noto_sans',
        font_size=48,
        bold=True
    )

    font_dict.preload_font(
       font_name='noto_sans',
       font_size = 24,
       bold=False
    )

    font_dict.preload_font(
        font_name='noto_sans',
        font_size=18,
        bold=False
    )


model = YOLO("yolov8n.pt")

bulb_queue = queue.Queue(maxsize=1)

d = tinytuya.BulbDevice(
    dev_id='eb6224cec2a4060340phnr',
    address='192.168.4.221',
    local_key='/dis#|JRO7RZUwh&',
    version='3.3'
)

d1 = tinytuya.BulbDevice(
    dev_id="eb06d3771e317b8ebbt2ar",
    address="192.168.4.215",
    local_key="g<u/OMLjg)j}Z[1c",
    version="3.3"
)



try:
    d.set_colour(255, 0, 0)
except Exception as e:
    print(f"⚠️ Initial Tuya connection failed d: {e}")

try:
    d1.set_colour(255, 0, 0)
except Exception as e:
    print(f"⚠️ Initial Tuya connection failed d1: {e}")

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


last_connect_attempt = 0.0
CONNECT_COOLDOWN = 5.0  

def handle_wifi_communication():
    global wifi, client_socket, to_write, write_string, to_remove, erase_line
    global bulb_on_red, bulb_on_green, bulb_on_blue, last_connect_attempt

    current_time = counter.perf_counter()

   
    if not wifi:
        if current_time - last_connect_attempt < CONNECT_COOLDOWN:
            return 

        last_connect_attempt = current_time
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(0.05)  
            client_socket.connect(("192.168.5.54", 65432))
            client_socket.setblocking(False)
            wifi = True
            print("Connected to Server Program")
        except (socket.error, TimeoutError, OSError):
            wifi = False
            return

  
    try:
        packet = client_socket.recv(1024)
        if not packet:
            wifi = False
            client_socket.close()
            return

        lines = packet.decode('utf-8', errors='ignore').strip().split('\n')
        for line in lines:
            if not line:
                continue

            data_key = line.split("@")
            if len(data_key) < 2:
                continue

            cmd = data_key[0].strip().lower()
            payload = data_key[1].strip()

            if cmd == "red":
                bulb_on_red = int(payload)
            elif cmd == "green":
                bulb_on_green = int(payload)
            elif cmd == "blue":
                bulb_on_blue = int(payload)
            elif cmd == "todo":
                to_write = True
                write_string = payload
            elif cmd == "remove":
                to_remove = True
                erase_line = payload

    except (BlockingIOError, InterruptedError):
        pass
    except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError, OSError):
        wifi = False
        try:
            client_socket.close()
        except Exception:
            pass
        

def get_slot_weather(hourly_slot: Optional[python_weather.forecast.HourlyForecast]) -> Dict[str, Any]:
    if not hourly_slot:
        return {
            "temp": "--",
            "kind": "N/A",
            "precipitation": 0.0,
            "chance": 0,
            "emoji": "N/A",
            "term": None
        }

    return {
        "temp": hourly_slot.temperature,
        "kind": hourly_slot.kind.name,
        "precipitation": hourly_slot.precipitation,
        "emoji": hourly_slot.kind.emoji,
        "term": hourly_slot.kind
    }

def detect_kind(kind):
    return WEATHER_PHOTOS[kind]

def load_quotes():
    global current_quote
    api = random.choice(QUOTE_API)
    try:
        res = requests.get(api["url"], timeout=5).json()
        current_quote = api["parse"](res)
    except Exception:
        current_quote = "Offline Mode: Insert profound thought here"
    stupid_quote.set_text(current_quote)

def load_main_weather():

    weather_box.set_text(
        f"<font size = 6>Current Weather</font><font size=5><br>Temperature: {current_weather["temp"]}<br>Feels Like: {current_weather["feels"]}<br>Kind: {current_weather["kind"]}<br>Precipitation: {current_weather["precipitation"]}</font>"
        f"<br><br><br><br><font size=6>Upcoming Holidays</font><br><font size=5>{html_holiday}</font>"
                         )
    temp_weather_image = pygame.image.load(detect_kind(current_weather["term"]))
    weather_image.set_image(temp_weather_image)

def load_weather_screens(slot, number):
    upload_text = f"Temperature: {slot["temp"]}°F\nKind: {slot["kind"]}\nPrecipitation: {slot["precipitation"]}"

    if number == 0:
        morning_weather_box.set_text(upload_text)
        temp_weather_image = pygame.image.load(detect_kind(slot["term"]))
        morning_image.set_image(temp_weather_image)
    if number == 1:
        afternoon_weather_box.set_text(upload_text)
        temp_weather_image = pygame.image.load(detect_kind(slot["term"]))
        afternoon_image.set_image(temp_weather_image)
    if number == 2:
        evening_weather_box.set_text(upload_text)
        temp_weather_image = pygame.image.load(detect_kind(slot["term"]))
        evening_image.set_image(temp_weather_image)

#function that retrieves and stores weather varaibles in a format that is used later.
async def get_weather():
    global morning_weather
    global afternoon_weather
    global evening_weather
    async with python_weather.Client(unit=python_weather.IMPERIAL) as client:
        weather = await client.get('Dallas')

        current_weather["temp"] = weather.temperature
        current_weather["kind"] = weather.kind.name
        current_weather["precipitation"] = weather.precipitation
        current_weather["term"] = weather.kind
        current_weather["feels"] = weather.feels_like

        today = next(iter(weather))

        morning_weather = get_slot_weather(next((h for h in today if h.time == time(9, 0)), None))
        afternoon_weather = get_slot_weather(next((h for h in today if h.time == time(12, 0)), None))
        evening_weather = get_slot_weather(next((h for h in today if h.time == time(18, 0)), None))

        load_main_weather()
        load_weather_screens(morning_weather, 0)
        load_weather_screens(afternoon_weather, 1)
        load_weather_screens(evening_weather, 2)

def fetch_weather_in_background():
    def _runner():
        try:
            asyncio.run(get_weather())
        except Exception as e:
            print(f"Weather fetch failed: {e}")

    threading.Thread(target=_runner, daemon=True).start()

#simple function to retrieve current time and check if the weather needs to be updated.
def get_time():
    global last_weather_update_min
    now = datetime.datetime.now()
    current_min = now.minute

    time_box.set_text(
        f'<font size=7><b>{now.hour}:{now.minute:02d}</b></font><br>'
        f'<font size=5>{now.month}/{now.day}/{now.year}</font>'
    )
    clock_ui.set_image(create_analog_clock_image(100))
    if current_min in (0, 30) and current_min != last_weather_update_min:
        last_weather_update_min = current_min
        load_quotes()
        fetch_weather_in_background()


def bulb_worker():
    """Background worker that handles Tuya network requests safely."""
    last_state = None
    while True:
        color = bulb_queue.get()
        if color is None:  
            break

        
        if color != last_state:
            try:
                # If color is (0,0,0), turn the bulb off completely
                if color == (0, 0, 0):
                    d.turn_off()
                    d1.turn_off()
                else:
                    d.set_colour(*color)
                    d1.set_colour(*color)
                last_state = color
            except Exception as e:
                print(f"⚠️ Tuya Communication Error: {e}")

        bulb_queue.task_done()


def detect_objects(frame):
    results = model(frame, classes=[0], conf=0.5, verbose=False)
    person_detected = False

    for r in results:
        for box in r.boxes:
            person_detected = True
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, "person", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    return frame, person_detected

def pygame_manager():
    global break_point
    if hud:
        time_delta = clock.tick(60) / 1000.0
        update_display_text()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                print("Break Point active")
                break_point = True
        manager.update(time_delta)
        screen.fill((0, 0, 0))
        manager.draw_ui(screen)
        pygame.display.update()
        get_time()
    else:
        pass

def load_todo():
    global morning_items
    global afternoon_items
    global evening_items
    try:
        with open("morning.txt", "r") as file:
            morning_items = [line.strip() for line in file.readlines() if line.strip()]
    except FileNotFoundError:
        morning_items = []
    try:
        with open("afternoon.txt", "r") as file:
            afternoon_items = [line.strip() for line in file.readlines() if line.strip()]
    except FileNotFoundError:
        afternoon_items = []
    try:
        with open("evening.txt", "r") as file:
            evening_items = [line.strip() for line in file.readlines() if line.strip()]
    except FileNotFoundError:
        evening_items = []

def update_display_text():
    global scan_again
    global morning_items
    global afternoon_items
    global evening_items
    global hud
    if hud and scan_again:
        load_todo()
        morning_string = "\n".join([f"• {item}" for item in morning_items])
        morning_box.set_text(morning_string)

        afternoon_string = "\n".join([f"• {item}" for item in afternoon_items])
        afternoon_box.set_text(afternoon_string)

        evening_string = "\n".join([f"• {item}" for item in evening_items])
        evening_box.set_text(evening_string)
        scan_again = False


def main():
    print("Initializing webcam...")
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    # Create and start the worker thread
    worker_thread = threading.Thread(target=bulb_worker, daemon=True)
    worker_thread.start()

    global scan_again
    global hud
    global break_point
    global wifi, client_socket, to_write, write_string, to_remove, erase_line
    global bulb_on_red, bulb_on_green, bulb_on_blue

    last_bulb_update = 0
    update_interval = 1.0 
    last_detection_time = counter.perf_counter()
    shutdown_cooldown = 5.0


    current_bulb_state = (0, 0, 255)



    if not cap.isOpened():
        print("🛑 Error: Camera could not be opened.")
        return

    if hud:
        fetch_weather_in_background()
        load_quotes()
        load_todo()


    while True:
        current_time = counter.perf_counter()

        pygame_manager()

        ret, frame = cap.read()
        if not ret:
            print("🛑 Error: Failed to grab frame.")
            break

        frame, person_detected = detect_objects(frame)
        cv2.imshow("AI Vision", frame)

        if person_detected:
            last_detection_time = current_time
            target_color = (bulb_on_red, bulb_on_green, bulb_on_blue)  
        else:
           
            if current_time - last_detection_time > shutdown_cooldown:
                target_color = (0, 0, 0)
            else:
                target_color = current_bulb_state  
           
        if target_color != current_bulb_state and (current_time - last_bulb_update > update_interval):
            try:
                
                while not bulb_queue.empty():
                    try:
                        bulb_queue.get_nowait()
                        bulb_queue.task_done()
                    except queue.Empty:
                        break

                print(f"Sending command to queue: {target_color}")
                bulb_queue.put_nowait(target_color)
                current_bulb_state = target_color
                last_bulb_update = current_time
            except queue.Full:
                pass


        #this interprets receives the data and interprets the data from wifi
        handle_wifi_communication()

        #writes to a txt file, if it doesnt exist it creates one
        if to_write:
            todo_key = write_string.split("%") #this splits the string into 2 parts, the identifier and the text
            if todo_key[0] == "morning": #sorts it to the morning to do list
                with open("morning.txt", "a") as file:
                    file.write(todo_key[1] + "\n")
            if todo_key[0] == "afternoon": #sorts it to the afternoon to do list
                with open("afternoon.txt", "a") as file:
                    file.write(todo_key[1] + "\n")
            if todo_key[0] == "evening": #sorts it to the evening to do list
                with open("evening.txt", "a") as file:
                    file.write(todo_key[1] + "\n")
            to_write = False
            scan_again = True

        #removes a line, if the line is -1 it skips, used as redundancy so it doesnt trigger twice
        if to_remove:
            erase_key = erase_line.split("%") #splits list identifier and line
            target_line_to_erase = int(erase_key[1]) #retrieves what line it wants

            if erase_key[0] == "morning": #retrieves all lines and removes the line it doesnt want
                with open("morning.txt", "r") as file:
                    lines = file.readlines()
                    if 0 <= target_line_to_erase < len(lines):
                        del lines[target_line_to_erase]
                with open("morning.txt", "w") as file:
                    file.writelines(lines)

            if erase_key[0] == "afternoon": #retrieves all lines and removes the line it doesnt want
                with open("afternoon.txt", "r") as file:
                    lines = file.readlines()
                    if 0 <= target_line_to_erase < len(lines):
                        del lines[target_line_to_erase]
                with open("afternoon.txt", "w") as file:
                    file.writelines(lines)

            if erase_key[0] == "evening": #retrieves all lines and removes the line it doesnt want
                with open("evening.txt", "r") as file:
                    lines = file.readlines()
                    if 0 <= target_line_to_erase < len(lines):
                        del lines[target_line_to_erase]
                with open("evening.txt", "w") as file:
                    file.writelines(lines)

            to_remove = False
            scan_again = True

        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Exiting...")
            break

        if break_point:
            print("Exiting...")
            break


    # Clean up
    print("Shutting down worker thread...")
    cap.release()
    bulb_queue.put(None)  # Signals worker thread loop to break
    client_socket.close()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

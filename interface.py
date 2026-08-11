import socket
import pygame
import pygame_gui
import threading

running = True

pygame.init()
screen = pygame.display.set_mode((1280, 720))
clock = pygame.time.Clock()

background = pygame.Surface(screen.get_size())
background.fill(pygame.Color('#000000'))

manager = pygame_gui.UIManager((1280, 720))

red_slider = pygame_gui.elements.UIHorizontalSlider(
    relative_rect=pygame.Rect((10, 100), (500, 50)),
    start_value=255, value_range=(0, 255), manager=manager
)
green_slider = pygame_gui.elements.UIHorizontalSlider(
    relative_rect=pygame.Rect((10, 150), (500, 50)),
    start_value=255, value_range=(0, 255), manager=manager
)
blue_slider = pygame_gui.elements.UIHorizontalSlider(
    relative_rect=pygame.Rect((10, 200), (500, 50)),
    start_value=255, value_range=(0, 255), manager=manager
)

write_morning = pygame_gui.elements.UITextEntryLine(relative_rect=pygame.Rect((550, 10), (500, 50)), initial_text="Write to Morning", manager=manager)
write_afternoon = pygame_gui.elements.UITextEntryLine(relative_rect=pygame.Rect((550, 70), (500, 50)),initial_text="Write to Afternoon", manager=manager)
write_evening = pygame_gui.elements.UITextEntryLine(relative_rect=pygame.Rect((550, 130), (500, 50)), initial_text="Write to Evening",manager=manager)

remove_morning = pygame_gui.elements.UITextEntryLine(relative_rect=pygame.Rect((550, 400), (500, 50)), initial_text="Remove from Morning (Numbers only)",manager=manager)
remove_afternoon = pygame_gui.elements.UITextEntryLine(relative_rect=pygame.Rect((550, 460), (500, 50)),initial_text="Remove from Morning (Numbers only)", manager=manager)
remove_evening = pygame_gui.elements.UITextEntryLine(relative_rect=pygame.Rect((550, 520), (500, 50)), initial_text="Remove from Morning (Numbers only)",manager=manager)


conn = None

def handle_network():
     global conn
     server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
     server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
     server_socket.bind(("", 65432))
     server_socket.listen(5)
     print("Server Listening...")
     while running:
         try:
             conn_socket, addr = server_socket.accept()
             print(f"Connected by {addr}")
             conn = conn_socket
         except Exception as e:
             print(f"Server connection error: {e}")

threading.Thread(target=handle_network, daemon=True).start()

def send_data_packet(message: str):
    global conn
    if conn:
        try:
            conn.sendall((message + "\n").encode('utf-8'))
        except (BrokenPipeError, ConnectionResetError) as e:
            print(f"Client disconnected ({e}). Resetting connection handle.")
            try:
                conn.close()
            except Exception:
                pass
            conn = None


last_slider_send = 0
SEND_INTERVAL_MS = 50 
while running:
    time_delta = clock.tick(60) / 1000.0
    current_time = pygame.time.get_ticks()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
            if current_time - last_slider_send > SEND_INTERVAL_MS:
                val = int(event.value)
                color_prefix = None

                if event.ui_element == red_slider:
                    color_prefix = "red"
                elif event.ui_element == green_slider:
                    color_prefix = "green"
                elif event.ui_element == blue_slider:
                    color_prefix = "blue"

                if color_prefix:
                    send_data_packet(f"{color_prefix}@{val}")
                    last_slider_send = current_time
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if write_afternoon.rect.collidepoint(event.pos):
                write_afternoon.set_text("")
            if write_morning.rect.collidepoint(event.pos):
                write_morning.set_text("")
            if write_evening.rect.collidepoint(event.pos):
                write_evening.set_text("")
            if remove_morning.rect.collidepoint(event.pos):
                remove_morning.set_text("")
            if remove_afternoon.rect.collidepoint(event.pos):
                remove_afternoon.set_text("")
            if remove_evening.rect.collidepoint(event.pos):
                remove_evening.set_text("")


        if event.type == pygame_gui.UI_TEXT_ENTRY_FINISHED:
            todo_prefix = None
            start_prefix = None
            text = None
            if event.ui_element == write_morning:
                todo_prefix = "morning"
                start_prefix = "todo"
                text = event.text
                write_morning.set_text("")
            elif event.ui_element == write_afternoon:
                todo_prefix = "afternoon"
                start_prefix = "todo"
                text = event.text
                write_afternoon.set_text("")
            elif event.ui_element == write_evening:
                todo_prefix = "evening"
                start_prefix = "todo"
                text = event.text
                write_evening.set_text("")
            elif event.ui_element == remove_morning:
                todo_prefix = "morning"
                start_prefix = "remove"
                remove_morning.set_text("")
                try:
                    text = int(event.text)
                except ValueError:
                    text = -1
            elif event.ui_element == remove_afternoon:
                todo_prefix = "afternoon"
                start_prefix = "remove"
                remove_afternoon.set_text("")
                try:
                    text = int(event.text)
                except ValueError:
                    text = -1
            elif event.ui_element == remove_evening:
                todo_prefix = "evening"
                start_prefix = "remove"
                remove_evening.set_text("")
                try:
                    text = int(event.text)
                except ValueError:
                    text = -1
            if todo_prefix:
                send_data_packet(f"{start_prefix}@{todo_prefix}%{text}")

        manager.process_events(event)

    manager.update(time_delta)
    screen.blit(background, (0, 0))
    manager.draw_ui(screen)
    pygame.display.flip()

pygame.quit()

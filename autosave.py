import time
from state_manager import save_data

def autosave_loop(player, state, content_name):
    while True:
        time.sleep(5) #guarda cada 5s
        t = player.get_time()

        #anti retroceso
        if t >= state[content_name]["timestamp"]:
            state[content_name]["timestamp"] = t
            save_data(state)
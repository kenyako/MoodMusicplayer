import time
import threading
import vlc

# список радио каналов
channels = []

# флаг, отвечающий за остановку проигрывания музыки
flag = 0

# отдельный поток


def thread(func):
    def wrapper(*args, **kwargs):
        my_thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        my_thread.start()
    return wrapper

# поток, включающий радио


@thread
def radioplay(channel):
    global flag
    flag = 1
    play_ = vlc.MediaPlayer(channel)
    play_.play()

    while flag == 1:
        time.sleep(0.7)

    play_.stop()

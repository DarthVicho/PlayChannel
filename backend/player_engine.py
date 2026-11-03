import vlc
import time

def reproducir_video(ruta_archivo):
    print("Iniciando reproducción...")
    print(f"Archivo: {ruta_archivo}")

    # Crear instancia de VLC
    instancia = vlc.Instance()

    # Crear reproductor
    reproductor = instancia.media_player_new()

    # Crear medio
    media = instancia.media_new(ruta_archivo)

    # Asociar el medio al reproductor
    reproductor.set_media(media)

    # Comenzar reproducción
    reproductor.play()

    # Esperar a que VLC comience
    time.sleep(1)
    print("Video reproduciéndose.")

    # Mantener el programa abierto mientras se reproduce
    while reproductor.is_playing():
        time.sleep(1)
    print("La reproducción terminó.")

if __name__ == "__main__":
    ruta_video = r"C:\RUTA\A\TU\VIDEO.mp4"
    reproducir_video(ruta_video)
import subprocess
import webbrowser
import time
import sys
import os
import signal

# IMPORTANTE: CONFIGURA EL PUERTO LOCAL
HOST = "127.0.0.1"
PORT = "8000"

def main():
    # OBTENER RUTA ABSOLUTA A manage.py
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # ARMAR COMANDO PARA LEVANTAR DJANGO
    # Nota: usamos sys.executable para que PyInstaller lo empotre con el propio Python interno
    cmd = [sys.executable, os.path.join(base_dir, "manage.py"), "runserver", f"{HOST}:{PORT}"]

    # LEVANTAR EL SERVIDOR
    server_process = subprocess.Popen(cmd)

    # ESPERAR UN MOMENTO A QUE ARRANQUE
    time.sleep(1.5)

    # ABRIR EL NAVEGADOR AUTOMATICAMENTE
    webbrowser.open(f"http://{HOST}:{PORT}")

    try:
        # QUEDARSE ESPERANDO HASTA QUE CIERRES
        server_process.wait()
    except KeyboardInterrupt:
        # SI CIERRAS LA CONSOLA, MATAMOS EL SERVIDOR LIMPIO
        server_process.send_signal(signal.SIGINT)
        server_process.wait()

if __name__ == "__main__":
    main()

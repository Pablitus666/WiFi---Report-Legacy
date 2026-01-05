import os
import subprocess
import tkinter as tk
from tkinter import filedialog, scrolledtext, Toplevel, PhotoImage
from PIL import Image, ImageTk
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import getpass
import platform

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ======================================================
# BANNER ASCII
# ======================================================
BANNER_ASCII = r"""_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
     ____       _     _ _ _                   
    |  _ \ __ _| |__ | (_) |_ _   _ ___       
    | |_) / _` | '_ \| | | __| | | / __|      
    |  __/ (_| | |_) | | | |_| |_| \__ \_ _ _ 
    |_|   \__,_|_.__/|_|_|\__|\__,_|___(_|_|_)
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

"""

# ======================================================
# ESTADO
# ======================================================
class AppState:
    def __init__(self):
        self.info_window = None
        self.cache_wifi = None

app_state = AppState()

SPINNER = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧"]
spinner_index = 0

# ======================================================
# UTILIDADES
# ======================================================
def centrar_ventana(win, w, h):
    win.update_idletasks()
    x = (win.winfo_screenwidth() // 2) - (w // 2)
    y = (win.winfo_screenheight() // 2) - (h // 2)
    win.geometry(f"{w}x{h}+{x}+{y}")

def ventana_mensaje(titulo, texto, cerrar=False):
    win = Toplevel(ventana)
    win.title(titulo)
    win.config(bg="#023047")
    win.resizable(0, 0)
    win.iconbitmap(os.path.join(BASE_DIR, "images/logo.ico"))
    centrar_ventana(win, 360, 140)
    win.grab_set()

    tk.Label(
        win, text=texto,
        bg="#023047", fg="white",
        font=("Comic Sans MS", 11, "bold"),
        justify="center", wraplength=320
    ).pack(pady=20)

    def cerrar_todo():
        win.destroy()
        if cerrar:
            ventana.destroy()

    crear_boton("Aceptar", cerrar_todo, win).pack(pady=5)

def ventana_confirmacion(titulo, texto):
    resultado = {"ok": False}

    win = Toplevel(ventana)
    win.title(titulo)
    win.config(bg="#023047")
    win.resizable(0, 0)
    win.iconbitmap(os.path.join(BASE_DIR, "images/logo.ico"))
    centrar_ventana(win, 380, 150)
    win.grab_set()

    tk.Label(
        win, text=texto,
        bg="#023047", fg="white",
        font=("Comic Sans MS", 11, "bold"),
        justify="center", wraplength=330
    ).pack(pady=20)

    frame = tk.Frame(win, bg="#023047")
    frame.pack()

    def aceptar():
        resultado["ok"] = True
        win.destroy()

    crear_boton("Sí", aceptar, frame).grid(row=0, column=0, padx=10)
    crear_boton("Cancelar", win.destroy, frame).grid(row=0, column=1, padx=10)

    win.wait_window()
    return resultado["ok"]

# ======================================================
# VERIFICACIÓN SISTEMA
# ======================================================
def verificar_sistema():
    if platform.system().lower() != "windows":
        ventana_mensaje(
            "Sistema no compatible",
            "Este programa solo funciona en Windows.",
            cerrar=True
        )
        return False
    return True

# ======================================================
# LÓGICA WIFI
# ======================================================
def obtener_redes_wifi():
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = subprocess.SW_HIDE

    salida = subprocess.check_output(
        ['netsh', 'wlan', 'show', 'profiles'],
        startupinfo=si,
        encoding='utf-8',
        errors='ignore'
    )

    redes = [
        l.split(":")[1].strip()
        for l in salida.split("\n")
        if "Perfil de todos los usuarios" in l
    ]

    def clave(red):
        try:
            out = subprocess.check_output(
                ['netsh', 'wlan', 'show', 'profile', f'name={red}', 'key=clear'],
                startupinfo=si,
                encoding='utf-8',
                errors='ignore'
            )
            for l in out.split("\n"):
                if "Contenido de la clave" in l:
                    return f"{red} = {l.split(':')[1].strip()}\n"
            return f"{red} = No disponible\n"
        except:
            return f"{red} = Error\n"

    with ThreadPoolExecutor(max_workers=4) as ex:
        datos = ''.join(ex.map(clave, redes))

    return datos, len(redes)

# ======================================================
# UI FUNCIONES
# ======================================================
def spinner_anim():
    global spinner_index
    if btn_scan["state"] == tk.DISABLED:
        spinner_index = (spinner_index + 1) % len(SPINNER)
        text_box.config(state=tk.NORMAL)
        text_box.delete("1.0", tk.END)
        text_box.insert(tk.END, f"Escaneando redes Wi-Fi {SPINNER[spinner_index]}")
        text_box.config(state=tk.DISABLED)
        ventana.after(120, spinner_anim)

def mostrar_redes():
    if not verificar_sistema():
        return

    btn_scan.config(state=tk.DISABLED)
    app_state.cache_wifi = None
    spinner_anim()
    ventana.after(300, ejecutar_escaneo)

def ejecutar_escaneo():
    datos, total = obtener_redes_wifi()
    app_state.cache_wifi = datos

    text_box.config(state=tk.NORMAL)
    text_box.delete("1.0", tk.END)
    text_box.insert(tk.END, datos)
    text_box.insert(tk.END, f"\nRedes encontradas: {total}\n")
    text_box.config(state=tk.DISABLED)

    btn_scan.config(state=tk.NORMAL)

def guardar_archivo():
    if not app_state.cache_wifi:
        ventana_mensaje("Aviso", "Primero debe realizar un escaneo.")
        return

    ruta = filedialog.asksaveasfilename(
        defaultextension=".txt",
        initialfile="Reporte WiFi.txt",
        filetypes=[("Text files", "*.txt")],
        confirmoverwrite=False
    )

    if not ruta:
        return

    if os.path.exists(ruta):
        if not ventana_confirmacion(
            "Confirmar",
            "El archivo ya existe.\n¿Desea reemplazarlo?"
        ):
            return

    with open(ruta, "w", encoding="utf-8") as file:
        file.write(BANNER_ASCII)
        file.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        file.write(f"Usuario: {getpass.getuser()}\n")
        file.write(f"Sistema: {platform.system()} {platform.release()}\n\n")
        file.write("Nombres de Red y Contraseñas:\n\n")
        file.write(app_state.cache_wifi)
        file.write("\n" + "-" * 50 + "\n")
        file.write("Generado por WiFi Scanner - Pablo Téllez A.\n")

    ventana_mensaje("Éxito", "Reporte guardado correctamente.")

def mostrar_informacion():
    if app_state.info_window and app_state.info_window.winfo_exists():
        return

    win = Toplevel(ventana)
    app_state.info_window = win
    win.title("Información")
    win.config(bg='#023047')
    win.resizable(0, 0)
    win.iconbitmap(os.path.join(BASE_DIR, 'images/logo.ico'))
    centrar_ventana(win, 370, 198)

    frame = tk.Frame(win, bg='#023047')
    frame.pack(padx=10, pady=10)

    img = PhotoImage(file=os.path.join(BASE_DIR, 'images/robot.png'))
    lbl = tk.Label(frame, image=img, bg='#023047')
    lbl.image = img
    lbl.grid(row=0, column=0, rowspan=3, padx=10)

    tk.Label(
        frame,
        text="Desarrollado por:\nPablo Téllez A.\n\nTarija - 2024.",
        bg='#023047', fg='white',
        font=("Comic Sans MS", 14, "bold"),
        justify="center"
    ).grid(row=0, column=1)

    crear_boton("Cerrar", win.destroy, frame).grid(row=2, column=1, pady=5)

# ======================================================
# VENTANA PRINCIPAL
# ======================================================
ventana = tk.Tk()
ventana.withdraw()

WINDOW_WIDTH = 410
WINDOW_HEIGHT = 260

ventana.title("WiFi Scanner")
ventana.config(bg='#023047')
ventana.iconbitmap(os.path.join(BASE_DIR, 'images/logo.ico'))
ventana.resizable(0, 0)
centrar_ventana(ventana, WINDOW_WIDTH, WINDOW_HEIGHT)

text_box_frame = tk.Frame(ventana, bg='#023047', padx=10, pady=5)
text_box_frame.pack(fill=tk.BOTH, expand=True)

text_box = scrolledtext.ScrolledText(
    text_box_frame, width=48, height=8,
    font=("Comic Sans MS", 10),
    wrap=tk.WORD, relief=tk.FLAT
)
text_box.pack(fill=tk.BOTH, expand=True)
text_box.config(state=tk.DISABLED)

button_frame = tk.Frame(ventana, bg='#023047')
button_frame.pack(pady=10)

button_image = ImageTk.PhotoImage(
    Image.open(os.path.join(BASE_DIR, 'images/boton.png')).resize((100, 40))
)

def crear_boton(texto, comando, parent=button_frame):
    btn = tk.Button(
        parent,
        image=button_image,
        text=texto,
        compound="center",
        fg="white",
        font=("Comic Sans MS", 10, "bold"),
        bd=0,
        bg='#033077',
        activebackground='#023047',
        activeforeground='#ffdd57',
        command=comando
    )
    btn.image = button_image
    btn.bind("<Enter>", lambda e: btn.config(fg='#ffdd57'))
    btn.bind("<Leave>", lambda e: btn.config(fg='white'))
    return btn

btn_scan = crear_boton("SCAN", mostrar_redes)
btn_save = crear_boton("SAVE", guardar_archivo)
btn_info = crear_boton("INFO", mostrar_informacion)

btn_scan.grid(row=0, column=0, padx=5)
btn_save.grid(row=0, column=1, padx=5)
btn_info.grid(row=0, column=2, padx=5)

ventana.deiconify()
ventana.after(150, mostrar_redes)
ventana.mainloop()

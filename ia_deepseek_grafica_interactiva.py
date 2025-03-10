import tkinter as tk
from tkinter import scrolledtext, messagebox, Menu
import requests
import json
import threading
import argparse
import warnings

warnings.filterwarnings("ignore", message="Unverified HTTPS request")

# Configuración de la API de DeepSeek
API_URL = "https://api.deepseek.com/v1/chat/completions"
API_KEY = "sk-e........746...............ddd"  # Reemplaza con tu API key de DeepSeek

# Mostrar la ventana y sus componentes
class ChatApp:
    def __init__(self, root, promptInicial=None, modelo="deepseek-chat"):
        self.root = root
        self.root.title("ProyectoA - IA")
        self.contexto = []  # Para mantener el contexto de la conversación
        self.modelo = modelo

        # Establecer un tamaño inicial para la ventana
        self.root.geometry("800x600")  # Ancho x Alto

        # Centrar la ventana en la pantalla
        self.centrarVentana()

        # Área de texto para mostrar la conversación
        self.txtConversacion = scrolledtext.ScrolledText(root, wrap=tk.WORD, state="disabled", selectbackground="yellow", selectforeground="black")
        self.txtConversacion.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

         # Configurar tags para resaltar "IA:" y "Tú:"
        self.txtConversacion.tag_config("user", foreground="blue", font=("Arial", 10, "bold"))
        self.txtConversacion.tag_config("assistant", foreground="green", font=("Arial", 10, "bold"))

        # Menú contextual para copiar texto, seleccionar todo y limpiar
        self.menuEmergenteConversacion = Menu(root, tearoff=0)
        self.menuEmergenteConversacion.add_command(label="Copiar", command=self.copiarTextoPortapapeles)
        self.menuEmergenteConversacion.add_command(label="Seleccionar todo", command=self.seleccionarTodoElTexto)
        self.menuEmergenteConversacion.add_command(label="Limpiar contexto y conversación", command=self.limpiarConversacion)        
        
        # Vincular el menú contextual al área de conversación
        self.txtConversacion.bind("<Button-3>", self.mostrarMenuEmergente)
        
        # Label para mostrar "IA: Procesando..."
        self.lProcesando = tk.Label(root, text="", fg="gray")
        self.lProcesando.pack(padx=10, pady=5)

        # Label encima del campo de Prompt
        prompt_label = tk.Label(root, text="ProyectoA IA, pregúntame lo que quieras:", fg="black", font=("Arial", 10))
        prompt_label.pack(padx=10, pady=(10, 0), anchor="w")  # Empaquetar antes del Frame de entrada

        # Frame para la entrada de texto y los botones
        input_frame = tk.Frame(root)
        input_frame.pack(padx=10, pady=10, fill=tk.BOTH)

        # Entrada de texto multilínea para el usuario
        self.txtPregunta = scrolledtext.ScrolledText(input_frame, wrap=tk.WORD, height=10)
        self.txtPregunta.pack(side=tk.LEFT, padx=5, fill=tk.BOTH, expand=True)
        self.txtPregunta.focus_set()  # Enfocar el campo de entrada al iniciar

        # Si se proporciona un prompt inicial, añadirlo al campo de entrada
        if promptInicial:
            self.txtPregunta.insert(tk.END, promptInicial)

        # Frame para los botones
        button_frame = tk.Frame(input_frame)
        button_frame.pack(side=tk.LEFT, padx=5)

        # Botón para enviar el mensaje
        self.btEnviarPregunta = tk.Button(button_frame, text="Enviar", command=self.enviarPreguntaIA)
        self.btEnviarPregunta.pack(side=tk.TOP, padx=5, pady=5)

        # Botón para cerrar la aplicación
        self.btCerrar = tk.Button(button_frame, text="Cerrar", command=root.quit)
        self.btCerrar.pack(side=tk.TOP, padx=5, pady=5)

        # Vincular la tecla INTRO (Enter) al botón Enviar
        # Desactivamos esta opción porque al ser multilínea, el INTRO lo dejamos para saltos de línea
        #self.txtPregunta.bind("<Return>", lambda event: self.enviarPreguntaIA())

        # Vincular la combinación de teclas Ctrl + Enter al botón Enviar
        self.txtPregunta.bind("<Control-Return>", lambda event: self.enviarPreguntaIA())        

        # Variable para controlar la visualización del mensaje de "procesando"
        self.processing = False

    """Centra la ventana en la pantalla"""
    def centrarVentana(self):        
        self.root.update_idletasks()  # Actualizar la geometría de la ventana
        width = self.root.winfo_width()  # Obtener el ancho de la ventana
        height = self.root.winfo_height()  # Obtener la altura de la ventana
        screen_width = self.root.winfo_screenwidth()  # Obtener el ancho de la pantalla
        screen_height = self.root.winfo_screenheight()  # Obtener la altura de la pantalla

        # Calcular la posición x e y para centrar la ventana
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)

        # Establecer la geometría de la ventana
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    """Enviar prompt (pregunta) a la IA"""
    def enviarPreguntaIA(self):
        pregunta = self.txtPregunta.get("1.0", tk.END).strip()
        if pregunta == "":
            return

        try:
            # Añadir el mensaje del usuario al contexto
            self.contexto.append({"role": "user", "content": pregunta})

            # Mostrar el mensaje del usuario en la conversación
            self.actualizarConversacion(f"Tú:\n{pregunta}\n", tag="user")

            # Limpiar la entrada del usuario
            self.txtPregunta.delete("1.0", tk.END)

            # Deshabilitar el botón de enviar mientras se procesa la respuesta
            self.btEnviarPregunta.config(state=tk.DISABLED)

            # Mostrar el mensaje de "procesando" en el Label
            self.mostrarProcesando()

            # Iniciar un hilo para obtener la respuesta de la IA
            self.processing = True
            threading.Thread(target=self.obtenerRespuestaIA, daemon=True).start()

        except Exception as e:
            self.mostrarError(f"Error al enviar el mensaje: {str(e)}")

    """ Obtener el mensaje de respuesta de la IA"""
    def obtenerRespuestaIA(self):
        try:
            respuestaCompletaIA = self.conectarAPIIA()
            mensajeIA = respuestaCompletaIA['choices'][0]['message']['content']

            # Añadir la respuesta de la IA al contexto
            self.contexto.append({"role": "assistant", "content": mensajeIA})

            # Ocultar el mensaje de "procesando" y mostrar la respuesta de la IA
            self.ocultarProcesando()
            self.actualizarConversacion(f"\nIA:\n{mensajeIA}\n", tag="assistant")

        except requests.exceptions.RequestException as e:
            self.mostrarError(f"Error de conexión con la API de la IA: {str(e)}")
        except KeyError as e:
            self.mostrarError(f"Error en el formato de la respuesta de la API de la IA: {str(e)}")
        except json.JSONDecodeError as e:
            self.mostrarError(f"Error al decodificar la respuesta JSON: {str(e)}")
        except Exception as e:
            self.mostrarError(f"Error al usar la API de la IA: {str(e)}")
        finally:
            # Restaurar el botón de enviar y detener el mensaje de "procesando"
            self.processing = False
            self.btEnviarPregunta.config(state=tk.NORMAL)
    
    """ Conectar con el API de la IA"""
    def conectarAPIIA(self):
        encabezado = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }

        datos = {
            "model": self.modelo,
            "messages": self.contexto
        }

        try:
            response = requests.post(API_URL, headers=encabezado, data=json.dumps(datos), verify=False)
            response.raise_for_status()  # Lanza una excepción si la solicitud no fue correcta
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                raise Exception("Error de autenticación: API key no válida")
            elif response.status_code == 429:
                raise Exception("Límite de tasa excedido: Demasiadas solicitudes")
            else:
                raise Exception(f"Error HTTP: {str(e)}")
        except requests.exceptions.ConnectionError as e:
            raise Exception(f"Error de conexión: {str(e)}")
        except requests.exceptions.Timeout as e:
            raise Exception(f"Tiempo de espera agotado: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error en la solicitud: {str(e)}")

    """Muestra el mensaje 'Procesando...' en el Label del formulario"""
    def mostrarProcesando(self):        
        try:
            self.lProcesando.config(text="Procesando pregunta por parte de la IA, espera por favor...")
        except Exception as e:
            self.mostrarError(f"Error al mostrar el mensaje de procesando: {str(e)}")

    """Oculta el mensaje 'Procesando ...' en el Label del formulario"""
    def ocultarProcesando(self):        
        try:
            self.lProcesando.config(text="")
        except Exception as e:
            self.mostrarError(f"Error al ocultar el mensaje de procesando: {str(e)}")

    """Actualiza el área de conversación con un nuevo mensaje"""
    def actualizarConversacion(self, message, tag=None):        
        try:
            self.txtConversacion.config(state='normal')
            self.txtConversacion.insert(tk.END, message, tag)
            self.txtConversacion.config(state='disabled')
            self.txtConversacion.yview(tk.END)
        except Exception as e:
            self.mostrarError(f"Error al actualizar la conversación: {str(e)}")

    """Muestra un menú contextual al hacer clic con el botón derecho sobre el campo Conversación"""
    def mostrarMenuEmergente(self, event):        
        try:
            self.menuEmergenteConversacion.tk_popup(event.x_root, event.y_root)
        finally:
            self.menuEmergenteConversacion.grab_release()

    """Copia el texto seleccionado al portapapeles"""
    def copiarTextoPortapapeles(self):        
        try:
            selected_text = self.txtConversacion.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.root.clipboard_clear()
            self.root.clipboard_append(selected_text)
        except tk.TclError:
            # No hay texto seleccionado
            pass

    """Selecciona todo el texto del área de conversación"""
    def seleccionarTodoElTexto(self):        
        self.txtConversacion.config(state='normal')
        self.txtConversacion.tag_add(tk.SEL, "1.0", tk.END)
        self.txtConversacion.config(state='disabled')

    """Limpia todo el contenido del área de conversación"""
    def limpiarConversacion(self):        
        self.txtConversacion.config(state='normal')
        self.txtConversacion.delete("1.0", tk.END)
        self.txtConversacion.config(state='disabled')
        self.contexto.clear()  # Limpiar también el contexto de la conversación            

    """Manejo de errores para mostrar un mensaje en un cuadro de diálogo"""
    def mostrarError(self, error_message):        
        try:
            self.actualizarConversacion(f"{error_message}\n")
            messagebox.showerror("Error", error_message)
            self.ocultarProcesando()
        except Exception as e:
            print(f"Error crítico al manejar el error: {str(e)}")

"""Analiza los argumentos de línea de comandos"""
def comArgumentos():    
    parser = argparse.ArgumentParser(description="ProyectoA - IA")
    parser.add_argument("--prompt", type=str, 
                        help="Pregunta inicial para la IA. Si incluye '[FICHERO]Nombre_Fichero', se usará el contenido del archivo especificado.")
    return parser.parse_args()

"""Carga el contenido de un archivo para usarlo como prompt"""
def cargarPromptDesdeFichero(fichero):    
    try:
        with open(fichero, "r", encoding="utf-8") as file:
            return file.read()
    except Exception as e:
        raise Exception(f"Error al leer el archivo: {str(e)}")

"""Obtiene el prompt inicial, manejando el caso de [FICHERO]Nombre_Fichero"""
def obtenerPromptInicial(prompt):    
    # Si el argumento prompt (pregunta) contiene [FICHERO], obtenemos el nombre del fichero
    if prompt and "[FICHERO]" in prompt:        
        fichero = prompt.split("[FICHERO]")[1].strip()
        if not fichero:
            raise Exception("Debes especificar un nombre de archivo después de [FICHERO].")
        return cargarPromptDesdeFichero(fichero)
    return prompt

"""Iniciamos el programa principal"""
if __name__ == "__main__":
    try:
        # Analizar argumentos de la línea de comandos
        args = comArgumentos()

        # Obtener el prompt inicial, manejando el caso de [FICHERO]NombreFichero
        promptArg = obtenerPromptInicial(args.prompt)

        # Iniciar la aplicación
        root = tk.Tk()
        app = ChatApp(root, promptInicial=promptArg)
        root.mainloop()
    except Exception as e:
        print(f"Error al abrir la IA de ProyectoA: {str(e)}")
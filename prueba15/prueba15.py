import sys
from io import BytesIO

import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
import xlwings as xw
import win32gui, win32con
from PyPDF2 import PdfMerger
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from langdetect import detect
from PIL import Image, ImageTk
import os

""" # Ocultar la CMD de Windows al ejecutar el .exe
hide = win32gui.GetForegroundWindow()
win32gui.ShowWindow(hide, win32con.SW_HIDE) """

# Clase para redirigir stdout a un widget Text de Tkinter
class RedirectStdout:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, string):
        self.text_widget.insert(ctk.END, string)
        self.text_widget.see(ctk.END)

    def flush(self):
        pass

# Función que muestra una ventana emergente con un ícono de advertencia
def show_warning(message):
    tk.messagebox.showwarning("Advertencia", message)

# Función para seleccionar un archivo Excel
def select_file():
    file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xls *.xlsx")])

    if not file_path:
        show_warning("No se seleccionó ningún archivo. El programa se cerrará.") # El programa se cierra si no se selecciona un archivo Excel
        root.destroy()
        
    else:
        file_entry.delete(0, ctk.END)
        file_entry.insert(0, file_path)

# Función para verificar la extensión del archivo Excel
def is_valid_extension(file_path, valid_extensions=('.xls', '.xlsx')):
    return file_path.endswith(valid_extensions)

# Función para guardar el archivo PDF combinado
def save_file(pdf_merger):
    pdf_combined_file = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")])
    
    if not pdf_combined_file:
        show_warning("No se seleccionó ninguna ruta para guardar el archivo. El programa se cerrará.") # El programa se cierra si no se selecciona una ruta
        root.destroy()
        return None

    try:
        with open(pdf_combined_file, 'wb') as output_pdf:
            pdf_merger.write(output_pdf)
        return pdf_combined_file

    except Exception as e:
        show_warning(f"Error al guardar el archivo PDF: {str(e)}")
        return None

# Función para filtrar el archivo Excel
def filter_file():
    file_path = file_entry.get()
    if not file_path:
        show_warning("No se ha seleccionado ningún archivo.")
        return

    app = xw.App(visible=False)
    wb = app.books.open(file_path)
    sheet = wb.sheets[0]
    data = sheet.used_range.value
    df = pd.DataFrame(data[1:], columns=data[0])

    # Filtrar filas donde la mayoría del texto esté en español
    def is_spanish(text):
        try:
            return detect(text) == 'es'
        except:
            return False

    df_filtered = df[df.apply(lambda row: any(is_spanish(str(cell)) for cell in row), axis=1)]

    # Guardar el archivo filtrado
    filtered_file_path = os.path.join(os.path.dirname(file_path), 'filtered_' + os.path.basename(file_path))
    df_filtered.to_excel(filtered_file_path, index=False)
    wb.close()
    app.quit()

    filtered_file_entry.delete(0, ctk.END)
    filtered_file_entry.insert(0, filtered_file_path)
    messagebox.showinfo("Información", f"El archivo ha sido filtrado y guardado como: {filtered_file_path}")

# Función para procesar el archivo seleccionado
def process_file():
    filtered_file_path = filtered_file_entry.get()
    if not filtered_file_path:
        show_warning("No se ha seleccionado ningún archivo filtrado.")
        return

    tamaño_hoja = size_var.get()
    figsize, x_position_max = get_figsize_and_max_pos(tamaño_hoja)

    # Crear un objeto para combinar PDFs
    pdf_merger = PdfMerger()

    # Abrir el archivo de Excel con xlwings
    app = xw.App(visible=False)
    wb = app.books.open(filtered_file_path)
    sheet = wb.sheets[0]

    # Leer datos desde Excel
    df = sheet.used_range.value

    if not df:
        show_warning("No se pudieron leer los datos del archivo Excel.")
        return

    # Convertir los datos a DataFrame
    df = pd.DataFrame(df[1:], columns=df[0])

    # Iterar sobre las filas del DataFrame
    for idx, row in enumerate(df.itertuples(index=False), start=1):
        row = list(row)

        # Filtrar valores NaN
        row = [cell for cell in row if pd.notna(cell)]
        
        # Verificar si la fila tiene suficientes valores para dibujar el gráfico
        if len(row) > 1:
            # Crear un nuevo grafo para cada fila
            G = create_graph_from_row(row)

            # Dibujar el gráfico con el tamaño adecuado
            fig, ax = plt.subplots(figsize=figsize)
            
            # Calcular posiciones de los nodos
            pos = generate_positions(G, x_position_max)

            draw_graph(G, pos, ax)

            # Guardar la figura en un objeto BytesIO
            buf = BytesIO()
            plt.savefig(buf, format='pdf')
            buf.seek(0)
            pdf_merger.append(buf)

            print(f"El diagrama de unifilares para la fila {idx} se ha generado con éxito\n")
            plt.close(fig)

        else:
            print(f"No ha sido posible hacer un diagrama para la fila {idx} porque no hay suficientes datos.\n")

    # Guardar el archivo PDF combinado
    pdf_combined_file = save_file(pdf_merger)

    if pdf_combined_file:
        messagebox.showinfo("Información", f"El archivo PDF se ha generado correctamente en: {pdf_combined_file}\n")

        # Cerrar el libro de Excel y la aplicación de xlwings
        wb.close()
        app.quit()

        # Eliminar el archivo filtrado
        os.remove(filtered_file_path)
    filtered_file_entry.delete(0, ctk.END)

# Función para obtener el tamaño de la figura y la posición máxima en X
def get_figsize_and_max_pos(tamaño_hoja):

    if tamaño_hoja == 'A4': 
        return (210 / 25.4, 297 / 25.4), 4 # Tamaño A4
    
    else:                   
        return (420 / 25.4, 297 / 25.4), 8 # Tamaño A3

# Función para crear un grafo a partir de una fila
def create_graph_from_row(row):

    # Crear un nuevo grafo G
    G = nx.Graph() 
    
    # Agregar nodos al grafo G
    for cell in row:
        G.add_node(cell)

    # Agregar conexiones entre nodos en la fila actual
    for i in range(len(row) - 1):
        G.add_edge(row[i], row[i + 1])
    return G

# Función para generar posiciones de los nodos
def generate_positions(G, x_position_max):

    # Inicializar el diccionario de posiciones
    pos = {} 
    x_position, y_position = 0, 0

    for node in G.nodes():

        pos[node] = (x_position, y_position) # Inicializar el diccionario de posiciones

        # Posición de los nodos
        if x_position < x_position_max:
            x_position += 1

        else:
            x_position = 1
            y_position -= 1

        if y_position < -6:
            y_position = x_position - 1

    return pos

# Función para dibujar el grafo
def draw_graph(G, pos, ax):

    # Dibujar los nodos
    node_colors = ['skyblue' if i % 2 == 0 else 'lightgreen' for i in range(len(G.nodes))]
    node_shapes = ['s' if i % 2 == 0 else 'd' for i in range(len(G.nodes))]

    for i, (node, (x, y)) in enumerate(pos.items()): # Aquí, "pos.items()" devuelve una vista de los elementos (clave, valor) de "pos".

        nx.draw_networkx_nodes(G, pos, nodelist=[node], node_size=3000, node_shape=node_shapes[i], node_color=node_colors[i])
        ax.text(x, y, node, ha='center', va='center')

    nx.draw_networkx_edges(G, pos)
    ax.axis('off')

###### Configuración de la apariencia de la ventana principal con customtkinter #####

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

root = ctk.CTk() # Crear la ventana principal
root.title("Generador de Diagramas Unifilares")
root.resizable(False, False)  # Desactivar redimensionamiento

# Botón 'Examinar'
ctk.CTkLabel(root, text="Seleccionar archivo de Excel:").grid(row=0, column=0, padx=10, pady=10)
file_entry = ctk.CTkEntry(root, width=300)
file_entry.grid(row=0, column=1, padx=10, pady=10)
ctk.CTkButton(root, text="Examinar", command=select_file).grid(row=0, column=2, padx=10, pady=10)

# Campo para mostrar el archivo filtrado
ctk.CTkLabel(root, text="Archivo filtrado:").grid(row=1, column=0, padx=10, pady=10)
filtered_file_entry = ctk.CTkEntry(root, width=300)
filtered_file_entry.grid(row=1, column=1, padx=10, pady=10)

# Botón 'Filtrar Datos'
ctk.CTkButton(root, text="Filtrar Datos", command=filter_file).grid(row=1, column=2, padx=10, pady=10)

# Botón 'Tamaño hoja'
ctk.CTkLabel(root, text="Seleccionar tamaño de hoja:").grid(row=2, column=0, padx=10, pady=10)
size_var = ctk.StringVar(value="A4")
size_combobox = ctk.CTkComboBox(root, variable=size_var, values=["A4", "A3"])
size_combobox.grid(row=2, column=1, padx=10, pady=10)

text_widget = ctk.CTkTextbox(root, wrap='word', height=200, width=600)
text_widget.grid(row=3, column=0, columnspan=3, padx=10, pady=10)

sys.stdout = RedirectStdout(text_widget)

# Botón 'Generar PDF'
ctk.CTkButton(root, text="Generar PDF", command=process_file).grid(row=4, column=0, columnspan=3, pady=10)

# Botón 'Salir'
ctk.CTkButton(root, text="Salir", command=root.quit).grid(row=5, column=0, columnspan=3, pady=10)

# Mantener la ventana abierta y a la espera de eventos (clics de ratón, pulsaciones de teclas, etc.)
root.mainloop()

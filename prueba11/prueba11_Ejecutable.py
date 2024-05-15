import sys
from io import BytesIO

import matplotlib.pyplot as plt
import networkx as nx
import xlwings as xw
from PyPDF2 import PdfMerger
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# Clase para redirigir stdout a un widget Text de Tkinter
class RedirectStdout:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, string):
        self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END)

    def flush(self):
        pass

# Función que muestra una ventana emergente con un ícono de advertencia
def show_warning(message):
    messagebox.showwarning("Advertencia", message)

# Función para seleccionar un archivo Excel
def select_file():
    file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xls *.xlsx")])

    if not file_path:
        show_warning("No se seleccionó ningún archivo. El programa se cerrará.")
        root.destroy()
        
    else:
        file_entry.delete(0, tk.END)
        file_entry.insert(0, file_path)

# Función para verificar la extensión del archivo Excel
def is_valid_extension(file_path, valid_extensions=('.xls', '.xlsx')):
    return file_path.endswith(valid_extensions)

# Función para guardar el archivo PDF
def save_file():
    pdf_combined_file = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")])
    
    if not pdf_combined_file:
        show_warning("No se seleccionó ningún lugar para guardar el archivo. El programa se cerrará.")
        root.destroy()

    return pdf_combined_file

# Función para procesar el archivo seleccionado
def process_file():
    file_path = file_entry.get()

    if not file_path:
        show_warning("No se seleccionó ningún archivo. El programa se cerrará.")
        root.destroy()
        return

    if not is_valid_extension(file_path):
        show_warning("El archivo seleccionado no tiene una extensión compatible (.xls, .xlsx). El programa se cerrará.")
        root.destroy()
        return

    tamaño_hoja = size_var.get()
    figsize, x_position_max = get_figsize_and_max_pos(tamaño_hoja)

    # Crear un objeto para combinar PDFs
    pdf_merger = PdfMerger()

    # Abrir el archivo de Excel con xlwings
    app = xw.App(visible=False)
    wb = app.books.open(file_path) # Abrir el archivo seleccionado por el usuario
    sheet = wb.sheets[0]

    # Leer datos desde Excel
    df = sheet.used_range.value

    # Iterar sobre las filas del DataFrame
    for idx, row in enumerate(df):

        # Filtrar valores NaN
        row = [cell for cell in row if cell is not None]
        
        # Verificar si la fila tiene suficientes valores para dibujar el gráfico
        if len(row) > 1: # Por lo menos dos nodos para crear una conexión

             # Crear un nuevo grafo para cada fila
            G = create_graph_from_row(row)

            # Dibujar el gráfico con el tamaño adecuado
            fig, ax = plt.subplots(figsize=figsize)
            
            # Calcular posiciones de los nodos utilizando el algoritmo spring de NetworkX
            pos = generate_positions(G, x_position_max)

            draw_graph(G, pos, ax)

            # Guardar la figura en un objeto BytesIO
            buf = BytesIO()
            plt.savefig(buf, format='pdf')
            buf.seek(0)
            pdf_merger.append(buf)

            print(f"El diagrama de flujo para la fila {idx + 1} se ha generado con éxito\n")

    # Guardar el archivo PDF combinado
    pdf_combined_file = save_file()

    if pdf_combined_file:
        with open(pdf_combined_file, 'wb') as output_pdf:
            pdf_merger.write(output_pdf)

        print(f"El archivo PDF se ha guardado correctamente en: {pdf_combined_file}")
        messagebox.showinfo("Éxito", f"El archivo PDF se ha generado correctamente en: {pdf_combined_file}\n")
    
    else:
        print("El usuario canceló el guardado.\n")

    # Cerrar el libro de Excel y la aplicación de xlwings
    wb.close()
    app.quit()

# Función para obtener el tamaño de la figura y la posición máxima en X
def get_figsize_and_max_pos(tamaño_hoja):

    if tamaño_hoja == 'A4':
        return (210 / 25.4, 297 / 25.4), 4
    
    else:
        return (420 / 25.4, 297 / 25.4), 8

# Función para crear un grafo a partir de una fila
def create_graph_from_row(row):

    G = nx.Graph()
    
    for cell in row:
        G.add_node(cell)
    for i in range(len(row) - 1):
        G.add_edge(row[i], row[i + 1])
    return G

# Función para generar posiciones de los nodos
def generate_positions(G, x_position_max):

    pos = {}
    x_position, y_position = 0, 0

    for node in G.nodes():

        pos[node] = (x_position, y_position) # Inicializar el diccionario de posiciones

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

    node_colors = ['skyblue' if i % 2 == 0 else 'lightgreen' for i in range(len(G.nodes))]
    node_shapes = ['s' if i % 2 == 0 else 'd' for i in range(len(G.nodes))]

    for i, (node, (x, y)) in enumerate(pos.items()):

        nx.draw_networkx_nodes(G, pos, nodelist=[node], node_size=3000, node_shape=node_shapes[i], node_color=node_colors[i])
        ax.text(x, y, node, ha='center', va='center')

    nx.draw_networkx_edges(G, pos)
    ax.axis('off')

# Configuración de la ventana principal
root = tk.Tk()
root.title("Generador de Diagramas Unifilares")

tk.Label(root, text="Seleccionar archivo de Excel:").grid(row=0, column=0, padx=10, pady=10)
file_entry = tk.Entry(root, width=50)
file_entry.grid(row=0, column=1, padx=10, pady=10)
tk.Button(root, text="Examinar", command=select_file).grid(row=0, column=2, padx=10, pady=10)

tk.Label(root, text="Seleccionar tamaño de hoja:").grid(row=1, column=0, padx=10, pady=10)
size_var = tk.StringVar(value="A4")
size_combobox = ttk.Combobox(root, textvariable=size_var, values=["A4", "A3"], state="readonly")
size_combobox.grid(row=1, column=1, padx=10, pady=10)

text_widget = tk.Text(root, wrap='word', height=15, width=80)
text_widget.grid(row=2, column=0, columnspan=3, padx=10, pady=10)

sys.stdout = RedirectStdout(text_widget)

tk.Button(root, text="Generar PDF", command=process_file).grid(row=3, column=0, columnspan=2, pady=10)
tk.Button(root, text="Salir", command=root.quit).grid(row=3, column=2, pady=10)

root.mainloop()

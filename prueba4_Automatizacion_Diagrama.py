import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx

# Cargar datos desde Excel
datos = pd.read_excel('diagrama1.xlsx', header=None)  # No usar la primera fila como encabezados

# Crear un gráfico utilizando NetworkX
G = nx.Graph()

# Agregar nodos
for col in datos.columns:
    G.add_node(datos[col].iloc[0])  # Añadir elemento como nodo

# Agregar conexiones entre elementos
for i in range(len(datos.columns) - 1):
    G.add_edge(datos[i].iloc[0], datos[i + 1].iloc[0])  # Añadir conexión entre elementos adyacentes

# Verificar si hay más de 16 nodos
if len(G.nodes()) > 16:
    print("El software no está preparado.")
else:
    # Preguntar al usuario por el tamaño de la hoja
    tamaño_hoja = input("¿Desea que el tamaño de la hoja sea A4 o A3?: ").upper()
    if tamaño_hoja != 'A4' and tamaño_hoja != 'A3':
        print("Opción no válida. Se utilizará A4 por defecto.")
        tamaño_hoja = 'A4'

    # Definir el tamaño del gráfico según la eleccion
    if tamaño_hoja == 'A4':
        figsize = (297 / 25.4, 210 / 25.4)  # Tamaño A4 en orientación paisaje en milímetros (ancho, alto)
    else:
        figsize = (420 / 25.4, 297 / 25.4)  # Tamaño A3 en orientación paisaje en milímetros (ancho, alto)

    # Dibujar el gráfico con el tamaño adecuado
    plt.figure(figsize=figsize)

    pos = {}  # Inicializar el diccionario de posiciones
    x_position = 0
    y_position = 0        
    x_position_max = 4
    y_position_max = 2

    for node in G.nodes():
        pos[node] = (x_position, y_position)
        if x_position == 0 or x_position % 2 == 0:
            nx.draw_networkx_nodes(G, pos, nodelist=[node], node_size=3000, node_shape='s', node_color='skyblue')
        else:
            nx.draw_networkx_nodes(G, pos, nodelist=[node], node_size=3000, node_shape='d', node_color='lightgreen')

        if x_position < 4:
            x_position += 1
        else:
            x_position = 1
            y_position -= 1

    # Dibujar bordes
    nx.draw_networkx_edges(G, pos)

    # Dibujar etiquetas
    for node, (x, y) in pos.items():
        plt.text(x, y, node, ha='center', va='center')

    # Eliminar ejes
    plt.axis('off')

    # Guardar el gráfico como PDF
    plt.savefig('prueba4_diagrama.pdf', format='pdf')

    # Mostrar el gráfico en pantalla
    plt.show()

    print("El diagrama de flujo se ha generado con éxito ")
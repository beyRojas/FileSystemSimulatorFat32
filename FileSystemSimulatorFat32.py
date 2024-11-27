import tkinter as tk
from tkinter import ttk, messagebox
import random
import time  # Añadido para la prueba de estrés

class FAT32Simulator:
    def __init__(self, total_clusters=1024):
        self.total_clusters = total_clusters
        self.fat = [-1] * total_clusters
        self.directory = []
        self.free_clusters = total_clusters

    def assign_clusters(self, file_name, file_size):
        """Asigna clústeres para un archivo en la FAT."""
        if file_size > self.free_clusters:
            return False
       
        # Encuentra clústeres libres
        assigned_clusters = []
        for i in range(self.total_clusters):
            if self.fat[i] == -1:
                assigned_clusters.append(i)
                if len(assigned_clusters) == file_size:
                    break
       
        # Actualiza la FAT
        for i in range(len(assigned_clusters) - 1):
            self.fat[assigned_clusters[i]] = assigned_clusters[i + 1]
        self.fat[assigned_clusters[-1]] = 0  # Último clúster como final
       
        # Marcar clústeres como ocupados
        for cluster in assigned_clusters:
            self.fat[cluster] = assigned_clusters[(assigned_clusters.index(cluster) + 1) 
                                                  % len(assigned_clusters)]
       
        # Agregar al directorio
        self.directory.append({
            'file_name': file_name, 
            'start_cluster': assigned_clusters[0],
            'size': file_size,
            'assigned_clusters': assigned_clusters
        })
        self.free_clusters -= file_size
        return True

    def free_clusters_for_file(self, file_name):
        """Libera los clústeres de un archivo en la FAT."""
        file_entry = next((f for f in self.directory if f['file_name'] == file_name), None)
        if not file_entry:
            return False
       
        # Liberar todos los clústeres asignados a este archivo
        for cluster in file_entry['assigned_clusters']:
            self.fat[cluster] = -1
       
        # Actualizar directorio y contadores
        self.directory.remove(file_entry)
        self.free_clusters += file_entry['size']
        return True

class FAT32SimulatorGUI:
    def __init__(self, master):
        self.master = master
        master.title("FAT32 Simulator")
        master.geometry("800x800")  # Increased height

        # Crear simulador
        self.simulator = FAT32Simulator()

        # Crear frames
        self.create_main_frame()
        self.create_disk_status_frame()
        self.create_file_management_frame()
        self.create_cluster_visualization_frame()
        self.create_stress_test_frame()

        # Actualizar vista inicial
        self.update_views()

    def create_main_frame(self):
        """Crear el frame principal"""
        self.main_frame = ttk.Frame(self.master, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

    def create_disk_status_frame(self):
        """Crear frame de estado del disco"""
        status_frame = ttk.LabelFrame(self.main_frame, text="Estado del disco")
        status_frame.pack(fill=tk.X, pady=5)

        # Variables para mostrar estado
        self.total_clusters_var = tk.StringVar(value="Clústeres total: 1024")
        self.free_clusters_var = tk.StringVar(value="Clústeres libres: 1024")
        self.used_clusters_var = tk.StringVar(value="Clústeres usados: 0")

        ttk.Label(status_frame, textvariable=self.total_clusters_var).pack(side=tk.LEFT, padx=5)
        ttk.Label(status_frame, textvariable=self.free_clusters_var).pack(side=tk.LEFT, padx=5)
        ttk.Label(status_frame, textvariable=self.used_clusters_var).pack(side=tk.LEFT, padx=5)

    def create_file_management_frame(self):
        """Crear frame de gestión de archivos"""
        file_frame = ttk.LabelFrame(self.main_frame, text="Gestión de archivos")
        file_frame.pack(fill=tk.X, pady=5)

        # Botones de gestión
        create_btn = ttk.Button(file_frame, text="Crear archivo aleatorio", command=self.create_random_file)
        create_btn.pack(side=tk.LEFT, padx=5)

        reset_btn = ttk.Button(file_frame, text="Reiniciar simulador", command=self.reset_simulator)
        reset_btn.pack(side=tk.LEFT, padx=5)

        # Tabla de archivos
        self.file_table = ttk.Treeview(self.main_frame, columns=("Name", "Start Cluster", "Size"), show="headings")
        self.file_table.heading("Name", text="Nombre del archivo")
        self.file_table.heading("Start Cluster", text="Clúster inicial")
        self.file_table.heading("Size", text="Tamaño (Clúster)")
        
        # Añadir botón de eliminación
        delete_btn = ttk.Button(file_frame, text="Eliminar archivo seleccionado", command=self.delete_selected_file)
        delete_btn.pack(side=tk.LEFT, padx=5)

        self.file_table.pack(fill=tk.X, pady=5)

    def create_cluster_visualization_frame(self):
        """Crear frame de visualización de clústeres"""
        cluster_frame = ttk.LabelFrame(self.main_frame, text="Visualización de clústeres")
        cluster_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Canvas para visualización de clústeres
        self.cluster_canvas = tk.Canvas(cluster_frame, bg="white")
        self.cluster_canvas.pack(fill=tk.BOTH, expand=True)

        # Asegurar que el canvas se redibuje cuando cambie de tamaño
        self.cluster_canvas.bind("<Configure>", self.on_canvas_resize)

    def create_stress_test_frame(self):
        """Crear frame para pruebas de estrés"""
        stress_frame = ttk.LabelFrame(self.main_frame, text="Prueba de Estrés")
        stress_frame.pack(fill=tk.X, pady=5)

        # Contenedor para los parámetros de tamaño
        size_frame = ttk.Frame(stress_frame)
        size_frame.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        # Parámetros de número de archivos
        ttk.Label(stress_frame, text="Número de archivos:").pack(side=tk.LEFT, padx=5)
        self.file_count_var = tk.StringVar(value="100")
        file_count_entry = ttk.Entry(stress_frame, textvariable=self.file_count_var, width=10)
        file_count_entry.pack(side=tk.LEFT, padx=5)

        # Contenedor para tamaño máximo
        max_size_subframe = ttk.Frame(size_frame)
        max_size_subframe.pack(fill=tk.X)
        ttk.Label(max_size_subframe, text="Tamaño máximo (clusters):").pack(side=tk.LEFT, padx=5)
        self.max_file_size_var = tk.StringVar(value="10")
        max_file_size_entry = ttk.Entry(max_size_subframe, textvariable=self.max_file_size_var, width=10)
        max_file_size_entry.pack(side=tk.LEFT, padx=5)

        # Contenedor para tamaño mínimo
        min_size_subframe = ttk.Frame(size_frame)
        min_size_subframe.pack(fill=tk.X)
        ttk.Label(min_size_subframe, text="Tamaño mínimo (clusters):").pack(side=tk.LEFT, padx=5)
        self.min_file_size_var = tk.StringVar(value="1")
        min_file_size_entry = ttk.Entry(min_size_subframe, textvariable=self.min_file_size_var, width=10)
        min_file_size_entry.pack(side=tk.LEFT, padx=5)

        # Botón de prueba de estrés
        stress_btn = ttk.Button(stress_frame, text="Iniciar Prueba de Estrés", command=self.run_stress_test)
        stress_btn.pack(side=tk.LEFT, padx=5)

        # Etiqueta de resultados
        self.stress_result_var = tk.StringVar()
        stress_result_label = ttk.Label(stress_frame, textvariable=self.stress_result_var)
        stress_result_label.pack(side=tk.LEFT, padx=5)

    def run_stress_test(self):
        """Ejecutar prueba de estrés"""
        try:
            file_count = int(self.file_count_var.get())
            min_file_size = int(self.min_file_size_var.get())
            max_file_size = int(self.max_file_size_var.get())

            # Validar que el tamaño mínimo no sea mayor que el máximo
            if min_file_size > max_file_size:
                messagebox.showerror("Error", "El tamaño mínimo no puede ser mayor que el tamaño máximo")
                return

        except ValueError:
            messagebox.showerror("Error", "Por favor, ingrese números válidos")
            return

        # Reiniciar simulador antes de la prueba
        self.reset_simulator()

        # Registrar inicio de la prueba
        start_time = time.time()
        successful_files = 0
        failed_files = 0

        # Crear archivos aleatorios
        for i in range(file_count):
            file_name = f"stress_file_{i+1}.txt"
            file_size = random.randint(min_file_size, max_file_size)

            if self.simulator.assign_clusters(file_name, file_size):
                successful_files += 1
            else:
                failed_files += 1
                break  # Detener si no hay más espacio

        # Calcular tiempo transcurrido
        end_time = time.time()
        duration = end_time - start_time

        # Mostrar resultados
        result_msg = (
            f"Prueba de Estrés Completada:\n"
            f"Archivos creados: {successful_files}\n"
            f"Archivos fallidos: {failed_files}\n"
            f"Tiempo total: {duration:.2f} segundos"
        )
        self.stress_result_var.set(result_msg)  
        # Actualizar vistas
        self.update_views()
        # Mostrar mensaje emergente con detalles
        messagebox.showinfo("Prueba de Estrés", result_msg)

    def on_canvas_resize(self, event):
        """Manejar el redimensionamiento del canvas"""
        self.visualize_clusters()

    def create_random_file(self):
        """Crear un archivo con nombre y tamaño aleatorios"""
        file_name = f"file_{random.randint(1, 1000)}.txt"
        file_size = random.randint(1, 10)

        if self.simulator.assign_clusters(file_name, file_size):
            self.update_views()
        else:
            messagebox.showerror("Error", "Not enough free clusters!")

    def delete_selected_file(self):
        """Eliminar el archivo seleccionado"""
        selected_item = self.file_table.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a file to delete")
            return

        file_name = self.file_table.item(selected_item)['values'][0]
        if self.simulator.free_clusters_for_file(file_name):
            self.update_views()

    def reset_simulator(self):
        """Reiniciar el simulador"""
        self.simulator = FAT32Simulator()
        self.update_views()

    def update_views(self):
        """Actualizar todas las vistas"""
        # Actualizar estado del disco
        used_clusters = self.simulator.total_clusters - self.simulator.free_clusters
        self.total_clusters_var.set(f"Clústeres totales: {self.simulator.total_clusters}")
        self.free_clusters_var.set(f"Clústeres libres: {self.simulator.free_clusters}")
        self.used_clusters_var.set(f"Clústeres usados: {used_clusters}")

        # Actualizar tabla de archivos
        for i in self.file_table.get_children():
            self.file_table.delete(i)
        
        for file in self.simulator.directory:
            self.file_table.insert("", "end", values=(
                file['file_name'], 
                file['start_cluster'], 
                file['size']
            ))

        # Actualizar visualización de clústeres
        self.visualize_clusters()

    def visualize_clusters(self):
        """Visualizar el estado de los clústeres"""
        # Limpiar el canvas
        self.cluster_canvas.delete("all")
        
        # Tamaño del canvas
        canvas_width = self.cluster_canvas.winfo_width()
        canvas_height = self.cluster_canvas.winfo_height()

        # Calcular dimensiones de cuadrados de clúster
        clusters_per_row = 64  # Ajustar según sea necesario
        cluster_size = min(canvas_width // clusters_per_row, 20)
        
        for i in range(self.simulator.total_clusters):
            # Calcular posición
            row = i // clusters_per_row
            col = i % clusters_per_row
            
            x = col * cluster_size
            y = row * cluster_size
            
            # Colorear según estado del clúster
            color = "green" if self.simulator.fat[i] == -1 else "blue"
            
            self.cluster_canvas.create_rectangle(
                x, y, 
                x + cluster_size, y + cluster_size, 
                fill=color, 
                outline="gray"
            )

def main():
    root = tk.Tk()
    app = FAT32SimulatorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
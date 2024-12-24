import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter import ttk
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
import datetime
from win10toast import ToastNotifier



# Variável global para armazenar o caminho do arquivo mais recente
arquivo_atual = None

# Diretório padrão para logs
DIRETORIO_LOGS = r"C:\Log_Monitora_Pasta"

# Cria o diretório se não existir
os.makedirs(DIRETORIO_LOGS, exist_ok=True)

class MonitoramentoHandler(FileSystemEventHandler):
    def __init__(self, log_file, atualizar_grid_callback):
        self.log_file = log_file
        self.toaster = ToastNotifier()
        self.atualizar_grid_callback = atualizar_grid_callback  # Callback para atualizar o grid

    def on_created(self, event):
        global arquivo_atual
        arquivo_atual = event.src_path  # Armazena o caminho do arquivo criado
        self.registrar_evento("Adicionado", event.src_path)

    def on_deleted(self, event):
        global arquivo_atual
        arquivo_atual = event.src_path  # Armazena o caminho do arquivo excluído
        self.registrar_evento("Excluído", event.src_path)

    def registrar_evento(self, tipo_evento, arquivo):
        timestamp = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        diretorio = os.path.dirname(arquivo)
        with open(self.log_file, 'a') as log:
            log.write(f"{timestamp} - {tipo_evento} - {diretorio} - {os.path.basename(arquivo)}\n")

        # Atualiza o grid chamando o callback
        self.atualizar_grid_callback()  # Apenas chama a atualização do grid

        # Mostra a notificação
        self.toaster.show_toast("Monitoramento",
                                f"Arquivo {tipo_evento}: {os.path.basename(arquivo)}",
                                duration=10)

class MonitoramentoApp:
    def __init__(self, master):
        self.master = master
        self.master.resizable(False, False)
        self.master.title("Monitoramento da Pasta")

        self.diretorio_var = tk.StringVar()
        self.observer = Observer()
        self.log_file = self.gerar_nome_arquivo_log()  # Gera um novo arquivo de log com a data atual
        self.caminho_logs = DIRETORIO_LOGS  # Armazena o diretório dos logs
        self.logs_carregados = set()
        self.dados_carregados = []  # Lista para armazenar os dados dos arquivos
        self.logs_ja_carregados = False  # Adiciona um sinalizador para controle de carregamento

        # Aplicando tema e estilo
        self.style = ttk.Style()
        self.style.theme_use('clam')  # Escolha um tema padrão
        self.style.configure("Treeview",
                             background="white",
                             foreground="black",
                             rowheight=25,
                             fieldbackground="lightgray")
        self.style.map('Treeview',
                       background=[('selected', 'blue')],
                       foreground=[('selected', 'white')])

        # Personalizando botões
        self.style.configure("TButton",
                             foreground="blue",
                             background="lightgray",
                             padding=5)

        tk.Label(master, text="Digite o Diretório:").pack()

        # Frame para o campo de texto e botão de pesquisa
        frame = tk.Frame(master)
        frame.pack(pady=5)

        tk.Entry(frame, textvariable=self.diretorio_var, width=50).pack(side=tk.LEFT)
        ttk.Button(frame, text="Pesquisar", command=self.selecionar_diretorio).pack(side=tk.LEFT, padx=10)

        # Frame para os botões
        button_frame = tk.Frame(master)
        button_frame.pack(pady=5)

        ttk.Button(button_frame, text="Salvar", command=self.salvar_diretorio).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Iniciar", command=self.iniciar_monitoramento).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Carregar Logs Antigos", command=self.carregar_logs_antigos).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Limpar", command=self.limpar_grid).pack(side=tk.LEFT, padx=5)

        # Botão para atualizar a lista
        ttk.Button(button_frame, text="Atualizar lista", command=self.atualizar_grid).pack(side=tk.LEFT, padx=5)

        # Grid para exibir os logs
        self.grid = ttk.Treeview(master, columns=("Data", "Evento", "Diretório", "Arquivo"), show="headings", height=10)
        self.grid.pack(pady=10, padx=20)

        self.grid.heading("Data", text="Data")
        self.grid.heading("Evento", text="Evento")
        self.grid.heading("Diretório", text="Diretório")
        self.grid.heading("Arquivo", text="Arquivo")

        self.grid.column("Data", width=150)
        self.grid.column("Evento", width=100)
        self.grid.column("Diretório", width=350)
        self.grid.column("Arquivo", width=250)

        # Criação de tags para destacar eventos
        self.grid.tag_configure("excluido", foreground="red", background="white")

        # Bind para abrir arquivo ao clicar duas vezes
        self.grid.bind("<Double-1>", self.abrir_arquivo)

        # Filtros - entradas para cada coluna
        filter_frame = tk.Frame(master)
        filter_frame.pack(pady=10, fill='x', expand=True)


        # Criação dos campos de entrada
        self.filter_data = tk.Entry(filter_frame, width=18)
        self.filter_event = tk.Entry(filter_frame, width=15)
        self.filter_directory = tk.Entry(filter_frame, width=55)
        self.filter_file = tk.Entry(filter_frame, width=37)

        # Posicionamento dos campos de entrada
        self.filter_data.grid(row=1, column=0, padx=20, pady=5)
        self.filter_event.grid(row=1, column=1, padx=5, pady=5)
        self.filter_directory.grid(row=1, column=2, padx=5, pady=5)
        self.filter_file.grid(row=1, column=3, padx=5, pady=5)

        # Bind dos eventos de retorno para aplicar filtro
        self.filter_data.bind("<Return>", lambda event: self.aplicar_filtro())
        self.filter_event.bind("<Return>", lambda event: self.aplicar_filtro())
        self.filter_directory.bind("<Return>", lambda event: self.aplicar_filtro())
        self.filter_file.bind("<Return>", lambda event: self.aplicar_filtro())

        # Carregamento dos logs
        self.carregar_logs()

    def gerar_nome_arquivo_log(self):
        data_atual = datetime.datetime.now().strftime("%d-%m-%Y")
        return os.path.join(DIRETORIO_LOGS, f"monitoramento_log_{data_atual}.txt")  # Salva no diretório de logs

    def selecionar_diretorio(self):
        diretorio = filedialog.askdirectory()
        if diretorio:
            self.diretorio_var.set(diretorio)

    def salvar_diretorio(self):
        diretorio = self.diretorio_var.get()
        if os.path.isdir(diretorio):
            self.diretorio_monitorado = diretorio
            messagebox.showinfo("Sucesso", "Diretório salvo com sucesso!")
        else:
            messagebox.showerror("Erro", "Diretório inválido!")

    def iniciar_monitoramento(self):
        if hasattr(self, 'diretorio_monitorado'):
            handler = MonitoramentoHandler(self.log_file, self.atualizar_grid)  # Passa o callback
            self.observer.schedule(handler, self.diretorio_monitorado, recursive=False)
            self.observer.start()
            messagebox.showinfo("Monitoramento", "Monitoramento iniciado!")
        else:
            messagebox.showerror("Erro", "Por favor, salve um diretório primeiro!")

    def carregar_logs(self):
        # Verifica se o arquivo de log existe
        if os.path.exists(self.log_file):
            with open(self.log_file, 'r') as log:
                linhas = log.readlines()
                # Carrega os últimos 100 logs (ou todos se houver menos de 100)
                for linha in linhas[-100:][::-1]:  # Mostra os últimos 100 logs
                    dados = linha.strip().split(" - ")
                    if len(dados) == 4:
                        # Adiciona os dados à lista se ainda não estiverem lá
                        if dados not in self.dados_carregados:
                            self.dados_carregados.append(dados)  # Adiciona os dados à lista
                            # Atualiza o grid diretamente
                            if dados[1] == "Excluído":
                                self.grid.insert("", "end", values=(dados[0], dados[1], dados[2], dados[3]),
                                                 tags=("excluido",))
                            else:
                                self.grid.insert("", "end", values=(dados[0], dados[1], dados[2], dados[3]))

    def carregar_logs_antigos(self):
        arquivos_antigos = filedialog.askopenfilenames(
            title="Selecionar arquivos de log antigos",
            initialdir=self.caminho_logs,
            filetypes=[("Text files", "*.txt")]
        )

        if arquivos_antigos:
            for arquivo_antigo in arquivos_antigos:
                with open(arquivo_antigo, 'r') as log:
                    linhas = log.readlines()
                    for linha in linhas:
                        dados = linha.strip().split(" - ")
                        if len(dados) == 4:
                            # Adiciona os dados ao grid e também à lista de todos os dados carregados
                            self.dados_carregados.append(dados)

                            if dados[1] == "Excluído":
                                self.grid.insert("", "end", values=(dados[0], dados[1], dados[2], dados[3]),
                                                 tags=("excluido",))
                            else:
                                self.grid.insert("", "end", values=(dados[0], dados[1], dados[2], dados[3]))


    def atualizar_grid(self):
        self.limpar_grid()  # Limpa o grid antes de carregar novos dados
        self.carregar_logs()        # Carrega os dados mais recentes no grid

        # Reinsere todos os dados carregados no grid
        for dados in self.dados_carregados:
            if len(dados) == 4:
                if dados[1] == "Excluído":
                    self.grid.insert("", "end", values=(dados[0], dados[1], dados[2], dados[3]), tags=("excluido",))
                else:
                    self.grid.insert("", "end", values=(dados[0], dados[1], dados[2], dados[3]))

    def limpar_grid(self):
        for item in self.grid.get_children():
            self.grid.delete(item)

    def abrir_arquivo(self, event):
        selected_item = self.grid.selection()
        if selected_item:
            values = self.grid.item(selected_item[0], "values")
            caminho_arquivo = os.path.join(values[2], values[3])
            if os.path.exists(caminho_arquivo):
                os.startfile(caminho_arquivo)
            else:
                messagebox.showerror("Erro", "O arquivo não existe mais.")

    def aplicar_filtro(self):
        # Limpa o grid antes de aplicar o filtro
        self.limpar_grid()

        # Obtém os valores dos filtros e os converte para minúsculas
        filtro_data = self.filter_data.get().strip().lower()
        filtro_event = self.filter_event.get().strip().lower()
        filtro_directory = self.filter_directory.get().strip().lower()
        filtro_file = self.filter_file.get().strip().lower()

        # Aplica os filtros aos dados carregados
        for dados in self.dados_carregados:
            data, evento, diretorio, arquivo = dados

            # Converte os dados para minúsculas para comparação
            data_lower = data.lower()
            evento_lower = evento.lower()
            diretorio_lower = diretorio.lower()
            arquivo_lower = arquivo.lower()

            # Verifica se os filtros estão vazios ou se correspondem
            if ((filtro_data == "" or filtro_data in data_lower) and
                    (filtro_event == "" or filtro_event in evento_lower) and
                    (filtro_directory == "" or filtro_directory in diretorio_lower) and
                    (filtro_file == "" or filtro_file in arquivo_lower)):
                # Adiciona a linha ao grid
                if evento == "Excluído":
                    self.grid.insert("", "end", values=(data, evento, diretorio, arquivo), tags=("excluido",))
                else:
                    self.grid.insert("", "end", values=(data, evento, diretorio, arquivo))


if __name__ == "__main__":
    root = tk.Tk()

    # Define o tamanho da janela
    largura_janela = 850  # Largura desejada
    altura_janela = 450   # Altura desejada

    # Obtém a largura e altura da tela
    largura_tela = root.winfo_screenwidth()
    altura_tela = root.winfo_screenheight()

    # Calcula a posição central
    x = (largura_tela // 2) - (largura_janela // 2)
    y = (altura_tela // 2) - (altura_janela // 2)

    # Define a geometria da janela
    root.geometry(f"{largura_janela}x{altura_janela}+{x}+{y}")

    app = MonitoramentoApp(root)
    root.mainloop()

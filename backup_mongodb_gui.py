#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistema de Backup MongoDB - Interface Gráfica
Exporta todos os bancos de dados MongoDB para pastas organizadas
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import subprocess
import os
from datetime import datetime
import json
import sys
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError


class MongoDBBackupGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Backup e Restauração MongoDB")
        self.root.geometry("900x800")
        self.root.resizable(True, True)
        
        # Determinar se rodando como script ou executável
        if getattr(sys, 'frozen', False):
            self.base_dir = os.path.dirname(sys.executable)
        else:
            self.base_dir = os.path.dirname(os.path.abspath(__file__))
            
        # Variáveis Backup
        self.backup_dir = tk.StringVar(value="C:\\backup\\mongodb")
        self.mongo_uri = tk.StringVar(value="mongodb://localhost:27017/")
        self.bancos_lista = []
        self.client = None
        self.backup_em_andamento = False
        
        # Variáveis Restauração
        self.restore_uri = tk.StringVar(value="mongodb://localhost:27017/")
        self.pasta_backup_selecionada = tk.StringVar()
        self.bancos_backup_lista = []
        self.restore_em_andamento = False
        self.preservar_dados = tk.BooleanVar(value=True)
        
        # Variáveis Agendamento
        self.config_path = os.path.join(self.base_dir, "config.json")
        self.agendamento_ativo = tk.BooleanVar(value=False)
        self.modo_agendamento = tk.StringVar(value="semanal") # 'semanal' ou 'intervalo'
        self.intervalo_minutos = tk.IntVar(value=30)
        self.hora_backup = tk.StringVar(value="00:00")
        self.dias_semana = {
            "Segunda": tk.BooleanVar(value=False),
            "Terça": tk.BooleanVar(value=False),
            "Quarta": tk.BooleanVar(value=False),
            "Quinta": tk.BooleanVar(value=False),
            "Sexta": tk.BooleanVar(value=False),
            "Sábado": tk.BooleanVar(value=False),
            "Domingo": tk.BooleanVar(value=False)
        }
        
        self.carregar_configuracoes()
        self.criar_interface()
        
    def criar_interface(self):
        """Cria a interface gráfica"""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Título
        titulo = ttk.Label(main_frame, text="Sistema de Backup e Restauração MongoDB", 
                          font=("Arial", 16, "bold"))
        titulo.grid(row=0, column=0, pady=(0, 10))
        
        # Notebook (abas)
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Aba de Backup
        aba_backup = ttk.Frame(notebook, padding="10")
        notebook.add(aba_backup, text="Backup (Exportar)")
        self.criar_aba_backup(aba_backup)
        
        # Aba de Restauração
        aba_restore = ttk.Frame(notebook, padding="10")
        notebook.add(aba_restore, text="Restauração (Importar)")
        self.criar_aba_restore(aba_restore)
        
        # Aba de Agendamento
        aba_agendamento = ttk.Frame(notebook, padding="10")
        notebook.add(aba_agendamento, text="Agendamento Automático")
        self.criar_aba_agendamento(aba_agendamento)
        
    def criar_aba_backup(self, parent):
        """Cria a interface da aba de backup"""
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(3, weight=1)
        
        # Seção de Configurações
        config_frame = ttk.LabelFrame(parent, text="Configurações", padding="10")
        config_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        config_frame.columnconfigure(1, weight=1)
        
        # Diretório de Backup
        ttk.Label(config_frame, text="Diretório de Backup:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10), pady=5)
        dir_entry = ttk.Entry(config_frame, textvariable=self.backup_dir, width=50)
        dir_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5), pady=5)
        ttk.Button(config_frame, text="Procurar", command=self.selecionar_diretorio).grid(row=0, column=2, pady=5)
        
        # URI do MongoDB
        ttk.Label(config_frame, text="URI do MongoDB:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=5)
        uri_entry = ttk.Entry(config_frame, textvariable=self.mongo_uri, width=50)
        uri_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 5), pady=5)
        ttk.Button(config_frame, text="Testar Conexão", command=self.testar_conexao).grid(row=1, column=2, pady=5)
        
        # Seção de Bancos de Dados
        bancos_frame = ttk.LabelFrame(parent, text="Bancos de Dados", padding="10")
        bancos_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        bancos_frame.columnconfigure(0, weight=1)
        bancos_frame.rowconfigure(1, weight=1)
        
        # Botão para listar bancos
        btn_frame = ttk.Frame(bancos_frame)
        btn_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        ttk.Button(btn_frame, text="Listar Bancos de Dados", 
                  command=self.listar_bancos_thread).pack(side=tk.LEFT, padx=(0, 10))
        
        # Lista de bancos com scrollbar
        list_frame = ttk.Frame(bancos_frame)
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.lista_bancos = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, height=6)
        self.lista_bancos.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.lista_bancos.yview)
        
        # Seção de Log
        log_frame = ttk.LabelFrame(parent, text="Log de Execução", padding="10")
        log_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, width=80, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Barra de progresso
        self.progress = ttk.Progressbar(parent, mode='indeterminate')
        self.progress.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Botões de ação
        btn_action_frame = ttk.Frame(parent)
        btn_action_frame.grid(row=4, column=0)
        
        self.btn_backup = ttk.Button(btn_action_frame, text="Executar Backup", 
                                     command=self.executar_backup_thread, state=tk.DISABLED)
        self.btn_backup.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_action_frame, text="Limpar Log", command=self.limpar_log).pack(side=tk.LEFT, padx=5)
        
        # Mensagem inicial
        self.log("Sistema de Backup MongoDB iniciado.")
        self.log("Configure o diretório de backup e a URI do MongoDB.")
        self.log("Clique em 'Listar Bancos de Dados' para começar.\n")
        
    def criar_aba_restore(self, parent):
        """Cria a interface da aba de restauração"""
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(3, weight=1)
        
        # Seção de Configurações
        config_frame = ttk.LabelFrame(parent, text="Configurações", padding="10")
        config_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        config_frame.columnconfigure(1, weight=1)
        
        # Pasta de Backup
        ttk.Label(config_frame, text="Pasta de Backup:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10), pady=5)
        pasta_entry = ttk.Entry(config_frame, textvariable=self.pasta_backup_selecionada, width=50)
        pasta_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5), pady=5)
        ttk.Button(config_frame, text="Procurar", command=self.selecionar_pasta_backup).grid(row=0, column=2, pady=5)
        
        # URI do MongoDB (destino)
        ttk.Label(config_frame, text="URI do MongoDB (Destino):").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=5)
        uri_entry = ttk.Entry(config_frame, textvariable=self.restore_uri, width=50)
        uri_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 5), pady=5)
        ttk.Button(config_frame, text="Testar Conexão", command=self.testar_conexao_restore).grid(row=1, column=2, pady=5)
        
        # Opção de Preservar Dados
        ttk.Checkbutton(config_frame, text="Preservar dados existentes (Não sobrescrever)", 
                        variable=self.preservar_dados).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Seção de Bancos de Backup
        bancos_frame = ttk.LabelFrame(parent, text="Bancos de Dados no Backup", padding="10")
        bancos_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        bancos_frame.columnconfigure(0, weight=1)
        bancos_frame.rowconfigure(1, weight=1)
        
        # Botão para listar bancos no backup
        btn_frame = ttk.Frame(bancos_frame)
        btn_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        ttk.Button(btn_frame, text="Listar Bancos no Backup", 
                  command=self.listar_bancos_backup_thread).pack(side=tk.LEFT, padx=(0, 10))
        
        # Lista de bancos com scrollbar
        list_frame = ttk.Frame(bancos_frame)
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        scrollbar_restore = ttk.Scrollbar(list_frame)
        scrollbar_restore.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.lista_bancos_backup = tk.Listbox(list_frame, yscrollcommand=scrollbar_restore.set, height=6)
        self.lista_bancos_backup.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_restore.config(command=self.lista_bancos_backup.yview)
        
        # Seção de Log
        log_frame = ttk.LabelFrame(parent, text="Log de Execução", padding="10")
        log_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text_restore = scrolledtext.ScrolledText(log_frame, height=8, width=80, wrap=tk.WORD)
        self.log_text_restore.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Barra de progresso
        self.progress_restore = ttk.Progressbar(parent, mode='indeterminate')
        self.progress_restore.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Botões de ação
        btn_action_frame = ttk.Frame(parent)
        btn_action_frame.grid(row=4, column=0)
        
        self.btn_restore = ttk.Button(btn_action_frame, text="Importar/Restaurar", 
                                      command=self.executar_restore_thread, state=tk.DISABLED)
        self.btn_restore.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_action_frame, text="Limpar Log", command=self.limpar_log_restore).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_action_frame, text="Sair", command=self.root.quit).pack(side=tk.LEFT, padx=5)
        
        # Mensagem inicial
        self.log_restore("Sistema de Restauração MongoDB iniciado.")
        self.log_restore("Selecione a pasta de backup e configure a URI do MongoDB de destino.")
        self.log_restore("Clique em 'Listar Bancos no Backup' para começar.\n")
        
    def criar_aba_agendamento(self, parent):
        """Cria a interface da aba de agendamento"""
        parent.columnconfigure(0, weight=1)
        
        # Frame de status
        status_frame = ttk.LabelFrame(parent, text="Status do Agendamento", padding="10")
        status_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.lbl_status_agendamento = ttk.Label(status_frame, text="Agendamento desativado", 
                                               font=("Arial", 10, "bold"), foreground="red")
        self.lbl_status_agendamento.pack(side=tk.LEFT)
        
        # Frame de Modo de Agendamento
        modo_frame = ttk.LabelFrame(parent, text="Modo de Agendamento", padding="10")
        modo_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Radiobutton(modo_frame, text="Por Dias da Semana / Horário Fixo", 
                        variable=self.modo_agendamento, value="semanal", 
                        command=self.alternar_modo_ui).grid(row=0, column=0, sticky=tk.W)
        ttk.Radiobutton(modo_frame, text="Por Intervalo de Tempo (A cada X minutos)", 
                        variable=self.modo_agendamento, value="intervalo",
                        command=self.alternar_modo_ui).grid(row=1, column=0, sticky=tk.W)
        
        # Frame de Horário (Semanal)
        self.horario_frame = ttk.LabelFrame(parent, text="Configuração de Horário (Modo Semanal)", padding="10")
        self.horario_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(self.horario_frame, text="Executar backup às (HH:MM):").pack(side=tk.LEFT, padx=(0, 10))
        self.ent_hora = ttk.Entry(self.horario_frame, textvariable=self.hora_backup, width=10)
        self.ent_hora.pack(side=tk.LEFT)
        ttk.Label(self.horario_frame, text="Ex: 03:00, 23:30").pack(side=tk.LEFT, padx=(10, 0))
        
        # Frame de Dias da Semana (Semanal)
        self.dias_frame = ttk.LabelFrame(parent, text="Dias da Semana (Modo Semanal)", padding="10")
        self.dias_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        for i, (dia, var) in enumerate(self.dias_semana.items()):
            ttk.Checkbutton(self.dias_frame, text=dia, variable=var).grid(row=i//4, column=i%4, sticky=tk.W, padx=10, pady=5)
            
        # Frame de Intervalo (Intervalo)
        self.intervalo_frame = ttk.LabelFrame(parent, text="Configuração de Intervalo", padding="10")
        self.intervalo_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(self.intervalo_frame, text="Executar backup a cada (minutos):").pack(side=tk.LEFT, padx=(0, 10))
        tk.Spinbox(self.intervalo_frame, from_=1, to=1440, textvariable=self.intervalo_minutos, width=10).pack(side=tk.LEFT)
        ttk.Label(self.intervalo_frame, text="Ex: 30, 60, 120").pack(side=tk.LEFT, padx=(10, 0))
        
        # Frame de Botões
        acoes_frame = ttk.Frame(parent, padding="10")
        acoes_frame.grid(row=5, column=0, sticky=(tk.W, tk.E))
        
        ttk.Button(acoes_frame, text="Salvar e Ativar Agendamento", 
                  command=self.ativar_agendamento).pack(side=tk.LEFT, padx=5)
        ttk.Button(acoes_frame, text="Remover Agendamento", 
                  command=self.remover_agendamento).pack(side=tk.LEFT, padx=5)
        
        # Informações sobre o agendador
        info_frame = ttk.Frame(parent, padding="10")
        info_frame.grid(row=6, column=0, sticky=(tk.W, tk.E))
        ttk.Label(info_frame, text="O agendamento utiliza o 'Agendador de Tarefas' do Windows.", 
                 font=("Arial", 9, "italic")).pack(side=tk.LEFT)
        
        # Inicializar status e visibilidade
        self.alternar_modo_ui()
        self.atualizar_visual_agendamento()

    def alternar_modo_ui(self):
        """Alterna a visibilidade dos frames de acordo com o modo selecionado"""
        if self.modo_agendamento.get() == "semanal":
            self.horario_frame.grid()
            self.dias_frame.grid()
            self.intervalo_frame.grid_remove()
        else:
            self.horario_frame.grid_remove()
            self.dias_frame.grid_remove()
            self.intervalo_frame.grid()

    def ativar_agendamento(self):
        """Salva configurações e cria tarefa no Windows"""
        self.salvar_configuracoes()
        
        # Caminhos para o agendamento
        nome_tarefa = "MongoDB_Backup_Automatico"
        
        if getattr(sys, 'frozen', False):
            # Se for executável, procuramos pelo exe do backup ou o próprio python
            backup_exe = os.path.join(self.base_dir, "backup_mongodb.exe")
            if os.path.exists(backup_exe):
                comando_tr = f'"{backup_exe}"'
            else:
                # Fallback para o script caso o exe não exista mas o python sim
                script_path = os.path.join(self.base_dir, "backup_mongodb.py")
                comando_tr = f'python "{script_path}"'
        else:
            script_path = os.path.join(self.base_dir, "backup_mongodb.py")
            python_exe = sys.executable
            comando_tr = f'"{python_exe}" "{script_path}"'
        
        if self.modo_agendamento.get() == "semanal":
            dias_selecionados = [dia for dia, var in self.dias_semana.items() if var.get()]
            if not dias_selecionados:
                messagebox.showwarning("Aviso", "Selecione pelo menos um dia da semana.")
                return
                
            mapa_dias = {
                "Segunda": "MON", "Terça": "TUE", "Quarta": "WED", 
                "Quinta": "THU", "Sexta": "FRI", "Sábado": "SAT", "Domingo": "SUN"
            }
            
            dias_cmd = ",".join([mapa_dias[dia] for dia in dias_selecionados])
            hora = self.hora_backup.get()
            
            # Validar formato da hora
            try:
                datetime.strptime(hora, "%H:%M")
            except ValueError:
                messagebox.showerror("Erro", "Formato de hora inválido. Use HH:MM (ex: 03:00)")
                return
            
            cmd = [
                "schtasks", "/create", "/tn", nome_tarefa, 
                "/tr", comando_tr, 
                "/sc", "weekly", "/d", dias_cmd, 
                "/st", hora, "/f"
            ]
            msg_sucesso = f"Agendamento Semanal configurado com sucesso!\nHorário: {hora}\nDias: {', '.join(dias_selecionados)}"
        else:
            # Modo Intervalo
            minutos = self.intervalo_minutos.get()
            if minutos < 1:
                messagebox.showwarning("Aviso", "O intervalo deve ser de pelo menos 1 minuto.")
                return
                
            cmd = [
                "schtasks", "/create", "/tn", nome_tarefa, 
                "/tr", comando_tr, 
                "/sc", "minute", "/mo", str(minutos), "/f"
            ]
            msg_sucesso = f"Agendamento por Intervalo configurado com sucesso!\nExecutar a cada: {minutos} minutos."
        
        try:
            resultado = subprocess.run(cmd, capture_output=True, text=True, check=True)
            self.agendamento_ativo.set(True)
            self.salvar_configuracoes()
            self.atualizar_visual_agendamento()
            messagebox.showinfo("Sucesso", msg_sucesso)
            self.log(f"Agendamento criado: {msg_sucesso}")
        except subprocess.CalledProcessError as e:
            self.log(f"Erro ao criar tarefa agendada: {e.stderr}")
            messagebox.showerror("Erro", f"Erro ao configurar agendamento no Windows:\n{e.stderr}")

    def remover_agendamento(self):
        """Remove a tarefa do Windows"""
        nome_tarefa = "MongoDB_Backup_Automatico"
        cmd = ["schtasks", "/delete", "/tn", nome_tarefa, "/f"]
        
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            self.agendamento_ativo.set(False)
            self.salvar_configuracoes()
            self.atualizar_visual_agendamento()
            messagebox.showinfo("Sucesso", "Agendamento removido com sucesso.")
            self.log("Agendamento removido do Windows.")
        except subprocess.CalledProcessError as e:
            # Se a tarefa não existir, apenas atualizamos o status local
            if "não encontrada" in e.stderr or "not found" in e.stderr.lower():
                self.agendamento_ativo.set(False)
                self.salvar_configuracoes()
                self.atualizar_visual_agendamento()
                messagebox.showinfo("Info", "Nenhum agendamento encontrado no Windows.")
            else:
                self.log(f"Erro ao remover tarefa agendada: {e.stderr}")
                messagebox.showerror("Erro", f"Erro ao remover agendamento:\n{e.stderr}")

    def atualizar_visual_agendamento(self):
        """Atualiza a label de status do agendamento"""
        if self.agendamento_ativo.get():
            self.lbl_status_agendamento.config(text="AGENDAMENTO ATIVO", foreground="green")
        else:
            self.lbl_status_agendamento.config(text="AGENDAMENTO DESATIVADO", foreground="red")
        
    def log(self, mensagem):
        """Adiciona mensagem ao log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {mensagem}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def limpar_log(self):
        """Limpa o log"""
        self.log_text.delete(1.0, tk.END)
        
    def log_restore(self, mensagem):
        """Adiciona mensagem ao log de restauração"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text_restore.insert(tk.END, f"[{timestamp}] {mensagem}\n")
        self.log_text_restore.see(tk.END)
        self.root.update_idletasks()
        
    def limpar_log_restore(self):
        """Limpa o log de restauração"""
        self.log_text_restore.delete(1.0, tk.END)
        
    def selecionar_pasta_backup(self):
        """Abre diálogo para selecionar pasta de backup"""
        pasta = filedialog.askdirectory(initialdir=self.backup_dir.get() if self.backup_dir.get() else None)
        if pasta:
            self.pasta_backup_selecionada.set(pasta)
            self.log_restore(f"Pasta de backup selecionada: {pasta}")
            self.salvar_configuracoes()

    def carregar_configuracoes(self):
        """Carrega configurações do arquivo config.json"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.backup_dir.set(config.get("backup_dir", "C:\\backup\\mongodb"))
                    self.mongo_uri.set(config.get("mongo_uri", "mongodb://localhost:27017/"))
                    self.restore_uri.set(config.get("restore_uri", "mongodb://localhost:27017/"))
                    self.agendamento_ativo.set(config.get("agendamento_ativo", False))
                    self.modo_agendamento.set(config.get("modo_agendamento", "semanal"))
                    self.intervalo_minutos.set(config.get("intervalo_minutos", 30))
                    self.hora_backup.set(config.get("hora_backup", "00:00"))
                    
                    dias_config = config.get("dias_semana", {})
                    for dia, valor in dias_config.items():
                        if dia in self.dias_semana:
                            self.dias_semana[dia].set(valor)
                return True
            except Exception as e:
                print(f"Erro ao carregar config.json: {e}")
        return False

    def salvar_configuracoes(self):
        """Salva configurações no arquivo config.json"""
        config = {
            "backup_dir": self.backup_dir.get(),
            "mongo_uri": self.mongo_uri.get(),
            "restore_uri": self.restore_uri.get(),
            "agendamento_ativo": self.agendamento_ativo.get(),
            "modo_agendamento": self.modo_agendamento.get(),
            "intervalo_minutos": self.intervalo_minutos.get(),
            "hora_backup": self.hora_backup.get(),
            "dias_semana": {dia: var.get() for dia, var in self.dias_semana.items()}
        }
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            self.log(f"Erro ao salvar configurações: {e}")
            return False
            
    def testar_conexao_restore(self):
        """Testa a conexão com o MongoDB para restauração"""
        self.log_restore("Testando conexão com MongoDB...")
        uri = self.restore_uri.get()
        
        try:
            client = MongoClient(uri, serverSelectionTimeoutMS=5000)
            client.server_info()
            client.close()
            messagebox.showinfo("Sucesso", "Conexão estabelecida com sucesso!")
            self.log_restore("✓ Conexão estabelecida com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao conectar:\n{str(e)}")
            self.log_restore(f"✗ Erro ao conectar: {e}")
        
    def selecionar_diretorio(self):
        """Abre diálogo para selecionar diretório"""
        diretorio = filedialog.askdirectory(initialdir=self.backup_dir.get())
        if diretorio:
            self.backup_dir.set(diretorio)
            self.log(f"Diretório de backup selecionado: {diretorio}")
            self.salvar_configuracoes()
            
    def testar_conexao(self):
        """Testa a conexão com o MongoDB"""
        self.salvar_configuracoes()
        self.log("Testando conexão com MongoDB...")
        uri = self.mongo_uri.get()
        
        try:
            client = MongoClient(uri, serverSelectionTimeoutMS=5000)
            client.server_info()
            client.close()
            messagebox.showinfo("Sucesso", "Conexão estabelecida com sucesso!")
            self.log("✓ Conexão estabelecida com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao conectar:\n{str(e)}")
            self.log(f"✗ Erro ao conectar: {e}")
            
    def conectar_mongodb(self):
        """Conecta ao MongoDB"""
        try:
            self.log("Conectando ao MongoDB...")
            self.client = MongoClient(self.mongo_uri.get(), serverSelectionTimeoutMS=5000)
            self.client.server_info()
            self.log("✓ Conexão estabelecida com sucesso!")
            return True
        except Exception as e:
            self.log(f"✗ Erro ao conectar ao MongoDB: {e}")
            messagebox.showerror("Erro de Conexão", f"Erro ao conectar ao MongoDB:\n{str(e)}")
            return False
            
    def listar_bancos_thread(self):
        """Executa listagem de bancos em thread separada"""
        if self.backup_em_andamento:
            messagebox.showwarning("Aviso", "Backup em andamento. Aguarde a conclusão.")
            return
            
        thread = threading.Thread(target=self.listar_bancos, daemon=True)
        thread.start()
        
    def listar_bancos(self):
        """Lista todos os bancos de dados"""
        self.lista_bancos.delete(0, tk.END)
        self.bancos_lista = []
        
        if not self.conectar_mongodb():
            return
            
        try:
            bancos = self.client.list_database_names()
            bancos_sistema = ['admin', 'config', 'local']
            self.bancos_lista = [b for b in bancos if b not in bancos_sistema]
            
            self.log(f"Bancos de dados encontrados: {len(self.bancos_lista)}")
            
            for banco in self.bancos_lista:
                self.lista_bancos.insert(tk.END, banco)
                self.log(f"  - {banco}")
                
            if self.bancos_lista:
                self.btn_backup.config(state=tk.NORMAL)
                self.log(f"\n✓ {len(self.bancos_lista)} banco(s) pronto(s) para backup.")
            else:
                self.btn_backup.config(state=tk.DISABLED)
                self.log("Nenhum banco de dados encontrado para backup.")
                
        except Exception as e:
            self.log(f"✗ Erro ao listar bancos de dados: {e}")
            messagebox.showerror("Erro", f"Erro ao listar bancos:\n{str(e)}")
        finally:
            if self.client:
                self.client.close()
                self.client = None
                
    def executar_backup_thread(self):
        """Executa backup em thread separada"""
        if self.backup_em_andamento:
            return
            
        if not self.bancos_lista:
            messagebox.showwarning("Aviso", "Nenhum banco de dados listado. Liste os bancos primeiro.")
            return
            
        thread = threading.Thread(target=self.executar_backup, daemon=True)
        thread.start()
        
    def executar_backup(self):
        """Executa o processo completo de backup"""
        self.backup_em_andamento = True
        self.btn_backup.config(state=tk.DISABLED)
        self.progress.start(10)
        
        try:
            self.log("\n" + "="*60)
            self.log("INICIANDO PROCESSO DE BACKUP")
            self.log("="*60)
            
            # Conecta ao MongoDB
            if not self.conectar_mongodb():
                return
                
            # Cria pasta de backup
            data_hora = datetime.now().strftime("%d-%m-%Y - %H-%M-%S")
            pasta_backup = os.path.join(self.backup_dir.get(), data_hora)
            
            try:
                os.makedirs(pasta_backup, exist_ok=True)
                self.log(f"\nPasta de backup criada: {pasta_backup}")
            except Exception as e:
                self.log(f"✗ Erro ao criar pasta de backup: {e}")
                messagebox.showerror("Erro", f"Erro ao criar pasta de backup:\n{str(e)}")
                return
                
            # Exporta cada banco
            self.log("\n" + "="*60)
            self.log("EXPORTANDO BANCOS DE DADOS...")
            self.log("="*60 + "\n")
            
            sucessos = 0
            falhas = 0
            
            for i, banco in enumerate(self.bancos_lista, 1):
                self.log(f"[{i}/{len(self.bancos_lista)}] Exportando banco '{banco}'...")
                
                if self.exportar_banco(banco, pasta_backup):
                    sucessos += 1
                    self.log(f"✓ Banco '{banco}' exportado com sucesso!\n")
                else:
                    falhas += 1
                    self.log(f"✗ Falha ao exportar banco '{banco}'\n")
                    
            # Resumo final
            self.log("\n" + "="*60)
            self.log("RESUMO DO BACKUP")
            self.log("="*60)
            self.log(f"Bancos exportados com sucesso: {sucessos}")
            self.log(f"Bancos com falha: {falhas}")
            self.log(f"Pasta de backup: {pasta_backup}")
            self.log("="*60)
            
            # Mensagem final
            if falhas == 0:
                messagebox.showinfo("Sucesso", 
                    f"Backup concluído com sucesso!\n\n"
                    f"Bancos exportados: {sucessos}\n"
                    f"Pasta: {pasta_backup}")
            else:
                messagebox.showwarning("Concluído com Avisos",
                    f"Backup concluído com algumas falhas.\n\n"
                    f"Sucessos: {sucessos}\n"
                    f"Falhas: {falhas}\n"
                    f"Pasta: {pasta_backup}")
                    
        except Exception as e:
            self.log(f"\n✗ Erro fatal: {e}")
            messagebox.showerror("Erro Fatal", f"Erro durante o backup:\n{str(e)}")
        finally:
            self.progress.stop()
            self.backup_em_andamento = False
            self.btn_backup.config(state=tk.NORMAL)
            if self.client:
                self.client.close()
                self.client = None
                
    def exportar_banco(self, nome_banco, pasta_destino):
        """Exporta um banco de dados usando mongodump"""
        try:
            # Modificacao: Exportar diretamente para a pasta destino
            # O mongodump ja cria uma subpasta com o nome do banco
            
            comando = [
                "mongodump",
                "--db", nome_banco,
                "--out", pasta_destino
            ]
            
            resultado = subprocess.run(
                comando,
                capture_output=True,
                text=True,
                check=True
            )

            # Log output to help debugging
            if resultado.stderr:
                self.log(f"  [Mongo Log]: {resultado.stderr}")
            if resultado.stdout:
                self.log(f"  [Output]: {resultado.stdout}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            self.log(f"  Erro: {e.stderr}")
            return False
        except FileNotFoundError:
            self.log("  Erro: 'mongodump' não encontrado!")
            self.log("  Certifique-se de que o MongoDB está instalado e mongodump está no PATH.")
            messagebox.showerror("Erro", 
                "mongodump não encontrado!\n\n"
                "Certifique-se de que o MongoDB está instalado\n"
                "e mongodump está no PATH do sistema.")
            return False
        except Exception as e:
            self.log(f"  Erro inesperado: {e}")
            return False
            
    def listar_bancos_backup_thread(self):
        """Executa listagem de bancos no backup em thread separada"""
        if self.restore_em_andamento:
            messagebox.showwarning("Aviso", "Restauração em andamento. Aguarde a conclusão.")
            return
            
        thread = threading.Thread(target=self.listar_bancos_backup, daemon=True)
        thread.start()
        
    def listar_bancos_backup(self):
        """Lista os bancos de dados disponíveis na pasta de backup"""
        self.lista_bancos_backup.delete(0, tk.END)
        self.bancos_backup_lista = []
        
        pasta = self.pasta_backup_selecionada.get()
        if not pasta:
            messagebox.showwarning("Aviso", "Selecione uma pasta de backup primeiro.")
            return
            
        if not os.path.exists(pasta):
            messagebox.showerror("Erro", "A pasta selecionada não existe!")
            self.log_restore(f"✗ Pasta não encontrada: {pasta}")
            return
            
        try:
            # Lista os diretórios na pasta de backup (cada diretório é um banco)
            itens = os.listdir(pasta)
            self.bancos_backup_lista = [item for item in itens 
                                       if os.path.isdir(os.path.join(pasta, item)) 
                                       and not item.startswith('.')]
            
            if not self.bancos_backup_lista:
                self.log_restore("Nenhum banco de dados encontrado na pasta de backup.")
                messagebox.showinfo("Info", "Nenhum banco de dados encontrado na pasta selecionada.")
                return
                
            self.log_restore(f"Bancos de dados encontrados no backup: {len(self.bancos_backup_lista)}")
            
            for banco in self.bancos_backup_lista:
                self.lista_bancos_backup.insert(tk.END, banco)
                self.log_restore(f"  - {banco}")
                
            self.btn_restore.config(state=tk.NORMAL)
            self.log_restore(f"\n✓ {len(self.bancos_backup_lista)} banco(s) pronto(s) para restauração.")
            
        except Exception as e:
            self.log_restore(f"✗ Erro ao listar bancos no backup: {e}")
            messagebox.showerror("Erro", f"Erro ao listar bancos:\n{str(e)}")
            
    def executar_restore_thread(self):
        """Executa restauração em thread separada"""
        if self.restore_em_andamento:
            return
            
        if not self.bancos_backup_lista:
            messagebox.showwarning("Aviso", "Nenhum banco de dados listado. Liste os bancos primeiro.")
            return
            
        # Confirmação
        if self.preservar_dados.get():
            msg = (f"Deseja importar {len(self.bancos_backup_lista)} banco(s) de dados?\n\n"
                   "Os dados existentes no seu banco local SERÃO PRESERVADOS. "
                   "Apenas novas informações serão adicionadas.")
        else:
            msg = (f"Deseja restaurar {len(self.bancos_backup_lista)} banco(s) de dados?\n\n"
                   "ATENÇÃO: Isso irá SOBRESCREVER os bancos existentes no MongoDB de destino!")
            
        resposta = messagebox.askyesno("Confirmar Restauração", msg)
        
        if not resposta:
            return
            
        thread = threading.Thread(target=self.executar_restore, daemon=True)
        thread.start()
        
    def executar_restore(self):
        """Executa o processo completo de restauração"""
        self.restore_em_andamento = True
        self.btn_restore.config(state=tk.DISABLED)
        self.progress_restore.start(10)
        
        try:
            self.log_restore("\n" + "="*60)
            self.log_restore("INICIANDO PROCESSO DE RESTAURAÇÃO")
            self.log_restore("="*60)
            
            pasta_backup = self.pasta_backup_selecionada.get()
            
            # Testa conexão
            try:
                self.log_restore("Testando conexão com MongoDB...")
                client = MongoClient(self.restore_uri.get(), serverSelectionTimeoutMS=5000)
                client.server_info()
                client.close()
                self.log_restore("✓ Conexão estabelecida com sucesso!")
            except Exception as e:
                self.log_restore(f"✗ Erro ao conectar ao MongoDB: {e}")
                messagebox.showerror("Erro", f"Erro ao conectar ao MongoDB:\n{str(e)}")
                return
                
            # Restaura cada banco
            self.log_restore("\n" + "="*60)
            self.log_restore("RESTAURANDO BANCOS DE DADOS...")
            self.log_restore("="*60 + "\n")
            
            sucessos = 0
            falhas = 0
            
            for i, banco in enumerate(self.bancos_backup_lista, 1):
                self.log_restore(f"[{i}/{len(self.bancos_backup_lista)}] Restaurando banco '{banco}'...")
                
                if self.restaurar_banco(banco, pasta_backup):
                    sucessos += 1
                    self.log_restore(f"✓ Banco '{banco}' restaurado com sucesso!\n")
                else:
                    falhas += 1
                    self.log_restore(f"✗ Falha ao restaurar banco '{banco}'\n")
                    
            # Resumo final
            self.log_restore("\n" + "="*60)
            self.log_restore("RESUMO DA RESTAURAÇÃO")
            self.log_restore("="*60)
            self.log_restore(f"Bancos restaurados com sucesso: {sucessos}")
            self.log_restore(f"Bancos com falha: {falhas}")
            self.log_restore("="*60)
            
            # Mensagem final
            if falhas == 0:
                messagebox.showinfo("Sucesso", 
                    f"Restauração concluída com sucesso!\n\n"
                    f"Bancos restaurados: {sucessos}")
            else:
                messagebox.showwarning("Concluído com Avisos",
                    f"Restauração concluída com algumas falhas.\n\n"
                    f"Sucessos: {sucessos}\n"
                    f"Falhas: {falhas}")
                    
        except Exception as e:
            self.log_restore(f"\n✗ Erro fatal: {e}")
            messagebox.showerror("Erro Fatal", f"Erro durante a restauração:\n{str(e)}")
        finally:
            self.progress_restore.stop()
            self.restore_em_andamento = False
            self.btn_restore.config(state=tk.NORMAL)
            
    def restaurar_banco(self, nome_banco, pasta_backup):
        """Restaura um banco de dados usando mongorestore"""
        try:
            pasta_banco = os.path.join(pasta_backup, nome_banco)
            
            # Verificacao de aninhamento duplo (correção para backups antigos)
            # Estrutura antiga: backup/dbName/dbName/arquivo.bson
            # Estrutura nova/correta: backup/dbName/arquivo.bson
            pasta_aninhada = os.path.join(pasta_banco, nome_banco)
            
            if os.path.exists(pasta_aninhada):
                self.log_restore(f"  [Info] Detectada estrutura aninhada para '{nome_banco}'")
                path_to_restore = pasta_aninhada
            else:
                path_to_restore = pasta_banco
            
            if not os.path.exists(path_to_restore):
                self.log_restore(f"  Erro: Pasta do banco não encontrada: {path_to_restore}")
                return False
                
            comando = [
                "mongorestore",
                "--uri", self.restore_uri.get(),
                "--db", nome_banco
            ]
            
            # Se NÃO for para preservar, adicionamos o --drop para limpar antes
            if not self.preservar_dados.get():
                comando.append("--drop")
                
            comando.append(path_to_restore)
            
            resultado = subprocess.run(
                comando,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Log output to help debugging
            if resultado.stderr:
                self.log_restore(f"  [Mongo Log]: {resultado.stderr}")
            if resultado.stdout:
                self.log_restore(f"  [Output]: {resultado.stdout}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            self.log_restore(f"  Erro: {e.stderr}")
            return False
        except FileNotFoundError:
            self.log_restore("  Erro: 'mongorestore' não encontrado!")
            self.log_restore("  Certifique-se de que o MongoDB está instalado e mongorestore está no PATH.")
            messagebox.showerror("Erro", 
                "mongorestore não encontrado!\n\n"
                "Certifique-se de que o MongoDB está instalado\n"
                "e mongorestore está no PATH do sistema.")
            return False
        except Exception as e:
            self.log_restore(f"  Erro inesperado: {e}")
            return False


def main():
    """Função principal"""
    root = tk.Tk()
    app = MongoDBBackupGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()


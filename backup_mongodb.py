#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistema de Backup MongoDB
Exporta todos os bancos de dados MongoDB para pastas organizadas
"""

import subprocess
import os
import sys
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError


class MongoDBBackup:
    def __init__(self, backup_dir="C:\\backup\\mongodb", mongo_uri="mongodb://localhost:27017/"):
        """
        Inicializa o sistema de backup
        
        Args:
            backup_dir: Diretório onde os backups serão salvos
            mongo_uri: URI de conexão do MongoDB
        """
        self.backup_dir = backup_dir
        self.mongo_uri = mongo_uri
        self.client = None
        
    def conectar_mongodb(self):
        """Conecta ao MongoDB e retorna True se bem-sucedido"""
        try:
            print("Conectando ao MongoDB...")
            self.client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=5000)
            # Testa a conexão
            self.client.server_info()
            print("✓ Conexão estabelecida com sucesso!")
            return True
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            print(f"✗ Erro ao conectar ao MongoDB: {e}")
            print("Verifique se o MongoDB está rodando e acessível.")
            return False
    
    def listar_bancos_dados(self):
        """Lista todos os bancos de dados disponíveis"""
        try:
            bancos = self.client.list_database_names()
            # Remove bancos de sistema padrão (opcional)
            bancos_sistema = ['admin', 'config', 'local']
            bancos_uteis = [b for b in bancos if b not in bancos_sistema]
            
            print(f"\nBancos de dados encontrados: {len(bancos_uteis)}")
            for banco in bancos_uteis:
                print(f"  - {banco}")
            
            return bancos_uteis
        except Exception as e:
            print(f"✗ Erro ao listar bancos de dados: {e}")
            return []
    
    def criar_pasta_backup(self):
        """Cria a pasta de backup com timestamp"""
        data_hora = datetime.now().strftime("%d-%m-%Y - %H-%M-%S")
        pasta_backup = os.path.join(self.backup_dir, data_hora)
        
        try:
            os.makedirs(pasta_backup, exist_ok=True)
            print(f"\nPasta de backup criada: {pasta_backup}")
            return pasta_backup
        except Exception as e:
            print(f"✗ Erro ao criar pasta de backup: {e}")
            return None
    
    def exportar_banco(self, nome_banco, pasta_destino):
        """
        Exporta um banco de dados usando mongodump
        
        Args:
            nome_banco: Nome do banco de dados a ser exportado
            pasta_destino: Pasta onde o backup será salvo
        """
        try:
            # Cria pasta específica para este banco
            pasta_banco = os.path.join(pasta_destino, nome_banco)
            os.makedirs(pasta_banco, exist_ok=True)
            
            print(f"\nExportando banco '{nome_banco}'...")
            
            # Comando mongodump
            comando = [
                "mongodump",
                "--db", nome_banco,
                "--out", pasta_banco
            ]
            
            # Executa o comando
            resultado = subprocess.run(
                comando,
                capture_output=True,
                text=True,
                check=True
            )
            
            print(f"✓ Banco '{nome_banco}' exportado com sucesso!")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"✗ Erro ao exportar banco '{nome_banco}': {e.stderr}")
            return False
        except FileNotFoundError:
            print("✗ Erro: 'mongodump' não encontrado!")
            print("Certifique-se de que o MongoDB está instalado e mongodump está no PATH.")
            return False
        except Exception as e:
            print(f"✗ Erro inesperado ao exportar '{nome_banco}': {e}")
            return False
    
    def executar_backup(self):
        """Executa o processo completo de backup"""
        print("=" * 60)
        print("SISTEMA DE BACKUP MONGODB")
        print("=" * 60)
        
        # Conecta ao MongoDB
        if not self.conectar_mongodb():
            return False
        
        # Lista bancos de dados
        bancos = self.listar_bancos_dados()
        
        if not bancos:
            print("\nNenhum banco de dados encontrado para backup.")
            return False
        
        # Cria pasta de backup
        pasta_backup = self.criar_pasta_backup()
        if not pasta_backup:
            return False
        
        # Exporta cada banco
        print("\n" + "=" * 60)
        print("INICIANDO EXPORTAÇÃO...")
        print("=" * 60)
        
        sucessos = 0
        falhas = 0
        
        for banco in bancos:
            if self.exportar_banco(banco, pasta_backup):
                sucessos += 1
            else:
                falhas += 1
        
        # Resumo final
        print("\n" + "=" * 60)
        print("RESUMO DO BACKUP")
        print("=" * 60)
        print(f"Bancos exportados com sucesso: {sucessos}")
        print(f"Bancos com falha: {falhas}")
        print(f"Pasta de backup: {pasta_backup}")
        print("=" * 60)
        
        return falhas == 0
    
    def fechar_conexao(self):
        """Fecha a conexão com o MongoDB"""
        if self.client:
            self.client.close()


def main():
    """Função principal"""
    # Configurações (podem ser alteradas aqui)
    BACKUP_DIR = "C:\\backup\\mongodb"
    MONGO_URI = "mongodb://localhost:27017/"
    
    # Verifica argumentos da linha de comando
    if len(sys.argv) > 1:
        BACKUP_DIR = sys.argv[1]
    if len(sys.argv) > 2:
        MONGO_URI = sys.argv[2]
    
    backup = MongoDBBackup(backup_dir=BACKUP_DIR, mongo_uri=MONGO_URI)
    
    try:
        sucesso = backup.executar_backup()
        sys.exit(0 if sucesso else 1)
    except KeyboardInterrupt:
        print("\n\nBackup cancelado pelo usuário.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Erro fatal: {e}")
        sys.exit(1)
    finally:
        backup.fechar_conexao()


if __name__ == "__main__":
    main()


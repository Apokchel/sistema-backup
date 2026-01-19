# Sistema de Backup e Restauração MongoDB

Sistema completo para exportar e importar bancos de dados MongoDB de forma automatizada.

## Funcionalidades

### Backup (Exportar)
- ✅ Interface gráfica intuitiva e fácil de usar
- ✅ Lista automaticamente todos os bancos de dados disponíveis no MongoDB
- ✅ Exporta cada banco de dados usando `mongodump`
- ✅ Organiza os backups em pastas com formato "DD-MM-YYYY - HH-MM-SS"
- ✅ Exibe progresso em tempo real e resumo do processo
- ✅ Teste de conexão antes de executar backup
- ✅ Log detalhado de todas as operações

### Restauração (Importar)
- ✅ Importa backups de outros computadores
- ✅ Lista bancos de dados disponíveis na pasta de backup
- ✅ Restaura bancos usando `mongorestore`
- ✅ Suporta diferentes URIs do MongoDB (local ou remoto)
- ✅ Confirmação antes de sobrescrever dados existentes
- ✅ Log detalhado do processo de restauração

## Requisitos

- Python 3.6 ou superior
- MongoDB instalado e rodando
- `mongodump` e `mongorestore` disponíveis no PATH do sistema
- Biblioteca `pymongo` (instalada automaticamente)

## Instalação

1. Instale as dependências:
```bash
pip install -r requirements.txt
```

## Uso

### Interface Gráfica (Recomendado)

**Opção 1:** Duplo clique no arquivo `executar_backup_gui.bat`

**Opção 2:** Execute via linha de comando:
```bash
python backup_mongodb_gui.py
```

A interface gráfica possui duas abas:

### Aba "Backup (Exportar)"
- Configurar o diretório de backup
- Configurar a URI do MongoDB
- Testar a conexão antes de executar
- Listar bancos de dados disponíveis
- Executar backup com acompanhamento visual
- Ver log detalhado em tempo real

### Aba "Restauração (Importar)"
- Selecionar pasta de backup para importar
- Configurar URI do MongoDB de destino
- Testar conexão com o MongoDB de destino
- Listar bancos disponíveis na pasta de backup
- Restaurar/importar bancos de dados
- Ver log detalhado do processo de restauração

### Linha de Comando

Execute o script Python:
```bash
python backup_mongodb.py
```

O sistema irá:
1. Conectar ao MongoDB local (mongodb://localhost:27017/)
2. Listar todos os bancos de dados disponíveis
3. Criar uma pasta de backup com timestamp em `C:\backup\mongodb\backup_YYYYMMDD_HHMMSS`
4. Exportar cada banco de dados para sua respectiva pasta

**Personalização via argumentos:**
```bash
python backup_mongodb.py "D:\meus_backups" "mongodb://usuario:senha@localhost:27017/"
```

**Argumentos:**
1. Diretório de backup (opcional, padrão: `C:\backup\mongodb`)
2. URI do MongoDB (opcional, padrão: `mongodb://localhost:27017/`)

## Estrutura dos Backups

Os backups são organizados da seguinte forma:

```
C:\backup\mongodb\
└── 15-01-2024 - 14-30-45\
    ├── banco1\
    │   └── (arquivos do mongodump)
    ├── banco2\
    │   └── (arquivos do mongodump)
    └── banco3\
        └── (arquivos do mongodump)
```

**Formato do nome da pasta:** `DD-MM-YYYY - HH-MM-SS`

## Como Importar Backup em Outro Computador

1. Copie a pasta de backup completa para o novo computador
2. Abra o sistema e vá para a aba **"Restauração (Importar)"**
3. Clique em **"Procurar"** e selecione a pasta de backup copiada
4. Configure a URI do MongoDB de destino (onde os dados serão importados)
5. Clique em **"Testar Conexão"** para verificar a conexão
6. Clique em **"Listar Bancos no Backup"** para ver os bancos disponíveis
7. Clique em **"Importar/Restaurar"** para iniciar o processo
8. Confirme a operação (atenção: isso irá sobrescrever bancos existentes com o mesmo nome)

**Importante:** O sistema usa `--drop` ao restaurar, o que remove o banco existente antes de restaurar. Certifique-se de que deseja sobrescrever os dados antes de confirmar.

## Notas

- O script ignora bancos de sistema padrão (`admin`, `config`, `local`)
- Certifique-se de executar com permissões adequadas se necessário
- O MongoDB deve estar rodando e acessível antes de executar o script

## Solução de Problemas

### Erro: "mongodump não encontrado" ou "mongorestore não encontrado"
- Certifique-se de que o MongoDB está instalado
- Adicione o diretório `bin` do MongoDB ao PATH do sistema

### Erro de conexão
- Verifique se o MongoDB está rodando
- Verifique se a URI de conexão está correta
- Verifique permissões de acesso ao MongoDB


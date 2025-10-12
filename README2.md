# Guia de Instalação e Configuração do Painel CZ7 Host

Este guia irá detalhar o passo a passo para configurar e rodar o painel CZ7 Host em um servidor dedicado ou VPS com um sistema operacional baseado em Debian/Ubuntu.

## 1. Pré-requisitos do Sistema

Antes de começar, você precisa garantir que o seu sistema tenha todos os componentes necessários. O painel depende de **Docker** para gerenciar contêineres e **KVM/QEMU** com **libvirt** para gerenciar as VPS.

### 1.1. Instalar Docker
Execute os seguintes comandos para instalar o Docker:
```bash
sudo apt-get update
sudo apt-get install -y docker.io
sudo systemctl start docker
sudo systemctl enable docker
```

### 1.2. Instalar KVM e Libvirt
Execute os seguintes comandos para instalar o KVM e as ferramentas de gerenciamento:
```bash
sudo apt-get install -y qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils
```

### 1.3. Adicionar seu Usuário aos Grupos Corretos
Para que a aplicação possa gerenciar o Docker e o libvirt sem precisar de `sudo` o tempo todo, adicione seu usuário atual aos grupos `docker` e `libvirt`:
```bash
sudo usermod -aG docker $USER
sudo usermod -aG libvirt $USER
```
**Importante:** Após executar esses comandos, você precisa **fazer logout e login novamente** no seu servidor para que as alterações de grupo entrem em vigor.

## 2. Configuração do Projeto

### 2.1. Clonar o Repositório
Primeiro, clone o código do projeto para o seu servidor:
```bash
git clone <URL_DO_SEU_REPOSITORIO>
cd <NOME_DO_DIRETORIO_DO_PROJETO>
```

### 2.2. Instalar Dependências Python
Instale o Python 3.10 ou superior e o `pip`. Em seguida, instale todas as dependências do projeto:
```bash
sudo apt-get install -y python3-pip
pip3 install -r requirements.txt
```

### 2.3. Configurar o Banco de Dados (PostgreSQL)
A aplicação usa um banco de dados PostgreSQL. Instale-o:
```bash
sudo apt-get install -y postgresql postgresql-contrib
sudo -u postgres createuser --interactive # Crie um usuário para a aplicação
sudo -u postgres createdb cz7host # Crie o banco de dados
```
Lembre-se de definir uma senha para o usuário que você criou.

### 2.4. Configurar as Variáveis de Ambiente
Copie o arquivo de exemplo `.env.example` para um novo arquivo chamado `.env`:
```bash
cp .env.example .env
```
Agora, edite o arquivo `.env` com um editor de texto (como `nano .env`) e preencha todas as variáveis com suas chaves e credenciais reais:

*   `DISCORD_CLIENT_ID` e `DISCORD_CLIENT_SECRET`: Pegue no portal de desenvolvedores do Discord.
*   `SESSION_SECRET`: Gere uma string longa e aleatória para a segurança das sessões.
*   `DATABASE_URL`: Formato: `postgresql://USUARIO:SENHA@localhost/cz7host`.
*   `STRIPE_PUBLIC_KEY`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`: Pegue no seu dashboard do Stripe.

## 3. Inicialização do Sistema

### 3.1. Rodar as Migrações do Banco de Dados
Com o banco de dados e as configurações prontas, aplique o schema da aplicação:
```bash
alembic upgrade head
```
Isso criará todas as tabelas necessárias (`users`, `services`, `plans`, etc.).

### 3.2. Criar os Planos de Serviço
Use o script que criamos para adicionar os planos ao seu sistema. Comece pelo plano gratuito, que é essencial para o registro de novos usuários.

**Exemplo para criar o Plano Gratuito:**
```bash
python3 scripts/manage_plans.py create \
--name "Free" \
--price 0.00 \
--stripe-price-id "price_free_tier" \
--ram-mb 256 \
--cpu-vcore 0.5 \
--disk-gb 1 \
--max-services 1
```
Crie outros planos pagos conforme necessário, certificando-se de que o `stripe_price_id` corresponde a um preço que você criou no seu dashboard do Stripe.

### 3.3. Preparar a Imagem Base da VPS (Opcional)
Se você for oferecer VPS, precisa de uma imagem de sistema operacional base. O sistema espera encontrá-la em `/var/lib/libvirt/images/base.qcow2`. Você pode baixar uma imagem cloud (como a do Ubuntu) e colocá-la neste local.

## 4. Iniciar a Aplicação

Finalmente, para iniciar o painel, execute o seguinte comando:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
É recomendado usar um gerenciador de processos como o `systemd` para manter a aplicação rodando em produção.

Seu painel CZ7 Host estará agora acessível em `http://SEU_IP:8000`.
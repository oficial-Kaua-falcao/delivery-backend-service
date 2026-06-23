# Sistema de Gerenciamento de Pedidos com Autenticação JWT

## 1. Visão Geral do Projeto
Este projeto consiste em uma API REST desenvolvida em Python com **FastAPI** para gerenciamento de usuários, autenticação e controle de pedidos. A aplicação implementa mecanismos de autenticação baseados em **JSON Web Tokens (JWT)**, controle de permissões por perfil de usuário e persistência de dados por meio do **SQLAlchemy ORM** integrado ao **SQLite**.

A solução foi estruturada em camadas independentes responsáveis pelo gerenciamento de rotas, modelos de dados, validações de entrada, serviços de autenticação e migrações de banco de dados. Essa separação reduz o acoplamento entre os componentes e facilita a manutenção, a expansão e a reutilização do código.

O sistema permite o cadastro de usuários, autenticação segura, emissão de tokens de acesso e atualização de sessões por meio de *refresh tokens*. Após autenticado, o usuário pode criar, consultar, editar, finalizar e cancelar pedidos, além de gerenciar os itens vinculados a cada pedido.

---

## 2. Funcionamento da Solução
O fluxo operacional inicia-se com a criação de uma conta de usuário. Durante o processo de cadastro, a senha informada não é armazenada em texto puro. Antes da persistência, ela é submetida ao algoritmo **bcrypt**, gerando um hash criptográfico utilizado posteriormente para validação das credenciais.

Após o cadastro, o usuário pode realizar autenticação utilizando suas credenciais. Em caso de sucesso, o sistema gera dois tokens distintos:
* **Access Token:** Utilizado para autenticação das requisições protegidas.
* **Refresh Token:** Utilizado para renovação da sessão sem necessidade de novo login.

As rotas protegidas validam automaticamente o token recebido por meio de dependências do FastAPI. O processo verifica integridade, validade temporal e tipo do token antes de liberar o acesso aos recursos solicitados.

Uma vez autenticado, o usuário pode gerenciar seus próprios pedidos. Cada pedido pode conter diversos itens, formando uma relação hierárquica entre o pedido e seus respectivos componentes. O valor total do pedido é atualizado dinamicamente conforme novos itens são adicionados.

O sistema também implementa autorização baseada em permissões. Usuários comuns possuem acesso apenas aos seus próprios registros, enquanto usuários administradores podem visualizar e consultar pedidos pertencentes a qualquer usuário cadastrado.

---

## 3. Arquitetura e Fluxo de Dados
A aplicação segue uma arquitetura organizada em módulos especializados.

A **camada de apresentação** é composta pelos roteadores do FastAPI, responsáveis por receber as requisições HTTP, validar parâmetros e encaminhar as operações para as regras de negócio correspondentes.

A **camada de validação** utiliza modelos Pydantic para garantir integridade e tipagem dos dados recebidos e enviados pela API.

A **camada de persistência** utiliza SQLAlchemy ORM para mapear entidades do domínio para tabelas relacionais. O modelo de dados é composto por três entidades principais:
1. **Usuário**
2. **Pedido**
3. **Item do Pedido**

A relação entre as entidades segue o modelo:
$$\text{Usuário} \longrightarrow \text{Pedidos} \longrightarrow \text{Itens do Pedido}$$

Um usuário pode possuir diversos pedidos e cada pedido pode conter múltiplos itens. O fluxo de dados ocorre da seguinte forma:
1. A requisição chega à rota FastAPI.
2. O payload é validado pelos schemas Pydantic.
3. O token JWT é validado quando necessário.
4. As operações são executadas via SQLAlchemy.
5. Os dados são persistidos no banco SQLite.
6. As migrações do esquema são gerenciadas com **Alembic**.
7. A resposta é serializada e retornada ao cliente.

---

## 4. Tecnologias Utilizadas

### Backend
* Python
* FastAPI

### Persistência de Dados
* SQLite
* SQLAlchemy ORM
* Alembic

### Segurança
* JWT (JSON Web Token)
* Bcrypt

### Validação e Serialização
* Pydantic

### Gerenciamento de Configurações
* Python Dotenv

### Padrões Utilizados
* Dependency Injection
* RESTful API
* Data Validation Layer
* ORM Mapping
* Database Migration Management

---

## 5. Implementação Técnica
* A autenticação foi implementada utilizando o padrão *Bearer Token* por meio do componente `OAuth2PasswordBearer` do FastAPI.
* Os tokens JWT armazenam informações essenciais do usuário, incluindo identificador, e-mail, tipo do token e tempo de expiração. Essa estratégia permite autenticação *stateless*, eliminando a necessidade de armazenamento de sessões no servidor.
* O sistema diferencia explicitamente tokens de acesso e tokens de renovação por meio do campo `type`, impedindo que *refresh tokens* sejam utilizados para acessar recursos protegidos.
* A proteção contra escalonamento indevido de privilégios é aplicada durante o cadastro de usuários. O atributo administrativo é definido internamente pela aplicação, impedindo que um usuário comum se registre como administrador manipulando a requisição.
* A camada ORM utiliza relacionamentos bidirecionais entre entidades, permitindo navegação eficiente entre usuários, pedidos e itens associados.
* A exclusão em cascata garante consistência referencial, removendo automaticamente registros dependentes quando um elemento pai é excluído.
* O controle de autorização é realizado em nível de rota, verificando se o usuário autenticado possui permissão para acessar ou modificar determinado recurso antes da execução das operações.
* As alterações estruturais do banco de dados são versionadas e aplicadas por meio do **Alembic**, garantindo rastreabilidade e consistência entre o modelo da aplicação e o esquema persistido.

---

## 6. Resultados Gerados pelo Sistema
O sistema disponibiliza uma API capaz de:
* Gerenciar contas de usuários.
* Realizar autenticação segura.
* Emitir e renovar tokens JWT.
* Controlar permissões administrativas.
* Registrar pedidos associados a usuários específicos.
* Gerenciar itens pertencentes a cada pedido.
* Atualizar automaticamente o valor total dos pedidos.
* Controlar estados operacionais dos pedidos.
* Restringir acesso a dados sensíveis conforme o perfil do usuário.

As informações são retornadas em formato JSON estruturado, facilitando a integração com aplicações web, mobile ou outros serviços externos.

---

## 7. Possíveis Evoluções Futuras
A arquitetura atual permite expansão sem alterações significativas na estrutura principal da aplicação. Entre as possíveis evoluções estão:
* Migração do SQLite para PostgreSQL.
* Inclusão de testes automatizados com Pytest.
* Containerização utilizando Docker.
* Registro de logs estruturados.
* Sistema de recuperação de senha.
* Controle granular de permissões baseado em papéis.
* Integração com serviços de monitoramento.
* Paginação avançada e filtros de consulta.
* Implementação de cache para otimização de desempenho.

Essas extensões permitiriam a utilização da aplicação em cenários com maior volume de dados e requisitos mais avançados de escalabilidade e observabilidade.

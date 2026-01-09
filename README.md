# FISCA - Sistema de Análise de Fiscalizações

Sistema de análise e monitoramento de fiscalizações tributárias desenvolvido para a Secretaria de Estado da Fazenda de Santa Catarina (SEFAZ/SC).

## Sobre o Projeto

O **FISCA** (Sistema de Análise de Fiscalizações) é um dashboard interativo que permite a análise multidimensional de dados de fiscalizações tributárias. O sistema fornece insights em tempo real sobre a efetividade das ações fiscais, performance dos auditores fiscais (AFREs) e métricas de conformidade tributária desde 2020.

### Funcionalidades Principais

- **Dashboard Executivo**: KPIs consolidados, taxas de conversão e métricas de efetividade
- **Análise por Ciclo de Vida**: Acompanhamento dos estados dos documentos fiscais
- **Análise por Gerência**: Performance das unidades de gestão
- **Análise por GES**: Métricas por setor fiscal
- **Análise por CNAE**: Distribuição por setores econômicos
- **Análise por Município**: Distribuição geográfica e performance regional
- **Performance de AFREs**: Produtividade e ranking dos auditores fiscais
- **Tipos de Infrações**: Análise detalhada das infrações mais recorrentes
- **Drill-Down de Empresas**: Histórico fiscal detalhado por contribuinte
- **Machine Learning**: Modelos preditivos para efetividade das fiscalizações

## Tecnologias Utilizadas

### Frontend e Visualização
- **Streamlit** - Framework web para dashboards interativos
- **Plotly** - Gráficos interativos e visualizações de dados

### Processamento de Dados
- **Pandas** - Manipulação e agregação de dados
- **NumPy** - Computação numérica
- **SQLAlchemy** - ORM para consultas ao banco de dados

### Machine Learning
- **scikit-learn** - Algoritmos de ML:
  - RandomForestClassifier
  - GradientBoostingClassifier
  - StandardScaler
  - Métricas de classificação e curvas ROC

### Banco de Dados
- **Apache Impala** - Motor de consultas SQL distribuído
- Autenticação LDAP com criptografia SSL/TLS

## Estrutura do Projeto

```
FISCA_NEW/
├── FISCA (1).py      # Aplicação principal Streamlit (dashboard)
├── FISCA.ipynb       # Notebook Jupyter para pipeline ETL
├── FISCA.json        # Configurações de queries Impala/Hue
└── README.md         # Documentação do projeto
```

### Descrição dos Arquivos

| Arquivo | Descrição |
|---------|-----------|
| `FISCA (1).py` | Aplicação principal contendo toda a lógica do dashboard, carregamento de dados, visualizações e funcionalidades de ML |
| `FISCA.ipynb` | Notebook para processamento e transformação de dados (ETL) usando Spark |
| `FISCA.json` | Arquivo de configuração do Hue/Impala com queries SQL pré-definidas |

## Pré-requisitos

- Python 3.8 ou superior
- Acesso à rede interna SEFAZ/SC
- Credenciais LDAP válidas

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/tiagossevero/FISCA_NEW.git
cd FISCA_NEW
```

2. Crie um ambiente virtual (recomendado):
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

3. Instale as dependências:
```bash
pip install streamlit pandas numpy plotly sqlalchemy impyla scikit-learn
```

4. Configure as credenciais do Streamlit:

Crie o arquivo `.streamlit/secrets.toml`:
```toml
[impala_credentials]
user = "seu_usuario_ldap"
password = "sua_senha_ldap"
```

## Execução

Execute a aplicação com o comando:

```bash
streamlit run "FISCA (1).py"
```

Acesse o sistema em: `http://localhost:8501`

### Autenticação

O sistema possui autenticação por senha. Ao acessar, informe a senha do sistema para ter acesso ao dashboard.

## Arquitetura

```
Usuário
    ↓
[Autenticação por Senha]
    ↓
[Interface Streamlit]
    ↓
[Camada de Carregamento de Dados]
    ↓
[Consultas SQL - Apache Impala]
    ↓
[Processamento com Pandas]
    ↓
[Renderização de Páginas com Plotly]
    ↓
[Visualizações Interativas e Tabelas]
```

## Banco de Dados

O sistema utiliza tabelas no Apache Impala (schema `teste`):

### Tabelas Principais
- `fisca_infracoes_base` - Infrações tributárias
- `fisca_notificacoes_fiscais` - Notificações fiscais emitidas
- `fisca_empresas_base` - Cadastro de empresas
- `fisca_termos_encerramento` - Termos de encerramento de fiscalização
- `fisca_acompanhamentos` - Acompanhamentos de fiscalizações
- `fisca_afres_cadastro` - Cadastro de auditores fiscais
- `fisca_catalogo_infracoes` - Catálogo de tipos de infrações

### Tabelas Agregadas para Dashboard
- `fisca_dashboard_executivo` - Métricas do dashboard executivo
- `fisca_metricas_por_gerencia` - Métricas por gerência
- `fisca_metricas_por_ges` - Métricas por GES
- `fisca_metricas_por_afre` - Métricas por auditor fiscal
- `fisca_fiscalizacoes_consolidadas` - Ciclo de vida consolidado das fiscalizações

## Módulos de Análise

### 1. Dashboard Executivo
Visão consolidada com KPIs principais:
- Total de infrações e valores
- Taxas de conversão de notificações
- Efetividade das fiscalizações
- Evolução temporal

### 2. Análise por Ciclo de Vida
- Distribuição dos estados dos documentos
- Normalização de status
- Métricas de validade

### 3. Performance de AFREs
- Produtividade individual
- Distribuição de performance
- Rankings e benchmarking

### 4. Machine Learning
Modelos preditivos para classificação da efetividade das fiscalizações:
- Random Forest Classifier
- Gradient Boosting Classifier
- Análise de importância de features
- Curvas ROC e métricas de avaliação

## Configurações

### Conexão com o Banco de Dados
```python
IMPALA_HOST = 'bdaworkernode02.sef.sc.gov.br'
IMPALA_PORT = 21050
DATABASE = 'teste'
```

### Cache de Dados
Os dados são cacheados por 1 hora (`ttl=3600`) para otimização de performance.

## Interface do Usuário

### Menu de Navegação
- Dashboard Executivo
- Ciclo de Vida - Estados
- Análise por Gerência
- Análise por GES
- Análise por CNAE
- Análise por Município
- Performance AFREs
- Tipos de Infrações
- Drill-Down Empresa
- Machine Learning
- Sobre o Sistema

### Filtros Disponíveis
- Ano/Período
- Gerência
- GES (Setor Fiscal)
- Município
- CNAE (Classificação Econômica)
- Status

## Desenvolvimento

### Pipeline ETL
O notebook `FISCA.ipynb` contém o pipeline de ETL usando Apache Spark para:
- Extração de dados das tabelas fonte
- Transformação e limpeza de dados
- Criação de tabelas agregadas para o dashboard
- Cálculo de métricas e indicadores

### Atualização de Dados
Os dados são atualizados via processo batch através do notebook ETL, que processa os dados das fontes originais e atualiza as tabelas do dashboard.

## Segurança

- Autenticação por senha no acesso ao sistema
- Autenticação LDAP para conexão com o banco de dados
- Conexão SSL/TLS criptografada
- Credenciais armazenadas em Streamlit Secrets

## Contato

**Secretaria de Estado da Fazenda de Santa Catarina (SEFAZ/SC)**

---

**Versão**: 1.0
**Última atualização**: Janeiro 2026

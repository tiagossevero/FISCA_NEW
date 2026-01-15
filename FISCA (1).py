import streamlit as st
import hashlib
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from sqlalchemy import create_engine
import warnings
import ssl
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, roc_curve
import pickle

# =============================================================================
# 1. CONFIGURAÇÕES INICIAIS
# =============================================================================

# Configuração SSL
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

warnings.filterwarnings('ignore')

# Configuração da página
st.set_page_config(
    page_title="Sistema FISCA - Análise de Fiscalizações",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# 2. SISTEMA DE SENHA
# =============================================================================

SENHA = "fisca2025"  # ← TROQUE para cada projeto

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        st.markdown("<div style='text-align: center; padding: 50px;'><h1>🔐 Sistema FISCA - Acesso Restrito</h1></div>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            senha_input = st.text_input("Digite a senha:", type="password", key="pwd_input")
            if st.button("Entrar", use_container_width=True):
                if senha_input == SENHA:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("❌ Senha incorreta")
        st.stop()

check_password()

# =============================================================================
# 3. ESTILOS CSS CUSTOMIZADOS
# =============================================================================

st.markdown("""
<style>
    /* ================================================
       CABEÇALHO PRINCIPAL
       ================================================ */
    .main-header {
        font-size: 2.8rem;
        font-weight: bold;
        color: #0d47a1;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        padding: 20px;
        background: linear-gradient(135deg, #1976d2 0%, #0d47a1 100%);
        border-radius: 15px;
        color: white;
    }
    
    .sub-header {
        font-size: 1.8rem;
        font-weight: bold;
        color: #1565c0;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 3px solid #1565c0;
        padding-bottom: 10px;
    }

    /* ================================================
       GRÁFICOS PLOTLY
       ================================================ */
    div[data-testid="stPlotlyChart"] {
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        padding: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        background-color: #ffffff;
    }
    
    /* ================================================
       MÉTRICAS
       ================================================ */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 2px solid #2c3e50;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    div[data-testid="stMetric"] > label {
        font-weight: 600;
        color: #2c3e50;
    }
    
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: bold;
        color: #1976d2;
    }
    
    /* ================================================
       ALERTAS PERSONALIZADOS
       ================================================ */
    .alert-critico {
        background-color: #ffebee;
        border-left: 5px solid #c62828;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .alert-alto {
        background-color: #fff3e0;
        border-left: 5px solid #ef6c00;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .alert-positivo {
        background-color: #e8f5e9;
        border-left: 5px solid #2e7d32;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .info-box {
        background-color: #e3f2fd;
        border-left: 4px solid #1976d2;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
    
    .kpi-container {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin: 10px 0;
    }

    /* ================================================
       TABELAS - DATAFRAME (st.dataframe)
       ================================================ */
    
    /* Container principal da tabela */
    div[data-testid="stDataFrame"] {
        border: 2px solid #e0e0e0 !important;
        border-radius: 10px !important;
        padding: 10px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
        background-color: #ffffff !important;
        overflow: hidden !important;
    }

    /* Cabeçalho da tabela - Estilo Escuro */
    div[data-testid="stDataFrame"] thead tr th {
        background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%) !important;
        color: white !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        padding: 16px 12px !important;
        text-align: center !important;
        border-bottom: 3px solid #1976d2 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        position: sticky !important;
        top: 0 !important;
        z-index: 100 !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    }

    /* Linhas do corpo */
    div[data-testid="stDataFrame"] tbody tr {
        border-bottom: 1px solid #e0e0e0 !important;
        transition: all 0.2s ease !important;
    }

    /* Efeito hover nas linhas */
    div[data-testid="stDataFrame"] tbody tr:hover {
        background-color: #e3f2fd !important;
        transform: translateX(3px) !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08) !important;
        cursor: pointer !important;
    }

    /* Células do corpo */
    div[data-testid="stDataFrame"] tbody td {
        padding: 14px 12px !important;
        font-size: 13px !important;
        color: #2c3e50 !important;
        border-right: 1px solid #f0f0f0 !important;
        vertical-align: middle !important;
    }

    /* Remover borda da última célula */
    div[data-testid="stDataFrame"] tbody td:last-child {
        border-right: none !important;
    }

    /* Linhas alternadas (zebra striping) */
    div[data-testid="stDataFrame"] tbody tr:nth-child(even) {
        background-color: #f8f9fa !important;
    }

    div[data-testid="stDataFrame"] tbody tr:nth-child(odd) {
        background-color: #ffffff !important;
    }

    /* Primeira coluna destacada */
    div[data-testid="stDataFrame"] tbody td:first-child {
        font-weight: 700 !important;
        color: #1976d2 !important;
        background-color: #e3f2fd !important;
        border-right: 2px solid #1976d2 !important;
    }

    /* Última coluna alinhada à direita (números) */
    div[data-testid="stDataFrame"] tbody td:last-child {
        text-align: right !important;
        font-weight: 600 !important;
        font-family: 'Courier New', monospace !important;
    }

    /* ================================================
       SCROLLBAR PERSONALIZADA
       ================================================ */
    div[data-testid="stDataFrame"]::-webkit-scrollbar {
        width: 10px !important;
        height: 10px !important;
    }

    div[data-testid="stDataFrame"]::-webkit-scrollbar-track {
        background: #f1f3f4 !important;
        border-radius: 10px !important;
    }

    div[data-testid="stDataFrame"]::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #1976d2 0%, #0d47a1 100%) !important;
        border-radius: 10px !important;
        border: 2px solid #f1f3f4 !important;
    }

    div[data-testid="stDataFrame"]::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #0d47a1 0%, #01579b 100%) !important;
    }

    /* ================================================
       TABELA ESTÁTICA (st.table)
       ================================================ */
    div[data-testid="stTable"] {
        border: 2px solid #e0e0e0 !important;
        border-radius: 10px !important;
        padding: 15px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
        background-color: #ffffff !important;
    }

    div[data-testid="stTable"] thead tr th {
        background: linear-gradient(135deg, #3498db 0%, #2980b9 100%) !important;
        color: white !important;
        font-weight: 700 !important;
        padding: 14px !important;
        text-align: center !important;
        border-bottom: 3px solid #2980b9 !important;
        text-transform: uppercase !important;
        font-size: 13px !important;
    }

    div[data-testid="stTable"] tbody td {
        padding: 12px !important;
        text-align: center !important;
        border-bottom: 1px solid #ecf0f1 !important;
        font-size: 13px !important;
    }

    div[data-testid="stTable"] tbody tr:hover {
        background-color: #ebf5fb !important;
        transition: background-color 0.2s ease !important;
    }

    /* ================================================
       RESPONSIVIDADE
       ================================================ */
    @media (max-width: 768px) {
        div[data-testid="stDataFrame"] thead tr th,
        div[data-testid="stDataFrame"] tbody td {
            font-size: 11px !important;
            padding: 10px 6px !important;
        }
        
        .main-header {
            font-size: 2rem !important;
            padding: 15px !important;
        }
        
        .sub-header {
            font-size: 1.4rem !important;
        }
    }
    
    /* ================================================
       MELHORIAS ADICIONAIS
       ================================================ */
    
    /* Destacar células com valores negativos em vermelho */
    div[data-testid="stDataFrame"] tbody td[data-negative="true"] {
        color: #c62828 !important;
        font-weight: 600 !important;
    }
    
    /* Destacar células com valores positivos em verde */
    div[data-testid="stDataFrame"] tbody td[data-positive="true"] {
        color: #2e7d32 !important;
        font-weight: 600 !important;
    }
    
    /* Animação suave para tabelas */
    div[data-testid="stDataFrame"] {
        animation: fadeIn 0.5s ease-in !important;
    }
    
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 4. CONFIGURAÇÃO DE CONEXÃO IMPALA
# =============================================================================

IMPALA_HOST = 'bdaworkernode02.sef.sc.gov.br'
IMPALA_PORT = 21050
DATABASE = 'teste'

# Credenciais
IMPALA_USER = st.secrets.get("impala_credentials", {}).get("user", "tsevero")
IMPALA_PASSWORD = st.secrets.get("impala_credentials", {}).get("password", "")

@st.cache_resource
def get_impala_engine():
    """Cria engine de conexão Impala."""
    try:
        engine = create_engine(
            f'impala://{IMPALA_HOST}:{IMPALA_PORT}/{DATABASE}',
            connect_args={
                'user': IMPALA_USER,
                'password': IMPALA_PASSWORD,
                'auth_mechanism': 'LDAP',
                'use_ssl': True
            }
        )
        return engine
    except Exception as e:
        st.sidebar.error(f"❌ Erro na conexão: {str(e)[:100]}")
        return None

# =============================================================================
# 5. FUNÇÕES DE CARREGAMENTO DE DADOS (ESTRATÉGIA HÍBRIDA)
# =============================================================================

@st.cache_data(ttl=3600)
def carregar_dados_sistema(_engine):
    """Carrega dados agregados do sistema - ESTRATÉGIA RÁPIDA."""
    dados = {}
    
    if _engine is None:
        return {}
    
    # Testar conexão
    try:
        with _engine.connect() as conn:
            st.sidebar.success("✅ Conexão Impala OK!")
    except Exception as e:
        st.sidebar.error(f"❌ Falha na conexão: {str(e)[:100]}")
        return {}
    
    # Configuração de tabelas
    tabelas_config = {
        # ========== DASHBOARD EXECUTIVO (AGREGADO) ==========
        'dashboard_executivo': {
            'query': f"SELECT * FROM {DATABASE}.fisca_dashboard_executivo ORDER BY ano DESC",
            'tipo': 'completo'
        },
        
        # ========== ANÁLISE DE ESTADOS ==========
        'analise_estados': {
            'query': f"""
                SELECT 
                    estado_documento,
                    status_normalizado,
                    eh_valida,
                    eh_regularizada_sem_nf,
                    COUNT(*) AS qtd,
                    SUM(gerou_notificacao) AS com_nf,
                    SUM(valor_total) AS valor_total,
                    ROUND(AVG(valor_total), 2) AS valor_medio
                FROM {DATABASE}.fisca_infracoes_base
                WHERE ano_infracao >= 2020
                GROUP BY estado_documento, status_normalizado, eh_valida, eh_regularizada_sem_nf
                ORDER BY qtd DESC
            """,
            'tipo': 'completo'
        },
        
        # ========== RESUMO DE CONVERSÕES POR ANO ==========
        'resumo_conversoes': {
            'query': f"""
                SELECT 
                    ano_infracao AS ano,
                    COUNT(*) AS total_infracoes,
                    SUM(eh_valida) AS infracoes_validas,
                    SUM(CASE WHEN eh_valida = 0 THEN 1 ELSE 0 END) AS canceladas,
                    SUM(CASE WHEN eh_valida = 1 AND gerou_notificacao = 1 THEN 1 ELSE 0 END) AS com_nf,
                    SUM(eh_regularizada_sem_nf) AS regularizadas_sem_nf,
                    ROUND(
                        SUM(CASE WHEN eh_valida = 1 AND gerou_notificacao = 1 THEN 1 ELSE 0 END) * 100.0 
                        / NULLIF(SUM(eh_valida), 0),
                        2
                    ) AS taxa_conversao_formal,
                    ROUND(
                        (SUM(CASE WHEN eh_valida = 1 AND gerou_notificacao = 1 THEN 1 ELSE 0 END) 
                         + SUM(eh_regularizada_sem_nf)) * 100.0 
                        / NULLIF(SUM(eh_valida), 0),
                        2
                    ) AS taxa_efetividade_fiscal
                FROM {DATABASE}.fisca_infracoes_base
                WHERE ano_infracao >= 2020
                GROUP BY ano_infracao
                ORDER BY ano_infracao DESC
            """,
            'tipo': 'completo'
        },
        
        # ========== MÉTRICAS POR GERÊNCIA (AGREGADO) ==========
        'metricas_gerencia': {
            'query': f"SELECT * FROM {DATABASE}.fisca_metricas_por_gerencia ORDER BY ano DESC, qtd_fiscalizacoes DESC",
            'tipo': 'completo'
        },
        
        # ========== MÉTRICAS POR GES (NOVO) ==========
        'metricas_ges': {
            'query': f"""
                SELECT * FROM {DATABASE}.fisca_metricas_por_ges 
                ORDER BY ano DESC, qtd_fiscalizacoes DESC
            """,
            'tipo': 'completo'
        },
        
        # ========== DISTRIBUIÇÃO DE EMPRESAS POR GES (NOVO) ==========
        'distribuicao_empresas_ges': {
            'query': f"""
                SELECT 
                    nm_ges,
                    COUNT(*) AS qtd_empresas,
                    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) AS percentual
                FROM {DATABASE}.fisca_empresas_base
                WHERE nm_ges IS NOT NULL
                    AND nm_ges LIKE 'GES%'
                GROUP BY nm_ges
                ORDER BY qtd_empresas DESC
            """,
            'tipo': 'completo'
        },
        
        # ========== MÉTRICAS POR CNAE (AGREGADO) ==========
        'metricas_cnae': {
            'query': f"SELECT * FROM {DATABASE}.fisca_metricas_por_cnae ORDER BY ano DESC, qtd_fiscalizacoes DESC LIMIT 500",
            'tipo': 'completo'
        },
        
        # ========== MÉTRICAS POR MUNICÍPIO (AGREGADO) ==========
        'metricas_municipio': {
            'query': f"SELECT * FROM {DATABASE}.fisca_metricas_por_municipio ORDER BY ano DESC, qtd_fiscalizacoes DESC LIMIT 500",
            'tipo': 'completo'
        },
        
        # ========== RANKING DE INFRAÇÕES (CORRIGIDO - SEM FILTROS) ==========
        'ranking_infracoes': {
            'query': f"""
                SELECT * FROM {DATABASE}.fisca_ranking_infracoes 
                ORDER BY ano DESC, qtd_ocorrencias DESC
            """,
            'tipo': 'completo'
        },
        
        # ========== MÉTRICAS POR AFRE (AGREGADO) ==========
        'metricas_afre': {
            'query': f"""
                SELECT * FROM {DATABASE}.fisca_metricas_por_afre 
                WHERE ano >= YEAR(CURRENT_DATE()) - 3
                ORDER BY ano DESC, qtd_nfs DESC
            """,
            'tipo': 'completo'
        },
        
        # ========== CADASTRO DE AFRES ==========
        'cadastro_afres': {
            'query': f"SELECT * FROM {DATABASE}.fisca_afres_cadastro",
            'tipo': 'completo'
        },
        
        # ========== CATÁLOGO DE INFRAÇÕES ==========
        'catalogo_infracoes': {
            'query': f"SELECT * FROM {DATABASE}.fisca_catalogo_infracoes",
            'tipo': 'completo'
        },
        
        # ========== EMPRESAS BASE - RESUMO (apenas CNPJs para seleção) ==========
        'empresas_resumo': {
            'query': f"""
                SELECT DISTINCT cnpj, nm_razao_social, municipio, regime_tributario
                FROM {DATABASE}.fisca_empresas_base
                ORDER BY nm_razao_social
                LIMIT 10000
            """,
            'tipo': 'resumo'
        },
        
        # ========== SCORES DE EFETIVIDADE - RESUMO ==========
        'scores_resumo': {
            'query': f"""
                SELECT 
                    classificacao_efetividade,
                    COUNT(*) as qtd,
                    ROUND(AVG(score_efetividade_final), 2) as score_medio,
                    ROUND(AVG(valor_total_infracao), 2) as valor_medio
                FROM {DATABASE}.fisca_scores_efetividade
                GROUP BY classificacao_efetividade
            """,
            'tipo': 'agregacao'
        },
        
        # ========== FISCALIZAÇÕES CONSOLIDADAS - APENAS ESTATÍSTICAS ==========
        'fiscalizacoes_stats': {
            'query': f"""
                SELECT 
                    COUNT(DISTINCT id_documento) as total_fiscalizacoes,
                    COUNT(DISTINCT identificador) as total_empresas,
                    SUM(gerou_notificacao) as total_nfs,
                    SUM(CASE WHEN gerou_notificacao = 1 THEN 1 ELSE 0 END) as fiscalizacoes_com_nf,
                    SUM(ciclo_completo) as total_ciclos_completos,
                    ROUND(AVG(valor_total_infracao), 2) as valor_medio_infracao,
                    ROUND(AVG(dias_infracao_ate_nf), 0) as media_dias_ate_nf,
                    SUM(eh_valida) as fiscalizacoes_validas,
                    SUM(CASE WHEN eh_valida = 0 THEN 1 ELSE 0 END) as fiscalizacoes_canceladas,
                    SUM(eh_regularizada_sem_nf) as fiscalizacoes_regularizadas_sem_nf
                FROM {DATABASE}.fisca_fiscalizacoes_consolidadas
            """,
            'tipo': 'agregacao'
        }
    }
    
    progress_bar = st.sidebar.progress(0)
    status_text = st.sidebar.empty()
    
    total = len(tabelas_config)
    
    for idx, (key, config) in enumerate(tabelas_config.items()):
        try:
            query = config['query']
            tipo = config['tipo']
            
            status_text.text(f"📥 Carregando {key} ({tipo})...")
            progress_bar.progress((idx + 1) / total)
            
            # Executar query
            df = pd.read_sql(query, _engine)
            df.columns = [col.lower() for col in df.columns]
            
            # Converter tipos numéricos
            for col in df.select_dtypes(include=['object']).columns:
                try:
                    df[col] = pd.to_numeric(df[col], errors='ignore')
                except:
                    pass
            
            dados[key] = df
            
            # Log do tamanho carregado
            mem_mb = df.memory_usage(deep=True).sum() / 1024 / 1024
            status_text.text(f"✅ {key}: {len(df):,} registros ({mem_mb:.1f} MB)")
            
        except Exception as e:
            st.sidebar.warning(f"⚠️ Erro em {key}: {str(e)[:80]}")
            dados[key] = pd.DataFrame()
    
    progress_bar.empty()
    status_text.empty()
    
    # Resumo do carregamento
    total_registros = sum(len(df) for df in dados.values() if not df.empty)
    total_mem = sum(df.memory_usage(deep=True).sum() / 1024 / 1024 for df in dados.values() if not df.empty)
    
    st.sidebar.success(f"✅ {total_registros:,} registros ({total_mem:.1f} MB)")
    
    return dados

# =============================================================================
# 6. FUNÇÕES DE CARREGAMENTO SOB DEMANDA
# =============================================================================

@st.cache_data(ttl=1800)
def carregar_empresa_detalhada(_engine, cnpj):
    """Carrega dados completos de uma empresa específica - SOB DEMANDA."""
    try:
        query = f"""
            SELECT * 
            FROM {DATABASE}.fisca_empresas_base
            WHERE cnpj = '{cnpj}'
        """
        df = pd.read_sql(query, _engine)
        df.columns = [col.lower() for col in df.columns]
        return df
    except Exception as e:
        st.error(f"Erro ao carregar empresa: {str(e)[:100]}")
        return pd.DataFrame()

@st.cache_data(ttl=1800)
def carregar_fiscalizacoes_empresa(_engine, cnpj):
    """Carrega fiscalizações de uma empresa - SOB DEMANDA."""
    try:
        query = f"""
            SELECT * 
            FROM {DATABASE}.fisca_fiscalizacoes_consolidadas
            WHERE cnpj = '{cnpj}'
            ORDER BY data_infracao DESC
        """
        df = pd.read_sql(query, _engine)
        df.columns = [col.lower() for col in df.columns]
        return df
    except Exception as e:
        st.error(f"Erro ao carregar fiscalizações: {str(e)[:100]}")
        return pd.DataFrame()

@st.cache_data(ttl=1800)
def carregar_afres_fiscalizacao(_engine, id_documento):
    """Carrega AFREs de uma fiscalização - SOB DEMANDA."""
    try:
        query = f"""
            SELECT apd.*, ac.nome_afre, ac.cargo
            FROM {DATABASE}.fisca_afres_por_documento apd
            LEFT JOIN {DATABASE}.fisca_afres_cadastro ac
                ON apd.matricula_afre = ac.matricula_afre
            WHERE apd.id_documento = '{id_documento}'
            ORDER BY apd.percentual_participacao DESC
        """
        df = pd.read_sql(query, _engine)
        df.columns = [col.lower() for col in df.columns]
        return df
    except Exception as e:
        st.error(f"Erro ao carregar AFREs: {str(e)[:100]}")
        return pd.DataFrame()

@st.cache_data(ttl=1800)
def carregar_scores_efetividade(_engine, limit=1000):
    """Carrega scores de efetividade - SOB DEMANDA."""
    try:
        query = f"""
            SELECT * 
            FROM {DATABASE}.fisca_scores_efetividade
            ORDER BY score_efetividade_final DESC
            LIMIT {limit}
        """
        df = pd.read_sql(query, _engine)
        df.columns = [col.lower() for col in df.columns]
        return df
    except Exception as e:
        st.error(f"Erro ao carregar scores: {str(e)[:100]}")
        return pd.DataFrame()

@st.cache_data(ttl=1800)
def carregar_dataset_ml(_engine):
    """Carrega dataset completo para Machine Learning - SOB DEMANDA."""
    try:
        query = f"""
            SELECT 
                fc.*,
                se.score_efetividade_final,
                se.classificacao_efetividade,
                eb.regime_tributario,
                eb.cnae_secao,
                eb.cnae_divisao
            FROM {DATABASE}.fisca_fiscalizacoes_consolidadas fc
            LEFT JOIN {DATABASE}.fisca_scores_efetividade se
                ON fc.id_documento = se.id_documento
            LEFT JOIN {DATABASE}.fisca_empresas_base eb
                ON fc.cnpj = eb.cnpj
            WHERE fc.ano_infracao >= YEAR(CURRENT_DATE()) - 3
        """
        df = pd.read_sql(query, _engine)
        df.columns = [col.lower() for col in df.columns]
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dataset ML: {str(e)[:100]}")
        return pd.DataFrame()

# =============================================================================
# 6.1. FUNÇÕES DE CARREGAMENTO - ITCMD
# =============================================================================

# Coordenadores ITCMD
COORDENADORES_ITCMD = ['9507248', '6172598']

@st.cache_data(ttl=1800)
def carregar_dados_itcmd(_engine):
    """Carrega dados das OFs do setor ITCMD - filtrado por coordenadores específicos."""
    dados_itcmd = {}

    if _engine is None:
        return {}

    try:
        # 1. Ordens de Fiscalização (filtradas pelos coordenadores ITCMD)
        query_of = f"""
            SELECT
                id_documento,
                numero_documento,
                nu_of,
                dt_documento,
                data_emissao,
                nm_estado,
                situacao,
                cd_usuario_emitente,
                tx_recomendacoes,
                dt_inicio,
                dt_fim,
                tx_motivacao_of,
                nm_local_execucao,
                nm_gerencia,
                nm_local_emissao,
                nu_mat_emitente,
                nu_mat_coordenador,
                nm_origem,
                dt_alteracao_ods,
                cd_ges,
                nm_ges,
                YEAR(dt_documento) as ano
            FROM usr_sat_ods.fis_of_raw
            WHERE cd_usuario_emitente IN ('9507248', '6172598')
            ORDER BY dt_documento DESC
        """
        df_of = pd.read_sql(query_of, _engine)
        df_of.columns = [col.lower() for col in df_of.columns]
        dados_itcmd['of_itcmd'] = df_of

        # Obter lista de nu_of para filtrar as outras tabelas
        if not df_of.empty:
            lista_ofs = df_of['nu_of'].dropna().unique().tolist()
            lista_ofs_str = "', '".join([str(x) for x in lista_ofs])

            # 2. Declarações (DDE) vinculadas às OFs do ITCMD
            query_dde = f"""
                SELECT
                    nu_declaracao,
                    nu_of,
                    nu_ie,
                    nm_razao_social,
                    cd_ges,
                    cd_gerfe,
                    cd_munic,
                    cd_motivo,
                    cd_estado_conta,
                    dt_entrega,
                    vl_declarado,
                    vl_data_declaracao,
                    vl_total_saldo,
                    vl_pago,
                    vl_parc_pago,
                    vl_parc_saldo,
                    vl_dva_total,
                    vl_dva_saldo,
                    vl_dva_pago,
                    dt_ultima_atualizacao,
                    YEAR(dt_entrega) as ano
                FROM usr_sat_ods.fis_of_em_numeros_dde
                WHERE nu_of IN ('{lista_ofs_str}')
                ORDER BY dt_entrega DESC
            """
            df_dde = pd.read_sql(query_dde, _engine)
            df_dde.columns = [col.lower() for col in df_dde.columns]
            dados_itcmd['dde_itcmd'] = df_dde

            # 3. Notificações Fiscais vinculadas às OFs do ITCMD
            query_notif = f"""
                SELECT
                    nu_notificacao_fiscal,
                    nu_of,
                    nu_ie,
                    nu_cpf,
                    nu_cnpj,
                    nm_razao_social,
                    cd_gerfe,
                    cd_ges,
                    cd_munic,
                    cd_infracao,
                    cd_edo_det_conta,
                    nm_estado,
                    dt_documento,
                    vl_total,
                    vl_pago,
                    vl_parc_pago,
                    vl_parc_saldo,
                    vl_recl_tot,
                    vl_dva_total,
                    vl_dva_saldo,
                    vl_dva_pago,
                    dt_ultima_atualizacao,
                    dt_ciencia,
                    YEAR(dt_documento) as ano
                FROM usr_sat_ods.fis_of_em_numeros_notif
                WHERE nu_of IN ('{lista_ofs_str}')
                ORDER BY dt_documento DESC
            """
            df_notif = pd.read_sql(query_notif, _engine)
            df_notif.columns = [col.lower() for col in df_notif.columns]
            dados_itcmd['notif_itcmd'] = df_notif

            # 4. Termos de Infração (TIFDP) vinculados às OFs do ITCMD
            query_tifdp = f"""
                SELECT
                    nu_infr_fiscal,
                    nu_notificacao_gerada,
                    nu_of,
                    nu_ie,
                    nu_cpf,
                    nu_cnpj,
                    nm_razao_social,
                    cd_ges,
                    cd_gerfe,
                    cd_munic,
                    cd_infracao,
                    nm_estado,
                    dt_documento,
                    vl_apurado,
                    vl_pago,
                    vl_parc_pago,
                    vl_parc_saldo,
                    vl_convertido_notif,
                    vl_cancelado,
                    vl_dva_total,
                    vl_dva_saldo,
                    vl_dva_pago,
                    dt_ultima_atualizacao,
                    dt_ciencia,
                    YEAR(dt_documento) as ano
                FROM usr_sat_ods.fis_of_em_numeros_tifdp
                WHERE nu_of IN ('{lista_ofs_str}')
                ORDER BY dt_documento DESC
            """
            df_tifdp = pd.read_sql(query_tifdp, _engine)
            df_tifdp.columns = [col.lower() for col in df_tifdp.columns]
            dados_itcmd['tifdp_itcmd'] = df_tifdp

            # 5. Catálogo de Infrações (para enriquecer com descrições)
            query_infracoes = """
                SELECT
                    cd_infracao,
                    de_infracao,
                    nm_tributo,
                    vl_multa
                FROM usr_sat_ods.fis_tabela_infracoes
            """
            df_infracoes = pd.read_sql(query_infracoes, _engine)
            df_infracoes.columns = [col.lower() for col in df_infracoes.columns]
            dados_itcmd['catalogo_infracoes'] = df_infracoes

            # 6. AFREs por Período (para análise de performance)
            lista_matriculas = df_of['nu_mat_emitente'].dropna().unique().tolist()
            lista_coord = df_of['nu_mat_coordenador'].dropna().unique().tolist()
            todas_matriculas = list(set([str(m).strip() for m in lista_matriculas + lista_coord if m]))

            if todas_matriculas:
                matriculas_str = "', '".join(todas_matriculas)
                query_afre = f"""
                    SELECT
                        cd_matricula,
                        nu_ano_ref,
                        nu_per_ref,
                        qt_dias_ativa
                    FROM usr_sat_ods.fis_afre_periodo
                    WHERE CAST(cd_matricula AS STRING) IN ('{matriculas_str}')
                """
                try:
                    df_afre = pd.read_sql(query_afre, _engine)
                    df_afre.columns = [col.lower() for col in df_afre.columns]
                    dados_itcmd['afre_periodo'] = df_afre
                except:
                    dados_itcmd['afre_periodo'] = pd.DataFrame()
            else:
                dados_itcmd['afre_periodo'] = pd.DataFrame()

            # 7. Dados dos Contribuintes (para perfil CNAE/regime)
            lista_ies = set()
            if not df_dde.empty and 'nu_ie' in df_dde.columns:
                lista_ies.update(df_dde['nu_ie'].dropna().unique())
            if not df_notif.empty and 'nu_ie' in df_notif.columns:
                lista_ies.update(df_notif['nu_ie'].dropna().unique())
            if not df_tifdp.empty and 'nu_ie' in df_tifdp.columns:
                lista_ies.update(df_tifdp['nu_ie'].dropna().unique())

            if lista_ies:
                ies_str = "', '".join([str(ie) for ie in lista_ies])
                query_contrib = f"""
                    SELECT DISTINCT
                        nu_ie,
                        nu_cnpj,
                        nm_razao_social,
                        cd_cnae,
                        de_cnae,
                        de_secao,
                        nm_enq_empresa,
                        nm_munic
                    FROM usr_sat_ods.vw_ods_contrib
                    WHERE nu_ie IN ('{ies_str}')
                """
                try:
                    df_contrib = pd.read_sql(query_contrib, _engine)
                    df_contrib.columns = [col.lower() for col in df_contrib.columns]
                    dados_itcmd['contribuintes'] = df_contrib
                except:
                    dados_itcmd['contribuintes'] = pd.DataFrame()
            else:
                dados_itcmd['contribuintes'] = pd.DataFrame()

            # 8. Acompanhamentos (Follow-ups)
            query_acomp = f"""
                SELECT
                    id_documento_os,
                    nu_documento_of,
                    nm_estado_os,
                    dt_documento_os,
                    de_motivo_os
                FROM usr_sat_ods.fis_acomp_raw
                WHERE nu_documento_of IN ('{lista_ofs_str}')
                ORDER BY dt_documento_os DESC
            """
            try:
                df_acomp = pd.read_sql(query_acomp, _engine)
                df_acomp.columns = [col.lower() for col in df_acomp.columns]
                dados_itcmd['acompanhamentos'] = df_acomp
            except:
                dados_itcmd['acompanhamentos'] = pd.DataFrame()

            # 9. Termos de Encerramento
            query_termo = f"""
                SELECT
                    nu_termo_encerramento,
                    os,
                    nm_estado,
                    dt_documento,
                    dt_encerramento
                FROM usr_sat_ods.fis_termo_encerram_fisc_raw
                WHERE os IN ('{lista_ofs_str}')
                ORDER BY dt_documento DESC
            """
            try:
                df_termo = pd.read_sql(query_termo, _engine)
                df_termo.columns = [col.lower() for col in df_termo.columns]
                dados_itcmd['termos_encerramento'] = df_termo
            except:
                dados_itcmd['termos_encerramento'] = pd.DataFrame()

        else:
            dados_itcmd['dde_itcmd'] = pd.DataFrame()
            dados_itcmd['notif_itcmd'] = pd.DataFrame()
            dados_itcmd['tifdp_itcmd'] = pd.DataFrame()
            dados_itcmd['catalogo_infracoes'] = pd.DataFrame()
            dados_itcmd['afre_periodo'] = pd.DataFrame()
            dados_itcmd['contribuintes'] = pd.DataFrame()
            dados_itcmd['acompanhamentos'] = pd.DataFrame()
            dados_itcmd['termos_encerramento'] = pd.DataFrame()

        return dados_itcmd

    except Exception as e:
        st.error(f"Erro ao carregar dados ITCMD: {str(e)[:150]}")
        return {}

# =============================================================================
# 7. FUNÇÕES AUXILIARES DE VISUALIZAÇÃO
# =============================================================================

def criar_card_metrica(label: str, valor, icone: str = "📊", cor: str = "#1976d2"):
    """Cria um card de métrica colorido."""
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, {cor} 0%, {cor}dd 100%); 
                padding: 1.5rem; border-radius: 10px; color: white; 
                box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin: 10px 0;'>
        <div style='font-size: 2rem; margin-bottom: 0.5rem;'>{icone}</div>
        <div style='font-size: 0.9rem; opacity: 0.9;'>{label}</div>
        <div style='font-size: 2.5rem; font-weight: bold;'>{valor}</div>
    </div>
    """, unsafe_allow_html=True)

def formatar_valor(valor):
    """Formata valores monetários."""
    if pd.isna(valor) or valor == 0:
        return "R$ 0,00"
    
    if valor >= 1_000_000_000:
        return f"R$ {valor/1_000_000_000:.2f}B"
    elif valor >= 1_000_000:
        return f"R$ {valor/1_000_000:.2f}M"
    elif valor >= 1_000:
        return f"R$ {valor/1_000:.2f}K"
    else:
        return f"R$ {valor:,.2f}"

def criar_filtros_sidebar(dados):
    """Cria painel de filtros na sidebar."""
    filtros = {}
    
    with st.sidebar.expander("🔍 Filtros Globais", expanded=True):
        
        # Ano
        df_dash = dados.get('dashboard_executivo', pd.DataFrame())
        if not df_dash.empty and 'ano' in df_dash.columns:
            anos = sorted(df_dash['ano'].unique(), reverse=True)
            filtros['anos'] = st.multiselect(
                "Anos",
                anos,
                default=anos[:3] if len(anos) >= 3 else anos
            )
        
        # Gerência
        df_gerencia = dados.get('metricas_gerencia', pd.DataFrame())
        if not df_gerencia.empty and 'gerfe' in df_gerencia.columns:
            gerencias = sorted(df_gerencia['gerfe'].dropna().unique())
            filtros['gerencias'] = st.multiselect(
                "Gerências (GRAF)",
                gerencias,
                default=[]
            )
        
        # Valor mínimo
        filtros['valor_minimo'] = st.number_input(
            "Valor Mínimo (R$)",
            min_value=0,
            max_value=10000000,
            value=0,
            step=100000
        )
        
        st.divider()
        
        # Visualização
        st.subheader("🎨 Visualização")
        filtros['tema'] = st.selectbox(
            "Tema dos Gráficos",
            ["plotly", "plotly_white", "plotly_dark"],
            index=1
        )
        
        filtros['mostrar_valores'] = st.checkbox("Mostrar valores", value=True)
    
    return filtros

# =============================================================================
# 8. PÁGINAS DO DASHBOARD
# =============================================================================

def pagina_dashboard_executivo(dados, filtros):
    """Dashboard executivo principal."""
    st.markdown("<h1 class='main-header'>📊 Dashboard Executivo - Sistema FISCA</h1>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class='info-box'>
    <b>🎯 Sistema de Análise de Fiscalizações</b><br>
    Monitoramento completo das ações fiscais da Receita Estadual de SC, incluindo infrações, 
    notificações fiscais, encerramentos e análise de efetividade.
    <br><br>
    ✅ <b>Dados corrigidos:</b> Excluindo 1,541 infrações canceladas/excluídas das métricas
    </div>
    """, unsafe_allow_html=True)
    
    df_dash = dados.get('dashboard_executivo', pd.DataFrame())
    df_resumo = dados.get('resumo_conversoes', pd.DataFrame())
    
    if df_dash.empty:
        st.warning("Dados do dashboard não disponíveis.")
        return
    
    # Filtrar por anos selecionados
    if filtros.get('anos'):
        df_dash = df_dash[df_dash['ano'].isin(filtros['anos'])]
        if not df_resumo.empty:
            df_resumo = df_resumo[df_resumo['ano'].isin(filtros['anos'])]
    
    if df_dash.empty:
        st.warning("⚠️ Nenhum dado encontrado com os filtros aplicados.")
        return
    
    # ========== ALERTA DE CORREÇÃO ==========
    if not df_dash.empty and 'qtd_canceladas' in df_dash.columns:
        total_canceladas = df_dash['qtd_canceladas'].sum()
        if total_canceladas > 0:
            st.markdown(f"""
            <div class='alert-positivo'>
            <b>✅ MÉTRICAS CORRIGIDAS:</b><br>
            • {int(total_canceladas):,} infrações canceladas/excluídas foram <b>excluídas</b> das métricas<br>
            • Taxa de conversão calculada apenas sobre infrações <b>válidas</b><br>
            • Regularizações sem NF (parcelamentos/quitações) disponíveis em métrica separada
            </div>
            """, unsafe_allow_html=True)
    
    # ========== KPIs PRINCIPAIS ==========
    st.markdown("<div class='sub-header'>📈 Indicadores Gerais (Infrações Válidas)</div>", unsafe_allow_html=True)
    
    # Primeira linha
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_fisc = df_dash['qtd_infracoes_lavradas'].sum()
        st.metric("📋 Infrações Válidas", f"{int(total_fisc):,}")
    
    with col2:
        total_empresas = df_dash['empresas_fiscalizadas'].sum()
        st.metric("🏢 Empresas", f"{int(total_empresas):,}")
    
    with col3:
        total_nfs = df_dash['qtd_nfs_emitidas'].sum()
        st.metric("📄 NFs Emitidas", f"{int(total_nfs):,}")
    
    with col4:
        valor_total_infr = df_dash['valor_total_infracoes'].sum()
        st.metric("💰 Valor Infrações", formatar_valor(valor_total_infr))
    
    with col5:
        valor_total_nfs = df_dash['valor_total_nfs'].sum()
        st.metric("💵 Valor NFs", formatar_valor(valor_total_nfs))
    
    # Segunda linha - ATUALIZADA
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        taxa_conversao = (total_nfs / total_fisc * 100) if total_fisc > 0 else 0
        st.metric("📊 Taxa Conversão", f"{taxa_conversao:.2f}%",
                 delta="Apenas NFs", delta_color="normal")
    
    with col2:
        # ✅ NOVO: Regularizações
        if 'qtd_regularizadas_sem_nf' in df_dash.columns:
            regularizadas = df_dash['qtd_regularizadas_sem_nf'].sum()
            st.metric("🔄 Regularizadas", f"{int(regularizadas):,}",
                     delta="Sem NF formal")
        else:
            st.metric("🔄 Regularizadas", "N/A")
    
    with col3:
        # ✅ NOVO: Taxa ampliada
        if 'taxa_efetividade_fiscal' in df_dash.columns:
            taxa_ampliada = df_dash['taxa_efetividade_fiscal'].mean()
            st.metric("📈 Efetividade Fiscal", f"{taxa_ampliada:.2f}%",
                     delta="NFs + Regularizações", delta_color="normal")
        else:
            st.metric("📈 Efetividade Fiscal", "N/A")
    
    with col4:
        media_dias = df_dash['media_dias_infracao_nf'].mean()
        st.metric("⏱️ Dias Médios (NF)", f"{media_dias:.0f}")
    
    with col5:
        afres_ativos = df_dash['qtd_afres_ativos'].iloc[-1] if 'qtd_afres_ativos' in df_dash.columns else 0
        st.metric("👥 AFREs Ativos", f"{int(afres_ativos)}")
    
    st.divider()
    
    # ========== COMPARAÇÃO: CONVERSÃO FORMAL vs EFETIVIDADE ==========
    if not df_resumo.empty:
        st.markdown("<div class='sub-header'>📊 Comparação: Taxa de Conversão vs Efetividade Fiscal</div>", unsafe_allow_html=True)
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=df_resumo['ano'],
            y=df_resumo['com_nf'],
            name='NFs Emitidas',
            marker_color='#1976d2',
            text=df_resumo['com_nf'],
            textposition='auto'
        ))
        
        fig.add_trace(go.Bar(
            x=df_resumo['ano'],
            y=df_resumo['regularizadas_sem_nf'],
            name='Regularizadas sem NF',
            marker_color='#388e3c',
            text=df_resumo['regularizadas_sem_nf'],
            textposition='auto'
        ))
        
        fig.update_layout(
            title='Volume: NFs vs Regularizações sem NF',
            template=filtros['tema'],
            height=400,
            barmode='stack',
            xaxis_title='Ano',
            yaxis_title='Quantidade'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # ========== EVOLUÇÃO TEMPORAL ==========
    st.markdown("<div class='sub-header'>📈 Evolução Temporal</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=df_dash['ano'],
            y=df_dash['qtd_infracoes_lavradas'],
            name='Infrações Válidas',
            marker_color='#1976d2'
        ))
        
        fig.add_trace(go.Bar(
            x=df_dash['ano'],
            y=df_dash['qtd_nfs_emitidas'],
            name='NFs',
            marker_color='#388e3c'
        ))
        
        fig.update_layout(
            title='Volume de Infrações e NFs por Ano',
            template=filtros['tema'],
            height=400,
            xaxis_title='Ano',
            yaxis_title='Quantidade',
            barmode='group'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df_dash['ano'],
            y=df_dash['valor_total_infracoes'],
            name='Valor Infrações',
            mode='lines+markers',
            line=dict(color='#d32f2f', width=3),
            marker=dict(size=10)
        ))
        
        fig.add_trace(go.Scatter(
            x=df_dash['ano'],
            y=df_dash['valor_total_nfs'],
            name='Valor NFs',
            mode='lines+markers',
            line=dict(color='#388e3c', width=3),
            marker=dict(size=10)
        ))
        
        fig.update_layout(
            title='Evolução dos Valores por Ano',
            template=filtros['tema'],
            height=400,
            xaxis_title='Ano',
            yaxis_title='Valor (R$)',
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # ========== TAXA DE CONVERSÃO ==========
    col1, col2 = st.columns(2)
    
    with col1:
        if not df_resumo.empty:
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=df_resumo['ano'],
                y=df_resumo['taxa_conversao_formal'],
                name='Taxa Formal (apenas NFs)',
                mode='lines+markers',
                line=dict(color='#1976d2', width=3),
                marker=dict(size=10)
            ))
            
            fig.add_trace(go.Scatter(
                x=df_resumo['ano'],
                y=df_resumo['taxa_efetividade_fiscal'],
                name='Efetividade (NFs + Regularizações)',
                mode='lines+markers',
                line=dict(color='#388e3c', width=3),
                marker=dict(size=10)
            ))
            
            fig.add_hline(y=70, line_dash="dash", line_color="gray", 
                         annotation_text="Meta: 70%")
            
            fig.update_layout(
                title='Evolução das Taxas de Conversão',
                template=filtros['tema'],
                height=400,
                yaxis_title='Taxa (%)',
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if 'media_infracoes_por_afre' in df_dash.columns:
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=df_dash['ano'],
                y=df_dash['media_infracoes_por_afre'],
                name='Infrações/AFRE',
                mode='lines+markers',
                line=dict(color='#1976d2', width=3)
            ))
            
            fig.update_layout(
                title='Produtividade Média por AFRE',
                template=filtros['tema'],
                height=400,
                xaxis_title='Ano',
                yaxis_title='Infrações/AFRE'
            )
            
            st.plotly_chart(fig, use_container_width=True)

def pagina_analise_gerencias(dados, filtros):
    """Análise por gerência regional (GRAF)."""
    st.markdown("<h1 class='main-header'>🏢 Análise por Gerência Regional</h1>", unsafe_allow_html=True)
    
    df_gerencia = dados.get('metricas_gerencia', pd.DataFrame())
    
    if df_gerencia.empty:
        st.error("Dados de gerências não disponíveis.")
        return
    
    # Filtrar por anos e gerências
    if filtros.get('anos'):
        df_gerencia = df_gerencia[df_gerencia['ano'].isin(filtros['anos'])]
    
    if filtros.get('gerencias'):
        df_gerencia = df_gerencia[df_gerencia['gerfe'].isin(filtros['gerencias'])]
    
    if df_gerencia.empty:
        st.warning("⚠️ Nenhum dado encontrado com os filtros aplicados.")
        return
    
    # ========== RESUMO POR GERÊNCIA ==========
    st.markdown("<div class='sub-header'>📊 Performance Consolidada</div>", unsafe_allow_html=True)
    
    # Agregar por gerência
    df_resumo = df_gerencia.groupby('gerfe').agg({
        'qtd_fiscalizacoes': 'sum',
        'qtd_empresas_unicas': 'sum',
        'qtd_infracoes': 'sum',
        'qtd_nfs': 'sum',
        'valor_total_infracoes': 'sum',
        'valor_total_lancado': 'sum',
        'media_dias_infracao_nf': 'mean'
    }).reset_index()
    
    df_resumo['taxa_conversao'] = (df_resumo['qtd_nfs'] / df_resumo['qtd_infracoes'] * 100).round(2)
    
    # Ranking
    col1, col2 = st.columns(2)
    
    with col1:
        # Top 10 por valor lançado
        df_top = df_resumo.nlargest(10, 'valor_total_lancado')
        
        fig = px.bar(
            df_top,
            y='gerfe',
            x='valor_total_lancado',
            orientation='h',
            title='Top 10 Gerências - Valor Lançado',
            template=filtros['tema'],
            color='valor_total_lancado',
            color_continuous_scale='Blues'
        )
        
        fig.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            height=500,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Taxa de conversão
        fig = px.scatter(
            df_resumo,
            x='qtd_fiscalizacoes',
            y='taxa_conversao',
            size='valor_total_lancado',
            color='gerfe',
            title='Taxa de Conversão vs Volume',
            template=filtros['tema'],
            hover_data=['gerfe', 'qtd_nfs']
        )
        
        fig.add_hline(y=70, line_dash="dash", line_color="green", annotation_text="Meta: 70%")
        fig.update_layout(height=500, showlegend=False)
        
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # ========== TABELA DETALHADA ==========
    st.markdown("<div class='sub-header'>📋 Ranking Completo</div>", unsafe_allow_html=True)
    
    df_resumo_display = df_resumo.sort_values('valor_total_lancado', ascending=False).copy()
    df_resumo_display['ranking'] = range(1, len(df_resumo_display) + 1)
    
    cols_display = ['ranking', 'gerfe', 'qtd_fiscalizacoes', 'qtd_empresas_unicas', 
                    'qtd_nfs', 'valor_total_lancado', 'taxa_conversao', 'media_dias_infracao_nf']
    
    st.dataframe(
        df_resumo_display[cols_display].style.format({
            'valor_total_lancado': 'R$ {:,.2f}',
            'taxa_conversao': '{:.2f}%',
            'media_dias_infracao_nf': '{:.0f}'
        }).background_gradient(subset=['valor_total_lancado'], cmap='Greens'),
        use_container_width=True,
        height=600
    )

def pagina_analise_cnae(dados, filtros):
    """Análise por setor econômico (CNAE)."""
    st.markdown("<h1 class='main-header'>🏭 Análise por Setor Econômico (CNAE)</h1>", unsafe_allow_html=True)
    
    df_cnae = dados.get('metricas_cnae', pd.DataFrame())
    
    if df_cnae.empty:
        st.error("Dados de CNAE não disponíveis.")
        return
    
    # Filtrar por anos
    if filtros.get('anos'):
        df_cnae = df_cnae[df_cnae['ano'].isin(filtros['anos'])]
    
    if df_cnae.empty:
        st.warning("⚠️ Nenhum dado encontrado com os filtros aplicados.")
        return
    
    # ========== SELEÇÃO DE NÍVEL ==========
    col1, col2 = st.columns([1, 3])
    
    with col1:
        nivel_analise = st.radio(
            "Nível de Análise:",
            ['Seção (Macro)', 'Divisão (Detalhado)'],
            index=0
        )
    
    # Agregar conforme nível
    if nivel_analise == 'Seção (Macro)':
        df_analise = df_cnae.groupby(['cnae_secao', 'cnae_secao_descricao']).agg({
            'qtd_fiscalizacoes': 'sum',
            'qtd_empresas_unicas': 'sum',
            'qtd_nfs': 'sum',
            'valor_total_infracoes': 'sum',
            'valor_total_nfs': 'sum'
        }).reset_index()
        
        df_analise.columns = ['codigo', 'descricao', 'qtd_fiscalizacoes', 'qtd_empresas', 
                              'qtd_nfs', 'valor_infracoes', 'valor_nfs']
    else:
        df_analise = df_cnae.groupby(['cnae_divisao', 'cnae_divisao_descricao']).agg({
            'qtd_fiscalizacoes': 'sum',
            'qtd_empresas_unicas': 'sum',
            'qtd_nfs': 'sum',
            'valor_total_infracoes': 'sum',
            'valor_total_nfs': 'sum'
        }).reset_index()
        
        df_analise.columns = ['codigo', 'descricao', 'qtd_fiscalizacoes', 'qtd_empresas', 
                              'qtd_nfs', 'valor_infracoes', 'valor_nfs']
    
    df_analise['taxa_conversao'] = (df_analise['qtd_nfs'] / df_analise['qtd_fiscalizacoes'] * 100).round(2)
    
    # ========== VISUALIZAÇÕES ==========
    st.markdown("<div class='sub-header'>📊 Distribuição por Setor</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Top 15 setores por valor
        df_top = df_analise.nlargest(15, 'valor_nfs')
        
        fig = px.bar(
            df_top,
            y='descricao',
            x='valor_nfs',
            orientation='h',
            title='Top 15 Setores - Valor Lançado (NFs)',
            template=filtros['tema'],
            color='valor_nfs',
            color_continuous_scale='Viridis'
        )
        
        fig.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            height=600,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Pizza - Distribuição
        df_pizza = df_analise.nlargest(10, 'qtd_fiscalizacoes')
        
        fig = px.pie(
            df_pizza,
            values='qtd_fiscalizacoes',
            names='descricao',
            title='Top 10 Setores - Distribuição do Volume',
            template=filtros['tema'],
            hole=0.4
        )
        
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(height=600)
        
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # ========== TABELA COMPLETA ==========
    st.markdown("<div class='sub-header'>📋 Tabela Detalhada</div>", unsafe_allow_html=True)
    
    df_display = df_analise.sort_values('valor_nfs', ascending=False).copy()
    
    st.dataframe(
        df_display.style.format({
            'valor_infracoes': 'R$ {:,.2f}',
            'valor_nfs': 'R$ {:,.2f}',
            'taxa_conversao': '{:.2f}%'
        }).background_gradient(subset=['valor_nfs'], cmap='Greens'),
        use_container_width=True,
        height=600
    )

def pagina_analise_municipios(dados, filtros):
    """Análise por município."""
    st.markdown("<h1 class='main-header'>🗺️ Análise Geográfica - Municípios</h1>", unsafe_allow_html=True)
    
    df_mun = dados.get('metricas_municipio', pd.DataFrame())
    
    if df_mun.empty:
        st.error("Dados de municípios não disponíveis.")
        return
    
    # Filtrar por anos
    if filtros.get('anos'):
        df_mun = df_mun[df_mun['ano'].isin(filtros['anos'])]
    
    if df_mun.empty:
        st.warning("⚠️ Nenhum dado encontrado com os filtros aplicados.")
        return
    
    # Agregar por município
    df_resumo = df_mun.groupby(['municipio', 'uf']).agg({
        'qtd_fiscalizacoes': 'sum',
        'qtd_empresas_unicas': 'sum',
        'qtd_nfs': 'sum',
        'valor_total_infracoes': 'sum',
        'valor_total_nfs': 'sum'
    }).reset_index()
    
    df_resumo['taxa_conversao'] = (df_resumo['qtd_nfs'] / df_resumo['qtd_fiscalizacoes'] * 100).round(2)
    
    # ========== VISUALIZAÇÕES ==========
    st.markdown("<div class='sub-header'>📊 Concentração Geográfica</div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_mun = df_resumo['municipio'].nunique()
        st.metric("Total Municípios", f"{total_mun}")
    
    with col2:
        top_5_fisc = df_resumo.nlargest(5, 'qtd_fiscalizacoes')['qtd_fiscalizacoes'].sum()
        concentracao = (top_5_fisc / df_resumo['qtd_fiscalizacoes'].sum() * 100)
        st.metric("Concentração Top 5", f"{concentracao:.1f}%")
    
    with col3:
        total_valor = df_resumo['valor_total_nfs'].sum()
        st.metric("Valor Total", formatar_valor(total_valor))
    
    # Top 20 municípios
    st.markdown("### 🏆 Top 20 Municípios")
    
    col1, col2 = st.columns(2)
    
    with col1:
        df_top = df_resumo.nlargest(20, 'qtd_fiscalizacoes')
        
        fig = px.bar(
            df_top,
            y='municipio',
            x='qtd_fiscalizacoes',
            orientation='h',
            title='Top 20 - Volume de Fiscalizações',
            template=filtros['tema'],
            color='qtd_fiscalizacoes',
            color_continuous_scale='Blues'
        )
        
        fig.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            height=600,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        df_top_valor = df_resumo.nlargest(20, 'valor_total_nfs')
        
        fig = px.bar(
            df_top_valor,
            y='municipio',
            x='valor_total_nfs',
            orientation='h',
            title='Top 20 - Valor Lançado',
            template=filtros['tema'],
            color='valor_total_nfs',
            color_continuous_scale='Greens'
        )
        
        fig.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            height=600,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # ========== TABELA COMPLETA ==========
    st.markdown("<div class='sub-header'>📋 Ranking Completo</div>", unsafe_allow_html=True)
    
    df_display = df_resumo.sort_values('valor_total_nfs', ascending=False).copy()
    df_display['ranking'] = range(1, len(df_display) + 1)
    
    cols = ['ranking', 'municipio', 'uf', 'qtd_fiscalizacoes', 'qtd_empresas_unicas', 
            'qtd_nfs', 'valor_total_nfs', 'taxa_conversao']
    
    st.dataframe(
        df_display[cols].style.format({
            'valor_total_nfs': 'R$ {:,.2f}',
            'taxa_conversao': '{:.2f}%'
        }).background_gradient(subset=['valor_total_nfs'], cmap='Greens'),
        use_container_width=True,
        height=600
    )

def pagina_analise_afres(dados, filtros):
    """Análise de produtividade dos AFREs."""
    st.markdown("<h1 class='main-header'>👥 Análise de Produtividade - AFREs</h1>", unsafe_allow_html=True)
    
    df_afres = dados.get('metricas_afre', pd.DataFrame())
    
    if df_afres.empty:
        st.error("Dados de AFREs não disponíveis.")
        return
    
    # Filtrar por anos
    if filtros.get('anos'):
        df_afres = df_afres[df_afres['ano'].isin(filtros['anos'])]
    
    if df_afres.empty:
        st.warning("⚠️ Nenhum dado encontrado com os filtros aplicados.")
        return
    
    # Filtrar apenas AFREs com produção significativa
    df_afres = df_afres[df_afres['meses_ativos'] >= 6].copy()
    
    # ========== ESTATÍSTICAS GERAIS ==========
    st.markdown("<div class='sub-header'>📊 Estatísticas Gerais</div>", unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_afres = df_afres['matricula_afre'].nunique()
        st.metric("Total AFREs", f"{total_afres}")
    
    with col2:
        media_nfs_mes = df_afres['nfs_por_mes'].mean()
        st.metric("Média NFs/Mês", f"{media_nfs_mes:.2f}")
    
    with col3:
        media_conversao = df_afres['taxa_conversao_infracao_nf'].mean()
        st.metric("Taxa Conversão Média", f"{media_conversao:.1f}%")
    
    with col4:
        total_nfs = df_afres['qtd_nfs'].sum()
        st.metric("Total NFs", f"{int(total_nfs):,}")
    
    with col5:
        valor_total = df_afres['valor_total_lancado'].sum()
        st.metric("Valor Total", formatar_valor(valor_total))
    
    st.divider()
    
    # ========== DISTRIBUIÇÃO DE PRODUTIVIDADE ==========
    st.markdown("<div class='sub-header'>📈 Distribuição de Produtividade</div>", unsafe_allow_html=True)
    
    # Criar faixas
    df_afres['faixa_produtividade'] = pd.cut(
        df_afres['nfs_por_mes'],
        bins=[0, 0.5, 1.0, 2.0, 3.0, 100],
        labels=['Muito Baixa (<0.5)', 'Baixa (0.5-1)', 'Média (1-2)', 'Alta (2-3)', 'Muito Alta (>3)']
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        dist_faixa = df_afres['faixa_produtividade'].value_counts().reset_index()
        dist_faixa.columns = ['Faixa', 'Quantidade']
        
        fig = px.pie(
            dist_faixa,
            values='Quantidade',
            names='Faixa',
            title='Distribuição por Faixa de Produtividade',
            template=filtros['tema'],
            hole=0.4
        )
        
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.histogram(
            df_afres,
            x='nfs_por_mes',
            nbins=30,
            title='Histograma - NFs por Mês',
            template=filtros['tema'],
            color_discrete_sequence=['#1976d2']
        )
        
        fig.update_layout(
            xaxis_title='NFs/Mês',
            yaxis_title='Quantidade de AFREs',
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # ========== RANKING DE AFREs ==========
    st.markdown("<div class='sub-header'>🏆 Ranking de AFREs</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        ordem = st.radio("Ordenar por:", ['Melhores', 'Todos'], index=0)
        top_n = st.slider("Mostrar top:", 10, 100, 50, 10)
    
    if ordem == 'Melhores':
        df_rank = df_afres.nlargest(top_n, 'nfs_por_mes')
    else:
        df_rank = df_afres.sort_values('nfs_por_mes', ascending=False).head(top_n)
    
    cols = ['matricula_afre', 'nome_afre', 'meses_ativos', 'qtd_infracoes', 'qtd_nfs', 
            'nfs_por_mes', 'taxa_conversao_infracao_nf', 'valor_total_lancado']
    
    # Filtrar apenas colunas existentes
    cols_existentes = [col for col in cols if col in df_rank.columns]
    
    st.dataframe(
        df_rank[cols_existentes].style.format({
            'nfs_por_mes': '{:.2f}',
            'taxa_conversao_infracao_nf': '{:.2f}%',
            'valor_total_lancado': 'R$ {:,.2f}'
        }).background_gradient(subset=['nfs_por_mes'], cmap='Greens'),
        use_container_width=True,
        height=600
    )

def pagina_tipos_infracoes(dados, filtros):
    """Análise dos tipos de infrações mais comuns."""
    st.markdown("<h1 class='main-header'>⚖️ Análise de Tipos de Infrações</h1>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class='info-box'>
    <b>⚖️ Tipos de Infrações Fiscais</b><br>
    Análise detalhada dos tipos de infrações mais comuns, valores envolvidos e 
    empresas afetadas, permitindo identificar padrões de irregularidades.
    </div>
    """, unsafe_allow_html=True)
    
    df_rank = dados.get('ranking_infracoes', pd.DataFrame())
    
    if df_rank.empty:
        st.error("📊 Dados de infrações não disponíveis.")
        st.markdown("""
        <div class='alert-alto'>
        <b>⚠️ Tabela vazia!</b><br>
        Execute o SQL de criação da tabela `fisca_ranking_infracoes` fornecido.
        </div>
        """, unsafe_allow_html=True)
        return
    
    # ========== DEBUG EXPANDIDO ==========
    with st.expander("🔍 Debug - Análise dos Dados"):
        st.write(f"**Total de registros:** {len(df_rank):,}")
        st.write("**Colunas disponíveis:**", df_rank.columns.tolist())
        
        st.write("**Distribuição por ano:**")
        if 'ano' in df_rank.columns:
            st.write(df_rank.groupby('ano').agg({
                'qtd_ocorrencias': 'sum',
                'qtd_empresas': 'sum',
                'valor_total': 'sum'
            }))
        
        st.write("**Amostra de dados:**")
        st.dataframe(df_rank.head(20))
        
        # Verificar valores zerados
        if 'valor_total' in df_rank.columns:
            total_com_valor = df_rank[df_rank['valor_total'] > 0].shape[0]
            total_sem_valor = df_rank[df_rank['valor_total'] == 0].shape[0]
            
            st.write(f"**Registros COM valor:** {total_com_valor:,} ({total_com_valor/len(df_rank)*100:.1f}%)")
            st.write(f"**Registros SEM valor:** {total_sem_valor:,} ({total_sem_valor/len(df_rank)*100:.1f}%)")
    
    # Filtrar por anos
    if filtros.get('anos') and 'ano' in df_rank.columns:
        df_rank = df_rank[df_rank['ano'].isin(filtros['anos'])]
    
    if df_rank.empty:
        st.warning("⚠️ Nenhum dado encontrado com os filtros aplicados.")
        return
    
    # ========== NORMALIZAR NOMES DE COLUNAS ==========
    # Garantir que as colunas existam com os nomes esperados
    colunas_necessarias = {
        'codigo_infracao': ['codigo_infracao', 'cd_infracao', 'tipo_infracao'],
        'descricao_infracao': ['descricao_infracao', 'de_infracao', 'descricao'],
        'tipo_infracao_descricao': ['tipo_infracao_descricao', 'tipo_infracao', 'tipo']
    }
    
    for coluna_padrao, possiveis_nomes in colunas_necessarias.items():
        if coluna_padrao not in df_rank.columns:
            for nome in possiveis_nomes:
                if nome in df_rank.columns:
                    df_rank = df_rank.rename(columns={nome: coluna_padrao})
                    break
    
    # Verificar se temos as colunas essenciais
    if 'codigo_infracao' not in df_rank.columns:
        st.error("❌ Coluna 'codigo_infracao' não encontrada nos dados!")
        st.write("**Colunas disponíveis:**", df_rank.columns.tolist())
        return
    
    # ========== AGREGAR POR TIPO ==========
    colunas_group = ['codigo_infracao']
    if 'descricao_infracao' in df_rank.columns:
        colunas_group.append('descricao_infracao')
    if 'tipo_infracao_descricao' in df_rank.columns:
        colunas_group.append('tipo_infracao_descricao')
    
    df_agregado = df_rank.groupby(colunas_group).agg({
        'qtd_ocorrencias': 'sum',
        'qtd_empresas': 'sum',
        'valor_total': 'sum',
        'valor_medio': 'mean'
    }).reset_index()
    
    # Renomear coluna para compatibilidade se necessário
    if 'tipo_infracao_descricao' in df_agregado.columns and 'tipo_infracao' not in df_agregado.columns:
        df_agregado = df_agregado.rename(columns={'tipo_infracao_descricao': 'tipo_infracao'})
    
    # Adicionar coluna tipo_infracao se não existir
    if 'tipo_infracao' not in df_agregado.columns:
        df_agregado['tipo_infracao'] = 'Não especificado'
    
    # Adicionar coluna descricao_infracao se não existir
    if 'descricao_infracao' not in df_agregado.columns:
        df_agregado['descricao_infracao'] = df_agregado['codigo_infracao'].astype(str)
    
    # Remover nulos em codigo_infracao
    df_agregado = df_agregado[df_agregado['codigo_infracao'].notna()]
    
    if df_agregado.empty:
        st.warning("⚠️ Não há dados válidos para exibir após agregação.")
        return
    
    # ========== ALERTA DE QUALIDADE DOS DADOS ==========
    registros_sem_valor = df_agregado[df_agregado['valor_total'] == 0].shape[0]
    percentual_sem_valor = (registros_sem_valor / len(df_agregado) * 100) if len(df_agregado) > 0 else 0
    
    if percentual_sem_valor > 50:
        st.markdown(f"""
        <div class='alert-alto'>
        <b>⚠️ ATENÇÃO - Qualidade dos Dados:</b><br>
        • {registros_sem_valor} tipos de infrações ({percentual_sem_valor:.1f}%) estão sem valores monetários<br>
        • Isso pode indicar que os valores não foram preenchidos na origem dos dados<br>
        • As análises de valor podem estar subestimadas
        </div>
        """, unsafe_allow_html=True)
    
    # ========== ESTATÍSTICAS GERAIS ==========
    st.markdown("<div class='sub-header'>📊 Estatísticas Gerais</div>", unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_tipos = df_agregado['codigo_infracao'].nunique()
        st.metric("Tipos de Infrações", f"{total_tipos}")
    
    with col2:
        total_ocorrencias = df_agregado['qtd_ocorrencias'].sum()
        st.metric("Total Ocorrências", f"{int(total_ocorrencias):,}")
    
    with col3:
        total_empresas = df_agregado['qtd_empresas'].sum()
        st.metric("Empresas Afetadas", f"{int(total_empresas):,}")
    
    with col4:
        valor_total = df_agregado['valor_total'].sum()
        st.metric("Valor Total", formatar_valor(valor_total))
    
    with col5:
        # Calcular valor médio apenas de registros com valor > 0
        df_com_valor = df_agregado[df_agregado['valor_total'] > 0]
        if not df_com_valor.empty:
            valor_medio_geral = df_com_valor['valor_medio'].mean()
            st.metric("Valor Médio", formatar_valor(valor_medio_geral))
        else:
            st.metric("Valor Médio", "R$ 0,00")
    
    st.divider()
    
    # ========== ANÁLISE POR ANO ==========
    if 'ano' in df_rank.columns:
        st.markdown("<div class='sub-header'>📅 Distribuição Temporal</div>", unsafe_allow_html=True)
        
        df_temporal = df_rank.groupby('ano').agg({
            'qtd_ocorrencias': 'sum',
            'qtd_empresas': 'sum',
            'valor_total': 'sum'
        }).reset_index()
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=df_temporal['ano'],
                y=df_temporal['qtd_ocorrencias'],
                name='Ocorrências',
                marker_color='#1976d2',
                text=df_temporal['qtd_ocorrencias'],
                textposition='auto'
            ))
            
            fig.update_layout(
                title='Evolução do Número de Infrações por Ano',
                template=filtros['tema'],
                height=400,
                xaxis_title='Ano',
                yaxis_title='Quantidade'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=df_temporal['ano'],
                y=df_temporal['valor_total'],
                mode='lines+markers',
                name='Valor Total',
                line=dict(color='#388e3c', width=3),
                marker=dict(size=10),
                text=[formatar_valor(v) for v in df_temporal['valor_total']],
                textposition='top center'
            ))
            
            fig.update_layout(
                title='Evolução dos Valores por Ano',
                template=filtros['tema'],
                height=400,
                xaxis_title='Ano',
                yaxis_title='Valor (R$)'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
    
    # ========== TOP INFRAÇÕES ==========
    st.markdown("<div class='sub-header'>🏆 Top 30 Infrações Mais Comuns</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        df_top = df_agregado.nlargest(30, 'qtd_ocorrencias')
        
        # Criar label melhor
        df_top['label'] = df_top.apply(
            lambda x: f"Tipo {x['codigo_infracao']}" if pd.isna(x.get('descricao_infracao')) or str(x.get('descricao_infracao')).strip() == ''
            else f"{x['codigo_infracao']}: {str(x['descricao_infracao'])[:30]}...",
            axis=1
        )
        
        fig = px.bar(
            df_top.sort_values('qtd_ocorrencias', ascending=True),
            y='label',
            x='qtd_ocorrencias',
            orientation='h',
            title='Top 30 - Por Volume de Ocorrências',
            template=filtros['tema'],
            color='qtd_ocorrencias',
            color_continuous_scale='Reds'
        )
        
        fig.update_layout(
            height=800,
            showlegend=False,
            yaxis_title='Tipo de Infração'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Top por valor (apenas os que têm valor > 0)
        df_com_valor = df_agregado[df_agregado['valor_total'] > 0]
        
        if not df_com_valor.empty:
            df_top_valor = df_com_valor.nlargest(30, 'valor_total')
            
            df_top_valor['label'] = df_top_valor.apply(
                lambda x: f"Tipo {x['codigo_infracao']}" if pd.isna(x.get('descricao_infracao')) or str(x.get('descricao_infracao')).strip() == ''
                else f"{x['codigo_infracao']}: {str(x['descricao_infracao'])[:30]}...",
                axis=1
            )
            
            fig = px.bar(
                df_top_valor.sort_values('valor_total', ascending=True),
                y='label',
                x='valor_total',
                orientation='h',
                title='Top 30 - Por Valor Total',
                template=filtros['tema'],
                color='valor_total',
                color_continuous_scale='Greens'
            )
            
            fig.update_layout(
                height=800,
                showlegend=False,
                yaxis_title='Tipo de Infração'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Não há infrações com valores registrados para exibir este gráfico.")
    
    st.divider()
    
    # ========== TABELA COMPLETA ==========
    st.markdown("<div class='sub-header'>📋 Tabela Detalhada</div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        busca = st.text_input("🔍 Buscar:", "")
    
    with col2:
        ordem = st.selectbox("Ordenar por:", ['Quantidade', 'Valor Total'], index=0)
    
    with col3:
        limite = st.slider("Mostrar top:", 10, 200, 50, 10)
    
    # Aplicar busca
    df_filtrado = df_agregado.copy()
    
    if busca:
        mascara = df_filtrado['codigo_infracao'].astype(str).str.contains(busca, case=False, na=False)
        
        if 'descricao_infracao' in df_filtrado.columns:
            mascara = mascara | df_filtrado['descricao_infracao'].astype(str).str.contains(busca, case=False, na=False)
        
        df_filtrado = df_filtrado[mascara]
    
    # Ordenar
    coluna_ordem = 'qtd_ocorrencias' if ordem == 'Quantidade' else 'valor_total'
    df_filtrado = df_filtrado.sort_values(coluna_ordem, ascending=False).head(limite)
    
    # Adicionar ranking e percentual
    df_filtrado['ranking'] = range(1, len(df_filtrado) + 1)
    total_ocorrencias_geral = df_agregado['qtd_ocorrencias'].sum()
    df_filtrado['percentual'] = (df_filtrado['qtd_ocorrencias'] / total_ocorrencias_geral * 100).round(2)
    
    # Definir colunas para exibição
    cols_base = ['ranking', 'codigo_infracao']
    cols_opcionais = ['descricao_infracao', 'tipo_infracao']
    cols_metricas = ['qtd_ocorrencias', 'percentual', 'qtd_empresas', 'valor_total', 'valor_medio']
    
    # Montar lista de colunas existentes
    cols = cols_base.copy()
    for col in cols_opcionais:
        if col in df_filtrado.columns:
            cols.append(col)
    cols.extend(cols_metricas)
    
    # Filtrar apenas colunas que existem
    cols_existentes = [col for col in cols if col in df_filtrado.columns]
    
    # Exibir tabela
    st.dataframe(
        df_filtrado[cols_existentes].style.format({
            'percentual': '{:.2f}%',
            'valor_total': 'R$ {:,.2f}',
            'valor_medio': 'R$ {:,.2f}'
        })
        .background_gradient(subset=['qtd_ocorrencias'], cmap='Reds')
        .background_gradient(subset=['valor_total'], cmap='Greens'),
        use_container_width=True,
        height=600
    )
    
    # Download
    csv = df_agregado.to_csv(index=False).encode('utf-8')
    st.download_button(
        "📥 Baixar CSV Completo",
        csv,
        f"ranking_infracoes_{datetime.now().strftime('%Y%m%d')}.csv",
        "text/csv"
    )
            
def pagina_drill_down_empresa(dados, filtros):
    """Drill-down detalhado por empresa."""
    st.markdown("<h1 class='main-header'>🔎 Drill-Down - Análise de Empresa</h1>", unsafe_allow_html=True)
    
    engine = st.session_state.get('engine')
    
    if not engine:
        st.error("Engine não disponível.")
        return
    
    df_empresas = dados.get('empresas_resumo', pd.DataFrame())
    
    if df_empresas.empty:
        st.warning("Lista de empresas não disponível.")
        return
    
    # ========== SELEÇÃO DE EMPRESA ==========
    st.markdown("<div class='sub-header'>🔍 Busca de Empresa</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Busca por nome ou CNPJ
        busca = st.text_input("Digite o nome da empresa ou CNPJ:", "")
        
        if busca:
            df_filtrado = df_empresas[
                df_empresas['nm_razao_social'].str.contains(busca, case=False, na=False) |
                df_empresas['cnpj'].str.contains(busca, na=False)
            ].head(50)
            
            if not df_filtrado.empty:
                opcoes = df_filtrado.apply(
                    lambda x: f"{x['cnpj']} - {x['nm_razao_social']} ({x['municipio']})", 
                    axis=1
                ).tolist()
                
                empresa_selecionada = st.selectbox(
                    "Selecione a empresa:",
                    opcoes,
                    key="select_empresa"
                )
                
                if empresa_selecionada:
                    cnpj_selecionado = empresa_selecionada.split(' - ')[0]
                else:
                    cnpj_selecionado = None
            else:
                st.warning("Nenhuma empresa encontrada com esse critério.")
                cnpj_selecionado = None
        else:
            st.info("👆 Digite o nome ou CNPJ da empresa para buscar.")
            cnpj_selecionado = None
    
    if not cnpj_selecionado:
        return
    
    # ========== CARREGAR DADOS DETALHADOS ==========
    with st.spinner(f"Carregando dados detalhados da empresa {cnpj_selecionado}..."):
        df_empresa = carregar_empresa_detalhada(engine, cnpj_selecionado)
        df_fiscalizacoes = carregar_fiscalizacoes_empresa(engine, cnpj_selecionado)
    
    if df_empresa.empty:
        st.error("Dados cadastrais não encontrados.")
        return
    
    empresa_info = df_empresa.iloc[0]
    
    # ========== CABEÇALHO ==========
    st.markdown(f"<h2 style='color: #1976d2;'>🏢 {empresa_info['nm_razao_social']}</h2>", unsafe_allow_html=True)
    
    # Dados cadastrais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("CNPJ", cnpj_selecionado)
    
    with col2:
        st.metric("Município", empresa_info.get('municipio', 'N/A'))
    
    with col3:
        st.metric("Regime", empresa_info.get('regime_tributario', 'N/A'))
    
    with col4:
        st.metric("CNAE Seção", empresa_info.get('cnae_secao_descricao', 'N/A'))
    
    st.divider()
    
    # ========== HISTÓRICO DE FISCALIZAÇÕES ==========
    if df_fiscalizacoes.empty:
        st.info("Esta empresa não possui fiscalizações registradas.")
        return
    
    st.markdown("<div class='sub-header'>📋 Histórico de Fiscalizações</div>", unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_fisc = len(df_fiscalizacoes)
        st.metric("Total Fiscalizações", f"{total_fisc}")
    
    with col2:
        total_nfs = df_fiscalizacoes['gerou_notificacao'].sum()
        st.metric("NFs Emitidas", f"{int(total_nfs)}")
    
    with col3:
        valor_total = df_fiscalizacoes['valor_total_infracao'].sum()
        st.metric("Valor Total Infrações", formatar_valor(valor_total))
    
    with col4:
        valor_nfs = df_fiscalizacoes['valor_total_nf'].sum()
        st.metric("Valor Total NFs", formatar_valor(valor_nfs))
    
    with col5:
        taxa_conv = (total_nfs / total_fisc * 100) if total_fisc > 0 else 0
        st.metric("Taxa Conversão", f"{taxa_conv:.1f}%")
    
    # Gráfico temporal
    if 'data_infracao' in df_fiscalizacoes.columns:
        df_temp = df_fiscalizacoes.copy()
        df_temp['ano'] = pd.to_datetime(df_temp['data_infracao']).dt.year
        
        df_ano = df_temp.groupby('ano').agg({
            'id_documento': 'count',
            'valor_total_infracao': 'sum'
        }).reset_index()
        df_ano.columns = ['ano', 'quantidade', 'valor']
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=df_ano['ano'],
            y=df_ano['quantidade'],
            name='Quantidade',
            marker_color='#1976d2'
        ))
        
        fig.update_layout(
            title='Evolução de Fiscalizações por Ano',
            template=filtros['tema'],
            height=400,
            xaxis_title='Ano',
            yaxis_title='Quantidade'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # ========== TABELA DE FISCALIZAÇÕES ==========
    st.markdown("### 📄 Detalhamento das Fiscalizações")
    
    cols_display = ['data_infracao', 'numero_infracao', 'tipo_infracao', 
                    'valor_total_infracao', 'gerou_notificacao', 'numero_nf', 
                    'valor_total_nf', 'situacao_final']
    
    cols_existentes = [col for col in cols_display if col in df_fiscalizacoes.columns]
    
    st.dataframe(
        df_fiscalizacoes[cols_existentes].style.format({
            'valor_total_infracao': 'R$ {:,.2f}',
            'valor_total_nf': 'R$ {:,.2f}'
        }),
        use_container_width=True,
        height=400
    )
    
    # ========== DETALHES DE FISCALIZAÇÃO ESPECÍFICA ==========
    st.markdown("### 🔍 Detalhes de Fiscalização Específica")
    
    if not df_fiscalizacoes.empty:
        fisc_opcoes = df_fiscalizacoes.apply(
            lambda x: f"{x['numero_infracao']} - {x['data_infracao']} - {formatar_valor(x['valor_total_infracao'])}", 
            axis=1
        ).tolist()
        
        fisc_selecionada = st.selectbox(
            "Selecione uma fiscalização para ver detalhes:",
            fisc_opcoes,
            key="select_fisc"
        )
        
        if fisc_selecionada:
            numero_infracao = fisc_selecionada.split(' - ')[0]
            fisc_dados = df_fiscalizacoes[df_fiscalizacoes['numero_infracao'] == numero_infracao].iloc[0]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**Dados da Infração:**")
                st.write(f"Número: {fisc_dados.get('numero_infracao', 'N/A')}")
                st.write(f"Data: {fisc_dados.get('data_infracao', 'N/A')}")
                st.write(f"Tipo: {fisc_dados.get('tipo_infracao', 'N/A')}")
                st.write(f"Valor: {formatar_valor(fisc_dados.get('valor_total_infracao', 0))}")
            
            with col2:
                st.markdown("**Notificação Fiscal:**")
                if fisc_dados.get('gerou_notificacao', 0) == 1:
                    st.write(f"Número NF: {fisc_dados.get('numero_nf', 'N/A')}")
                    st.write(f"Data NF: {fisc_dados.get('data_nf', 'N/A')}")
                    st.write(f"Valor NF: {formatar_valor(fisc_dados.get('valor_total_nf', 0))}")
                    st.write(f"Dias até NF: {fisc_dados.get('dias_infracao_ate_nf', 'N/A')}")
                else:
                    st.write("Não gerou NF")
            
            with col3:
                st.markdown("**Situação:**")
                st.write(f"Status: {fisc_dados.get('situacao_final', 'N/A')}")
                st.write(f"Ciclo Completo: {'Sim' if fisc_dados.get('ciclo_completo', 0) == 1 else 'Não'}")
                st.write(f"Teve Encerramento: {'Sim' if fisc_dados.get('teve_encerramento', 0) == 1 else 'Não'}")
            
            # Carregar AFREs da fiscalização
            if 'id_documento' in fisc_dados.index:
                st.markdown("**👥 AFREs Envolvidos:**")
                
                df_afres_fisc = carregar_afres_fiscalizacao(engine, fisc_dados['id_documento'])
                
                if not df_afres_fisc.empty:
                    cols_afres = ['matricula_afre', 'nome_afre', 'cargo', 
                                 'percentual_participacao', 'eh_coordenador']
                    
                    cols_existentes_afres = [col for col in cols_afres if col in df_afres_fisc.columns]
                    
                    st.dataframe(
                        df_afres_fisc[cols_existentes_afres],
                        use_container_width=True
                    )
                else:
                    st.info("Informações de AFREs não disponíveis.")

def pagina_machine_learning(dados, filtros):
    """Sistema de Machine Learning para priorização de fiscalizações."""
    st.markdown("<h1 class='main-header'>🤖 Machine Learning - Priorização Inteligente</h1>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class='info-box'>
    <b>🎯 Sistema de Priorização Inteligente de Fiscalizações</b><br>
    Utiliza algoritmos de Machine Learning para identificar empresas com maior probabilidade 
    de conversão (Infração → NF) e maior impacto financeiro, otimizando a alocação de recursos.
    </div>
    """, unsafe_allow_html=True)
    
    engine = st.session_state.get('engine')
    
    if not engine:
        st.error("Engine não disponível.")
        return
    
    # ========== CONFIGURAÇÃO DO MODELO ==========
    st.markdown("<div class='sub-header'>⚙️ Configuração do Modelo</div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        algoritmo = st.selectbox(
            "Algoritmo:",
            ['Random Forest', 'Gradient Boosting'],
            index=0
        )
    
    with col2:
        test_size = st.slider("% Teste:", 10, 40, 30, 5)
    
    with col3:
        threshold = st.slider("Threshold:", 0.3, 0.7, 0.5, 0.05)
    
    if st.button("🚀 Treinar Modelo e Gerar Recomendações", type="primary"):
        
        # Carregar dataset
        with st.spinner("Carregando dados para Machine Learning..."):
            df_ml = carregar_dataset_ml(engine)
        
        if df_ml.empty:
            st.error("Dataset não disponível.")
            return
        
        st.success(f"✅ {len(df_ml):,} registros carregados")
        
        # ========== PREPARAÇÃO DOS DADOS ==========
        with st.spinner("Preparando features..."):
            
            # Target: gerou_notificacao
            if 'gerou_notificacao' not in df_ml.columns:
                st.error("Coluna target 'gerou_notificacao' não encontrada.")
                return
            
            # Features numéricas
            features_numericas = []
            
            if 'valor_total_infracao' in df_ml.columns:
                df_ml['log_valor_infracao'] = np.log1p(df_ml['valor_total_infracao'])
                features_numericas.append('log_valor_infracao')
            
            if 'dias_infracao_ate_nf' in df_ml.columns:
                df_ml['dias_infracao_ate_nf_filled'] = df_ml['dias_infracao_ate_nf'].fillna(
                    df_ml['dias_infracao_ate_nf'].median()
                )
                features_numericas.append('dias_infracao_ate_nf_filled')
            
            if 'ano_infracao' in df_ml.columns:
                features_numericas.append('ano_infracao')
            
            # Features categóricas (One-Hot Encoding)
            features_categoricas = []
            
            if 'regime_tributario' in df_ml.columns:
                df_ml['regime_simples'] = (df_ml['regime_tributario'] == 'SIMPLES NACIONAL').astype(int)
                df_ml['regime_normal'] = (df_ml['regime_tributario'] == 'REGIME NORMAL').astype(int)
                features_categoricas.extend(['regime_simples', 'regime_normal'])
            
            if 'cnae_secao' in df_ml.columns:
                # Top 5 CNAEs
                top_cnaes = df_ml['cnae_secao'].value_counts().head(5).index
                for cnae in top_cnaes:
                    col_name = f'cnae_{cnae}'
                    df_ml[col_name] = (df_ml['cnae_secao'] == cnae).astype(int)
                    features_categoricas.append(col_name)
            
            # Combinar features
            all_features = features_numericas + features_categoricas
            
            if len(all_features) == 0:
                st.error("Nenhuma feature disponível para treinamento.")
                return
            
            # Preparar X e y
            X = df_ml[all_features].fillna(0)
            y = df_ml['gerou_notificacao'].fillna(0)
            
            # Remover NaN restantes
            mask_valid = ~X.isna().any(axis=1) & ~y.isna()
            X = X[mask_valid]
            y = y[mask_valid]
            
            if len(X) < 100:
                st.error("Dataset muito pequeno após limpeza.")
                return
        
        st.success(f"✅ Features preparadas: {len(all_features)} features, {len(X):,} registros")
        
        # ========== TREINAMENTO ==========
        with st.spinner(f"Treinando {algoritmo}..."):
            
            # Split
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size/100, random_state=42, stratify=y
            )
            
            # Normalizar
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Modelo
            if algoritmo == 'Random Forest':
                modelo = RandomForestClassifier(
                    n_estimators=100,
                    max_depth=10,
                    random_state=42,
                    n_jobs=-1
                )
            else:
                modelo = GradientBoostingClassifier(
                    n_estimators=100,
                    max_depth=5,
                    random_state=42
                )
            
            modelo.fit(X_train_scaled, y_train)
            y_pred = modelo.predict(X_test_scaled)
            y_proba = modelo.predict_proba(X_test_scaled)[:, 1]
        
        st.success("✅ Modelo treinado com sucesso!")
        
        # ========== MÉTRICAS ==========
        st.markdown("<div class='sub-header'>📊 Performance do Modelo</div>", unsafe_allow_html=True)
        
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            acc = accuracy_score(y_test, y_pred)
            st.metric("Acurácia", f"{acc:.2%}")
        
        with col2:
            prec = precision_score(y_test, y_pred)
            st.metric("Precisão", f"{prec:.2%}")
        
        with col3:
            rec = recall_score(y_test, y_pred)
            st.metric("Recall", f"{rec:.2%}")
        
        with col4:
            f1 = f1_score(y_test, y_pred)
            st.metric("F1-Score", f"{f1:.2%}")
        
        # ========== VISUALIZAÇÕES ==========
        col1, col2 = st.columns(2)
        
        with col1:
            # Matriz de confusão
            cm = confusion_matrix(y_test, y_pred)
            
            fig = px.imshow(
                cm,
                labels=dict(x="Predito", y="Real", color="Quantidade"),
                x=['Não Gerou NF', 'Gerou NF'],
                y=['Não Gerou NF', 'Gerou NF'],
                title='Matriz de Confusão',
                template=filtros['tema'],
                color_continuous_scale='Blues',
                text_auto=True
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Curva ROC
            fpr, tpr, _ = roc_curve(y_test, y_proba)
            auc = roc_auc_score(y_test, y_proba)
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=fpr,
                y=tpr,
                mode='lines',
                name=f'ROC (AUC={auc:.3f})',
                line=dict(color='#1976d2', width=3)
            ))
            
            fig.add_trace(go.Scatter(
                x=[0, 1],
                y=[0, 1],
                mode='lines',
                name='Random',
                line=dict(color='gray', width=1, dash='dash')
            ))
            
            fig.update_layout(
                title='Curva ROC',
                xaxis_title='Taxa de Falsos Positivos',
                yaxis_title='Taxa de Verdadeiros Positivos',
                template=filtros['tema'],
                showlegend=True
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # ========== FEATURE IMPORTANCE ==========
        if hasattr(modelo, 'feature_importances_'):
            st.markdown("<div class='sub-header'>🎯 Importância das Features</div>", unsafe_allow_html=True)
            
            importances = pd.DataFrame({
                'Feature': all_features,
                'Importância': modelo.feature_importances_
            }).sort_values('Importância', ascending=False)
            
            fig = px.bar(
                importances.head(15),
                x='Importância',
                y='Feature',
                orientation='h',
                title='Top 15 Features Mais Importantes',
                template=filtros['tema'],
                color='Importância',
                color_continuous_scale='Viridis'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # ========== RECOMENDAÇÕES ==========
        st.markdown("<div class='sub-header'>🎯 Empresas Prioritárias para Fiscalização</div>", unsafe_allow_html=True)
        
        with st.spinner("Gerando recomendações..."):
            # Aplicar modelo em todo dataset
            X_full = df_ml[all_features].fillna(0)
            X_full_scaled = scaler.transform(X_full)
            
            df_ml['probabilidade_nf'] = modelo.predict_proba(X_full_scaled)[:, 1]
            df_ml['score_prioridade'] = (
                df_ml['probabilidade_nf'] * 0.6 +
                (df_ml['valor_total_infracao'] / df_ml['valor_total_infracao'].max()) * 0.4
            )
            
            # Filtrar empresas sem fiscalização recente
            df_recomendacoes = df_ml[
                (df_ml['gerou_notificacao'] == 0) &
                (df_ml['score_prioridade'] >= 0.5)
            ].copy()
            
            df_recomendacoes = df_recomendacoes.nlargest(100, 'score_prioridade')
            
            if not df_recomendacoes.empty:
                st.success(f"✅ {len(df_recomendacoes)} empresas identificadas como prioritárias")
                
                cols_rec = ['cnpj', 'nm_razao_social', 'municipio', 'regime_tributario',
                           'valor_total_infracao', 'probabilidade_nf', 'score_prioridade']
                
                cols_existentes = [col for col in cols_rec if col in df_recomendacoes.columns]
                
                st.dataframe(
                    df_recomendacoes[cols_existentes].style.format({
                        'valor_total_infracao': 'R$ {:,.2f}',
                        'probabilidade_nf': '{:.2%}',
                        'score_prioridade': '{:.3f}'
                    }).background_gradient(subset=['score_prioridade'], cmap='Reds'),
                    use_container_width=True,
                    height=600
                )
                
                # Download das recomendações
                csv = df_recomendacoes[cols_existentes].to_csv(index=False)
                st.download_button(
                    label="📥 Baixar Lista de Empresas Prioritárias (CSV)",
                    data=csv,
                    file_name=f"empresas_prioritarias_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                st.info("Nenhuma empresa atende aos critérios de priorização.")

def pagina_sobre(dados, filtros):
    """Informações sobre o sistema."""
    st.markdown("<h1 class='main-header'>ℹ️ Sobre o Sistema FISCA</h1>", unsafe_allow_html=True)
    
    st.markdown("""
    ## Sistema de Análise de Fiscalizações - FISCA
    
    ### 📝 Descrição
    
    O **Sistema FISCA** é uma plataforma desenvolvida pela Receita Estadual de Santa Catarina 
    para monitoramento, análise e gestão inteligente das ações fiscais de ICMS.
    
    ### ✨ Principais Funcionalidades
    
    #### 1. Dashboard Executivo
    - Visão consolidada do sistema
    - KPIs principais em tempo real
    - Evolução temporal de infrações e notificações
    - Análise de produtividade dos AFREs
    
    #### 2. Análise por Gerência (GRAF)
    - Performance por gerência regional
    - Ranking de gerências
    - Taxa de conversão e tempestividade
    - Valores lançados e efetividade
    
    #### 3. Análise por Setor (CNAE)
    - Distribuição por setor econômico
    - Identificação de setores críticos
    - Volume e valores por CNAE
    
    #### 4. Análise Geográfica
    - Concentração por município
    - Ranking de municípios fiscalizados
    - Mapa de calor (futuro)
    
    #### 5. Performance de AFREs
    - Produtividade individual
    - Ranking de auditores
    - Taxa de conversão por AFRE
    - Distribuição de faixas de produtividade
    
    #### 6. Tipos de Infrações
    - Infrações mais comuns
    - Análise de valores
    - Tendências temporais
    - Catálogo de infrações
    
    #### 7. Drill-Down por Empresa
    - Histórico completo de fiscalizações
    - Detalhamento de cada infração
    - AFREs envolvidos
    - Análise temporal
    
    #### 8. Machine Learning
    - Priorização inteligente de fiscalizações
    - Predição de conversão (Infração → NF)
    - Feature importance
    - Recomendações automáticas
    
    ### 📊 Dados e Métricas
    
    - **Período de Análise:** 2020 até atual
    - **Infrações Monitoradas:** Todas as infrações lavradas
    - **Notificações Fiscais:** NFs emitidas
    - **Encerramentos:** Termos de encerramento
    - **Atualização:** Dados atualizados periodicamente
    
    ### 🎯 Objetivos
    
    1. **Aumentar a Taxa de Conversão**
       - Meta: ≥ 70% de conversão Infração → NF
       - Reduzir infrações não convertidas
    
    2. **Reduzir Tempo Médio de Fiscalização**
       - Meta: ≤ 60 dias (Infração → NF)
       - Otimizar processos
    
    3. **Priorizar Ações de Alto Impacto**
       - Foco em valores relevantes
       - Machine Learning para priorização
    
    4. **Melhorar Produtividade**
       - Identificar melhores práticas
       - Benchmarking entre AFREs e gerências
    
    ### 🛠️ Tecnologias Utilizadas
    
    - **Frontend:** Streamlit
    - **Visualização:** Plotly
    - **Análise:** Pandas, NumPy
    - **Machine Learning:** Scikit-learn
    - **Banco de Dados:** Impala (Hadoop)
    
    ### 📞 Desenvolvimento
    
    **Versão:** 1.0  
    **Data:** Outubro 2025  
    **Desenvolvedor:** Thiago Severo
    
    ### 📞 Contato e Suporte
    
    Para dúvidas, sugestões ou suporte técnico, entre em contato com a equipe de TI.
    
    ---
    
    *Sistema desenvolvido com foco em eficiência, precisão e facilidade de uso.*
    """)
    
    # Estatísticas do sistema
    st.markdown("<div class='sub-header'>📊 Estatísticas Atuais</div>", unsafe_allow_html=True)
    
    df_stats = dados.get('fiscalizacoes_stats', pd.DataFrame())
    
    if not df_stats.empty and len(df_stats) > 0:
        stats = df_stats.iloc[0]
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Fiscalizações", f"{int(stats.get('total_fiscalizacoes', 0)):,}")
        
        with col2:
            st.metric("Empresas", f"{int(stats.get('total_empresas', 0)):,}")
        
        with col3:
            st.metric("NFs Emitidas", f"{int(stats.get('total_nfs', 0)):,}")
        
        with col4:
            taxa = (stats.get('fiscalizacoes_com_nf', 0) / stats.get('total_fiscalizacoes', 1) * 100)
            st.metric("Taxa Conversão", f"{taxa:.1f}%")

def pagina_analise_estados(dados, filtros):
    """Análise do ciclo de vida das infrações."""
    st.markdown("<h1 class='main-header'>📋 Ciclo de Vida das Infrações</h1>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class='info-box'>
    <b>🔄 Fluxo de Estados</b><br>
    Esta página analisa o ciclo de vida completo das infrações fiscais, desde a lavratura 
    até a conversão em NF ou regularização, permitindo entender o impacto dos estados 
    nas métricas de performance.
    </div>
    """, unsafe_allow_html=True)
    
    df_estados = dados.get('analise_estados', pd.DataFrame())
    df_resumo = dados.get('resumo_conversoes', pd.DataFrame())
    
    if df_estados.empty:
        st.error("Dados não disponíveis.")
        return
    
    # ========== CARDS DE IMPACTO ==========
    st.markdown("<div class='sub-header'>🎯 Impacto do Filtro de Estados</div>", unsafe_allow_html=True)
    
    total = df_estados['qtd'].sum()
    validas = df_estados[df_estados['eh_valida'] == 1]['qtd'].sum()
    canceladas = df_estados[df_estados['eh_valida'] == 0]['qtd'].sum()
    com_nf = df_estados['com_nf'].sum()
    regularizadas = df_estados[df_estados['eh_regularizada_sem_nf'] == 1]['qtd'].sum()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #ef5350 0%, #e53935 100%); 
                    padding: 2rem; border-radius: 15px; color: white; text-align: center;'>
            <h2 style='margin: 0; color: white;'>66.01%</h2>
            <p style='margin: 0.5rem 0; font-size: 0.9rem;'>Taxa INCORRETA</p>
            <p style='margin: 0; font-size: 0.8rem; opacity: 0.9;'>(com canceladas)</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        taxa_correta = (com_nf / validas * 100) if validas > 0 else 0
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #66bb6a 0%, #4caf50 100%); 
                    padding: 2rem; border-radius: 15px; color: white; text-align: center;'>
            <h2 style='margin: 0; color: white;'>{taxa_correta:.2f}%</h2>
            <p style='margin: 0.5rem 0; font-size: 0.9rem;'>Taxa CORRETA</p>
            <p style='margin: 0; font-size: 0.8rem; opacity: 0.9;'>(apenas NFs)</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        taxa_ampliada = ((com_nf + regularizadas) / validas * 100) if validas > 0 else 0
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #42a5f5 0%, #1e88e5 100%); 
                    padding: 2rem; border-radius: 15px; color: white; text-align: center;'>
            <h2 style='margin: 0; color: white;'>{taxa_ampliada:.2f}%</h2>
            <p style='margin: 0.5rem 0; font-size: 0.9rem;'>Taxa AMPLIADA</p>
            <p style='margin: 0; font-size: 0.8rem; opacity: 0.9;'>(+ regularizações)</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class='alert-alto' style='margin-top: 2rem;'>
    <b>⚠️ IMPACTO NAS MÉTRICAS:</b><br>
    • <b>{int(canceladas):,} infrações ({canceladas/total*100:.1f}%)</b> estão canceladas/excluídas<br>
    • Diferença na taxa: <b>+{(taxa_correta - 66.01):.2f} pontos percentuais</b> ao excluir canceladas<br>
    • <b>{int(regularizadas):,} regularizações sem NF</b> representam cobranças efetivas
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # ========== MÉTRICAS DETALHADAS ==========
    st.markdown("<div class='sub-header'>📊 Métricas Detalhadas</div>", unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Infrações", f"{int(total):,}")
    
    with col2:
        st.metric("✅ Válidas", f"{int(validas):,}", 
                 delta=f"{validas/total*100:.1f}%")
    
    with col3:
        st.metric("❌ Canceladas", f"{int(canceladas):,}", 
                 delta=f"{canceladas/total*100:.1f}%",
                 delta_color="inverse")
    
    with col4:
        st.metric("📄 Com NF", f"{int(com_nf):,}", 
                 delta=f"{com_nf/validas*100:.1f}% das válidas")
    
    with col5:
        st.metric("🔄 Regularizadas", f"{int(regularizadas):,}",
                 delta=f"{regularizadas/validas*100:.1f}% das válidas")
    
    # ========== EVOLUÇÃO TEMPORAL ==========
    if not df_resumo.empty:
        st.markdown("<div class='sub-header'>📈 Evolução das Taxas de Conversão</div>", unsafe_allow_html=True)
        
        fig = go.Figure()
        
        # Taxa incorreta
        df_resumo['taxa_incorreta'] = (df_resumo['com_nf'] / df_resumo['total_infracoes'] * 100).round(2)
        
        fig.add_trace(go.Scatter(
            x=df_resumo['ano'],
            y=df_resumo['taxa_incorreta'],
            name='Taxa Incorreta (com canceladas)',
            mode='lines+markers',
            line=dict(color='#ef5350', width=2, dash='dash'),
            marker=dict(size=8)
        ))
        
        fig.add_trace(go.Scatter(
            x=df_resumo['ano'],
            y=df_resumo['taxa_conversao_formal'],
            name='Taxa Correta (apenas NFs)',
            mode='lines+markers',
            line=dict(color='#4caf50', width=3),
            marker=dict(size=10)
        ))
        
        fig.add_trace(go.Scatter(
            x=df_resumo['ano'],
            y=df_resumo['taxa_efetividade_fiscal'],
            name='Taxa Ampliada (+ regularizações)',
            mode='lines+markers',
            line=dict(color='#1e88e5', width=3),
            marker=dict(size=10)
        ))
        
        fig.add_hline(y=70, line_dash="dot", line_color="gray", 
                     annotation_text="Meta: 70%", annotation_position="right")
        
        fig.update_layout(
            title='Comparação das Taxas de Conversão ao Longo do Tempo',
            template=filtros['tema'],
            height=500,
            xaxis_title='Ano',
            yaxis_title='Taxa de Conversão (%)',
            hovermode='x unified',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # ========== DISTRIBUIÇÃO POR STATUS ==========
    st.markdown("<div class='sub-header'>🔄 Distribuição por Status Normalizado</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        df_status = df_estados.groupby('status_normalizado').agg({
            'qtd': 'sum',
            'com_nf': 'sum',
            'valor_total': 'sum'
        }).reset_index()
        
        fig = px.pie(
            df_status,
            values='qtd',
            names='status_normalizado',
            title='Distribuição de Infrações por Status',
            template=filtros['tema'],
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            y=df_status['status_normalizado'],
            x=df_status['qtd'],
            name='Total',
            orientation='h',
            marker_color='lightblue',
            text=df_status['qtd'],
            textposition='auto'
        ))
        
        fig.add_trace(go.Bar(
            y=df_status['status_normalizado'],
            x=df_status['com_nf'],
            name='Com NF',
            orientation='h',
            marker_color='darkblue',
            text=df_status['com_nf'],
            textposition='auto'
        ))
        
        fig.update_layout(
            title='Infrações vs NFs por Status',
            template=filtros['tema'],
            barmode='group',
            height=400,
            yaxis={'categoryorder': 'total ascending'}
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # ========== TABELA COMPLETA ==========
    st.markdown("<div class='sub-header'>📋 Detalhamento por Estado</div>", unsafe_allow_html=True)
    
    df_display = df_estados.copy()
    df_display['taxa_nf'] = (df_display['com_nf'] / df_display['qtd'] * 100).round(2)
    df_display['perc_total'] = (df_display['qtd'] / total * 100).round(2)
    
    st.dataframe(
        df_display[['estado_documento', 'status_normalizado', 'eh_valida', 
                    'qtd', 'perc_total', 'com_nf', 'taxa_nf', 'valor_total', 'valor_medio']]
        .sort_values('qtd', ascending=False)
        .style.format({
            'perc_total': '{:.2f}%',
            'taxa_nf': '{:.2f}%',
            'valor_total': 'R$ {:,.2f}',
            'valor_medio': 'R$ {:,.2f}'
        })
        .apply(lambda x: ['background-color: #ffebee' if v == 0 else '' 
                         for v in x], subset=['eh_valida'])
        .background_gradient(subset=['qtd'], cmap='YlOrRd'),
        use_container_width=True,
        height=600
    )

def pagina_analise_ges(dados, filtros):
    """Análise por GES (Grupos Especialistas Setoriais)."""
    st.markdown("<h1 class='main-header'>🏭 Análise por GES - Grupos Especialistas Setoriais</h1>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class='info-box'>
    <b>🎯 Grupos Especialistas Setoriais (GES)</b><br>
    Os GES são grupos especializados em setores econômicos específicos, atuando em âmbito estadual 
    com foco em combate à sonegação, análise técnica e planejamento de ações fiscais direcionadas.
    <br><br>
    📌 <b>Análise focada apenas em empresas vinculadas a GES</b> (excluindo GRAFs)
    </div>
    """, unsafe_allow_html=True)
    
    df_ges = dados.get('metricas_ges', pd.DataFrame())
    df_dist_empresas = dados.get('distribuicao_empresas_ges', pd.DataFrame())
    
    if df_ges.empty:
        st.error("Dados de GES não disponíveis.")
        return
    
    # Filtrar por anos
    if filtros.get('anos'):
        df_ges = df_ges[df_ges['ano'].isin(filtros['anos'])]
    
    if df_ges.empty:
        st.warning("⚠️ Nenhum dado encontrado com os filtros aplicados.")
        return
    
    # ========== RESUMO EXECUTIVO ==========
    st.markdown("<div class='sub-header'>📊 Visão Geral dos GES</div>", unsafe_allow_html=True)
    
    # Agregar por GES
    df_resumo = df_ges.groupby('nm_ges').agg({
        'qtd_fiscalizacoes': 'sum',
        'qtd_empresas_unicas': 'sum',
        'qtd_infracoes': 'sum',
        'qtd_nfs': 'sum',
        'valor_total_infracoes': 'sum',
        'valor_total_lancado': 'sum',
        'qtd_regularizadas_sem_nf': 'sum',
        'media_dias_infracao_nf': 'mean',
        'taxa_conversao_infracao_nf': 'mean',
        'taxa_efetividade_fiscal': 'mean'
    }).reset_index()
    
    # KPIs Gerais
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_ges = df_resumo['nm_ges'].nunique()
        st.metric("Total de GES", f"{total_ges}")
    
    with col2:
        total_fisc = df_resumo['qtd_fiscalizacoes'].sum()
        st.metric("Total Fiscalizações", f"{int(total_fisc):,}")
    
    with col3:
        total_empresas = df_resumo['qtd_empresas_unicas'].sum()
        st.metric("Empresas Fiscalizadas", f"{int(total_empresas):,}")
    
    with col4:
        total_nfs = df_resumo['qtd_nfs'].sum()
        st.metric("NFs Emitidas", f"{int(total_nfs):,}")
    
    with col5:
        valor_total = df_resumo['valor_total_lancado'].sum()
        st.metric("Valor Total", formatar_valor(valor_total))
    
    st.divider()
    
    # ========== DISTRIBUIÇÃO DE EMPRESAS ==========
    if not df_dist_empresas.empty:
        st.markdown("<div class='sub-header'>🏢 Distribuição de Empresas por GES</div>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(
                df_dist_empresas.sort_values('qtd_empresas', ascending=True).tail(15),
                y='nm_ges',
                x='qtd_empresas',
                orientation='h',
                title='Top 15 GES - Quantidade de Empresas Cadastradas',
                template=filtros['tema'],
                color='qtd_empresas',
                color_continuous_scale='Blues',
                text='qtd_empresas'
            )
            
            fig.update_traces(textposition='outside')
            fig.update_layout(height=500, showlegend=False)
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.pie(
                df_dist_empresas.nlargest(10, 'qtd_empresas'),
                values='qtd_empresas',
                names='nm_ges',
                title='Top 10 GES - % do Total de Empresas',
                template=filtros['tema'],
                hole=0.4
            )
            
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(height=500)
            
            st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # ========== RANKING DE PERFORMANCE ==========
    st.markdown("<div class='sub-header'>🏆 Ranking de Performance por GES</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        metrica_rank = st.radio(
            "Ordenar por:",
            ['Valor Lançado', 'Quantidade de NFs', 'Taxa de Conversão', 'Efetividade Fiscal'],
            index=0
        )
    
    # Mapear métrica
    mapa_metricas = {
        'Valor Lançado': 'valor_total_lancado',
        'Quantidade de NFs': 'qtd_nfs',
        'Taxa de Conversão': 'taxa_conversao_infracao_nf',
        'Efetividade Fiscal': 'taxa_efetividade_fiscal'
    }
    
    coluna_ordenacao = mapa_metricas[metrica_rank]
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Top 10
        df_top = df_resumo.nlargest(10, coluna_ordenacao)
        
        fig = px.bar(
            df_top.sort_values(coluna_ordenacao, ascending=True),
            y='nm_ges',
            x=coluna_ordenacao,
            orientation='h',
            title=f'Top 10 GES - {metrica_rank}',
            template=filtros['tema'],
            color=coluna_ordenacao,
            color_continuous_scale='Viridis',
            text=coluna_ordenacao
        )
        
        fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        fig.update_layout(height=500, showlegend=False)
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Scatter: Quantidade vs Valor
        fig = px.scatter(
            df_resumo,
            x='qtd_fiscalizacoes',
            y='valor_total_lancado',
            size='qtd_nfs',
            color='taxa_conversao_infracao_nf',
            hover_data=['nm_ges', 'taxa_efetividade_fiscal'],
            title='Relação: Volume vs Valor (tamanho = NFs, cor = Taxa Conversão)',
            template=filtros['tema'],
            color_continuous_scale='RdYlGn',
            labels={
                'qtd_fiscalizacoes': 'Quantidade de Fiscalizações',
                'valor_total_lancado': 'Valor Total Lançado (R$)',
                'taxa_conversao_infracao_nf': 'Taxa Conversão (%)'
            }
        )
        
        fig.update_layout(height=500)
        
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # ========== COMPARAÇÃO DE TAXAS ==========
    st.markdown("<div class='sub-header'>📈 Comparação de Taxas de Conversão e Efetividade</div>", unsafe_allow_html=True)
    
    df_resumo_sorted = df_resumo.sort_values('taxa_conversao_infracao_nf', ascending=False)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=df_resumo_sorted['nm_ges'],
        x=df_resumo_sorted['taxa_conversao_infracao_nf'],
        name='Taxa Conversão (apenas NFs)',
        orientation='h',
        marker_color='#1976d2',
        text=df_resumo_sorted['taxa_conversao_infracao_nf'].round(2),
        textposition='auto'
    ))
    
    fig.add_trace(go.Bar(
        y=df_resumo_sorted['nm_ges'],
        x=df_resumo_sorted['taxa_efetividade_fiscal'],
        name='Efetividade Fiscal (NFs + Regularizações)',
        orientation='h',
        marker_color='#388e3c',
        text=df_resumo_sorted['taxa_efetividade_fiscal'].round(2),
        textposition='auto'
    ))
    
    fig.add_vline(x=70, line_dash="dash", line_color="red", 
                  annotation_text="Meta: 70%", annotation_position="top")
    
    fig.update_layout(
        title='Taxa de Conversão vs Efetividade Fiscal por GES',
        template=filtros['tema'],
        height=600,
        barmode='group',
        xaxis_title='Taxa (%)',
        yaxis={'categoryorder': 'total ascending'}
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # ========== TABELA DETALHADA ==========
    st.markdown("<div class='sub-header'>📋 Tabela Detalhada - Ranking Completo</div>", unsafe_allow_html=True)
    
    df_display = df_resumo.sort_values('valor_total_lancado', ascending=False).copy()
    df_display['ranking'] = range(1, len(df_display) + 1)
    
    # Adicionar participação no total
    total_valor = df_display['valor_total_lancado'].sum()
    df_display['participacao'] = (df_display['valor_total_lancado'] / total_valor * 100).round(2)
    
    cols_display = [
        'ranking', 'nm_ges', 'qtd_fiscalizacoes', 'qtd_empresas_unicas', 
        'qtd_nfs', 'qtd_regularizadas_sem_nf', 'valor_total_lancado', 'participacao',
        'taxa_conversao_infracao_nf', 'taxa_efetividade_fiscal', 'media_dias_infracao_nf'
    ]
    
    st.dataframe(
        df_display[cols_display].style.format({
            'valor_total_lancado': 'R$ {:,.2f}',
            'participacao': '{:.2f}%',
            'taxa_conversao_infracao_nf': '{:.2f}%',
            'taxa_efetividade_fiscal': '{:.2f}%',
            'media_dias_infracao_nf': '{:.0f}'
        }).background_gradient(subset=['valor_total_lancado'], cmap='Greens')
        .background_gradient(subset=['taxa_conversao_infracao_nf'], cmap='RdYlGn'),
        use_container_width=True,
        height=600
    )
    
    # ========== ANÁLISE TEMPORAL ==========
    st.markdown("<div class='sub-header'>📅 Evolução Temporal por GES</div>", unsafe_allow_html=True)
    
    # Seletor de GES
    ges_opcoes = sorted(df_ges['nm_ges'].unique())
    ges_selecionados = st.multiselect(
        "Selecione GES para comparação temporal:",
        ges_opcoes,
        default=ges_opcoes[:5] if len(ges_opcoes) >= 5 else ges_opcoes
    )
    
    if ges_selecionados:
        df_temporal = df_ges[df_ges['nm_ges'].isin(ges_selecionados)]
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.line(
                df_temporal,
                x='ano',
                y='qtd_nfs',
                color='nm_ges',
                title='Evolução do Número de NFs por Ano',
                template=filtros['tema'],
                markers=True
            )
            
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.line(
                df_temporal,
                x='ano',
                y='taxa_conversao_infracao_nf',
                color='nm_ges',
                title='Evolução da Taxa de Conversão por Ano',
                template=filtros['tema'],
                markers=True
            )
            
            fig.add_hline(y=70, line_dash="dash", line_color="gray", 
                         annotation_text="Meta: 70%")
            
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    # ========== INSIGHTS ==========
    st.markdown("<div class='sub-header'>💡 Insights e Recomendações</div>", unsafe_allow_html=True)
    
    # GES com melhor performance
    melhor_ges = df_resumo.nlargest(1, 'taxa_efetividade_fiscal').iloc[0]
    pior_ges = df_resumo.nsmallest(1, 'taxa_efetividade_fiscal').iloc[0]
    
    st.markdown(f"""
    <div class='alert-positivo'>
    <b>✅ MELHOR PERFORMANCE:</b><br>
    • <b>{melhor_ges['nm_ges']}</b>: {melhor_ges['taxa_efetividade_fiscal']:.2f}% de efetividade fiscal<br>
    • {int(melhor_ges['qtd_nfs']):,} NFs emitidas | {formatar_valor(melhor_ges['valor_total_lancado'])} lançados<br>
    • Tempo médio: {melhor_ges['media_dias_infracao_nf']:.0f} dias
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class='alert-alto'>
    <b>⚠️ NECESSITA ATENÇÃO:</b><br>
    • <b>{pior_ges['nm_ges']}</b>: {pior_ges['taxa_efetividade_fiscal']:.2f}% de efetividade fiscal<br>
    • {int(pior_ges['qtd_nfs']):,} NFs emitidas | {formatar_valor(pior_ges['valor_total_lancado'])} lançados<br>
    • Oportunidade de melhoria em processos e conversão
    </div>
    """, unsafe_allow_html=True)

# =============================================================================
# 8.12. PÁGINA ITCMD
# =============================================================================

def pagina_itcmd(dados, filtros):
    """Análise das Ordens de Fiscalização do setor ITCMD."""
    st.markdown("<h1 class='main-header'>📜 ITCMD - Análise de Fiscalizações</h1>", unsafe_allow_html=True)

    st.markdown("""
    <div class='info-box'>
    <b>📜 Setor ITCMD - Imposto sobre Transmissão Causa Mortis e Doação</b><br>
    Análise das Ordens de Fiscalização emitidas pelos coordenadores do setor ITCMD
    (usuários 9507248 e 6172598), incluindo declarações, notificações fiscais e termos de infração.
    </div>
    """, unsafe_allow_html=True)

    # Carregar dados ITCMD sob demanda
    engine = st.session_state.get('engine')
    if engine is None:
        st.error("❌ Conexão com banco de dados não disponível.")
        return

    with st.spinner('⏳ Carregando dados do ITCMD...'):
        dados_itcmd = carregar_dados_itcmd(engine)

    if not dados_itcmd:
        st.warning("⚠️ Não foi possível carregar os dados do ITCMD.")
        return

    # Obter dataframes
    df_of = dados_itcmd.get('of_itcmd', pd.DataFrame())
    df_dde = dados_itcmd.get('dde_itcmd', pd.DataFrame())
    df_notif = dados_itcmd.get('notif_itcmd', pd.DataFrame())
    df_tifdp = dados_itcmd.get('tifdp_itcmd', pd.DataFrame())

    if df_of.empty:
        st.warning("⚠️ Nenhuma Ordem de Fiscalização encontrada para o setor ITCMD.")
        return

    # Aplicar filtros de ano se disponíveis
    if filtros.get('anos') and 'ano' in df_of.columns:
        df_of = df_of[df_of['ano'].isin(filtros['anos'])]
        if not df_dde.empty and 'ano' in df_dde.columns:
            df_dde = df_dde[df_dde['ano'].isin(filtros['anos'])]
        if not df_notif.empty and 'ano' in df_notif.columns:
            df_notif = df_notif[df_notif['ano'].isin(filtros['anos'])]
        if not df_tifdp.empty and 'ano' in df_tifdp.columns:
            df_tifdp = df_tifdp[df_tifdp['ano'].isin(filtros['anos'])]

    # ========== KPIs PRINCIPAIS ==========
    st.markdown("<div class='sub-header'>📊 Indicadores Gerais do ITCMD</div>", unsafe_allow_html=True)

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        total_ofs = len(df_of)
        st.metric("📋 Total de OFs", f"{total_ofs:,}")

    with col2:
        if not df_dde.empty:
            total_dde = len(df_dde)
            st.metric("📄 Declarações (DDE)", f"{total_dde:,}")
        else:
            st.metric("📄 Declarações (DDE)", "0")

    with col3:
        if not df_notif.empty:
            total_notif = len(df_notif)
            st.metric("📑 Notificações", f"{total_notif:,}")
        else:
            st.metric("📑 Notificações", "0")

    with col4:
        if not df_tifdp.empty:
            total_tifdp = len(df_tifdp)
            st.metric("⚖️ Termos Infração", f"{total_tifdp:,}")
        else:
            st.metric("⚖️ Termos Infração", "0")

    with col5:
        # Contribuintes únicos
        contribuintes = set()
        if not df_dde.empty and 'nu_ie' in df_dde.columns:
            contribuintes.update(df_dde['nu_ie'].dropna().unique())
        if not df_notif.empty and 'nu_ie' in df_notif.columns:
            contribuintes.update(df_notif['nu_ie'].dropna().unique())
        st.metric("🏢 Contribuintes", f"{len(contribuintes):,}")

    # Segunda linha de KPIs - Valores
    st.markdown("<div class='sub-header'>💰 Valores Totais</div>", unsafe_allow_html=True)

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        if not df_dde.empty and 'vl_declarado' in df_dde.columns:
            valor_declarado = pd.to_numeric(df_dde['vl_declarado'], errors='coerce').sum()
            st.metric("📝 Valor Declarado", formatar_valor(valor_declarado))
        else:
            st.metric("📝 Valor Declarado", "R$ 0")

    with col2:
        if not df_notif.empty and 'vl_total' in df_notif.columns:
            valor_notif = pd.to_numeric(df_notif['vl_total'], errors='coerce').sum()
            st.metric("📑 Valor Notificações", formatar_valor(valor_notif))
        else:
            st.metric("📑 Valor Notificações", "R$ 0")

    with col3:
        if not df_tifdp.empty and 'vl_apurado' in df_tifdp.columns:
            valor_tifdp = pd.to_numeric(df_tifdp['vl_apurado'], errors='coerce').sum()
            st.metric("⚖️ Valor Apurado TIFDP", formatar_valor(valor_tifdp))
        else:
            st.metric("⚖️ Valor Apurado TIFDP", "R$ 0")

    with col4:
        # Total pago (todas as fontes)
        total_pago = 0
        if not df_dde.empty and 'vl_pago' in df_dde.columns:
            total_pago += pd.to_numeric(df_dde['vl_pago'], errors='coerce').sum()
        if not df_notif.empty and 'vl_pago' in df_notif.columns:
            total_pago += pd.to_numeric(df_notif['vl_pago'], errors='coerce').sum()
        if not df_tifdp.empty and 'vl_pago' in df_tifdp.columns:
            total_pago += pd.to_numeric(df_tifdp['vl_pago'], errors='coerce').sum()
        st.metric("💵 Total Pago", formatar_valor(total_pago))

    with col5:
        # Taxa de recuperação
        valor_total_lancado = 0
        if not df_notif.empty and 'vl_total' in df_notif.columns:
            valor_total_lancado = pd.to_numeric(df_notif['vl_total'], errors='coerce').sum()
        if valor_total_lancado > 0:
            taxa_recuperacao = (total_pago / valor_total_lancado) * 100
            st.metric("📈 Taxa Recuperação", f"{taxa_recuperacao:.1f}%")
        else:
            st.metric("📈 Taxa Recuperação", "N/A")

    st.divider()

    # ========== ANÁLISE TEMPORAL ==========
    st.markdown("<div class='sub-header'>📈 Evolução Temporal</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        # Evolução de OFs por ano
        if 'ano' in df_of.columns:
            df_of_ano = df_of.groupby('ano').size().reset_index(name='quantidade')
            df_of_ano = df_of_ano.sort_values('ano')

            fig = px.bar(
                df_of_ano,
                x='ano',
                y='quantidade',
                title='📋 Ordens de Fiscalização por Ano',
                template=filtros['tema'],
                color='quantidade',
                color_continuous_scale='Blues',
                text='quantidade'
            )
            fig.update_traces(textposition='outside')
            fig.update_layout(height=400, xaxis_title='Ano', yaxis_title='Quantidade de OFs')
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Evolução de valores por ano
        if not df_notif.empty and 'ano' in df_notif.columns:
            df_notif['vl_total_num'] = pd.to_numeric(df_notif['vl_total'], errors='coerce')
            df_notif['vl_pago_num'] = pd.to_numeric(df_notif['vl_pago'], errors='coerce')

            df_valor_ano = df_notif.groupby('ano').agg({
                'vl_total_num': 'sum',
                'vl_pago_num': 'sum'
            }).reset_index()

            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df_valor_ano['ano'],
                y=df_valor_ano['vl_total_num'],
                name='Valor Total',
                marker_color='#1976d2'
            ))
            fig.add_trace(go.Bar(
                x=df_valor_ano['ano'],
                y=df_valor_ano['vl_pago_num'],
                name='Valor Pago',
                marker_color='#388e3c'
            ))
            fig.update_layout(
                title='💰 Valores de Notificações por Ano',
                template=filtros['tema'],
                height=400,
                barmode='group',
                xaxis_title='Ano',
                yaxis_title='Valor (R$)'
            )
            st.plotly_chart(fig, use_container_width=True)

    # ========== ANÁLISE POR ESTADO DA OF ==========
    st.markdown("<div class='sub-header'>🔄 Situação das Ordens de Fiscalização</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if 'nm_estado' in df_of.columns:
            df_estado = df_of['nm_estado'].value_counts().reset_index()
            df_estado.columns = ['estado', 'quantidade']

            fig = px.pie(
                df_estado,
                values='quantidade',
                names='estado',
                title='📊 Distribuição por Situação',
                template=filtros['tema'],
                hole=0.4
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        if 'nm_estado' in df_of.columns and 'ano' in df_of.columns:
            df_estado_ano = df_of.groupby(['ano', 'nm_estado']).size().reset_index(name='quantidade')

            fig = px.bar(
                df_estado_ano,
                x='ano',
                y='quantidade',
                color='nm_estado',
                title='📈 Evolução por Situação',
                template=filtros['tema'],
                barmode='stack'
            )
            fig.update_layout(height=400, xaxis_title='Ano', yaxis_title='Quantidade')
            st.plotly_chart(fig, use_container_width=True)

    # ========== ANÁLISE POR GERÊNCIA ==========
    st.markdown("<div class='sub-header'>🏢 Análise por Gerência/Local</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if 'nm_gerencia' in df_of.columns:
            df_gerencia = df_of['nm_gerencia'].value_counts().head(10).reset_index()
            df_gerencia.columns = ['gerencia', 'quantidade']

            fig = px.bar(
                df_gerencia,
                y='gerencia',
                x='quantidade',
                title='🏢 OFs por Gerência (Top 10)',
                template=filtros['tema'],
                orientation='h',
                color='quantidade',
                color_continuous_scale='Blues',
                text='quantidade'
            )
            fig.update_traces(textposition='outside')
            fig.update_layout(height=400, yaxis_title='', xaxis_title='Quantidade')
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        if 'nm_local_emissao' in df_of.columns:
            df_local = df_of['nm_local_emissao'].value_counts().head(10).reset_index()
            df_local.columns = ['local', 'quantidade']

            fig = px.bar(
                df_local,
                y='local',
                x='quantidade',
                title='📍 OFs por Local de Emissão (Top 10)',
                template=filtros['tema'],
                orientation='h',
                color='quantidade',
                color_continuous_scale='Greens',
                text='quantidade'
            )
            fig.update_traces(textposition='outside')
            fig.update_layout(height=400, yaxis_title='', xaxis_title='Quantidade')
            st.plotly_chart(fig, use_container_width=True)

    # ========== CRUZAMENTO: NOTIFICAÇÕES ==========
    if not df_notif.empty:
        st.markdown("<div class='sub-header'>📑 Análise de Notificações Fiscais</div>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            if 'nm_estado' in df_notif.columns:
                df_notif_estado = df_notif['nm_estado'].value_counts().reset_index()
                df_notif_estado.columns = ['estado', 'quantidade']

                fig = px.pie(
                    df_notif_estado,
                    values='quantidade',
                    names='estado',
                    title='📊 Notificações por Estado',
                    template=filtros['tema'],
                    hole=0.4
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            if 'cd_infracao' in df_notif.columns:
                df_infracao = df_notif['cd_infracao'].value_counts().head(10).reset_index()
                df_infracao.columns = ['cod_infracao', 'quantidade']

                fig = px.bar(
                    df_infracao,
                    y='cod_infracao',
                    x='quantidade',
                    title='⚖️ Top 10 Códigos de Infração',
                    template=filtros['tema'],
                    orientation='h',
                    color='quantidade',
                    color_continuous_scale='Reds',
                    text='quantidade'
                )
                fig.update_traces(textposition='outside')
                fig.update_layout(height=400, yaxis_title='Código', xaxis_title='Quantidade')
                st.plotly_chart(fig, use_container_width=True)

        # Maiores notificações
        st.markdown("#### 🏆 Maiores Notificações por Valor")
        df_notif['vl_total_num'] = pd.to_numeric(df_notif['vl_total'], errors='coerce')
        df_top_notif = df_notif.nlargest(10, 'vl_total_num')[['nu_notificacao_fiscal', 'nm_razao_social', 'vl_total', 'vl_pago', 'nm_estado', 'dt_documento']]
        df_top_notif.columns = ['Notificação', 'Razão Social', 'Valor Total', 'Valor Pago', 'Estado', 'Data']
        st.dataframe(df_top_notif, use_container_width=True)

    # ========== CRUZAMENTO: TIFDP ==========
    if not df_tifdp.empty:
        st.markdown("<div class='sub-header'>⚖️ Análise de Termos de Infração (TIFDP)</div>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            if 'nm_estado' in df_tifdp.columns:
                df_tifdp_estado = df_tifdp['nm_estado'].value_counts().reset_index()
                df_tifdp_estado.columns = ['estado', 'quantidade']

                fig = px.pie(
                    df_tifdp_estado,
                    values='quantidade',
                    names='estado',
                    title='📊 TIFDP por Estado',
                    template=filtros['tema'],
                    hole=0.4
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Taxa de conversão em notificação
            total_tifdp = len(df_tifdp)
            convertidos = df_tifdp['nu_notificacao_gerada'].notna().sum() if 'nu_notificacao_gerada' in df_tifdp.columns else 0
            nao_convertidos = total_tifdp - convertidos

            fig = go.Figure(data=[go.Pie(
                labels=['Convertidos em NF', 'Não Convertidos'],
                values=[convertidos, nao_convertidos],
                hole=0.5,
                marker_colors=['#388e3c', '#c62828']
            )])
            fig.update_layout(
                title=f'📈 Taxa de Conversão TIFDP → NF ({(convertidos/total_tifdp*100):.1f}%)',
                template=filtros['tema'],
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)

        # Maiores valores apurados
        st.markdown("#### 🏆 Maiores Valores Apurados (TIFDP)")
        df_tifdp['vl_apurado_num'] = pd.to_numeric(df_tifdp['vl_apurado'], errors='coerce')
        df_top_tifdp = df_tifdp.nlargest(10, 'vl_apurado_num')[['nu_infr_fiscal', 'nm_razao_social', 'vl_apurado', 'vl_pago', 'nm_estado', 'dt_documento']]
        df_top_tifdp.columns = ['Termo Infração', 'Razão Social', 'Valor Apurado', 'Valor Pago', 'Estado', 'Data']
        st.dataframe(df_top_tifdp, use_container_width=True)

    # ========== CRUZAMENTO: DDE ==========
    if not df_dde.empty:
        st.markdown("<div class='sub-header'>📄 Análise de Declarações (DDE)</div>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            # Valores declarados vs pagos por ano
            df_dde['vl_declarado_num'] = pd.to_numeric(df_dde['vl_declarado'], errors='coerce')
            df_dde['vl_pago_num'] = pd.to_numeric(df_dde['vl_pago'], errors='coerce')

            if 'ano' in df_dde.columns:
                df_dde_ano = df_dde.groupby('ano').agg({
                    'vl_declarado_num': 'sum',
                    'vl_pago_num': 'sum'
                }).reset_index()

                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=df_dde_ano['ano'],
                    y=df_dde_ano['vl_declarado_num'],
                    name='Valor Declarado',
                    marker_color='#1976d2'
                ))
                fig.add_trace(go.Bar(
                    x=df_dde_ano['ano'],
                    y=df_dde_ano['vl_pago_num'],
                    name='Valor Pago',
                    marker_color='#388e3c'
                ))
                fig.update_layout(
                    title='💰 Declarações: Valores por Ano',
                    template=filtros['tema'],
                    height=400,
                    barmode='group',
                    xaxis_title='Ano',
                    yaxis_title='Valor (R$)'
                )
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Distribuição por estado da conta
            if 'cd_estado_conta' in df_dde.columns:
                df_estado_conta = df_dde['cd_estado_conta'].value_counts().reset_index()
                df_estado_conta.columns = ['estado_conta', 'quantidade']

                fig = px.bar(
                    df_estado_conta,
                    x='estado_conta',
                    y='quantidade',
                    title='📊 Declarações por Estado da Conta',
                    template=filtros['tema'],
                    color='quantidade',
                    color_continuous_scale='Purples',
                    text='quantidade'
                )
                fig.update_traces(textposition='outside')
                fig.update_layout(height=400, xaxis_title='Código Estado', yaxis_title='Quantidade')
                st.plotly_chart(fig, use_container_width=True)

    # ========== PERFORMANCE - TEMPO DE FISCALIZAÇÃO ==========
    st.markdown("<div class='sub-header'>⏱️ Performance - Tempo de Fiscalização</div>", unsafe_allow_html=True)

    if 'dt_inicio' in df_of.columns and 'dt_fim' in df_of.columns:
        df_of_tempo = df_of.copy()
        df_of_tempo['dt_inicio'] = pd.to_datetime(df_of_tempo['dt_inicio'], errors='coerce')
        df_of_tempo['dt_fim'] = pd.to_datetime(df_of_tempo['dt_fim'], errors='coerce')
        df_of_tempo['dias_fiscalizacao'] = (df_of_tempo['dt_fim'] - df_of_tempo['dt_inicio']).dt.days

        # Filtrar valores válidos
        df_of_tempo = df_of_tempo[df_of_tempo['dias_fiscalizacao'].notna() & (df_of_tempo['dias_fiscalizacao'] > 0)]

        if not df_of_tempo.empty:
            col1, col2, col3 = st.columns(3)

            with col1:
                media_dias = df_of_tempo['dias_fiscalizacao'].mean()
                st.metric("⏱️ Tempo Médio", f"{media_dias:.0f} dias")

            with col2:
                mediana_dias = df_of_tempo['dias_fiscalizacao'].median()
                st.metric("📊 Mediana", f"{mediana_dias:.0f} dias")

            with col3:
                max_dias = df_of_tempo['dias_fiscalizacao'].max()
                st.metric("📈 Máximo", f"{max_dias:.0f} dias")

            # Histograma de tempo
            fig = px.histogram(
                df_of_tempo,
                x='dias_fiscalizacao',
                nbins=30,
                title='📊 Distribuição do Tempo de Fiscalização',
                template=filtros['tema'],
                labels={'dias_fiscalizacao': 'Dias de Fiscalização'}
            )
            fig.update_layout(height=350, xaxis_title='Dias', yaxis_title='Frequência')
            st.plotly_chart(fig, use_container_width=True)

    # ========== ANÁLISE POR MOTIVAÇÃO ==========
    st.markdown("<div class='sub-header'>🎯 Análise por Motivação da OF</div>", unsafe_allow_html=True)

    if 'tx_motivacao_of' in df_of.columns:
        df_motivacao = df_of['tx_motivacao_of'].value_counts().head(10).reset_index()
        df_motivacao.columns = ['motivacao', 'quantidade']

        fig = px.bar(
            df_motivacao,
            y='motivacao',
            x='quantidade',
            title='🎯 OFs por Tipo de Motivação (Top 10)',
            template=filtros['tema'],
            orientation='h',
            color='quantidade',
            color_continuous_scale='Viridis',
            text='quantidade'
        )
        fig.update_traces(textposition='outside')
        fig.update_layout(height=400, yaxis_title='', xaxis_title='Quantidade')
        st.plotly_chart(fig, use_container_width=True)

    # ========== INFRAÇÕES COM DESCRIÇÕES ==========
    df_catalogo = dados_itcmd.get('catalogo_infracoes', pd.DataFrame())

    if not df_catalogo.empty and not df_notif.empty and 'cd_infracao' in df_notif.columns:
        st.markdown("<div class='sub-header'>📖 Análise de Infrações (com Descrições)</div>", unsafe_allow_html=True)

        # Enriquecer notificações com descrições
        df_notif_enriq = df_notif.merge(
            df_catalogo[['cd_infracao', 'de_infracao', 'nm_tributo']],
            on='cd_infracao',
            how='left'
        )

        col1, col2 = st.columns(2)

        with col1:
            # Top infrações por descrição
            df_inf_desc = df_notif_enriq.groupby('de_infracao').agg({
                'nu_notificacao_fiscal': 'count',
                'vl_total': lambda x: pd.to_numeric(x, errors='coerce').sum()
            }).reset_index()
            df_inf_desc.columns = ['descricao', 'quantidade', 'valor_total']
            df_inf_desc = df_inf_desc.nlargest(10, 'quantidade')

            fig = px.bar(
                df_inf_desc,
                y='descricao',
                x='quantidade',
                title='📖 Top 10 Infrações por Descrição',
                template=filtros['tema'],
                orientation='h',
                color='quantidade',
                color_continuous_scale='Reds',
                text='quantidade'
            )
            fig.update_traces(textposition='outside')
            fig.update_layout(height=450, yaxis_title='', xaxis_title='Quantidade')
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Valor por tipo de infração
            df_inf_valor = df_inf_desc.nlargest(10, 'valor_total')

            fig = px.bar(
                df_inf_valor,
                y='descricao',
                x='valor_total',
                title='💰 Valor Total por Tipo de Infração',
                template=filtros['tema'],
                orientation='h',
                color='valor_total',
                color_continuous_scale='Oranges',
                text_auto='.2s'
            )
            fig.update_layout(height=450, yaxis_title='', xaxis_title='Valor (R$)')
            st.plotly_chart(fig, use_container_width=True)

        # Tabela detalhada de infrações
        st.markdown("#### 📋 Catálogo de Infrações Utilizadas")
        infracoes_usadas = df_notif_enriq[['cd_infracao', 'de_infracao', 'nm_tributo']].drop_duplicates()
        infracoes_usadas.columns = ['Código', 'Descrição', 'Tributo']
        st.dataframe(infracoes_usadas.head(20), use_container_width=True)

    # ========== PERFORMANCE DOS AFREs ==========
    df_afre = dados_itcmd.get('afre_periodo', pd.DataFrame())

    if not df_afre.empty:
        st.markdown("<div class='sub-header'>👥 Performance dos AFREs no ITCMD</div>", unsafe_allow_html=True)

        # Contar OFs por AFRE (emitente)
        df_of_afre = df_of.copy()
        df_of_afre['nu_mat_emitente'] = df_of_afre['nu_mat_emitente'].astype(str).str.strip()

        df_ranking_afre = df_of_afre.groupby('nu_mat_emitente').agg({
            'nu_of': 'count',
            'dt_documento': ['min', 'max']
        }).reset_index()
        df_ranking_afre.columns = ['matricula', 'qtd_ofs', 'primeira_of', 'ultima_of']

        # Tentar enriquecer com nome do AFRE
        if 'nm_afre' in df_afre.columns:
            df_afre_nomes = df_afre[['cd_matricula', 'nm_afre']].drop_duplicates()
            df_afre_nomes['cd_matricula'] = df_afre_nomes['cd_matricula'].astype(str).str.strip()
            df_ranking_afre = df_ranking_afre.merge(
                df_afre_nomes,
                left_on='matricula',
                right_on='cd_matricula',
                how='left'
            )

        col1, col2, col3 = st.columns(3)

        with col1:
            total_afres = df_ranking_afre['matricula'].nunique()
            st.metric("👥 Total AFREs", f"{total_afres}")

        with col2:
            media_ofs = df_ranking_afre['qtd_ofs'].mean()
            st.metric("📊 Média OFs/AFRE", f"{media_ofs:.1f}")

        with col3:
            max_ofs = df_ranking_afre['qtd_ofs'].max()
            st.metric("🏆 Máximo OFs", f"{max_ofs}")

        # Ranking de AFREs
        st.markdown("#### 🏆 Ranking de AFREs por Volume de OFs")
        df_ranking_display = df_ranking_afre.nlargest(15, 'qtd_ofs')

        if 'nm_afre' in df_ranking_display.columns:
            colunas_rank = ['matricula', 'nm_afre', 'qtd_ofs', 'primeira_of', 'ultima_of']
        else:
            colunas_rank = ['matricula', 'qtd_ofs', 'primeira_of', 'ultima_of']

        colunas_rank = [c for c in colunas_rank if c in df_ranking_display.columns]
        st.dataframe(df_ranking_display[colunas_rank], use_container_width=True)

        # Gráfico de barras
        fig = px.bar(
            df_ranking_display.head(10),
            x='matricula',
            y='qtd_ofs',
            title='📊 Top 10 AFREs por Quantidade de OFs',
            template=filtros['tema'],
            color='qtd_ofs',
            color_continuous_scale='Blues',
            text='qtd_ofs'
        )
        fig.update_traces(textposition='outside')
        fig.update_layout(height=400, xaxis_title='Matrícula AFRE', yaxis_title='Quantidade de OFs')
        st.plotly_chart(fig, use_container_width=True)

    # ========== PERFIL DOS CONTRIBUINTES ==========
    df_contrib = dados_itcmd.get('contribuintes', pd.DataFrame())

    if not df_contrib.empty:
        st.markdown("<div class='sub-header'>🏢 Perfil dos Contribuintes</div>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            # Distribuição por CNAE
            if 'de_secao' in df_contrib.columns:
                df_cnae = df_contrib['de_secao'].value_counts().head(10).reset_index()
                df_cnae.columns = ['setor', 'quantidade']

                fig = px.pie(
                    df_cnae,
                    values='quantidade',
                    names='setor',
                    title='🏭 Distribuição por Setor Econômico (CNAE)',
                    template=filtros['tema'],
                    hole=0.4
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Distribuição por regime tributário
            if 'nm_enq_empresa' in df_contrib.columns:
                df_regime = df_contrib['nm_enq_empresa'].value_counts().reset_index()
                df_regime.columns = ['regime', 'quantidade']

                fig = px.bar(
                    df_regime,
                    x='regime',
                    y='quantidade',
                    title='📊 Distribuição por Regime Tributário',
                    template=filtros['tema'],
                    color='quantidade',
                    color_continuous_scale='Purples',
                    text='quantidade'
                )
                fig.update_traces(textposition='outside')
                fig.update_layout(height=400, xaxis_title='Regime', yaxis_title='Quantidade')
                st.plotly_chart(fig, use_container_width=True)

        # Análise de reincidência
        st.markdown("#### 🔄 Análise de Reincidência")

        # Contar contribuintes com múltiplas ocorrências
        df_todas_ies = pd.concat([
            df_dde[['nu_ie']].dropna() if not df_dde.empty and 'nu_ie' in df_dde.columns else pd.DataFrame(),
            df_notif[['nu_ie']].dropna() if not df_notif.empty and 'nu_ie' in df_notif.columns else pd.DataFrame(),
            df_tifdp[['nu_ie']].dropna() if not df_tifdp.empty and 'nu_ie' in df_tifdp.columns else pd.DataFrame()
        ])

        if not df_todas_ies.empty:
            reincidencia = df_todas_ies['nu_ie'].value_counts()
            reincidentes = (reincidencia > 1).sum()
            total_contrib = len(reincidencia)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🏢 Total Contribuintes", f"{total_contrib:,}")
            with col2:
                st.metric("🔄 Reincidentes", f"{reincidentes:,}")
            with col3:
                taxa_reinc = (reincidentes / total_contrib * 100) if total_contrib > 0 else 0
                st.metric("📊 Taxa Reincidência", f"{taxa_reinc:.1f}%")

    # ========== ACOMPANHAMENTOS (FOLLOW-UPS) ==========
    df_acomp = dados_itcmd.get('acompanhamentos', pd.DataFrame())

    if not df_acomp.empty:
        st.markdown("<div class='sub-header'>📋 Acompanhamentos (Follow-ups)</div>", unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)

        with col1:
            total_acomp = len(df_acomp)
            st.metric("📋 Total Acompanhamentos", f"{total_acomp:,}")

        with col2:
            ofs_com_acomp = df_acomp['nu_documento_of'].nunique()
            st.metric("📁 OFs com Follow-up", f"{ofs_com_acomp:,}")

        with col3:
            taxa_acomp = (ofs_com_acomp / len(df_of) * 100) if len(df_of) > 0 else 0
            st.metric("📊 Taxa Follow-up", f"{taxa_acomp:.1f}%")

        col1, col2 = st.columns(2)

        with col1:
            # Status dos acompanhamentos
            if 'nm_estado_os' in df_acomp.columns:
                df_status_acomp = df_acomp['nm_estado_os'].value_counts().reset_index()
                df_status_acomp.columns = ['status', 'quantidade']

                fig = px.pie(
                    df_status_acomp,
                    values='quantidade',
                    names='status',
                    title='📊 Status dos Acompanhamentos',
                    template=filtros['tema'],
                    hole=0.4
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Últimos acompanhamentos
            st.markdown("#### 📋 Últimos Acompanhamentos")
            colunas_acomp = ['nu_documento_of', 'nm_estado_os', 'dt_documento_os', 'de_motivo_os']
            colunas_acomp = [c for c in colunas_acomp if c in df_acomp.columns]
            st.dataframe(df_acomp[colunas_acomp].head(10), use_container_width=True)

    # ========== TERMOS DE ENCERRAMENTO ==========
    df_termo = dados_itcmd.get('termos_encerramento', pd.DataFrame())

    if not df_termo.empty:
        st.markdown("<div class='sub-header'>📑 Termos de Encerramento</div>", unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)

        with col1:
            total_termos = len(df_termo)
            st.metric("📑 Total Termos", f"{total_termos:,}")

        with col2:
            ofs_encerradas = df_termo['os'].nunique()
            st.metric("✅ OFs Encerradas", f"{ofs_encerradas:,}")

        with col3:
            taxa_encerramento = (ofs_encerradas / len(df_of) * 100) if len(df_of) > 0 else 0
            st.metric("📊 Taxa Encerramento", f"{taxa_encerramento:.1f}%")

        col1, col2 = st.columns(2)

        with col1:
            # Status dos encerramentos
            if 'nm_estado' in df_termo.columns:
                df_status_termo = df_termo['nm_estado'].value_counts().reset_index()
                df_status_termo.columns = ['status', 'quantidade']

                fig = px.pie(
                    df_status_termo,
                    values='quantidade',
                    names='status',
                    title='📊 Status dos Encerramentos',
                    template=filtros['tema'],
                    hole=0.4
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Funil de conclusão
            st.markdown("#### 🔄 Funil de Conclusão")

            total_ofs = len(df_of)
            ofs_com_notif = df_notif['nu_of'].nunique() if not df_notif.empty else 0
            ofs_encerradas = df_termo['os'].nunique()

            fig = go.Figure(go.Funnel(
                y=['OFs Abertas', 'Com Notificação', 'Encerradas'],
                x=[total_ofs, ofs_com_notif, ofs_encerradas],
                textinfo="value+percent initial",
                marker_color=['#1976d2', '#388e3c', '#7b1fa2']
            ))
            fig.update_layout(
                title='Funil: OF → Notificação → Encerramento',
                template=filtros['tema'],
                height=350
            )
            st.plotly_chart(fig, use_container_width=True)

        # Tabela de termos recentes
        st.markdown("#### 📋 Termos de Encerramento Recentes")
        colunas_termo = ['nu_termo_encerramento', 'os', 'nm_estado', 'dt_documento', 'dt_encerramento']
        colunas_termo = [c for c in colunas_termo if c in df_termo.columns]
        st.dataframe(df_termo[colunas_termo].head(15), use_container_width=True)

    # ========== DETALHAMENTO - TABELAS ==========
    st.markdown("<div class='sub-header'>📋 Detalhamento dos Dados</div>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["📋 Ordens de Fiscalização", "📄 Declarações (DDE)", "📑 Notificações", "⚖️ Termos Infração"])

    with tab1:
        st.markdown("#### Ordens de Fiscalização do ITCMD")
        colunas_of = ['nu_of', 'dt_documento', 'nm_estado', 'nm_gerencia', 'tx_motivacao_of', 'nm_local_emissao']
        colunas_of_disponiveis = [c for c in colunas_of if c in df_of.columns]
        st.dataframe(df_of[colunas_of_disponiveis].head(100), use_container_width=True)
        st.caption(f"Exibindo até 100 de {len(df_of):,} registros")

    with tab2:
        if not df_dde.empty:
            st.markdown("#### Declarações vinculadas às OFs do ITCMD")
            colunas_dde = ['nu_declaracao', 'nu_of', 'nm_razao_social', 'vl_declarado', 'vl_pago', 'dt_entrega']
            colunas_dde_disponiveis = [c for c in colunas_dde if c in df_dde.columns]
            st.dataframe(df_dde[colunas_dde_disponiveis].head(100), use_container_width=True)
            st.caption(f"Exibindo até 100 de {len(df_dde):,} registros")
        else:
            st.info("Nenhuma declaração encontrada.")

    with tab3:
        if not df_notif.empty:
            st.markdown("#### Notificações Fiscais vinculadas às OFs do ITCMD")
            colunas_notif = ['nu_notificacao_fiscal', 'nu_of', 'nm_razao_social', 'vl_total', 'vl_pago', 'nm_estado', 'dt_documento']
            colunas_notif_disponiveis = [c for c in colunas_notif if c in df_notif.columns]
            st.dataframe(df_notif[colunas_notif_disponiveis].head(100), use_container_width=True)
            st.caption(f"Exibindo até 100 de {len(df_notif):,} registros")
        else:
            st.info("Nenhuma notificação encontrada.")

    with tab4:
        if not df_tifdp.empty:
            st.markdown("#### Termos de Infração vinculados às OFs do ITCMD")
            colunas_tifdp = ['nu_infr_fiscal', 'nu_of', 'nm_razao_social', 'vl_apurado', 'vl_pago', 'nm_estado', 'dt_documento']
            colunas_tifdp_disponiveis = [c for c in colunas_tifdp if c in df_tifdp.columns]
            st.dataframe(df_tifdp[colunas_tifdp_disponiveis].head(100), use_container_width=True)
            st.caption(f"Exibindo até 100 de {len(df_tifdp):,} registros")
        else:
            st.info("Nenhum termo de infração encontrado.")

    # ========== RESUMO FINAL ==========
    st.markdown("<div class='sub-header'>📊 Resumo Consolidado ITCMD</div>", unsafe_allow_html=True)

    # Calcular métricas consolidadas
    valor_total_lancado = 0
    valor_total_pago = 0

    if not df_notif.empty and 'vl_total' in df_notif.columns:
        valor_total_lancado += pd.to_numeric(df_notif['vl_total'], errors='coerce').sum()
    if not df_tifdp.empty and 'vl_apurado' in df_tifdp.columns:
        valor_total_lancado += pd.to_numeric(df_tifdp['vl_apurado'], errors='coerce').sum()

    if not df_notif.empty and 'vl_pago' in df_notif.columns:
        valor_total_pago += pd.to_numeric(df_notif['vl_pago'], errors='coerce').sum()
    if not df_tifdp.empty and 'vl_pago' in df_tifdp.columns:
        valor_total_pago += pd.to_numeric(df_tifdp['vl_pago'], errors='coerce').sum()
    if not df_dde.empty and 'vl_pago' in df_dde.columns:
        valor_total_pago += pd.to_numeric(df_dde['vl_pago'], errors='coerce').sum()

    taxa_recuperacao_geral = (valor_total_pago / valor_total_lancado * 100) if valor_total_lancado > 0 else 0

    st.markdown(f"""
    <div class='alert-positivo'>
    <b>📊 RESUMO DO SETOR ITCMD:</b><br>
    • <b>Total de OFs:</b> {len(df_of):,}<br>
    • <b>Valor Total Lançado:</b> {formatar_valor(valor_total_lancado)}<br>
    • <b>Valor Total Recuperado:</b> {formatar_valor(valor_total_pago)}<br>
    • <b>Taxa de Recuperação:</b> {taxa_recuperacao_geral:.2f}%<br>
    • <b>Contribuintes Fiscalizados:</b> {len(contribuintes):,}
    </div>
    """, unsafe_allow_html=True)

# =============================================================================
# 9. FUNÇÃO PRINCIPAL
# =============================================================================

def main():
    """Função principal do dashboard."""
    
    # Sidebar - Header
    st.sidebar.markdown("""
    <div style='text-align: center; padding: 20px; background: linear-gradient(135deg, #1976d2 0%, #0d47a1 100%); border-radius: 10px; margin-bottom: 20px;'>
        <h1 style='color: white; margin: 0;'>🎯</h1>
        <p style='color: white; margin: 0; font-size: 0.9rem;'>Sistema FISCA</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Menu de navegação
    st.sidebar.markdown("### 📋 Menu de Navegação")
    
    paginas = {
        "📊 Dashboard Executivo": pagina_dashboard_executivo,
        "📜 ITCMD": pagina_itcmd,
        "📋 Ciclo de Vida - Estados": pagina_analise_estados,
        "🏢 Análise por Gerência": pagina_analise_gerencias,
        "🏭 Análise por GES": pagina_analise_ges,
        "🏭 Análise por CNAE": pagina_analise_cnae,
        "🗺️ Análise por Município": pagina_analise_municipios,
        "👥 Performance AFREs": pagina_analise_afres,
        "⚖️ Tipos de Infrações": pagina_tipos_infracoes,
        "🔎 Drill-Down Empresa": pagina_drill_down_empresa,
        "🤖 Machine Learning": pagina_machine_learning,
        "ℹ️ Sobre o Sistema": pagina_sobre
    }
    
    pagina_selecionada = st.sidebar.radio(
        "Selecione a página",
        list(paginas.keys()),
        label_visibility="collapsed"
    )
    
    st.sidebar.markdown("---")
    
    # Criar engine e carregar dados
    engine = get_impala_engine()
    
    # Salvar engine no session_state
    if 'engine' not in st.session_state:
        st.session_state['engine'] = engine
    
    if engine is None:
        st.error("❌ Não foi possível conectar ao banco de dados.")
        st.stop()
    
    with st.spinner('⏳ Carregando dados do sistema...'):
        dados = carregar_dados_sistema(engine)
    
    if not dados:
        st.error("❌ Falha no carregamento dos dados.")
        st.stop()
    
    # Info na sidebar
    df_stats = dados.get('fiscalizacoes_stats', pd.DataFrame())
    
    if not df_stats.empty:
        st.sidebar.success(f"✅ Dados carregados")
        
        stats = df_stats.iloc[0]
        
        st.sidebar.info(f"""
        **📊 Resumo:**
        
        📋 {int(stats.get('total_fiscalizacoes', 0)):,} fiscalizações  
        🏢 {int(stats.get('total_empresas', 0)):,} empresas  
        📄 {int(stats.get('total_nfs', 0)):,} NFs
        """)
    
    # Filtros
    filtros = criar_filtros_sidebar(dados)
    
    st.sidebar.markdown("---")
    
    # Rodapé sidebar
    with st.sidebar.expander("ℹ️ Informações do Sistema"):
        st.caption(f"""
        **Versão:** 1.0  
        **Atualização:** {datetime.now().strftime('%d/%m/%Y %H:%M')}   
        **Órgão:** SEFAZ/SC
        """)
    
    # Executar página selecionada
    try:
        paginas[pagina_selecionada](dados, filtros)
    except Exception as e:
        st.error(f"❌ Erro ao carregar a página: {str(e)}")
        with st.expander("🔍 Detalhes do erro"):
            st.exception(e)
    
    # Rodapé
    st.markdown("---")
    st.markdown(f"""
    <div style='text-align: center; color: #666; font-size: 0.85rem;'>
        <b>Sistema FISCA v1.0</b> | Receita Estadual de Santa Catarina<br>
        {datetime.now().strftime('%d/%m/%Y %H:%M')}
    </div>
    """, unsafe_allow_html=True)

# =============================================================================
# 10. EXECUÇÃO
# =============================================================================

if __name__ == "__main__":
    main()
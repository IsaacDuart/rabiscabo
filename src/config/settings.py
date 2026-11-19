
from .loader import load_environment, positive_number

LOOPBACK = "127.0.0.1"


MAX_COORDINATE = 65535
MAX_PRESSURE = 4095
MAX_EVENTS = 24
MAX_SCROLL = 960
MAX_BODY = 2048
MAX_SEQUENCE = 2**53 - 1
SCROLL_CODE = 3

_values = load_environment()
PROPORCAO = _values["MESA_PROPORCAO"]
TAMANHO_AREA = positive_number(_values, "MESA_TAMANHO_AREA", int)
TEMPO_SESSAO = positive_number(_values, "MESA_TEMPO_SESSAO", float)
INTERVALO_RECONEXAO = positive_number(_values, "MESA_INTERVALO_RECONEXAO", float)
TEMPO_ABERTURA_PAGINA = positive_number(_values, "MESA_TEMPO_ABERTURA_PAGINA", float)
INTERVALO_VERIFICACAO = positive_number(_values, "MESA_INTERVALO_VERIFICACAO", float)
TEMPO_CORPO_HTTP = positive_number(_values, "MESA_TEMPO_CORPO_HTTP", float)
LIMITE_CONEXOES_HTTP = positive_number(_values, "MESA_LIMITE_CONEXOES_HTTP", int)
TEMPO_KEEP_ALIVE_HTTP = positive_number(_values, "MESA_TEMPO_KEEP_ALIVE_HTTP", int)
TEMPO_ENCERRAMENTO_HTTP = positive_number(_values, "MESA_TEMPO_ENCERRAMENTO_HTTP", int)

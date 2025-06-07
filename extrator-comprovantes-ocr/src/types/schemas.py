from dataclasses import dataclass
from typing import Optional

@dataclass
class Pagador:
    nome: str
    cpf: str
    instituicao: str

@dataclass
class Devedor:
    nome: str
    cpf: str

@dataclass
class Transacao:
    situacao: str
    valor: float
    abatimento: float
    juros: float
    multa: float
    desconto: float
    valor_documento: float
    valor_pagamento: float
    vencimento: str
    validade_pagamento: int
    solicitacao_pagador: str
    id_transacao: str
    data_hora: str
    identificador: str
    codigo_operacao: str
    chave_seguranca: str
    valor_tarifa: float
    data: str

@dataclass
class Comprovante:
    pagador: Pagador
    devedor: Devedor
    transacao: Transacao
    valor_total: float
    nome_empresa: str
    cnpj_empresa: str
    instituicao_empresa: str
from typing import Dict, Tuple

def calcular_isencao_mei(receita_bruta: float, percentual_isencao: float) -> float:
    """
    Calcula a parcela isenta de lucro do MEI.
    """
    if receita_bruta < 0:
        raise ValueError("A Receita Bruta não pode ser negativa.")
    
    return receita_bruta * (percentual_isencao / 100.0)

def calcular_tributavel(receita_bruta: float, despesas: float, parcela_isenta: float) -> float:
    """
    Calcula a parcela tributável do lucro do MEI.
    Se o resultado for negativo, não há lucro tributável (retorna 0.0).
    """
    lucro_evidenciado = receita_bruta - despesas
    rendimento_tributavel = lucro_evidenciado - parcela_isenta
    
    # Se lucro for negativo, ele obteve prejuízo contábil na parte tributável.
    return max(0.0, rendimento_tributavel)

def processar_calculo_mei(receita_bruta: float, despesas: float, ramo_atividade: str, receita_comercio: float = 0.0, receita_servicos: float = 0.0) -> Dict[str, float]:
    """
    Orquestra o cálculo retornando os valores necessários para a DAA.
    Ramo de atividade esperado:
    - 'Comércio/Indústria' (8%)
    - 'Transporte de Passageiros' (16%)
    - 'Serviços' (32%)
    - 'Híbrido/Misto' (8% sobre comércio + 32% sobre serviços)
    """
    
    if ramo_atividade == 'Híbrido/Misto':
        receita_total = receita_comercio + receita_servicos
        parcela_isenta_comercio = receita_comercio * 0.08
        parcela_isenta_servico = receita_servicos * 0.32
        parcela_isenta = parcela_isenta_comercio + parcela_isenta_servico
    else:
        receita_total = receita_bruta
        percentuais = {
            'Comércio/Indústria': 8.0,
            'Transporte de Passageiros': 16.0,
            'Serviços': 32.0
        }
        perc = percentuais.get(ramo_atividade, 0.0)
        parcela_isenta = calcular_isencao_mei(receita_total, perc)
        
    parcela_tributavel = calcular_tributavel(receita_total, despesas, parcela_isenta)
    
    return {
        "receita_bruta": receita_total,
        "despesas": despesas,
        "parcela_isenta": parcela_isenta,
        "parcela_tributavel": parcela_tributavel,
        "lucro_total": receita_total - despesas
    }

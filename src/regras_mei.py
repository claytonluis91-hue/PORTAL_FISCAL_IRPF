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

def processar_calculo_mei(receita_bruta: float, despesas: float, ramo_atividade: str) -> Dict[str, float]:
    """
    Orquestra o cálculo retornando os valores necessários para a DAA.
    Ramo de atividade esperado:
    - 'Comércio/Indústria' (8%)
    - 'Transporte de Passageiros' (16%)
    - 'Serviços' (32%)
    """
    
    percentuais = {
        'Comércio/Indústria': 8.0,
        'Transporte de Passageiros': 16.0,
        'Serviços': 32.0
    }
    
    perc = percentuais.get(ramo_atividade, 0.0)
    
    parcela_isenta = calcular_isencao_mei(receita_bruta, perc)
    parcela_tributavel = calcular_tributavel(receita_bruta, despesas, parcela_isenta)
    
    return {
        "receita_bruta": receita_bruta,
        "despesas": despesas,
        "parcela_isenta": parcela_isenta,
        "parcela_tributavel": parcela_tributavel,
        "lucro_total": receita_bruta - despesas
    }

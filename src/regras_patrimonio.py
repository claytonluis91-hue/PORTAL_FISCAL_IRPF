def calcular_variacao_patrimonial(patrimonio_inicial: float, patrimonio_final: float, rendimentos: float, despesas: float) -> dict:
    """
    Motor base para auditar variação patrimonial a descoberto.
    :return: Dicionário com a variação e flag de risco.
    """
    aumento_patrimonial = patrimonio_final - patrimonio_inicial
    disponibilidade = rendimentos - despesas
    
    a_descoberto = aumento_patrimonial > disponibilidade
    
    return {
        "aumento_patrimonial": aumento_patrimonial,
        "disponibilidade": disponibilidade,
        "a_descoberto": a_descoberto,
        "diferenca": aumento_patrimonial - disponibilidade
    }

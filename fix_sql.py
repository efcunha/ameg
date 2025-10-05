#!/usr/bin/env python3

# Análise detalhada do problema SQL

# Campos da tabela cadastros (fixos, independente de arquivos)
campos_cadastros = """nome_completo, endereco, numero, bairro, cep, cidade, estado, telefone, ponto_referencia, genero, idade,
data_nascimento, titulo_eleitor, cidade_titulo, cpf, rg, nis, estado_civil,
escolaridade, profissao, nome_companheiro, cpf_companheiro, rg_companheiro,
idade_companheiro, escolaridade_companheiro, profissao_companheiro, data_nascimento_companheiro,
titulo_companheiro, cidade_titulo_companheiro, nis_companheiro, tipo_trabalho,
pessoas_trabalham, aposentados_pensionistas, num_pessoas_familia, num_familias,
adultos, criancas, adolescentes, idosos, gestantes, nutrizes, renda_familiar,
renda_per_capita, bolsa_familia, casa_tipo, casa_material, energia, lixo, agua,
esgoto, observacoes, tem_doenca_cronica, doencas_cronicas, usa_medicamento_continuo,
medicamentos_continuos, tem_doenca_mental, doencas_mentais, tem_deficiencia,
tipo_deficiencia, precisa_cuidados_especiais, cuidados_especiais,
com_que_trabalha, onde_trabalha, localizacao_trabalho, horario_trabalho, tempo_atividade, atua_ponto_fixo,
qual_ponto_fixo, dias_semana_trabalha, trabalho_continuo_temporada, sofreu_acidente_trabalho,
qual_acidente, trabalho_incomoda_calor, trabalho_incomoda_barulho, trabalho_incomoda_seguranca,
trabalho_incomoda_banheiros, trabalho_incomoda_outro, trabalho_incomoda_outro_desc,
acesso_banheiro_agua, trabalha_sozinho_ajudantes, possui_autorizacao_municipal,
problemas_fiscalizacao_policia, estrutura_barraca, estrutura_carrinho, estrutura_mesa,
estrutura_outro, estrutura_outro_desc, necessita_energia_eletrica, utiliza_gas_cozinha,
usa_veiculo_proprio, qual_veiculo, fonte_renda_trabalho_ambulante, fonte_renda_aposentadoria,
fonte_renda_outro_trabalho, fonte_renda_beneficio_social, fonte_renda_outro,
fonte_renda_outro_desc, pessoas_dependem_renda"""

# Placeholders atuais (INCORRETOS)
placeholders_atuais = "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s"

# Contar
campos = [f.strip() for f in campos_cadastros.replace('\n', ' ').split(',') if f.strip()]
placeholders = [p.strip() for p in placeholders_atuais.split(',') if p.strip()]

print("=== ANÁLISE DO PROBLEMA ===")
print(f"Campos na tabela cadastros: {len(campos)}")
print(f"Placeholders na query: {len(placeholders)}")
print(f"Diferença: {len(campos) - len(placeholders)}")

print("\n=== CORREÇÃO NECESSÁRIA ===")
placeholders_corretos = ",".join(["%s"] * len(campos))
print(f"Placeholders corretos: {placeholders_corretos}")

print("\n=== ARQUIVOS SÃO INDEPENDENTES ===")
print("• Tabela 'cadastros': campos fixos (98 campos)")
print("• Tabela 'arquivos_saude': 1 INSERT por arquivo")
print("• Quantidade de arquivos NÃO afeta a query da tabela cadastros")
print("• Problema está na incompatibilidade de campos fixos, não nos arquivos")

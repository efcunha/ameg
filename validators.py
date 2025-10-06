"""
Sistema de Validação Unificado AMEG
Validadores centralizados para uso em todas as rotas
"""

import re
from typing import Tuple, Dict, Any

class FormValidators:
    """Classe centralizada para validações do sistema"""
    
    @staticmethod
    def validate_senha(senha: str) -> Tuple[bool, str]:
        """
        Valida senha com requisitos de segurança
        Retorna: (is_valid, error_message)
        """
        if not senha:
            return False, "Senha é obrigatória"
        
        if len(senha) < 8:
            return False, "Senha deve ter pelo menos 8 caracteres"
        
        if not re.search(r'[A-Z]', senha):
            return False, "Senha deve conter pelo menos uma letra maiúscula"
        
        if not re.search(r'[a-z]', senha):
            return False, "Senha deve conter pelo menos uma letra minúscula"
        
        if not re.search(r'[0-9]', senha):
            return False, "Senha deve conter pelo menos um número"
        
        return True, "Senha válida"
    
    @staticmethod
    def validate_cpf(cpf: str) -> bool:
        """Valida CPF brasileiro"""
        if not cpf:
            return False
            
        # Remove caracteres não numéricos
        cpf = re.sub(r'[^\d]', '', cpf)
        
        # Verifica se tem 11 dígitos
        if len(cpf) != 11:
            return False
        
        # Verifica se não são todos iguais
        if cpf == cpf[0] * 11:
            return False
        
        # Validação dos dígitos verificadores
        def calculate_digit(cpf_partial, weights):
            total = sum(int(digit) * weight for digit, weight in zip(cpf_partial, weights))
            remainder = total % 11
            return 0 if remainder < 2 else 11 - remainder
        
        # Primeiro dígito
        first_digit = calculate_digit(cpf[:9], range(10, 1, -1))
        if first_digit != int(cpf[9]):
            return False
        
        # Segundo dígito
        second_digit = calculate_digit(cpf[:10], range(11, 1, -1))
        if second_digit != int(cpf[10]):
            return False
        
        return True
    
    @staticmethod
    def validate_telefone(telefone: str) -> bool:
        """Valida telefone brasileiro"""
        if not telefone:
            return False
        
        # Remove caracteres não numéricos
        phone = re.sub(r'[^\d]', '', telefone)
        
        # Verifica se tem 10 ou 11 dígitos
        return len(phone) >= 10 and len(phone) <= 11
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Valida formato de email"""
        if not email:
            return False
        
        pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_required_fields(form_data: Dict[str, Any], required_fields: list) -> Tuple[bool, list]:
        """
        Valida campos obrigatórios
        Retorna: (all_valid, error_list)
        """
        errors = []
        
        for field in required_fields:
            value = form_data.get(field, '').strip()
            if not value or value == 'None':
                errors.append(f"Campo '{field}' é obrigatório")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_numeric_ranges(form_data: Dict[str, Any], field_ranges: Dict[str, Dict]) -> Tuple[bool, list]:
        """
        Valida intervalos numéricos
        field_ranges = {'idade': {'min': 0, 'max': 120}, 'renda': {'min': 0.01}}
        """
        errors = []
        
        for field, ranges in field_ranges.items():
            value = form_data.get(field)
            if value is None or value == '':
                continue
                
            try:
                num_value = float(value)
                
                if 'min' in ranges and num_value < ranges['min']:
                    errors.append(f"Campo '{field}' deve ser maior que {ranges['min']}")
                
                if 'max' in ranges and num_value > ranges['max']:
                    errors.append(f"Campo '{field}' deve ser menor que {ranges['max']}")
                    
            except (ValueError, TypeError):
                errors.append(f"Campo '{field}' deve ser um número válido")
        
        return len(errors) == 0, errors

# Configurações de validação para diferentes formulários
VALIDATION_CONFIGS = {
    'cadastro': {
        'required_fields': ['nome_completo', 'cpf', 'telefone', 'endereco'],
        'numeric_ranges': {
            'idade': {'min': 0, 'max': 120},
            'renda_familiar': {'min': 0.01},
            'renda_per_capita': {'min': 0.01}
        }
    },
    'usuario': {
        'required_fields': ['usuario', 'senha'],
        'custom_validators': ['senha']
    }
}

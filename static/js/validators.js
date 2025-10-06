/**
 * Sistema de Validação Unificado AMEG
 * Validadores centralizados para uso em todos os formulários
 */

const Validators = {
    // Validação de senha
    senha: {
        rules: {
            length: { min: 8, message: 'Mínimo 8 caracteres' },
            uppercase: { pattern: /[A-Z]/, message: 'Pelo menos 1 letra maiúscula' },
            lowercase: { pattern: /[a-z]/, message: 'Pelo menos 1 letra minúscula' },
            number: { pattern: /[0-9]/, message: 'Pelo menos 1 número' }
        },
        validate: function(value) {
            return {
                length: value.length >= this.rules.length.min,
                uppercase: this.rules.uppercase.pattern.test(value),
                lowercase: this.rules.lowercase.pattern.test(value),
                number: this.rules.number.pattern.test(value)
            };
        },
        isValid: function(value) {
            const results = this.validate(value);
            return Object.values(results).every(result => result);
        }
    },

    // Validação de CPF
    cpf: {
        validate: function(value) {
            const cpf = value.replace(/[^\d]/g, '');
            if (cpf.length !== 11) return false;
            if (/^(\d)\1{10}$/.test(cpf)) return false;
            
            // Validação dos dígitos verificadores
            let sum = 0;
            for (let i = 0; i < 9; i++) {
                sum += parseInt(cpf.charAt(i)) * (10 - i);
            }
            let digit = 11 - (sum % 11);
            if (digit === 10 || digit === 11) digit = 0;
            if (digit !== parseInt(cpf.charAt(9))) return false;
            
            sum = 0;
            for (let i = 0; i < 10; i++) {
                sum += parseInt(cpf.charAt(i)) * (11 - i);
            }
            digit = 11 - (sum % 11);
            if (digit === 10 || digit === 11) digit = 0;
            return digit === parseInt(cpf.charAt(10));
        }
    },

    // Validação de telefone
    telefone: {
        validate: function(value) {
            const phone = value.replace(/[^\d]/g, '');
            return phone.length >= 10 && phone.length <= 11;
        }
    },

    // Validação de email
    email: {
        validate: function(value) {
            return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
        }
    }
};

/**
 * Classe para gerenciar validação de formulários
 */
class FormValidator {
    constructor(formId) {
        this.form = document.getElementById(formId);
        this.validators = {};
        this.init();
    }

    init() {
        if (!this.form) return;
        
        // Encontrar campos com validação
        const fields = this.form.querySelectorAll('[data-validator]');
        fields.forEach(field => {
            const validatorName = field.dataset.validator;
            if (Validators[validatorName]) {
                this.validators[field.name] = validatorName;
                this.setupFieldValidation(field, validatorName);
            }
        });
    }

    setupFieldValidation(field, validatorName) {
        const validator = Validators[validatorName];
        
        // Criar container de regras se for senha
        if (validatorName === 'senha') {
            this.createPasswordRules(field);
        }

        // Adicionar listener de validação
        field.addEventListener('input', () => {
            this.validateField(field, validatorName);
        });
    }

    createPasswordRules(field) {
        const container = field.closest('.form-group') || field.parentElement;
        const rulesContainer = document.createElement('div');
        rulesContainer.className = 'validation-rules';
        rulesContainer.innerHTML = `
            <div class="rule" data-rule="length">
                <span class="rule-icon">❌</span>
                <span>Mínimo 8 caracteres</span>
            </div>
            <div class="rule" data-rule="uppercase">
                <span class="rule-icon">❌</span>
                <span>Pelo menos 1 letra maiúscula</span>
            </div>
            <div class="rule" data-rule="lowercase">
                <span class="rule-icon">❌</span>
                <span>Pelo menos 1 letra minúscula</span>
            </div>
            <div class="rule" data-rule="number">
                <span class="rule-icon">❌</span>
                <span>Pelo menos 1 número</span>
            </div>
        `;
        container.appendChild(rulesContainer);
    }

    validateField(field, validatorName) {
        const validator = Validators[validatorName];
        
        if (validatorName === 'senha') {
            const results = validator.validate(field.value);
            this.updatePasswordRules(field, results);
            return validator.isValid(field.value);
        } else {
            const isValid = validator.validate(field.value);
            this.updateFieldStatus(field, isValid);
            return isValid;
        }
    }

    updatePasswordRules(field, results) {
        const container = field.closest('.form-group') || field.parentElement;
        const rules = container.querySelectorAll('.rule');
        
        rules.forEach(rule => {
            const ruleName = rule.dataset.rule;
            const icon = rule.querySelector('.rule-icon');
            const isValid = results[ruleName];
            
            if (isValid) {
                icon.textContent = '✅';
                rule.className = 'rule rule-valid';
            } else {
                icon.textContent = '❌';
                rule.className = 'rule rule-invalid';
            }
        });

        // Atualizar botão de submit se existir
        this.updateSubmitButton();
    }

    updateFieldStatus(field, isValid) {
        field.style.borderColor = isValid ? '#28a745' : '#dc3545';
    }

    updateSubmitButton() {
        const submitBtn = this.form.querySelector('button[type="submit"]');
        if (!submitBtn) return;

        const allValid = this.validateAll();
        submitBtn.disabled = !allValid;
        submitBtn.style.background = allValid ? '#3498db' : '#bdc3c7';
    }

    validateAll() {
        let allValid = true;
        
        for (const [fieldName, validatorName] of Object.entries(this.validators)) {
            const field = this.form.querySelector(`[name="${fieldName}"]`);
            if (field) {
                const isValid = this.validateField(field, validatorName);
                if (!isValid) allValid = false;
            }
        }
        
        return allValid;
    }
}

// CSS para as regras de validação
const validationCSS = `
.validation-rules {
    background: #f8f9fa;
    padding: 15px;
    border-radius: 5px;
    margin: 10px 0;
    border: 1px solid #e9ecef;
}

.rule {
    display: flex;
    align-items: center;
    margin: 5px 0;
    font-size: 14px;
}

.rule-icon {
    margin-right: 8px;
    font-weight: bold;
}

.rule-valid {
    color: #28a745;
}

.rule-invalid {
    color: #dc3545;
}
`;

// Adicionar CSS ao documento
if (!document.getElementById('validation-styles')) {
    const style = document.createElement('style');
    style.id = 'validation-styles';
    style.textContent = validationCSS;
    document.head.appendChild(style);
}

// Exportar para uso global
window.Validators = Validators;
window.FormValidator = FormValidator;

# Segurança do Sistema AMEG

## Proteção da Senha do Admin

### 1. Arquivos de Segurança (NÃO COMMITADOS)
- `.env.secure` - Credenciais locais
- `admin_credentials.txt` - Backup das credenciais
- `security_keys.txt` - Chaves de criptografia

### 2. Proteções Implementadas
- **Hash duplo**: Senha + salt personalizado + PBKDF2
- **Criptografia**: Dados sensíveis criptografados com Fernet
- **Admin protegido**: ID 1 tem proteções especiais
- **Geração segura**: Senhas aleatórias com 16 caracteres

### 3. Como Usar

#### Gerar Credenciais Seguras (Local)
```bash
python3 generate_admin_credentials.py
```

#### Configurar no Railway (Produção)
1. Acesse o painel do Railway
2. Vá em Variables
3. Adicione:
   - `ADMIN_PASSWORD=<senha_gerada>`
   - `ENCRYPTION_KEY=<chave_gerada>`
   - `SECURITY_SALT=<salt_personalizado>`

### 4. Estrutura de Segurança
```
security.py          # Módulo principal de segurança
├── SecurityManager  # Classe principal
├── hash_admin_password()     # Hash com salt adicional
├── verify_admin_password()   # Verificação segura
├── encrypt_sensitive_data()  # Criptografia de dados
└── is_admin_protected()      # Proteção do admin ID 1
```

### 5. Boas Práticas
- ✅ Senhas nunca em código fonte
- ✅ Hash com salt personalizado
- ✅ Criptografia para dados sensíveis
- ✅ Arquivos sensíveis no .gitignore
- ✅ Variáveis de ambiente em produção
- ✅ Admin ID 1 protegido contra alterações

### 6. Verificação de Segurança
```bash
# Verificar se arquivos sensíveis estão protegidos
git status --ignored

# Verificar se .env.secure não está no Git
git ls-files | grep -E "\.(env|key|pem)$"
```

## ⚠️ IMPORTANTE
- NUNCA commitar arquivos `.env.secure`, `.key`, `.pem`
- Sempre usar variáveis de ambiente em produção
- Manter backup seguro das credenciais
- Trocar senhas periodicamente

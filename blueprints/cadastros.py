from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import get_db_connection, registrar_auditoria
import base64
import logging

logger = logging.getLogger(__name__)

cadastros_bp = Blueprint('cadastros', __name__)

@cadastros_bp.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        try:
            # Coletar todos os dados do formulário
            dados = {}
            campos = [
                'nome_completo', 'cpf', 'rg', 'telefone', 'endereco', 'bairro', 'cep',
                'cidade', 'estado', 'companheiro', 'filhos', 'dependentes', 'renda_familiar',
                'beneficio_social', 'tipo_moradia', 'energia_eletrica', 'agua_encanada',
                'esgoto', 'doenca_cronica', 'qual_doenca', 'medicamento_continuo',
                'qual_medicamento', 'deficiencia', 'qual_deficiencia', 'tipo_trabalho',
                'localizacao_trabalho', 'renda_individual', 'observacoes'
            ]
            
            for campo in campos:
                dados[campo] = request.form.get(campo, '').strip()
            
            # Processar foto se enviada
            foto_base64 = None
            if 'foto_webcam' in request.form and request.form['foto_webcam']:
                foto_base64 = request.form['foto_webcam']
            elif 'foto_upload' in request.files:
                foto_file = request.files['foto_upload']
                if foto_file and foto_file.filename:
                    foto_data = foto_file.read()
                    foto_base64 = base64.b64encode(foto_data).decode('utf-8')
            
            # Inserir no banco
            conn = get_db_connection()
            cursor = conn.cursor()
            
            query = '''
                INSERT INTO cadastros (
                    nome_completo, cpf, rg, telefone, endereco, bairro, cep, cidade, estado,
                    companheiro, filhos, dependentes, renda_familiar, beneficio_social,
                    tipo_moradia, energia_eletrica, agua_encanada, esgoto, doenca_cronica,
                    qual_doenca, medicamento_continuo, qual_medicamento, deficiencia,
                    qual_deficiencia, tipo_trabalho, localizacao_trabalho, renda_individual,
                    observacoes, foto_base64, data_cadastro
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
                ) RETURNING id
            '''
            
            valores = [dados[campo] for campo in campos] + [foto_base64]
            cursor.execute(query, valores)
            cadastro_id = cursor.fetchone()[0]
            
            conn.commit()
            cursor.close()
            conn.close()
            
            # Registrar auditoria
            registrar_auditoria(
                session['usuario'], 'INSERT', 'cadastros', cadastro_id,
                None, f"Cadastro criado: {dados['nome_completo']}"
            )
            
            flash('Cadastro realizado com sucesso!', 'success')
            return redirect(url_for('dashboard.dashboard'))
            
        except Exception as e:
            logger.error(f"Erro ao cadastrar: {e}")
            flash('Erro ao realizar cadastro', 'error')
    
    return render_template('cadastrar.html')

@cadastros_bp.route('/editar_cadastro/<int:cadastro_id>', methods=['GET', 'POST'])
def editar_cadastro(cadastro_id):
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if request.method == 'GET':
            # Buscar dados do cadastro
            cursor.execute('SELECT * FROM cadastros WHERE id = %s', (cadastro_id,))
            cadastro = cursor.fetchone()
            
            if not cadastro:
                flash('Cadastro não encontrado', 'error')
                return redirect(url_for('dashboard.dashboard'))
            
            cursor.close()
            conn.close()
            return render_template('editar_cadastro.html', cadastro=cadastro)
        
        elif request.method == 'POST':
            # Buscar dados atuais para auditoria
            cursor.execute('SELECT * FROM cadastros WHERE id = %s', (cadastro_id,))
            dados_anteriores = cursor.fetchone()
            
            if not dados_anteriores:
                flash('Cadastro não encontrado', 'error')
                return redirect(url_for('dashboard.dashboard'))
            
            # Atualizar dados
            dados = {}
            campos = [
                'nome_completo', 'cpf', 'rg', 'telefone', 'endereco', 'bairro', 'cep',
                'cidade', 'estado', 'companheiro', 'filhos', 'dependentes', 'renda_familiar',
                'beneficio_social', 'tipo_moradia', 'energia_eletrica', 'agua_encanada',
                'esgoto', 'doenca_cronica', 'qual_doenca', 'medicamento_continuo',
                'qual_medicamento', 'deficiencia', 'qual_deficiencia', 'tipo_trabalho',
                'localizacao_trabalho', 'renda_individual', 'observacoes'
            ]
            
            for campo in campos:
                dados[campo] = request.form.get(campo, '').strip()
            
            # Processar nova foto se enviada
            foto_base64 = dados_anteriores[29]  # foto atual
            if 'foto_webcam' in request.form and request.form['foto_webcam']:
                foto_base64 = request.form['foto_webcam']
            elif 'foto_upload' in request.files:
                foto_file = request.files['foto_upload']
                if foto_file and foto_file.filename:
                    foto_data = foto_file.read()
                    foto_base64 = base64.b64encode(foto_data).decode('utf-8')
            
            # Atualizar no banco
            query = '''
                UPDATE cadastros SET
                    nome_completo=%s, cpf=%s, rg=%s, telefone=%s, endereco=%s, bairro=%s,
                    cep=%s, cidade=%s, estado=%s, companheiro=%s, filhos=%s, dependentes=%s,
                    renda_familiar=%s, beneficio_social=%s, tipo_moradia=%s, energia_eletrica=%s,
                    agua_encanada=%s, esgoto=%s, doenca_cronica=%s, qual_doenca=%s,
                    medicamento_continuo=%s, qual_medicamento=%s, deficiencia=%s,
                    qual_deficiencia=%s, tipo_trabalho=%s, localizacao_trabalho=%s,
                    renda_individual=%s, observacoes=%s, foto_base64=%s
                WHERE id = %s
            '''
            
            valores = [dados[campo] for campo in campos] + [foto_base64, cadastro_id]
            cursor.execute(query, valores)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            # Registrar auditoria
            registrar_auditoria(
                session['usuario'], 'UPDATE', 'cadastros', cadastro_id,
                str(dados_anteriores), f"Cadastro atualizado: {dados['nome_completo']}"
            )
            
            flash('Cadastro atualizado com sucesso!', 'success')
            return redirect(url_for('dashboard.dashboard'))
    
    except Exception as e:
        logger.error(f"Erro ao editar cadastro: {e}")
        flash('Erro ao editar cadastro', 'error')
        return redirect(url_for('dashboard.dashboard'))

@cadastros_bp.route('/ficha/<int:cadastro_id>')
def ficha(cadastro_id):
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM cadastros WHERE id = %s', (cadastro_id,))
        cadastro = cursor.fetchone()
        
        if not cadastro:
            flash('Cadastro não encontrado', 'error')
            return redirect(url_for('dashboard.dashboard'))
        
        cursor.close()
        conn.close()
        
        return render_template('ficha.html', cadastro=cadastro)
    
    except Exception as e:
        logger.error(f"Erro ao exibir ficha: {e}")
        flash('Erro ao carregar ficha', 'error')
        return redirect(url_for('dashboard.dashboard'))

@cadastros_bp.route('/deletar_cadastro/<int:cadastro_id>', methods=['POST'])
def deletar_cadastro(cadastro_id):
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Deletar arquivos de saúde relacionados primeiro
        cursor.execute('DELETE FROM arquivos_saude WHERE cadastro_id = %s', (cadastro_id,))
        
        # Deletar o cadastro
        cursor.execute('DELETE FROM cadastros WHERE id = %s', (cadastro_id,))
        
        if cursor.rowcount > 0:
            conn.commit()
            flash('Cadastro deletado com sucesso!', 'success')
        else:
            flash('Cadastro não encontrado!', 'error')
            
    except Exception as e:
        logger.error(f"Erro ao deletar cadastro {cadastro_id}: {e}")
        flash(f'Erro ao deletar cadastro: {str(e)}', 'error')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('dashboard.dashboard'))

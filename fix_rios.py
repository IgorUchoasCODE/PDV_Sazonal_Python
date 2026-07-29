import sqlite3

def corrigir_indicadores_rio():
    conn = sqlite3.connect('databaseSazonalizei.db')
    cursor = conn.cursor()

    try:
        # Atualiza para CHEIA
        cursor.execute("UPDATE snapshot_sazonal SET indicador_rio = 'CHEIA' WHERE nivel_rio_atual > 7.0;")
        
        # Atualiza para SECA
        cursor.execute("UPDATE snapshot_sazonal SET indicador_rio = 'SECA' WHERE nivel_rio_atual < 2.5 AND nivel_rio_atual > 0;")
        
        # Atualiza para NORMAL
        cursor.execute("UPDATE snapshot_sazonal SET indicador_rio = 'NORMAL' WHERE nivel_rio_atual >= 2.5 AND nivel_rio_atual <= 7.0;")
        
        conn.commit()
        print('Indicadores de rio atualizados com sucesso no banco de dados!')
    except Exception as e:
        print(f'Erro ao atualizar: {e}')
    finally:
        conn.close()

if __name__ == '__main__':
    corrigir_indicadores_rio()

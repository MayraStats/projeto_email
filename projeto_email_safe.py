import imapclient
from pyzmail import PyzMessage
import time

# Configurações
EMAIL = '<seu email>'
PASSWORD = '<sua senha>'
IMAP_SERVER = 'imap.gmail.com'
BATCH_SIZE = 5  # Reduzido para minimizar carga no servidor
MAX_GLOBAL_RETRIES = 3  # Máximo de reinicializações do script completo
MAX_RETRIES = 3  # Máximo de tentativas para cada lote

def conectar_ao_servidor():
    """Conecta ao servidor IMAP e faz login."""
    try:
        print("Conectando ao servidor...")
        mail = imapclient.IMAPClient(IMAP_SERVER, ssl=True, timeout=60)
        mail.login(EMAIL, PASSWORD)
        print("Conexão bem-sucedida!")
        return mail
    except Exception as e:
        print(f"Erro ao conectar ao servidor: {e}")
        return None

def processar_lote(mail, batch):
    """Processa um lote específico de e-mails."""
    try:
        mail.select_folder('INBOX')
        for msg_id in batch:
            try:
                raw_message = mail.fetch([msg_id], ['BODY[]'])
                message = PyzMessage.factory(raw_message[msg_id][b'BODY[]'])
                print(f"Apagando: {message.get_subject()}")
                mail.delete_messages([msg_id])
            except Exception as e:
                print(f"Erro ao processar e-mail {msg_id}: {e}")
        mail.expunge()
        print(f"Lote de {len(batch)} e-mails apagado com sucesso!")
    except Exception as batch_error:
        print(f"Erro no processamento do lote: {batch_error}")
        raise Exception("Erro ao processar lote.")

def executar_processamento():
    """Executa o processamento completo com reinicialização global e reconexões em caso de erro."""
    retries = 0
    while retries < MAX_GLOBAL_RETRIES:
        try:
            mail = conectar_ao_servidor()
            if not mail:
                raise Exception("Não foi possível conectar ao servidor para listar e-mails.")

            mail.select_folder('INBOX')
            messages = mail.search(['UNSEEN'])
            print(f"E-mails não lidos encontrados: {len(messages)}")
            mail.logout()

            # Processar em lotes
            for i in range(0, len(messages), BATCH_SIZE):
                batch = messages[i:i + BATCH_SIZE]
                print(f"Processando lote de {len(batch)} e-mails...")
                attempt = 0
                while attempt < MAX_RETRIES:
                    try:
                        processar_lote(mail, batch)
                        break  # Sai do loop se o lote for processado com sucesso
                    except Exception as lote_erro:
                        print(f"Erro no lote: {lote_erro}. Tentando reconectar...")
                        attempt += 1
                        time.sleep(5)  # Espera antes de tentar reconectar
                        mail = conectar_ao_servidor()
                        if not mail:
                            raise Exception("Reconexão falhou.")

            print("Processo concluído com sucesso!")
            return  # Sai do loop global ao concluir
        except Exception as geral_erro:
            retries += 1
            print(f"Erro global: {geral_erro}. Tentando novamente ({retries}/{MAX_GLOBAL_RETRIES})...")
            time.sleep(10)  # Aguarda antes de reiniciar
        if retries == MAX_GLOBAL_RETRIES:
            print("Número máximo de tentativas atingido. Encerrando.")

# Execução principal
if __name__ == "__main__":
    executar_processamento()
 

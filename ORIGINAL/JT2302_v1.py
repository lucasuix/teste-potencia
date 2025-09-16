import serial
import serial.tools.list_ports
import time
import os
import json
import sys
import numpy as np  


# Nome do arquivo de configuração
config_file = 'config.json'

# Constantes
V_fonte = 3.49
const_fonte = V_fonte / 4096
red_load= (3.9 + 27) / 3.9
red_DCDC= (3.9 + 27) / 3.9
red_ADCs = (3.9 + 27) / 3.9
red_cf = (100 + 33) / 33
red_batt = (2.2 + 27) / 2.2
red_PWM = (3.3 + 22) / 3.3

# --------------------- Configuração Serial --------------------

def listar_portas():
    portas = list(serial.tools.list_ports.comports())
    return [porta.device for porta in portas]

def selecionar_porta():
    portas = listar_portas()
    if not portas:
        print("Nenhuma porta serial encontrada.")
        exit()

    print("Portas seriais disponíveis:")
    for i, p in enumerate(portas, 1):
        print(f"[{i}] {p}")

    while True:
        try:
            escolha = int(input("Escolha a porta desejada (número): "))
            if 1 <= escolha <= len(portas):
                porta_escolhida = portas[escolha - 1]
                print(f"Porta {porta_escolhida} selecionada.")
                return porta_escolhida
            else:
                print("Escolha inválida.")
        except ValueError:
            print("Digite apenas o número da opção.")

def obter_porta_serial(config):
    porta_salva = config.get("porta")
    if porta_salva:
        usar = input(f"Porta salva: {porta_salva}. Pressione Enter para usar ou digite 'nova' para trocar: ").strip()
        if usar.lower() != 'nova':
            return porta_salva
    return selecionar_porta()

def carregar_config():
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Aviso: erro ao carregar configuração: {e}")
    return {}

def salvar_config(porta):
    with open(config_file, 'w') as f:
        json.dump({"porta": porta}, f, indent=4)

# --------------------- Função de Leitura ADC --------------------

def verificar_curto_bateria(ser, const_fonte, red_batt):
    try:
        ser.reset_input_buffer()

        # Liga a bateria
        ser.write(b'LIGBT')
        # Aguarda o ACK e salva a resposta em variável
        aguardar_ack(ser)
        time.sleep(0.3)

        # Faz leitura dos ADCs
        ser.write(b'AQADC')
        time.sleep(0.1)
        resposta_adc = ser.readline().decode(errors='ignore').strip()
        print(f"Resposta AQADC: [{resposta_adc}]")

        # Desliga a bateria
        ser.write(b'DESBT')
        aguardar_ack(ser)
        
        # Processamento do valor ADC
        if len(resposta_adc) < 7:
            adc_batt = 0
        else:
            try:
                valor_str = resposta_adc[25:30]  # Ajustar conforme sua resposta real
                adc_batt = float(valor_str) * const_fonte * red_batt
                if adc_batt != adc_batt:  # Detecta NaN
                    adc_batt = 0
            except (ValueError, IndexError):
                adc_batt = 0

        return adc_batt

    except Exception as e:
        print(f"[ERRO] Falha na leitura da bateria: {e}")
        return 0
    
def verificar_curto_DCDC(ser, const_fonte, red_DCDC):
    try:
        ser.reset_input_buffer()

        # Liga o DCDC
        ser.write(b'LIGDC')
        aguardar_ack(ser)
 
        time.sleep(0.3)

        # Faz leitura dos ADCs
        ser.write(b'AQADC')
        time.sleep(0.1)
        resposta_adc = ser.readline().decode(errors='ignore').strip()
        print(f"Resposta AQADC: [{resposta_adc}]")

        # Desliga o DCDC
        ser.write(b'DESDC')
        aguardar_ack(ser)
        
        # Processamento do valor ADC
        if len(resposta_adc) < 7:
            adc_dcdc = 0
        else:
            try:
                valor_str = resposta_adc[19:24]  # Ajustar conforme sua resposta real
                adc_dcdc = float(valor_str) * const_fonte * red_DCDC
                if adc_dcdc != adc_dcdc:  # Detecta NaN
                    adc_dcdc = 0
            except (ValueError, IndexError):
                adc_dcdc = 0

        return adc_dcdc

    except Exception as e:
        print(f"[ERRO] Falha na leitura da bateria: {e}")
        return 0


def aguardar_adc_5v(ser, const_fonte, red_ADCs, tempo_max=20):
    print("Aguardando ADC_5V", end='', flush=True)
    inicio = time.time()
    
    while True:
        tempo_decorrido = time.time() - inicio
        if tempo_decorrido > tempo_max:
            print(f"\n\033[31m[ERRO] Tempo excedido ({tempo_decorrido:.1f}s). ADC_5V não atingiu 4V\033[0m")
            return False, tempo_decorrido
        
        time.sleep(1)
        ser.reset_input_buffer()
        ser.write(b'AQADC\r')
        time.sleep(0.3)
        info = ser.readline().decode(errors='ignore').strip()
        
        try:
            ADC_5V = float(info[7:12]) * const_fonte * red_ADCs
        except:
            ADC_5V = 0
        
        print(".", end='', flush=True)

        if ADC_5V > 4.0:
            print(f"  ✔️ {ADC_5V:.2f}V em {tempo_decorrido:.1f} segundos")
            time.sleep(2)
            return True, tempo_decorrido

    print(f"\n\033[31m[ERRO] ADC_5V = {ADC_5V:.2f}V após {tempo_max}s\033[0m")
    return False


def testar_dcdc_e_carga(ser, const_fonte, red_cf, red_DCDC, red_batt, red_load, file_name_txt):
    try:
        ser.reset_input_buffer()

        # Liga o DCDC
        ser.write(b'LIGDC')
        aguardar_ack(ser)

        # Aguarda temporizador da placa
        #time.sleep(18)
        
        ok, tempo = aguardar_adc_5v(ser, const_fonte, red_ADCs)
        if not ok:
            return False, False
        
  
        # Faz leitura dos ADCs
        ser.reset_input_buffer()
        ser.write(b'AQADC\r')
        time.sleep(0.3)
        info = ser.readline().decode(errors='ignore').strip()
      
        # Conversão dos valores
        ADC_15V=float(info[1:6]) * const_fonte * red_ADCs
        ADC_5V=float(info[7:12]) * const_fonte * red_ADCs
        ADC_load = float(info[13:18]) * const_fonte * red_ADCs
        ADC_DCDC = float(info[19:24]) * const_fonte * red_ADCs
        ADC_Batt = float(info[25:30]) * const_fonte * red_batt
        ADC_cf= float(info[31:36]) * const_fonte * red_cf
        ADC_PWM= float(info[37:42]) * const_fonte * red_PWM
        ADC_Stepup=float(info[43:48]) * const_fonte * red_batt
        ADC_LeitCorr=float(info[49:54]) * const_fonte * red_load   
        
        
        # Teste funcionamento DCDC e carga
        # Gravar os valores dos ADC_15V, ADC_5V, ADC_Stepup em arquivo
        if ( 
            (ADC_Batt > 27.5) and (ADC_DCDC > 22) and (ADC_load > 21.5) 
            and (ADC_15V >14.5) and (ADC_5V >4.5) and (ADC_Stepup>29.5)
            ):
            Teste1A = True
            info_status = 'OK'
            print(f"\033[32mTeste 1A: {info_status}\033[0m")  # Texto verde no terminal
        else:
            Teste1A = False
            info_status = 'NG'
            print(f"\033[31mTeste 1A: {info_status}\033[0m")  # Texto vermelho no terminal

        # Registro no TXT
        with open(file_name_txt, 'a') as f:
            f.write('*********************************************************************************\n')
            f.write(f'Teste Tensao DCDC, Load, StepUp: {info_status}\n')
            f.write(f'DCDC {ADC_DCDC:.2f}V *** Batt {ADC_Batt:.2f}V ***\n')
            f.write(f'Load {ADC_load:.2f}V *** CF {ADC_cf:.2f}V ***\n')

        # Liga carga da bateria
        ser.write(b'LIGCB\r') # Tensão virá do Stepup
        ok, resposta_ack = aguardar_ack(ser)
        if ok:
            print(f"Resposta LIGCB: {resposta_ack}")  # ou: printf("... %s", resposta_ack)
        else:
            print(f"Timeout. Parcial: {resposta_ack}")
 

        time.sleep(0.5)

        # Faz leitura dos ADCs
        ser.write(b'AQADC\r')
        time.sleep(0.3)
        info = ser.readline().decode(errors='ignore').strip()

        time.sleep(0.3)

       
        # Conversão dos valores
        ADC_15V=float(info[1:6]) * const_fonte * red_ADCs
        ADC_5V=float(info[7:12]) * const_fonte * red_ADCs
        ADC_load = float(info[13:18]) * const_fonte * red_ADCs
        ADC_DCDC = float(info[19:24]) * const_fonte * red_ADCs
        ADC_Batt = float(info[25:30]) * const_fonte * red_batt
        ADC_cf= float(info[31:36]) * const_fonte * red_cf
        ADC_PWM= float(info[37:42]) * const_fonte * red_PWM
        ADC_Stepup=float(info[43:48]) * const_fonte * red_batt
        ADC_LeitCorr=float(info[49:54]) * const_fonte * red_load   

        # Teste do circuito de carga da bateria
        if (ADC_DCDC > 22) and (11 < ADC_cf < 14):
            Teste1B = True
            info_status = 'OK'
            print(f"\033[32mTeste 1B: {info_status}\033[0m")
        else:
            Teste1B = False
            info_status = 'NG'
            print(f"\033[31mTeste 1B: {info_status}\033[0m")

        # Registro no TXT
        with open(file_name_txt, 'a') as f:
            f.write('*********************************************************************************\n')
            f.write(f'Teste Circ Carga Bateria: {info_status}\n')
            f.write(f'DCDC {ADC_DCDC:.2f}V *** Batt {ADC_Batt:.2f}V ***\n')
            f.write(f'Load {ADC_load:.2f}V *** CF {ADC_cf:.2f}V ***\n')

        # Desliga carga
        ser.write(b'DESCB\r')
        ok, resposta_ack = aguardar_ack(ser)
        if ok:
            print(f"Resposta DESCB: {resposta_ack}")  # ou: printf("... %s", resposta_ack)
        else:
            print(f"Timeout. Parcial: {resposta_ack}")

        return Teste1A, Teste1B

    except Exception as e:
        print(f"[ERRO] Falha no teste: {e}")
        return False, False


def testar_bateria_isolada(ser, const_fonte, red_cf, red_ADCs, red_batt, file_name_txt):
    """
    Executa o teste de bateria isolada.

    Parâmetros:
    - ser: Instância da porta serial aberta.
    - const_fonte: constante de calibração (float).
    - red_cf: fator de calibração da carga fantasma.
    - red_ADCs: fator de calibração dos ADCs gerais.
    - red_batt: fator de calibração da bateria.
    - file_name_txt: nome do arquivo de log.

    Retorna:
    - Teste3 (bool): True se passou, False se falhou.
    """

    try:
        ser.reset_input_buffer()
        
        # Liga a bateria
        ser.write(b'LIGBT')
        # Aguarda o ACK e salva a resposta em variável
        ok, resposta_ack = aguardar_ack(ser)
        if ok:
            print(f"Resposta LIGBT: {resposta_ack}")  # ou: printf("... %s", resposta_ack)
        else:
            print(f"Timeout. Parcial: {resposta_ack}")
        
        # Desliga o DCDC
        ser.write(b'DESDC')
        ok, resposta_ack = aguardar_ack(ser)
        if ok:
            print(f"Resposta DESDC: {resposta_ack}")  # ou: printf("... %s", resposta_ack)
        else:
            print(f"Timeout. Parcial: {resposta_ack}")
        
        time.sleep(0.5)
        
        # Leitura dos ADCs
        ser.write(b'AQADC')
        time.sleep(0.3)
        info = ser.readline().decode(errors='ignore').strip()

        # Parsing dos valores
        ADC_15V=float(info[1:6]) * const_fonte * red_ADCs
        ADC_5V=float(info[7:12]) * const_fonte * red_ADCs
        ADC_cf= float(info[31:36]) * const_fonte * red_cf
        ADC_load = float(info[13:18]) * const_fonte * red_ADCs
        ADC_Batt = float(info[25:30]) * const_fonte * red_batt
        ADC_DCDC = float(info[19:24]) * const_fonte * red_ADCs


        print(f"Leitura ADC -> CF: {ADC_cf:.2f}V | Load: {ADC_load:.2f}V | Batt: {ADC_Batt:.2f}V | DCDC: {ADC_DCDC:.2f}V")

        # Condições de teste
        if (ADC_Batt > 22) and (ADC_DCDC < 5) and (ADC_load > 21.5):
            Teste3 = True
            info_status = 'OK'
            print("\033[32m✔️ Teste Bateria Isolada: OK\033[0m")
        else:
            Teste3 = False
            info_status = 'NG'
            print("\033[31m❌ Teste Bateria Isolada: NG\033[0m")

        # Log no arquivo
        with open(file_name_txt, 'a') as f:
            f.write('*********************************************************************************\n')
            f.write(f'Teste Bateria isolado: {info_status}\n')
            f.write(f'DCDC {ADC_DCDC:.2f}V *** Batt {ADC_Batt:.2f}V ***\n')
            f.write(f'Load {ADC_load:.2f}V *** CF {ADC_cf:.2f}V ***\n')

        return Teste3

    except Exception as e:
        print(f"[ERRO] Falha no teste de bateria isolada: {e}")
        return False
    
def teste_alarmes_temperatura(ser, const_fonte, red_cf, red_ADCs, red_batt, file_name_txt):
    """
    Executa o Teste 4 - Teste de Alarmes de Temperatura.

    Parâmetros:
    - ser: instância da porta serial aberta.
    - const_fonte, red_cf, red_ADCs, red_batt: fatores de calibração.
    - file_name_txt: nome do arquivo de log.

    Retorna:
    - Um dicionário com os resultados dos testes Teste4A, Teste4B, Teste4C, Teste4D.
    """
    resultados = {}

    def ler_adc():
        ser.write(b'AQADC\r')
        time.sleep(0.3)
        info = ser.readline().decode(errors='ignore').strip()

        ADC_15V=float(info[1:6]) * const_fonte * red_ADCs
        ADC_5V=float(info[7:12]) * const_fonte * red_ADCs
        ADC_cf= float(info[31:36]) * const_fonte * red_cf
        ADC_load = float(info[13:18]) * const_fonte * red_ADCs
        ADC_Batt = float(info[25:30]) * const_fonte * red_batt
        ADC_DCDC = float(info[19:24]) * const_fonte * red_ADCs

        return ADC_cf, ADC_load, ADC_Batt, ADC_DCDC

    def log_teste(titulo, ADC_cf, ADC_load, ADC_Batt, ADC_DCDC, status):
        with open(file_name_txt, 'a') as f:
            f.write('*********************************************************************************\n')
            f.write(f'{titulo}: {status}\n')
            f.write(f'DCDC {ADC_DCDC:.2f}V *** Batt {ADC_Batt:.2f}V ***\n')
            f.write(f'Load {ADC_load:.2f}V *** CF {ADC_cf:.2f}V ***\n')

    # ------------------------- Teste 4A -------------------------
    for cmd in [b'ACLOAD\r',b'ACTP1\r']:
        ser.write(cmd)
        aguardar_ack(ser)
        time.sleep(1)
 
    ADC_cf, ADC_load, ADC_Batt, ADC_DCDC = ler_adc()
    
    ser.write(b'DGLOAD\r')
    aguardar_ack(ser)

    if (ADC_Batt > 22) and (ADC_DCDC < 5) and (ADC_load < 10):
        Teste4A = True
        status = 'OK'
    else:
        Teste4A = False
        status = 'NG'

    resultados["Teste4A"] = Teste4A
    log_teste('Teste Alarme Temp1', ADC_cf, ADC_load, ADC_Batt, ADC_DCDC, status)

    # ------------------------- Teste 4B -------------------------
    ser.write(b'ACTPA\r')
    aguardar_ack(ser)
    time.sleep(1)

    ADC_cf, ADC_load, ADC_Batt, ADC_DCDC = ler_adc()

    if (ADC_Batt > 22) and (ADC_DCDC < 5) and (ADC_load > 21):
        Teste4B = True
        status = 'OK'
    else:
        Teste4B = False
        status = 'NG'

    resultados["Teste4B"] = Teste4B
    log_teste('Teste Retorno Al. Temp1', ADC_cf, ADC_load, ADC_Batt, ADC_DCDC, status)

    # ------------------------- Teste 4C -------------------------
    ser.write(b'ACLOAD\r')
    aguardar_ack(ser)
    time.sleep(1)
    
    ser.write(b'ACTP2\r')
    aguardar_ack(ser)
    time.sleep(1)

    ADC_cf, ADC_load, ADC_Batt, ADC_DCDC = ler_adc()
    
    ser.write(b'DGLOAD\r')
    aguardar_ack(ser)
    time.sleep(1)

    if (ADC_Batt > 22) and (ADC_DCDC < 5) and (ADC_load < 10):
        Teste4C = True
        status = 'OK'
    else:
        Teste4C = False
        status = 'NG'

    resultados["Teste4C"] = Teste4C
    log_teste('Teste Al. Temp2', ADC_cf, ADC_load, ADC_Batt, ADC_DCDC, status)

    # ------------------------- Teste 4D -------------------------
    ser.write(b'ACTPA\r')
    aguardar_ack(ser)
    time.sleep(2)

    ADC_cf, ADC_load, ADC_Batt, ADC_DCDC = ler_adc()

    if (ADC_Batt > 22) and (ADC_DCDC < 5) and (ADC_load > 21):
        Teste4D = True
        status = 'OK'
    else:
        Teste4D = False
        status = 'NG'

    resultados["Teste4D"] = Teste4D
    log_teste('Teste Retorno Al. Temp2', ADC_cf, ADC_load, ADC_Batt, ADC_DCDC, status)

    return resultados    
    
def teste_variando_pwm(
    ser,
    const_fonte,
    red_ADCs,
    red_batt,
    file_name_txt,
    use_enpth=False,
    check_adc_load=False
):
    """
    Varia o duty cycle de um PWM via comando FR1DXX.X.
    
    - Se use_enpth=True, envia 'ENPTH' no início.
    - Se check_adc_load=True, espera ADC_load < 5V antes de monitorar ADC_5V e ADC_15V.

    Parâmetros:
    - ser: Instância da porta serial aberta.
    - const_fonte, red_ADCs, red_batt: Fatores de calibração.
    - file_name_txt: Nome do arquivo de log.
    - use_enpth: Envia 'ENPTH' no início.
    - check_adc_load: Verifica ADC_load < 5V antes das outras detecções.

    Retorna:
    - Um dicionário contendo os duty em que ocorreu cada evento e os ADC_Batt registrados.
    """

    resultado = {
        'Duty_ADC_load_below5V': None,
        'ADC_Batt_at_load5V': None,
        'Duty_ADC5V_below5V': None,
        'ADC_Batt_at5V': None,
        'Duty_ADC15V_below15V': None,
        'ADC_Batt_at15V': None
    }

    flag_ADC_load = not check_adc_load
    flag_ADC5V = False
    flag_ADC15V = False
    flag_desbt = False
    ser.write(b'DGPTH\r')
    aguardar_ack(ser)
      
    try:
        if use_enpth:
            ser.write(b'ENPTH\r')
            aguardar_ack(ser)

        for duty in np.arange(70.0, 59.9, -0.2):
            comando = f'FR1D{duty:.1f}\r'.encode()
            ser.write(comando)
            aguardar_ack(ser)

            time.sleep(1)

            if not flag_desbt:
                ser.reset_input_buffer()
                ser.write(b'DESBT\r')
                aguardar_ack(ser)
                flag_desbt = True

            # Leitura dos ADCs
            ser.reset_input_buffer()
            ser.write(b'AQADC\r')
            time.sleep(0.3)
            info = ser.readline().decode(errors='ignore').strip()

            if len(info) < 30:
                print(f"⚠️ Dados inválidos na leitura ADC com duty {duty}.")
                continue

            try:
                ADC_15V = float(info[1:6]) * const_fonte * red_ADCs
                ADC_5V = float(info[7:12]) * const_fonte * red_ADCs
                ADC_load = float(info[13:18]) * const_fonte * red_ADCs
                ADC_Batt = float(info[25:30]) * const_fonte * red_batt
            except ValueError:
                print(f"❌ Erro ao processar ADC na iteração duty {duty}.")
                continue

            print(f"Duty {duty:.1f} → ADC_15V: {ADC_15V:.2f}V | ADC_5V: {ADC_5V:.2f}V | ADC_load: {ADC_load:.2f}V | ADC_Batt: {ADC_Batt:.2f}V")

            # Etapa 1: verifica ADC_load < 5V (se ativado)
            if check_adc_load and not flag_ADC_load and ADC_load < 4.8:
                resultado['Duty_ADC_load_below5V'] = duty
                resultado['ADC_Batt_at_load5V'] = ADC_Batt
                flag_ADC_load = True

                with open(file_name_txt, 'a') as f:
                    f.write('***** ADC_load caiu abaixo de 5V *****\n')
                    f.write(f'Duty: {duty:.1f}\n')
                    f.write(f'ADC_Batt: {ADC_Batt:.2f}V\n')

                print("✔️ ADC_load caiu abaixo de 5V.")

            # Etapas 2 e 3: só continuam após load < 5V (se ativado)
            if flag_ADC_load:
                if not flag_ADC5V and ADC_5V < 4.8:
                    resultado['Duty_ADC5V_below5V'] = duty
                    resultado['ADC_Batt_at5V'] = ADC_Batt
                    flag_ADC5V = True

                    with open(file_name_txt, 'a') as f:
                        f.write('***** ADC_5V caiu abaixo de 5V *****\n')
                        f.write(f'Duty: {duty:.1f}\n')
                        f.write(f'ADC_Batt: {ADC_Batt:.2f}V\n')

                    print("✔️ ADC_5V caiu abaixo de 5V.")

                if not flag_ADC15V and ADC_15V < 14.8:
                    resultado['Duty_ADC15V_below15V'] = duty
                    resultado['ADC_Batt_at15V'] = ADC_Batt
                    
                    flag_ADC15V = True

                    with open(file_name_txt, 'a') as f:
                        f.write('***** ADC_15V caiu abaixo de 15V *****\n')
                        f.write(f'Duty: {duty:.1f}\n')
                        f.write(f'ADC_Batt: {ADC_Batt:.2f}V\n')

                    print("✔️ ADC_15V caiu abaixo de 15V.")
                    
                    ser.write(b'FR1D80\r')
                    aguardar_ack(ser)
                    
                    ser.write(b'LIGDC\r')
                    aguardar_ack(ser)
                    
                    
                    
                    ok, tempo = aguardar_adc_5v(ser, const_fonte, red_ADCs)
                    if not ok:
                        return False, False
                    
                    
                    # # Loop até ADC_5V > 4.5
                    # while True:
                    #     time.sleep(1)
                        
                    #     ser.reset_input_buffer()
                    #     ser.write(b'AQADC\r')                 
                    #     info = ser.readline().decode(errors='ignore').strip()
                        
                    #     if len(info) < 30:
                    #         print("⚠️ Dados inválidos, tentando novamente...")
                    #         continue
                    
                    #     try:
                    #         ADC_5V = float(info[7:12]) * const_fonte * red_ADCs
                    #     except ValueError:
                    #         print("❌ Erro ao converter ADC_5V.")
                    #         continue
                    
                    #     print(f"🔁 ADC_5V = {ADC_5V:.2f}V")
                    
                    #     if ADC_5V > 4.5:
                    #         print("✅ ADC_5V está OK, continuando...")
                    #         break
                    time.sleep(2)
                    ser.write(b'DESDC\r')
                    aguardar_ack(ser)
 
            if flag_ADC_load and flag_ADC5V and flag_ADC15V:
                break

        if check_adc_load and not flag_ADC_load:
            print("⚠️ Condição ADC_load < 5V NÃO atingida.")
        if not flag_ADC5V:
            print("⚠️ Condição ADC_5V < 5V NÃO atingida.")
        if not flag_ADC15V:
            print("⚠️ Condição ADC_15V < 15V NÃO atingida.")

        return resultado

    except Exception as e:
        print(f"[ERRO] Durante teste PWM: {e}")
        return {}

def teste_variando_pwm_pth(
    ser,
    const_fonte,
    red_ADCs,
    red_batt,
    file_name_txt,
    use_enpth=False,
    check_adc_load=False
):
    """
    Teste PWM com detecção em dois estágios:
    1. (opcional) Detecta queda de ADC_load < 5V
    2. Detecta queda de ADC_5V < 5V e ADC_15V < 15V
    
    Parâmetros:
    - ser: serial
    - const_fonte, red_ADCs, red_batt: fatores de calibração
    - file_name_txt: arquivo de log
    - use_enpth: envia ENPTH no início
    - check_adc_load: ativa o primeiro estágio de verificação de carga

    Retorna:
    - Dict com duty e ADC_Batt nos três eventos detectados
    """
    resultado = {
        'Duty_ADC_at_load_alarm': None,
        'ADC_Batt_at_load_alarm': None,
        'Duty_ADC5V_below5V': None,
        'ADC_Batt_at5V': None,
        'Duty_ADC15V_below15V': None,
        'ADC_Batt_at15V': None
    }

    flag_ADC_load = not check_adc_load
    flag_ADC5V = False
    flag_ADC15V = False
    flag_desbt = False

    if use_enpth:
        ser.write(b'ENPTH\r')
        aguardar_ack(ser)
        ser.write(b'ACLOAD\r')
        aguardar_ack(ser)

    try:
        # Loop 1: verifica ADC_load < 5V se necessário
        if check_adc_load:
            if not flag_desbt:                            
                ser.write(b'FR1D80\r')
                aguardar_ack(ser)
                time.sleep(.5)
                ser.reset_input_buffer()
                ser.write(b'DESBT\r')
                aguardar_ack(ser)
                flag_desbt = True
                
            
                        # Inicialização antes do loop principal
            ema_load = None
            ema_batt = None
            alpha = 0.25  # Fator de suavização: 0.1 a 0.3 é comum para EMA em tempo real
            
            for duty in np.arange(63.0, 59.9, -0.001):
                comando = f'FR1D{duty:.1f}\r'.encode()
                ser.write(comando)
                aguardar_ack(ser)
                
                ser.reset_input_buffer()
                ser.write(b'AQADC\r')
                info = ser.readline().decode(errors='ignore').strip()

                
                # Dentro do loop principal...
                try:
                    ADC_load = float(info[13:18]) * const_fonte * red_ADCs
                    ADC_Batt = float(info[25:30]) * const_fonte * red_batt
                except ValueError:
                    continue
                                
                                # Inicializa EMA na primeira leitura
                if ema_load is None:
                    ema_load = ADC_load
                    ema_batt = ADC_Batt
                else:
                    ema_load = alpha * ADC_load + (1 - alpha) * ema_load
                    ema_batt = alpha * ADC_Batt + (1 - alpha) * ema_batt
                
                # Cálculo da diferença
                diferenca = abs(ema_load - ema_batt)
                
                print(f"📈 EMA ADC_load: {ema_load:.2f} V | EMA ADC_Batt: {ema_batt:.2f} V | Diferença: {diferenca:.2f} V")
                
                #print(f"Duty {duty:.1f} → ADC_load: {ADC_load:.2f}V | ADC_Batt: {ADC_Batt:.2f}V")

                if diferenca > 0.5:
                    ser.write(b'LIGBT\r') #acionar bateria
                    aguardar_ack(ser)
                    
                    ser.write(b'FR1D80\r')
                    aguardar_ack(ser)
                    resultado['Duty_ADC_at_load_alarm'] = duty
                    resultado['ADC_Batt_at_load_alarm'] = ADC_Batt
                    
                    ser.write(b'DESBT\r') #acionar bateria
                    aguardar_ack(ser)

                    with open(file_name_txt, 'a') as f:
                        f.write('***** ADC_load caiu abaixo de 5V *****\n')
                        f.write(f'Duty: {duty:.1f}\n')
                        f.write(f'ADC_Batt: {ADC_Batt:.2f}V\n')

                    print("✔️ Alarme de carga desligada (ADC_load).")
                    break  # Finaliza primeiro estágio

        # Loop 2: detecta queda de 5V e 15V
        for duty in np.arange(72.0, 59.9, -0.2):
            comando = f'FR1D{duty:.1f}\r'.encode()
            ser.write(comando)
            aguardar_ack(ser)
            time.sleep(.5)

            ser.reset_input_buffer()
            ser.write(b'AQADC\r')
            info = ser.readline().decode(errors='ignore').strip()

            try:
                ADC_15V = float(info[1:6]) * const_fonte * red_ADCs
                ADC_5V = float(info[7:12]) * const_fonte * red_ADCs
                ADC_Batt = float(info[25:30]) * const_fonte * red_batt
            except ValueError:
                continue

            print(f"Duty {duty:.1f} → ADC_15V: {ADC_15V:.2f}V | ADC_5V: {ADC_5V:.2f}V | ADC_Batt: {ADC_Batt:.2f}V")

            if not flag_ADC5V and ADC_5V < 4.8:
                resultado['Duty_ADC5V_below5V'] = duty
                resultado['ADC_Batt_at5V'] = ADC_Batt
                flag_ADC5V = True

                with open(file_name_txt, 'a') as f:
                    f.write('***** ADC_5V caiu abaixo de 5V *****\n')
                    f.write(f'Duty: {duty:.1f}\n')
                    f.write(f'ADC_Batt: {ADC_Batt:.2f}V\n')

            if not flag_ADC15V and ADC_15V < 14.8:
                resultado['Duty_ADC15V_below15V'] = duty
                resultado['ADC_Batt_at15V'] = ADC_Batt
                flag_ADC15V = True

                with open(file_name_txt, 'a') as f:
                    f.write('***** ADC_15V caiu abaixo de 15V *****\n')
                    f.write(f'Duty: {duty:.1f}\n')
                    f.write(f'ADC_Batt: {ADC_Batt:.2f}V\n')

            if flag_ADC5V and flag_ADC15V:
                break        
        
        ser.write(b'DGLOAD\r')
        aguardar_ack(ser)

        return resultado

    except Exception as e:
        print(f"[ERRO] Durante teste PWM: {e}")
        ser.write(b'DGLOAD\r')
        aguardar_ack(ser)
        return {}
  
def aguardar_ack(ser, timeout=1.0):
    """
    Aguarda até receber 'RXACKOK' ou até timeout.
    
    Retorna:
    - Tuple: (status_bool, resposta_string)
    """
    inicio = time.time()
    buffer = ""

    while time.time() - inicio < timeout:
        if ser.in_waiting:
            buffer += ser.read(ser.in_waiting).decode(errors='ignore')
            if "ACKOK" in buffer:
                return True, buffer.strip()
        else:
            time.sleep(0.005)

    return False, buffer.strip()

# --------------------- Função Principal --------------------

def main():
    config = carregar_config()
    porta_serial = obter_porta_serial(config)
    salvar_config(porta_serial)
    
    # Arquivo de log
    file_name_txt = "resultado_teste.txt"

    try:
        print(f"Tentando abrir porta {porta_serial}...")
        
        ser = serial.Serial(
        port=porta_serial,
        baudrate=115200,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=2,
        write_timeout=2,
        rtscts=False,    # Desabilita hardware flow control
        dsrdtr=False,    # Desabilita DSR/DTR
        xonxoff=False    # Desabilita software flow control
        )
        


        time.sleep(1)

        if ser.is_open:
            print(f"Porta {porta_serial} aberta com sucesso.")
            ser.reset_input_buffer()
            # Sequencia inicial de desligamento de cargas e fontes
            ser.write(b'DESDC\r')
            aguardar_ack(ser)
            ser.write(b'DESBT\r')
            aguardar_ack(ser)
            ser.write(b'FR1D0\r')
            aguardar_ack(ser)
            ser.write(b'DESCB\r')
            aguardar_ack(ser)
            ser.write(b'DGLOAD\r')
            aguardar_ack(ser)
            time.sleep(1)
        else:
            print("Falha ao abrir a porta.")
            sys.exit(1)

        adc_batt = verificar_curto_bateria(ser, const_fonte, red_batt)
        print(f"Leitura ADC Bateria: {adc_batt:.3f}")

        if adc_batt == 0:
            print("🔴 Atenção: possível curto na bateria detectado!")
        else:
            print("✅ Bateria operando normalmente.")
            
            
        adc_dcdc = verificar_curto_DCDC(ser, const_fonte, red_DCDC)
        print(f"Leitura ADC DCDC: {adc_dcdc:.3f}")

        if adc_dcdc == 0:
            print("🔴 Atenção: possível curto no DCDC detectado!")
        else:
            print("✅ DCDC operando normalmente.")
            
        #time.sleep(10)
        #  Chamada da função de teste
        Teste1A, Teste1B = testar_dcdc_e_carga(
            ser,
            const_fonte,
            red_cf,
            red_DCDC,
            red_batt,
            red_load,
            file_name_txt
        )

        # ✔️ Resultado no console
        if Teste1A and Teste1B:
            print("\n🟢 Todos os testes foram concluídos com sucesso!")
        else:
            print("\n🔴 Houve falha em um ou mais testes.")    
            
        resultado = testar_bateria_isolada(ser,const_fonte,red_cf,red_ADCs,red_batt,file_name_txt)

        if resultado:
            print("🟢 Teste passou com sucesso!")
        else:
            print("🔴 Teste falhou!")    
        
        # ✔️ Testes de alarmes de temperatura
        result = teste_alarmes_temperatura(
        ser,
        const_fonte,
        red_cf,
        red_ADCs,
        red_batt,
        file_name_txt
        )

        print(result)
        
        #função de variação do PWM para detectar limites de teste com PteH desl.
        resultado=teste_variando_pwm(
            ser,
            const_fonte,
            red_ADCs,
            red_batt,
            file_name_txt,
            use_enpth=False,
            check_adc_load=False
        )
        
        resultado=teste_variando_pwm_pth(
            ser,
            const_fonte,
            red_ADCs,
            red_batt,
            file_name_txt,
            use_enpth=True,
            check_adc_load=True
        )


        if resultado:
            print(f"{'Evento':<30} {'Valor':>10}")
            print("-" * 42)
            print(f"{'Duty (ADC_Batt)':<30} {resultado['Duty_ADC_at_load_alarm']:.1f}")
            print(f"{'ADC_Batt at Load Alarm':<30} {resultado['ADC_Batt_at_load_alarm']:.2f} V")
            print(f"{'Duty (ADC_5V < 5V)':<30} {resultado['Duty_ADC5V_below5V']:.1f}")
            print(f"{'ADC_Batt at 5V':<30} {resultado['ADC_Batt_at5V']:.2f} V")
            print(f"{'Duty (ADC_15V < 15V)':<30} {resultado['Duty_ADC15V_below15V']:.1f}")
            print(f"{'ADC_Batt at 15V':<30} {resultado['ADC_Batt_at15V']:.2f} V")
        else:
            print("🔴 Nenhuma queda detectada no range de duty.")
        
    except serial.SerialException as e:
        print(f"Erro de comunicação: {e}")
    except KeyboardInterrupt:
        print("\nExecução interrompida pelo usuário (Ctrl+C).")
    except Exception as e:
        print(f"Erro inesperado: {e}")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("Porta serial fechada.")

# --------------------- Execução --------------------

if __name__ == "__main__":
    main()

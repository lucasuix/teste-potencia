import threading
import time
from view import View
from model import Model, TestResult


class Controller:
    def __init__(self):
        self.view = View(self)
        self.model = Model()
        
    def start(self):
        self.view.run()

    def connect_btn_handler(self):
        usuario, porta_serial, numero_serie, is_test_mode = self.view.get_user_inputs()
        if not porta_serial or "Selecione" in porta_serial:
            self.view.add_update(self.view.show_message, "Selecione uma porta serial válida.", True)
            return

        self.view.add_update(self.view.toggle_connection, True)
        threading.Thread(target=self.run_tests, args=(porta_serial,), daemon=True).start()

    def _carregar_dados_iniciais(self):
        usuarios = ["Mário", "Thiago", "Thiago Dias", "João", "Márcia"]  # ou ler de config
        self.view.set_users_available(usuarios)

        # Preenche portas seriais disponíveis
        portas = self.model.get_available_ports()
        self.view.set_ports_available(portas)

    def cancel_btn_handler(self):
        self.view.add_update(self.view.show_message, "Cancelamento não implementado ainda.")

    def compile_btn_handler(self):
        self.view.add_update(self.view.show_message, "Compilação de logs ainda não implementada.")

    def run_tests(self, porta_serial: str):
        # Record start time
        start_time = time.time()
        overall_success = True
        final_results = []
        detailed_results = []  # Store all test details for display

        # Hide previous final results and show loading
        self.view.add_update(self.view.hide_final_results)
        self.view.add_update(self.view.show_loading, True)

        # Obter dados da sessão
        usuario, porta_serial, numero_serie, is_test_mode = self.view.get_user_inputs()

        try:
            self.view.add_update(self.view.show_message, f"Tentando abrir porta {porta_serial}...")
            
            # Iniciar sessão de testes
            self.model.start_test_session(numero_serie, usuario)
            
            # Conecta à porta serial
            if not self.model.connect(porta_serial):
                self.view.add_update(self.view.show_message, "❌ Falha ao abrir a porta.", True)
                overall_success = False
                return
            
            self.view.add_update(self.view.show_message, "✅ Porta aberta com sucesso.")
            
            # Inicialização do sistema
            if not self.model.initialize_system():
                self.view.add_update(self.view.show_message, "❌ Falha na inicialização do sistema.", True)
                overall_success = False
                return
            
            time.sleep(1)

            # Teste de curto na bateria
            battery_result = self.model.test_battery_short()
            self.model.update_test_result("teste_bateria_curto", battery_result.passed)
            
            if 'adc_batt' in battery_result.details:
                adc_msg = f"Leitura ADC Bateria: {battery_result.details['adc_batt']:.3f}V"
                self.view.add_update(self.view.show_message, adc_msg)
                detailed_results.append(adc_msg)
            
            if battery_result.passed:
                self.view.add_update(self.view.update_result_label, "bateria", True)
                msg = "✅ Bateria operando normalmente."
                self.view.add_update(self.view.show_message, msg)
                detailed_results.append("Teste Curto Bateria: OK")
            else:
                self.view.add_update(self.view.update_result_label, "bateria", False)
                msg = "🔴 Atenção: possível curto na bateria!"
                self.view.add_update(self.view.show_message, msg, True)
                detailed_results.append("Teste Curto Bateria: NG")
                overall_success = False

            # Teste de curto no DCDC
            dcdc_result = self.model.test_dcdc_short()
            self.model.update_test_result("teste_dcdc_curto", dcdc_result.passed)
            
            if 'adc_dcdc' in dcdc_result.details:
                adc_msg = f"Leitura ADC DCDC: {dcdc_result.details['adc_dcdc']:.3f}V"
                self.view.add_update(self.view.show_message, adc_msg)
                detailed_results.append(adc_msg)
            
            if dcdc_result.passed:
                self.view.add_update(self.view.update_result_label, "dcdc", True)
                msg = "✅ DCDC operando normalmente."
                self.view.add_update(self.view.show_message, msg)
                detailed_results.append("Teste Curto DCDC: OK")
            else:
                self.view.add_update(self.view.update_result_label, "dcdc", False)
                msg = "🔴 Atenção: possível curto no DCDC!"
                self.view.add_update(self.view.show_message, msg, True)
                detailed_results.append("Teste Curto DCDC: NG")
                overall_success = False

            # Teste DCDC e carga - separados na UI
            teste1a_result, teste1b_result = self.model.test_dcdc_and_load()
            self.model.update_test_result("teste1a", teste1a_result.passed)
            self.model.update_test_result("teste1b", teste1b_result.passed)
            
            # Update UI status for each test separately
            self.view.add_update(self.view.update_result_label, "teste1a", teste1a_result.passed)
            self.view.add_update(self.view.update_result_label, "teste1b", teste1b_result.passed)

            dcdc_load_success = teste1a_result.passed and teste1b_result.passed

            if dcdc_load_success:
                msg = "\n🟢 Testes DCDC e carga concluídos com sucesso!"
                self.view.add_update(self.view.show_message, msg)
            else:
                msg = "\n🔴 Houve falha nos testes DCDC e carga."
                self.view.add_update(self.view.show_message, msg)
                overall_success = False

            # Teste bateria isolada
            battery_isolated_result = self.model.test_isolated_battery()
            self.model.update_test_result("teste_bateria_isolada", battery_isolated_result.passed)
            self.view.add_update(self.view.update_result_label, "bateria_isolada", battery_isolated_result.passed)
            
            # Add detailed results
            detailed_results.append(f"Teste Bateria Isolada: {'OK' if battery_isolated_result.passed else 'NG'}")
            if 'adc_batt' in battery_isolated_result.details:
                detailed_results.append(f"  Batt: {battery_isolated_result.details['adc_batt']:.2f}V | DCDC: {battery_isolated_result.details.get('adc_dcdc', 0):.2f}V | Load: {battery_isolated_result.details.get('adc_load', 0):.2f}V")

            # Testes de alarme de temperatura
            temp_results = self.model.test_temperature_alarms()
            temp_success = all(result.passed for result in temp_results.values() if isinstance(result, TestResult))
            
            # Registrar resultados dos testes de temperatura e atualizar UI
            temp_mapping = {
                "Teste4A": "temp_alarm1",
                "Teste4B": "temp_return1", 
                "Teste4C": "temp_alarm2",
                "Teste4D": "temp_return2"
            }
            
            for test_name, result in temp_results.items():
                if isinstance(result, TestResult):
                    self.model.update_test_result(test_name, result.passed)
                    
                    # Update UI status for each temperature test
                    if test_name in temp_mapping:
                        ui_key = temp_mapping[test_name]
                        self.view.add_update(self.view.update_result_label, ui_key, result.passed)
            
            if temp_success:
                msg = "✅ Testes de temperatura concluídos com sucesso."
                self.view.add_update(self.view.show_message, msg)
            else:
                msg = "🔴 Falhas nos testes de temperatura."
                self.view.add_update(self.view.show_message, msg)
                overall_success = False
    
            # Teste PWM
            pwm_result = self.model.test_pwm_variation(use_enpth=False, check_adc_load=False)
            self.model.update_test_result("teste_pwm", pwm_result.is_valid())
            self.view.add_update(self.view.update_result_label, "pwm", pwm_result.is_valid())

            # Teste PWM PTH
            pwm_pth_result = self.model.test_pwm_pth_variation(use_enpth=True, check_adc_load=True)
            self.model.update_test_result("teste_pwm_pth", pwm_pth_result.is_valid())
            self.model.update_pwm_results(pwm_pth_result)  # Salvar resultados PWM detalhados
            self.view.add_update(self.view.update_result_label, "pwm_pth", pwm_pth_result.is_valid())

            # Testes de Comunicação
            self.view.add_update(self.view.show_message, "\n🔄 Iniciando testes de comunicação...")
            
            # Teste Inclinômetro
            inclinometro_result = self.model.test_inclinometro()
            self.model.update_test_result("teste_inclinometro", inclinometro_result.passed)
            self.view.add_update(self.view.update_result_label, "inclinometro", inclinometro_result.passed)
            
            # Teste ADC
            adc_result = self.model.test_adc_communication()  
            self.model.update_test_result("teste_adc", adc_result.passed)
            self.view.add_update(self.view.update_result_label, "adc", adc_result.passed)
            
            # Teste RAK
            rak_result = self.model.test_rak_communication()
            self.model.update_test_result("teste_rak", rak_result.passed)
            self.view.add_update(self.view.update_result_label, "rak", rak_result.passed)
            
            # Teste RTC
            rtc_result = self.model.test_rtc_communication()
            self.model.update_test_result("teste_rtc", rtc_result.passed)
            self.view.add_update(self.view.update_result_label, "rtc", rtc_result.passed)
            
            # Teste Serial Number
            serial_number_result = self.model.test_serial_number_communication()
            self.model.update_test_result("teste_serial_number", serial_number_result.passed)
            self.view.add_update(self.view.update_result_label, "serial_number", serial_number_result.passed)
            
            # Teste EEPROM
            eeprom_result = self.model.test_eeprom_communication()
            self.model.update_test_result("teste_eeprom", eeprom_result.passed)
            self.view.add_update(self.view.update_result_label, "eeprom", eeprom_result.passed)
            
            # Teste Ponte H
            ponte_h_result = self.model.test_ponte_h_communication()
            self.model.update_test_result("teste_ponte_h", ponte_h_result.passed)
            self.view.add_update(self.view.update_result_label, "ponte_h", ponte_h_result.passed)
            
            # Verificar se todos os testes de comunicação passaram
            comm_tests_passed = all([
                inclinometro_result.passed, adc_result.passed, rak_result.passed,
                rtc_result.passed, serial_number_result.passed, eeprom_result.passed,
                ponte_h_result.passed
            ])
            
            if comm_tests_passed:
                self.view.add_update(self.view.show_message, "✅ Todos os testes de comunicação concluídos com sucesso!")
            else:
                self.view.add_update(self.view.show_message, "🔴 Houve falha em um ou mais testes de comunicação.")
                overall_success = False

            if pwm_pth_result.is_valid():
                self.view.add_update(self.view.show_message, f"{'Evento':<30} {'Valor':>10}")
                self.view.add_update(self.view.show_message, "-" * 42)
                
                # Collect final results for display
                final_results.append(f"{'Evento':<30} {'Valor':>10}")
                final_results.append("-" * 42)
                
                if pwm_pth_result.duty_adc_at_load_alarm is not None:
                    duty_msg = f"{'Duty Cycle no Alarme de Carga':<30} {pwm_pth_result.duty_adc_at_load_alarm:.1f}%"
                    adc_msg = f"{'Tensão da Bateria no Alarme':<30} {pwm_pth_result.adc_batt_at_load_alarm:.2f} V"
                    self.view.add_update(self.view.show_message, duty_msg)
                    self.view.add_update(self.view.show_message, adc_msg)
                    final_results.append(duty_msg)
                    final_results.append(adc_msg)
                
                if pwm_pth_result.duty_adc5v_below5v is not None:
                    duty5v_msg = f"{'Duty Cycle na Queda de 5V':<30} {pwm_pth_result.duty_adc5v_below5v:.1f}%"
                    adc5v_msg = f"{'Tensão da Bateria em 5V':<30} {pwm_pth_result.adc_batt_at5v:.2f} V"
                    self.view.add_update(self.view.show_message, duty5v_msg)
                    self.view.add_update(self.view.show_message, adc5v_msg)
                    final_results.append(duty5v_msg)
                    final_results.append(adc5v_msg)
                
                if pwm_pth_result.duty_adc15v_below15v is not None:
                    duty15v_msg = f"{'Duty Cycle na Queda de 15V':<30} {pwm_pth_result.duty_adc15v_below15v:.1f}%"
                    adc15v_msg = f"{'Tensão da Bateria em 15V':<30} {pwm_pth_result.adc_batt_at15v:.2f} V"
                    self.view.add_update(self.view.show_message, duty15v_msg)
                    self.view.add_update(self.view.show_message, adc15v_msg)
                    final_results.append(duty15v_msg)
                    final_results.append(adc15v_msg)
            else:
                self.view.add_update(self.view.show_message, "🔴 Nenhuma queda detectada no range de duty.")
                overall_success = False
                final_results.append("🔴 Nenhuma queda detectada no range de duty.")

        except Exception as e:
            self.view.add_update(self.view.show_message, f"Erro inesperado: {e}", True)
            overall_success = False
        finally:
            # Calculate test duration
            end_time = time.time()
            duration = end_time - start_time
            
            # Finalizar sessão de testes e salvar na planilha Excel
            excel_saved = self.model.finalize_test_session()
            
            # Hide loading indicator
            self.view.add_update(self.view.show_loading, False)
            # Prepare and show final results - only PWM technical data
            pwm_details = []
            
            # Add only PWM measurement results (technical data only)
            if final_results:
                for result in final_results:
                    # Skip headers and separators, only include actual measurements
                    if not ('Evento' in result or 'Valor' in result or '─' in result or result.strip() == ''):
                        # Only include lines with actual measurement data
                        if any(x in result for x in ['Duty Cycle', 'Tensão da Bateria']):
                            pwm_details.append(result)
            
            if pwm_details:
                final_text = "\n".join(pwm_details)
                self.view.add_update(self.view.show_final_results, final_text, duration)
            else:
                # If no PWM data, show empty results
                self.view.add_update(self.view.show_final_results, "", duration)
            
            # Informar sobre salvamento na planilha
            if excel_saved:
                self.view.add_update(self.view.show_message, "📊 Resultados salvos na planilha Excel (log/resultados_testes.xlsx)")
            else:


                self.view.add_update(self.view.show_message, "⚠️ Erro ao salvar na planilha Excel")
            
            # Desconecta do model
            self.model.disconnect()
            self.view.add_update(self.view.show_message, "Porta serial fechada.")
            self.view.add_update(self.view.toggle_connection, False)

            # Mostrar popup no fim, só uma vez
            popup_message = "Todos os testes foram concluídos com sucesso!" if overall_success else "Houve falha em um ou mais testes."
            if excel_saved:
                popup_message += "\n\nResultados salvos na planilha Excel."
            
            self.view.add_update(self.view.show_test_result, popup_message, overall_success)


if __name__ == "__main__":
    Controller().start()
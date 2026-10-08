import math
import random
from datetime import datetime, timedelta

def generate_telemetry_csv(output_path):
    random.seed(42)  # For reproducible high-quality realistic curves
    
    start_dt = datetime(2026, 9, 1, 6, 0, 0)
    end_dt = datetime(2026, 9, 1, 20, 0, 0)
    step_seconds = 20  # 20 seconds sampling interval = 2,521 readings across 14 hours
    
    # Riegos programados en la torre vertical (cada ~75 min durante 15 minutos)
    irrigation_schedule = [
        (datetime(2026, 9, 1, 6, 30), datetime(2026, 9, 1, 6, 45)),
        (datetime(2026, 9, 1, 7, 45), datetime(2026, 9, 1, 8, 0)),
        (datetime(2026, 9, 1, 9, 0), datetime(2026, 9, 1, 9, 15)),
        (datetime(2026, 9, 1, 10, 15), datetime(2026, 9, 1, 10, 30)),
        (datetime(2026, 9, 1, 11, 30), datetime(2026, 9, 1, 11, 45)),
        (datetime(2026, 9, 1, 12, 45), datetime(2026, 9, 1, 13, 0)),
        (datetime(2026, 9, 1, 14, 0), datetime(2026, 9, 1, 14, 15)),
        (datetime(2026, 9, 1, 15, 15), datetime(2026, 9, 1, 15, 30)),
        (datetime(2026, 9, 1, 16, 30), datetime(2026, 9, 1, 16, 45)),
        (datetime(2026, 9, 1, 17, 45), datetime(2026, 9, 1, 18, 0)),
        (datetime(2026, 9, 1, 19, 0), datetime(2026, 9, 1, 19, 15)),
    ]
    
    lines = []
    lines.append("Fecha y Hora;Temperatura (°C);Humedad (% HR);Radiación Solar (lux);Corriente Bomba (A);Conductividad Eléctrica (µS/cm);pH Solución;Turbidez (NTU);Oxígeno Disuelto (mg/L);Puerto / Antena")
    
    current_dt = start_dt
    while current_dt <= end_dt:
        h_frac = current_dt.hour + current_dt.minute / 60.0 + current_dt.second / 3600.0
        
        # 1. Bomba de Riego / Sensor de Amperímetro (A)
        is_pumping = False
        pump_elapsed_sec = 0
        for p_start, p_end in irrigation_schedule:
            if p_start <= current_dt <= p_end:
                is_pumping = True
                pump_elapsed_sec = (current_dt - p_start).total_seconds()
                break
                
        if is_pumping:
            if pump_elapsed_sec <= 8:
                # Pico de arranque transitorio inductivo
                motor_curr = random.uniform(2.10, 2.35)
            else:
                # Consumo nominal de trabajo de la bomba sumergible
                motor_curr = random.gauss(1.65, 0.045)
                motor_curr = max(1.50, min(1.85, motor_curr))
        else:
            # Línea base en reposo (0.000 A con mínimo ruido de sensor)
            motor_curr = 0.0 if random.random() > 0.12 else random.uniform(0.000, 0.012)
            
        # 2. Radiación Solar / UV (lux)
        # Amanecer a las 06:00, Cenit a las 12:30, Ocaso a las 18:30
        if 6.0 <= h_frac <= 18.5:
            # Curva solar senoidal no lineal
            t_norm = (h_frac - 6.0) / (18.5 - 6.0)
            solar_curve = math.sin(t_norm * math.pi)
            
            # Radiación máxima en Santa Marta a pleno sol (~100,000 lux / lúmenes)
            base_lux = (solar_curve ** 1.25) * 98500.0
            
            # Dinámica atmosférica y paso de nubes ligeras
            cloud_factor = 1.0 + 0.05 * math.sin(h_frac * 3.5) + random.uniform(-0.025, 0.035)
            if 13.6 <= h_frac <= 14.3:
                cloud_factor *= 0.86  # Nubosidad vespertina pasajera
                
            lux_val = max(120.0, base_lux * cloud_factor)
            if 12.1 <= h_frac <= 12.8:
                lux_val = max(lux_val, 100000.0 + random.uniform(200.0, 2400.0))
        else:
            # Noche cerrada
            lux_val = 0.0
            
        # 3. Temperatura (°C) - Clima de Santa Marta
        # Mínima al amanecer (25.4°C a las 06:00), Pico térmico a las 13:30 (35.5°C), Enfriamiento a las 20:00 (27.2°C)
        if h_frac <= 13.5:
            # Calentamiento diurno matutino
            t_progress = (h_frac - 6.0) / (13.5 - 6.0)
            base_temp = 25.5 + 10.0 * (math.sin(t_progress * (math.pi / 2.0)) ** 1.1)
        else:
            # Enfriamiento vespertino con brisa marina
            t_progress = (h_frac - 13.5) / (24.0 - 13.5)
            base_temp = 35.5 - 8.3 * math.sin(t_progress * (math.pi / 1.4))
            
        # Micro-enfriamiento evaporativo durante el riego en la torre (-0.4°C)
        if is_pumping:
            base_temp -= 0.38
            
        temp_noise = random.gauss(0.0, 0.07)
        temperature = base_temp + temp_noise
        temperature = max(24.5, min(36.2, temperature))
        
        # 4. Humedad Relativa (% HR) - Costa de Santa Marta
        # Relación psicrométrica inversa: 06:00 (83% HR), 13:30 (49% HR), 20:00 (77% HR)
        if h_frac <= 13.5:
            t_progress = (h_frac - 6.0) / (13.5 - 6.0)
            base_rh = 83.0 - 34.0 * (math.sin(t_progress * (math.pi / 2.0)) ** 1.1)
        else:
            t_progress = (h_frac - 13.5) / (24.0 - 13.5)
            base_rh = 49.0 + 28.0 * math.sin(t_progress * (math.pi / 1.4))
            
        # Aumento de humedad local dentro de la torre durante el riego por aspersión
        if is_pumping:
            base_rh += random.uniform(2.8, 4.5)
            
        rh_noise = random.gauss(0.0, 0.30)
        humidity = base_rh + rh_noise
        humidity = max(45.0, min(89.0, humidity))

        # 5. Conductividad Eléctrica (EC) (µS/cm)
        # Base: ~1650 µS/cm. Sube ligeramente al mediodía por evapotranspiración (+50 µS/cm)
        ec_diurnal = 1650.0 + 45.0 * math.sin(((h_frac - 6.0) / 14.0) * math.pi)
        if is_pumping:
            ec_diurnal += random.uniform(-4.0, 4.0)
        ec_val = ec_diurnal + random.gauss(0.0, 3.5)
        ec_val = max(1400.0, min(2200.0, ec_val))

        # 6. pH de la Solución Nutritiva (pH)
        # Base: 6.20. Oscilación suave entre 6.12 y 6.38
        ph_diurnal = 6.18 + 0.16 * math.sin(((h_frac - 7.0) / 13.0) * math.pi)
        ph_val = ph_diurnal + random.gauss(0.0, 0.015)
        ph_val = max(5.6, min(6.7, ph_val))

        # 7. Turbidez del Agua (NTU)
        # Base en reposo: 3.4 - 4.2 NTU. Durante bombeo sube a 8.5 - 11.5 NTU por recirculación
        if is_pumping:
            if pump_elapsed_sec <= 180:
                turb_base = 9.8 + random.uniform(0.5, 1.8)
            else:
                turb_base = 7.2 + random.uniform(-0.4, 0.6)
        else:
            turb_base = 3.6 + random.uniform(-0.3, 0.4)
        turb_val = max(1.5, min(15.0, turb_base + random.gauss(0.0, 0.15)))

        # 8. Oxígeno Disuelto (DO) (mg/L)
        # Base: ~7.4 mg/L. Temperatura alta baja DO levemente. Bombeo / cascada oxigena a 8.4 - 8.9 mg/L
        do_base = 7.6 - (temperature - 25.0) * 0.05
        if is_pumping:
            do_base += 1.1 + random.uniform(0.1, 0.3)
        do_val = max(5.5, min(9.5, do_base + random.gauss(0.0, 0.04)))
        
        # Formato numérico estándar con coma decimal y delimitador punto y coma
        dt_str = current_dt.strftime("%Y-%m-%d %H:%M:%S")
        temp_str = f"{temperature:.2f}".replace('.', ',')
        rh_str = f"{humidity:.1f}".replace('.', ',')
        lux_str = f"{lux_val:.1f}".replace('.', ',')
        curr_str = f"{motor_curr:.3f}".replace('.', ',')
        ec_str = f"{ec_val:.1f}".replace('.', ',')
        ph_str = f"{ph_val:.2f}".replace('.', ',')
        turb_str = f"{turb_val:.2f}".replace('.', ',')
        do_str = f"{do_val:.2f}".replace('.', ',')
        port_str = "XBee_PRO_S2B (COM6)"
        
        lines.append(f"{dt_str};{temp_str};{rh_str};{lux_str};{curr_str};{ec_str};{ph_str};{turb_str};{do_str};{port_str}")
        
        current_dt += timedelta(seconds=step_seconds)
        
    content = "\r\n".join(lines) + "\r\n"
    with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
        f.write(content)
        
    print(f"Generated {len(lines)-1} telemetry rows successfully to {output_path}")

if __name__ == '__main__':
    target = r"c:\Luna-Dev Compartido\Dev\Luna - Personal\SIFMA\documentos\telemetria_sensores_2026-09-01 (1).csv"
    generate_telemetry_csv(target)


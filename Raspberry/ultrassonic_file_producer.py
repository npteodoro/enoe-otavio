import serial
import time
import csv
import datetime
import socket
import json
import os
import logging
import UltrassonicClass


# Criar a pasta "data" se não existir
if not os.path.exists("logs"):
    os.makedirs("logs")
    print("logs directory created.")

logger = logging.getLogger('ultrassonic_file_producer')
logger.setLevel(logging.INFO)

handler = logging.FileHandler('./logs/ultrassonic_file_producer.log')
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
# Carregar as configurações do arquivo config.json
try:
    with open("config.json") as f:
        config = json.load(f)
except (FileNotFoundError, json.JSONDecodeError) as e:
    logger.error(f"Error loading config file: {e}")
    exit(1)

config_csv_interval = config["CSV_INTERVALS"]

# Frequência de geração de arquivos em minutos (pode ser alterado conforme necessário)
csv_file_creation_minutes = config_csv_interval["file_creation_minutes"]
csv_file_creation_seconds = csv_file_creation_minutes * 60
csv_data_interval_seconds = config_csv_interval["data_interval_seconds"]

def main():

    ultrassonic_sensor = UltrassonicClass.UltrassonicClass(serialportname = '/dev/ttyS0', baudrate = 9600)
    ultrassonic_sensor.set_serial()
    
    # Criar a pasta "data" se não existir
    save_directory = "data_ultrassonic"
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)
        logger.info(f"{save_directory} created.")
    
    while True:
        try:
            # Nome do arquivo CSV baseado na data e hora atual
            timestamp = datetime.datetime.now()
            date_str = timestamp.strftime('%d-%m-%Y_%H:%M:%S')
            filename = os.path.join(save_directory, f"readings_{date_str}.csv")
            
            with open(filename, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["timestamp", "hostname", "distance", "epoch"])  # Header
                logger.info(f"Started writing to file {filename}.")
                
                end_time = time.time() + csv_file_creation_seconds
                while time.time() < end_time:
                    time.sleep(csv_data_interval_seconds)
                    

                    distance = ultrassonic_sensor.get_line()
                    
                    if distance is not None:
                        message = [
                            datetime.datetime.fromtimestamp(time.time()).strftime('%d-%m-%Y_%H:%M:%S'),
                            socket.gethostname(),
                            distance,
                            int(time.time())
                        ]
                        writer.writerow(message)
                        
                        # Forçar a gravação no disco após cada linha
                        file.flush()
                        os.fsync(file.fileno())
                        logger.info(f"Written data: {message}")
                    else:
                        logger.warning("Skipping write due to error reading distance.")
        except OSError as e:
            logger.error(f"File error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Program interrupted by user.")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
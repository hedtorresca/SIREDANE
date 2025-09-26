import logging

def basic_config():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("aplicacion.log"),
            logging.StreamHandler()
        ]
    )
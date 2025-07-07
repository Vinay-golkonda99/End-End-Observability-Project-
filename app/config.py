# config.py (instrumented with OTEL tracing + Loki log support)

import os
import configparser
import logging
from transformers import LlamaTokenizer, AutoModelForCausalLM, pipeline
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

def setup_logging(config_file='logging.ini'):
    config = configparser.ConfigParser()
    config.read(config_file)

    loggers = {
        'logger1': "/var/log/containers/Api_logs.log",
        'logger2': "/var/log/containers/Api_error_logs.log"
    }

    log_levels = {
        'logger1': 'INFO',
        'logger2': 'ERROR'
    }

    for log, filename in loggers.items():
        logger = logging.getLogger(log)
        logger.setLevel(getattr(logging, log_levels[log]))

        # File handler
        file_handler = logging.FileHandler(filename)
        file_handler.setLevel(getattr(logging, log_levels[log]))
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Stream handler for stdout (for OTEL or Promtail)
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(getattr(logging, log_levels[log]))
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    return logging.getLogger('logger1'), logging.getLogger('logger2')

def get_model(logger1, logger2):
    with tracer.start_as_current_span("load-model-pipeline"):
        CACHE_DIR = "./model_cache"
        model_path = os.getenv("MODEL_PATH", "/mnt/models/Deepseek") 
        logger1.info(f"modelpath : {model_path}")

        if not os.path.exists(model_path):
            logger2.error("no model path")
            raise FileNotFoundError(f"Model path does not exist: {model_path}")

        try:
            with tracer.start_as_current_span("load-tokenizer"):
                tokenizer = LlamaTokenizer.from_pretrained(model_path, cache_dir=CACHE_DIR)
            logger1.info(f"tokenizer loaded successfully")
        except Exception as e:
            logger2.error(f"Tokenizer loading failed: {e}")
            raise

        try:
            with tracer.start_as_current_span("load-model"):
                model = AutoModelForCausalLM.from_pretrained(model_path, cache_dir=CACHE_DIR)
            logger1.info(f"model loaded successfully")
        except Exception as e:
            logger2.error(f"Model loading failed: {e}")
            raise

        generator = pipeline("text-generation", model=model, tokenizer=tokenizer, device=-1)
        return tokenizer, model, generator

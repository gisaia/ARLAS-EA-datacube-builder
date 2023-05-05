import logging
import logging.config


class CustomLogger:
    __logger_name = "dc3-logger"

    @classmethod
    def get_logger(cls) -> logging.Logger:
        return logging.getLogger(cls.__logger_name)

    @classmethod
    def set_logger_name(cls, name: str):
        cls.__logger_name = name

    @classmethod
    def get_logger_name(cls):
        return cls.__logger_name

    @classmethod
    def register_logger(cls, logger_config: dict):
        if cls.__logger_name not in logger_config['loggers'].keys():
            raise ValueError('The given configuration does not have' +
                             f'the set logger name {cls.logger_name}')
        logging.config.dictConfig(logger_config)

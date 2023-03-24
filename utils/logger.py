import logging
import logging.config


class CustomLogger:
    logger_name = "dc3-logger"

    @classmethod
    def getLogger(cls) -> logging.Logger:
        return logging.getLogger(cls.logger_name)

    @classmethod
    def setLoggerName(cls, name: str):
        cls.logger_name = name

    @classmethod
    def getLoggerName(cls):
        return cls.logger_name

    @classmethod
    def registerLogger(cls, logger_config: dict):
        if cls.logger_name not in logger_config['loggers'].keys():
            raise ValueError('The given configuration does not have' +
                             f'the set logger name {cls.logger_name}')
        logging.config.dictConfig(logger_config)

# --*-- coding : utf-8 --*--
"""
Package : 

Author  : Trinity Core Team

MIT License

Copyright (c) 2018 Trinity

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NON-INFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import os
import copy
import logging.config


__all__ = ['init_logger']

LOG = logging.getLogger(__name__)

# This is a default configuration for Trinity system.
# DO NOT CHANGE THIS CONFIGURATION!!!!!
# Any developers want to set the log configuration, he/she could use BasicConfig
# to configure it.
log_default_settings = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] %(pathname)s line %(lineno)d '
                      '%(levelname)s :%(message)s'
        }
    },
    'handlers': {
        'default': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'default',
        }
    },
    'loggers': {
        '': {
            'handlers': ['default'],
            'level': 'INFO'
        }
    }
}


class BasicConfig(object):
    """
    Descriptions: Generate one basic dictionary as default configuration of
                  trinity LOG system.
    """
    def __init__(self):
        """
        Description: Constructor for logging system basic configuration
        """
        # Use default logging settings to initialize the logger
        self.basic_config = copy.deepcopy(log_default_settings)
        logging.config.dictConfig(self.basic_config)

        # Default log file path and name
        self.__log_file = './temp/trinity.log'

    def setup(self, path=None, file_name=None, level=logging.INFO,
              log_format=None, handlers='file', **kwargs):
        """
        Description: Setup the user loggers
        :param path: The path where saved the logs if file handler is set
        :param file_name: The log file name
        :param level: Log level settings. Please refer to the logging package.
        :param log_format: Define the log output format. Please refer to class
                           'Formatter' defined in the logging package.
        :param handlers: handlers name. default file handler name: 'file'
        :param kwargs:
        :return:
        """
        # Parse the log file
        file_name = self._parse_file_path(path, file_name)

        # Parse logger formatter
        self._parse_formatter(log_format)

        # Parse logger handlers
        self._parse_handlers(handlers, filename=file_name, **kwargs)

        # Parse which handler the logger uses
        self._parse_loggers(handlers, level, **kwargs)

        print(self.basic_config)
        # Finally, use the new dict to configure the loggers
        logging.config.dictConfig(self.basic_config)

    def set_level(self, level: int):
        """
        Description: set level by CLI to trace log conveniently.
        :param level: Refer to definition in logging package
        :return:
        """
        # set level
        level_name = logging.getLevelName(level)
        if level_name.__contains__('Level'):
            level_name = 'INFO'

        # Update this settings to the config dict
        self.basic_config['loggers']['']['level'] = level_name

        # Reset the logger
        logging.config.dictConfig(self.basic_config)

        return level_name

    def _parse_handlers(self, handlers=None, **kwargs):
        """
        Description: Set the file handlers for logger.
        :param handlers: String type.
        :param kwargs:
            ~
        :return:
        """
        # Valid handler name
        if not (handlers and isinstance(handlers, str)):
            # Use default handler name for file handler
            handlers = 'file'

        # Is it set a new handler for logger?
        handlers = handlers.strip()
        if 'default' == handlers:
            LOG.warning('Default handler should not be changed')
            return
        self.basic_config['handlers'][handlers] = dict()
        log_handler = self.basic_config['handlers'][handlers]

        # Start to parse the other parameters from kwargs
        # Get which class will be used by the file logger
        handler_class = kwargs.get('class') if kwargs.get('class') \
            else 'cloghandler.ConcurrentRotatingFileHandler'

        # Get the log file name
        log_file = kwargs.get('filename') if kwargs.get('filename') \
            else self.__log_file

        # Get the output formatter
        formatter = kwargs.get('formatter')
        formatter = formatter if formatter in self.basic_config['formatters'] \
            else 'default'

        # Get the count of files to saved and the size of each file
        # Default size: 5M
        max_size = kwargs.get('maxBytes') if kwargs.get('maxBytes') \
            else 5 * 1024 * 1024
        # Default total count of files: 10
        max_count = kwargs.get('backupCount') if kwargs.get('backupCount') \
            else 10

        # to set this handler with DEBUG level
        log_handler.update({
            'level': 'DEBUG',
            'class': handler_class,
            'filename': log_file,
            'formatter': formatter,
            'maxBytes': max_size,
            'backupCount': max_count
        })

        pass

    def _parse_loggers(self, handlers='file', level=logging.INFO, **kwargs):
        """

        :param handlers:
        :param kwargs:
        :return:
        """
        # Check whether this handler is in settings or not
        if handlers not in self.basic_config['handlers']:
            return

        default_logger = {'': {
            'handlers': ['default'],
            'level': 'INFO'
        }}
        # Get the flag which indicate keep default console output
        keep_default_logger = kwargs.get('use_default')
        if keep_default_logger:
            default_logger['']['handlers'] = ['default', handlers]
        else:
            default_logger['']['handlers'] = [handlers]

        # set level
        level_name = logging.getLevelName(level)
        if level_name.__contains__('Level'):
            level_name = 'INFO'
        default_logger['']['level'] = level_name

        # Update this settings to the config dict
        self.basic_config['loggers'].update(default_logger)

        return

    def _parse_formatter(self, formatter=None):
        """
        Description: Set the log output format.
                     Default format is defined in the log_default_settings.
        :param formatter: Dict type. Details to refer to the class 'Formatter'
        :return:
        """
        if isinstance(formatter, dict) and formatter:
            self.basic_config['formatters'].update(formatter)

        return

    @classmethod
    def _parse_file_path(cls, path=None, file_name=None):
        """

        :param path: String type. Refer to the comments of method 'setup'
        :param file_name:
        :return:
        """
        default_path = './temp'

        try:
            if not path:
                path = default_path

            # Create the folders to store the log files
            if isinstance(path, str) and not os.path.exists(path):
                os.makedirs(path)
                path = path.rstrip(r'/')

        except Exception as error:
            LOG.warning(
                'Path<{}> should be string type or fail to be created.'
                'Exception: {}'.format(path, error)
            )

            # use default path is current folder
            path = '.'

        file_name = file_name if file_name else 'trinity.log'

        return path + os.sep + file_name


LoggerSetter = BasicConfig()
init_logger = LoggerSetter.setup
set_logger_level = LoggerSetter.set_level

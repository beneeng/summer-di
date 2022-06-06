from typing import Optional, Type, List
from summer.bean_strereotype import BeanStereotype
from peewee import Model, Database, DatabaseProxy
from summer.configuration.configuration import SummerConfigurationContext

from summer.configuration.configuration_value import ConfigurationValue
from summer.database.connection_templates import DatabaseConnectionTemplate, SQLiteConnectionTemplate, MysqlConnectionTemplate, PostgreSQLConnectionTemplate
from summer.database.entities import DatabaseException
from summer.summer_logging import get_summer_logger
from bot.utils import config_keys


class DatabaseConnectionFactory(BeanStereotype):

    database_templates: List[DatabaseConnectionTemplate] = [
        SQLiteConnectionTemplate(),
        MysqlConnectionTemplate(),
        PostgreSQLConnectionTemplate()
    ]

    database_type = ConfigurationValue(
        config_keys.DATABASE_TYPE, str, default='sqlite').typed()

    def __init__(self, 
        configuration_context: SummerConfigurationContext
        ) -> None:
        super().__init__()
        self._configuration_context = configuration_context
        self._database: Optional[Database] = None

    def _assert_connected(self):
        if self._database is None:
            self._database = self._create_database_connection()
            self._database.connect()

    def _create_database_connection(self) -> Database:
        db_type = self.database_type
        for template in self.database_templates:
            if isinstance(template, DatabaseConnectionTemplate) and template.get_type().lower() == db_type.lower():
                configuration = self._configuration_context.get_configuration_value(
                    config_keys.DATABASE_CONFIGURATION, template.get_configuration_type())
                return template.get_connection(configuration)

        raise ValueError(f"Unknown database type \"{db_type}\"")

    def bind_entity(self, entity: Type[Model]):
        self._assert_connected()
        db_proxy = entity._meta.database
        if not isinstance(db_proxy, DatabaseProxy):
            raise DatabaseException(
                "Entity can not be bound to context, because it is not initialized with a database proxy")

        if db_proxy.obj is not None and db_proxy.obj != self._database:
            raise DatabaseException(
                "Entity can not be bound to context, because it isalready bound to another context")

        if db_proxy.obj != self._database:
            entity._meta.database.initialize(self._database)
        self._create_database_if_necessary(entity)

    def _create_database_if_necessary(self, entity: Type[Model]):
        if not entity.table_exists():
            get_summer_logger().debug("Creating table for class %s", entity)
            entity.create_table()

    def get_database(self) -> Database:
        return self._database

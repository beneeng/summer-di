from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Type, TypeVar, Generic
from peewee import Database, MySQLDatabase, PostgresqlDatabase, SqliteDatabase

CONFIGURATION_TYPE = TypeVar("CONFIGURATION_TYPE")

class DatabaseConnectionTemplate(Generic[CONFIGURATION_TYPE]):

    @abstractmethod
    def get_type(self) -> str:
        pass

    def get_configuration_type(self) -> Type[CONFIGURATION_TYPE]:
        return dict

    @abstractmethod
    def get_connection(self, configuration: CONFIGURATION_TYPE) -> Database:
        pass


@dataclass
class MysqlConnectionConfiguration:
    hostname: str
    username :str
    db_name :str
    port :int = field(default=3306)
    password: str= field(default=None)


class MysqlConnectionTemplate(DatabaseConnectionTemplate[MysqlConnectionConfiguration]):

    def get_type(self) -> str:
        return "mysql"

    def get_configuration_type(self) -> Type[MysqlConnectionConfiguration]:
        return MysqlConnectionConfiguration
    
    def get_connection(self, configuration: MysqlConnectionConfiguration) -> MySQLDatabase:

        kwargs = {}
        if configuration.password is not None:
            kwargs['password'] = configuration.password
        
        return MySQLDatabase(configuration.db_name,
            user=configuration.username, 
            host=configuration.hostname, 
            port=configuration.port, 
            **kwargs)

@dataclass
class PostgreSQLConnectionConfiguration:
    hostname: str
    username :str
    password: str
    db_name :str
    port :int = field(default=5432)


class PostgreSQLConnectionTemplate(DatabaseConnectionTemplate[PostgreSQLConnectionConfiguration]):

    def get_type(self) -> str:
        return "postgres"

    def get_configuration_type(self) -> Type[PostgreSQLConnectionConfiguration]:
        return PostgreSQLConnectionConfiguration
    
    def get_connection(self, configuration: PostgreSQLConnectionConfiguration) -> PostgresqlDatabase:

        
        return PostgresqlDatabase(configuration.db_name,
            user=configuration.username, 
            host=configuration.hostname, 
            port=configuration.port, 
            password=configuration.password)


@dataclass
class SQLiteConnectionConfiguration:
    filename: str = field(default=':memory:')


class SQLiteConnectionTemplate(DatabaseConnectionTemplate[SQLiteConnectionConfiguration]):

    def get_type(self) -> str:
        return "sqlite"

    def get_configuration_type(self) -> Type[SQLiteConnectionConfiguration]:
        return SQLiteConnectionConfiguration
    
    def get_connection(self, configuration: SQLiteConnectionConfiguration) -> SqliteDatabase:
        pragmas = {'journal_mode': 'wal'}
        return SqliteDatabase(configuration.filename, pragmas=pragmas)

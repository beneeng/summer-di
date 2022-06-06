

from queue import Queue
from typing import Any, Dict, Iterable, Type
from summer.application.context_extension import ContextExtension
from summer.database.database_connection_factory import DatabaseConnectionFactory
from summer.database.migration_manager import MigrationManager
from peewee import Model

class DatabaseContextExtension(ContextExtension):

    def __init__(self) -> None:
        super().__init__()
        self._entities = Queue()

    def get_beans(self) -> Iterable[Any]:
        return [MigrationManager, DatabaseConnectionFactory] 

    def register_entity(self, entity: Type[Model]):
        self._entities.put(entity)

    def process_beans(self, beans: Dict[str, Any]):
        connection_factory = None
        migration_manager = None
        for _, bean in beans.items():
            if isinstance(bean, DatabaseConnectionFactory):
                connection_factory = bean
            if isinstance(bean, MigrationManager):
                migration_manager = bean
        
        if migration_manager is None or connection_factory is None:
            return
        
        self._register_entities(connection_factory)
        migration_manager.run_migrations()



    def _register_entities(self, connection_factory: DatabaseConnectionFactory):
        for entity in self._entities.queue:
            connection_factory.bind_entity(entity)
    
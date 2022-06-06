

from abc import abstractmethod
from peewee import Database
from playhouse.migrate import SchemaMigrator


class Migration:

    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def migrate(self, db: Database, mogrator: SchemaMigrator):
        pass

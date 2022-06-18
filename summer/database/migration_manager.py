

from typing import List
from summer.bean_strereotype import BeanStereotype
from summer.database.database_connection_factory import DatabaseConnectionFactory
from summer.database.entities import BaseModelWithId
from summer.database.migration import Migration as ScriptedMigration
from summer.summer_logging import _SUMMER_LOGGER, get_summer_logger
from peewee import PostgresqlDatabase, MySQLDatabase, SqliteDatabase, Database, CharField, DateTimeField
from playhouse.migrate import PostgresqlMigrator, MySQLMigrator, SqliteMigrator, SchemaMigrator
import datetime


class MigrationZero(ScriptedMigration):
    def name(self) -> str:
        return "0"

    def migrate(self, db: Database, migrator: SchemaMigrator):
        pass

class Migration(BaseModelWithId):
    name = CharField()
    applied = DateTimeField()

class MigrationManager(BeanStereotype):

    MIGRATORS = {
            PostgresqlDatabase: PostgresqlMigrator,
            MySQLDatabase: MySQLMigrator,
            SqliteDatabase: SqliteMigrator
    }

    def __init__(self, migrations: List[ScriptedMigration], connection_factory: DatabaseConnectionFactory) -> None:
        super().__init__()
        self._migrations = sorted(migrations, key=lambda x: x.name()) if len(migrations) > 0 else [MigrationZero()]
        self._connection_factory = connection_factory

    def run_migrations(self):
        self._connection_factory.bind_entity(Migration)
        database = self._connection_factory.get_database()
        existing_migrations = Migration.select().order_by(Migration.name.desc())
        existing_migration_count = existing_migrations.count()
        get_summer_logger().info("Found %s already applied migrations, %s total", existing_migration_count, len(self._migrations))

        if existing_migration_count == 0:
            latest_migration = self._migrations[-1]
            Migration.create(name=latest_migration.name, applied=datetime.datetime.now())
        
        else:
            max_migration = existing_migrations[0]
            for migration in self._migrations:
                if migration.name() > max_migration.name:
                    get_summer_logger().info("applying migration \"%s\"", migration.name())
                    migration.migrate(database, self.get_migrator(database))
                    Migration.create(name=migration.name(), applied=datetime.datetime.now())


    def get_migrator(self, database: Database) -> SchemaMigrator:
        for db, migrator in self.MIGRATORS.items():
            if isinstance(database, db):
                return migrator(database)

        raise ValueError("Unknown database type %s", type(db))

    
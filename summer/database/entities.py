
from peewee import Model, DatabaseProxy, UUIDField
import uuid

class DatabaseException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class BaseModel(Model):
    class Meta:
        database = DatabaseProxy()

class BaseModelWithId(BaseModel):
    id = UUIDField(primary_key=True, index=True, default=uuid.uuid4)


 

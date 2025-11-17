from typing import Annotated

from bson import ObjectId
from pydantic import BaseModel, ConfigDict
from pydantic.functional_validators import BeforeValidator


def _validate_object_id(value: str | ObjectId) -> str:
    if isinstance(value, ObjectId):
        return str(value)
    if ObjectId.is_valid(value):
        return str(ObjectId(value))
    raise ValueError("Invalid ObjectId")


PyObjectId = Annotated[str, BeforeValidator(_validate_object_id)]


class MongoModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

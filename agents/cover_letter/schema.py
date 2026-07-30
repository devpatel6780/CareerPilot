from pydantic import BaseModel


class CoverLetter(BaseModel):
    cover_letter: str = ""

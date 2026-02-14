from pydantic import BaseModel, field_validator, model_validator
from typing import Optional

class AnalyzeRequest(BaseModel):
    text: Optional[str] = None
    imageUrl: Optional[str] = None
    
    @field_validator('text')
    @classmethod
    def text_min_length(cls, v):
        if v is not None and len(v) < 5:
            raise ValueError('Text must be at least 5 characters')
        return v
    
    @model_validator(mode='after')
    def validate_at_least_one(self) -> 'AnalyzeRequest':
        if not self.text and not self.imageUrl:
            raise ValueError('Either text or imageUrl must be provided')
        return self
    
    @field_validator('imageUrl')
    @classmethod
    def validate_url(cls, v):
        if v is not None and not v.startswith(('http://', 'https://')):
            raise ValueError('Image URL must be a valid URL')
        return v

from __future__ import annotations

from pydantic import BaseModel, Field


class SiteSettingOut(BaseModel):
    key: str
    value: str

    model_config = {"from_attributes": True}


class SiteSettingUpdate(BaseModel):
    value: str


class HomepageBannerCreate(BaseModel):
    image_url: str = ""
    title: str = ""
    link: str = ""
    display_order: int = 0


class HomepageBannerUpdate(BaseModel):
    image_url: str | None = None
    title: str | None = None
    link: str | None = None
    display_order: int | None = None
    enabled: bool | None = None


class HomepageBannerOut(BaseModel):
    id: int
    image_url: str
    title: str
    link: str
    display_order: int
    enabled: bool

    model_config = {"from_attributes": True}


class ScrollingMessageCreate(BaseModel):
    text: str = Field(min_length=1, max_length=500)
    display_order: int = 0


class ScrollingMessageUpdate(BaseModel):
    text: str | None = None
    display_order: int | None = None
    enabled: bool | None = None


class ScrollingMessageOut(BaseModel):
    id: int
    text: str
    display_order: int
    enabled: bool

    model_config = {"from_attributes": True}


class EducationalContentCreate(BaseModel):
    game_type_id: int | None = None
    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    how_it_works: str = ""
    example: str = ""
    probability_explanation: str = ""
    rules: str = ""


class EducationalContentOut(BaseModel):
    id: int
    game_type_id: int | None
    title: str
    description: str
    how_it_works: str
    example: str
    probability_explanation: str
    rules: str

    model_config = {"from_attributes": True}


class EducationalContentUpdate(BaseModel):
    game_type_id: int | None = None
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    how_it_works: str | None = None
    example: str | None = None
    probability_explanation: str | None = None
    rules: str | None = None


class FAQCreate(BaseModel):
    question: str = Field(min_length=1, max_length=300)
    answer: str = Field(min_length=1)
    display_order: int = 0


class FAQUpdate(BaseModel):
    question: str | None = None
    answer: str | None = None
    display_order: int | None = None
    enabled: bool | None = None


class FAQOut(BaseModel):
    id: int
    question: str
    answer: str
    display_order: int
    enabled: bool

    model_config = {"from_attributes": True}

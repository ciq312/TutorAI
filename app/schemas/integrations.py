from datetime import datetime
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, model_validator, field_validator
from app.schemas.data import Input, StudentCreate


class CalendarSelection(Input):
    calendar_id: str = Field(min_length=1, max_length=500)
    mode: Literal['mixed', 'teaching'] = 'mixed'


class CalendarSettings(Input):
    calendars: list[CalendarSelection] = Field(max_length=30)

    @model_validator(mode='after')
    def unique(self):
        if len({c.calendar_id for c in self.calendars}) != len(self.calendars):
            raise ValueError('Duplicate calendar')
        return self


class NotificationSettings(Input):
    brief_enabled: bool = True
    results_enabled: bool = True
    reminder_enabled: bool = True
    before_minutes: int = Field(default=30, ge=0, le=10080)
    after_minutes: int = Field(default=15, ge=0, le=1440)
    timezone: str = 'Europe/Minsk'

    @field_validator('timezone')
    @classmethod
    def valid_timezone(cls, value):
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError):
            raise ValueError('Unknown timezone') from None
        return value


class EventDecision(Input):
    action: Literal['link', 'ignore']
    student_id: UUID | None = None
    new_student: StudentCreate | None = None
    whole_series: bool = False

    @model_validator(mode='after')
    def target(self):
        if self.action == 'link' and (self.student_id is None) == (self.new_student is None):
            raise ValueError('Choose one existing or new student')
        if self.action == 'ignore' and (self.student_id or self.new_student):
            raise ValueError('Ignored event cannot have a student')
        return self


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    calendar_id: str
    external_id: str
    series_id: str | None
    title: str
    starts_at: datetime | None
    ends_at: datetime | None
    status: str
    decision: str
    lesson_id: UUID | None
    suggested_students: list[dict] = Field(default_factory=list)
    calendar_mode: str = 'mixed'


class ApprovalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    event_id: UUID
    homework: str
    description: str
    status: str
    expires_at: datetime
    event_title: str = ''
    starts_at: datetime | None = None
    visibility_notice: str = 'Описание может быть видно участникам события. Изменится только это занятие.'

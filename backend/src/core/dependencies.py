from backend.src.services.weather_service import WeatherService
from backend.src.services.calendar_service import CalendarService
from backend.src.services.email_service import EmailService
from backend.src.services.notetaker_service import NotetakerService
from backend.src.services.meeting_service import MeetingService


weather_service = WeatherService()
calendar_service = CalendarService()
email_service = EmailService()
notetaker_service = NotetakerService()
meeting_service = MeetingService()

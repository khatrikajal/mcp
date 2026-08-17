from server.services.weather_service import WeatherService
from server.services.calendar_service import CalendarService
from server.services.email_service import EmailService
from server.services.notetaker_service import NotetakerService
from server.services.meeting_service import MeetingService


weather_service = WeatherService()
calendar_service = CalendarService()
email_service = EmailService()
notetaker_service = NotetakerService()
meeting_service = MeetingService()

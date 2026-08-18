"""
Database seeding script.

Run this to create a default admin user and organization.
Usage: python -m server.api.seed
"""
from backend.src.db.connection import SessionLocal, init_db
from backend.src.db.models import User, Organization, Agent, UserRole, AgentToolPermission, PermissionLevel
from backend.src.api.auth_utils import get_password_hash


def seed_database():
    """Seed the database with initial data."""
    # Initialize database (create tables)
    init_db()
    print("Database tables created!")

    db = SessionLocal()

    try:
        # Check if data already exists
        existing_org = db.query(Organization).first()
        if existing_org:
            print("Database already seeded. Skipping...")
            return

        # Create default organization
        default_org = Organization(
            name="Default Organization",
            plan_type="pro"
        )
        db.add(default_org)
        db.flush()
        print(f"Created organization: {default_org.name}")

        # Create admin user
        admin_user = User(
            email="admin@example.com",
            password_hash=get_password_hash("admin123"),
            name="Admin User",
            role=UserRole.ADMIN,
            organization_id=default_org.id
        )
        db.add(admin_user)
        db.flush()
        print(f"Created admin user: {admin_user.email} (password: admin123)")

        # Create default agent
        default_agent = Agent(
            user_id=admin_user.id,
            organization_id=default_org.id,
            name="General Assistant",
            description="A versatile AI assistant with access to all tools",
            system_instructions="You are a helpful AI assistant. Help users with their tasks using the available tools."
        )
        db.add(default_agent)
        db.flush()
        print(f"Created default agent: {default_agent.name}")

        # Add all tool permissions for default agent
        tools = [
            "get_current_datetime",
            "list_calendar_events",
            "create_calendar_event",
            "get_weather",
            "send_email",
            "join_next_meeting",
            "join_meeting",
            "get_notetaker_status",
            "list_notetakers",
            "get_meeting_transcript",
            "get_meeting_summary"
        ]

        for tool_name in tools:
            permission = AgentToolPermission(
                agent_id=default_agent.id,
                tool_name=tool_name,
                permission_level=PermissionLevel.ENABLED
            )
            db.add(permission)

        print(f"Added {len(tools)} tool permissions to default agent")

        # Commit all changes
        db.commit()
        print("\nDatabase seeded successfully!")
        print("\nYou can now login with:")
        print("  Email: admin@example.com")
        print("  Password: admin123")

    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()

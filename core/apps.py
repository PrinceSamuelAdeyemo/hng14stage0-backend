from django.apps import AppConfig
import os


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    
    def ready(self):
        """Run migrations when the app starts (for Vercel)"""
        # Only run on Vercel (when DATABASE_URL is set)
        if os.environ.get('DATABASE_URL'):
            try:
                from django.core.management import call_command
                from django.db import connection
                
                # Test database connection first
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                
                # If connection works, run migrations
                call_command('migrate', verbosity=0, interactive=False)
                print("✓ Migrations completed successfully")
            except Exception as e:
                print(f"Migration info: {e}")
                # Don't fail if migrations have issues
                pass

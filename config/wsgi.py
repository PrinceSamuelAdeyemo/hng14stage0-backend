"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Get base application
base_application = get_wsgi_application()

# Wrap with migration middleware if using Neon/PostgreSQL
if os.environ.get('DATABASE_URL'):
    import sys
    from django.core.management import call_command
    from django.db import connection, connections
    
    _migrations_run = False
    
    def run_migrations():
        global _migrations_run
        if _migrations_run:
            return
        
        try:
            print("🔄 Running database migrations...", file=sys.stderr, flush=True)
            connections.close_all()
            
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            
            call_command('migrate', verbosity=0, interactive=False)
            _migrations_run = True
            print("✓ Migrations completed successfully", file=sys.stderr, flush=True)
        except Exception as e:
            _migrations_run = True
            print(f"⚠ Migration info: {str(e)[:200]}", file=sys.stderr, flush=True)
    
    class MigrationMiddleware:
        def __init__(self, wsgi_app):
            self.wsgi_app = wsgi_app
            run_migrations()
        
        def __call__(self, environ, start_response):
            run_migrations()
            return self.wsgi_app(environ, start_response)
    
    application = MigrationMiddleware(base_application)
else:
    application = base_application

#!/usr/bin/env python
"""
Vercel build script for Django + Neon PostgreSQL
This ensures migrations run during the build phase
"""
import os
import sys
import subprocess

def run_command(cmd, description):
    """Run a shell command and print status"""
    print(f"\n{'='*60}")
    print(f"📍 {description}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"⚠️  {description} completed with warnings/errors")
    return result.returncode

def main():
    print("🚀 Starting Vercel build process...")
    
    # Set environment
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    os.environ['PYTHONUNBUFFERED'] = '1'
    
    # Step 1: Install dependencies
    if run_command('pip install -r requirements.txt', 'Installing dependencies') != 0:
        print("❌ Failed to install dependencies")
        return 1
    
    # Step 2: Run migrations
    if os.environ.get('DATABASE_URL'):
        print("\n" + "="*60)
        print("🗄️  Running database migrations to Neon PostgreSQL...")
        print("="*60)
        result = run_command(
            'python manage.py migrate --no-input',
            'Database migrations'
        )
        if result != 0:
            print("⚠️  Migrations may have issues, app will retry at runtime")
    else:
        print("\n⚠️  No DATABASE_URL found, skipping migrations")
    
    # Step 3: Collect static files (optional, for completeness)
    try:
        run_command(
            'python manage.py collectstatic --no-input --clear',
            'Collecting static files'
        )
    except Exception as e:
        print(f"⚠️  Static files collection note: {e}")
    
    print("\n" + "="*60)
    print("✅ Build process completed!")
    print("="*60)
    return 0

if __name__ == '__main__':
    sys.exit(main())

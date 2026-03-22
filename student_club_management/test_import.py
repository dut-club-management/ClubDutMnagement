#!/usr/bin/env python3
"""
Test script to verify app can be imported correctly
"""
try:
    from app import create_app
    app = create_app()
    print("✅ App import successful!")
    print(f"✅ App name: {app.name}")
    print(f"✅ App debug: {app.debug}")
except Exception as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()

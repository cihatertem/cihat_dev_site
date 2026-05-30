#!/bin/bash
export SECRET_KEY='test-secret-key-for-running-tests'
uv run python manage.py test --parallel 8 --settings=cihat_dev.test_settings

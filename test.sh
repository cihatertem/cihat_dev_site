#!/bin/bash
uv run python manage.py test --parallel 8 --settings=cihat_dev.test_settings

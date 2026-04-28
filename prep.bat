@echo off
echo Starting Data Preparation...
python scripts/generate_mock_data.py
if %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%
echo Starting Preprocessing...
python scripts/preprocess.py
if %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%
echo Starting Model Training...
python scripts/train_model.py
if %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%
echo Generating Replay Events...
python scripts/generate_replay_events.py
if %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%
echo All preparation steps completed successfully!

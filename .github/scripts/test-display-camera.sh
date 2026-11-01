#!/usr/bin/env bash
set -euo pipefail
if [ "$VERIFY_DISPLAY_BASELINE" = true ]; then
  git fetch --depth=1 origin f7cd5cb6a4b77420e941b3f0eb234a6d08282483
  controller=app/src/main/java/com/luxisoft/realityos/MetaDisplayController.kt
  capture=app/src/main/java/com/luxisoft/realityos/host/operations/CaptureOperations.kt
  cp "android/$controller" /tmp/fixed-display-controller.kt
  cp "android/$capture" /tmp/fixed-display-capture.kt
  trap 'cp /tmp/fixed-display-controller.kt "android/$controller"; cp /tmp/fixed-display-capture.kt "android/$capture"' EXIT
  git show "f7cd5cb6a4b77420e941b3f0eb234a6d08282483:android/$controller" > "android/$controller"
  git show "f7cd5cb6a4b77420e941b3f0eb234a6d08282483:android/$capture" > "android/$capture"
  if (cd android && ./gradlew :app:connectedDebugAndroidTest '-Pandroid.testInstrumentationRunnerArguments.class=com.luxisoft.realityos.DisplaySearchCameraTest#activeOperationShowsFeedbackInsteadOfIgnoringSearchButton,com.luxisoft.realityos.DisplaySearchCameraTest#generationChangeWhileCameraStartsDoesNotLeaveBusyLatched'); then
    echo 'The previous implementation unexpectedly passed the regression cases.'
    exit 1
  fi
  cp /tmp/fixed-display-controller.kt "android/$controller"
  cp /tmp/fixed-display-capture.kt "android/$capture"
  trap - EXIT
  python3 - <<'PY'
from pathlib import Path
import xml.etree.ElementTree as ET
expected = {
    'activeOperationShowsFeedbackInsteadOfIgnoringSearchButton': 'DISPLAY_SEARCH_BUSY_NO_FEEDBACK',
    'generationChangeWhileCameraStartsDoesNotLeaveBusyLatched': 'DISPLAY_CAMERA_BUSY_NOT_RELEASED',
}
failed = set()
for path in Path('android/app/build/outputs/androidTest-results').rglob('*.xml'):
    for case in ET.parse(path).iter('testcase'):
        failure = case.find('failure')
        if failure is not None and expected.get(case.get('name'), 'NO_MATCH') in ET.tostring(failure, encoding='unicode'):
            failed.add(case.get('name'))
assert expected.keys() <= failed, f'Baseline did not reproduce the expected failures: {failed}'
print('Both Display regressions reproduced on the previous implementation.')
PY
fi
cd android
./gradlew :app:connectedDebugAndroidTest --stacktrace --info || { adb logcat -d -v brief | tail -n 1000; exit 1; }

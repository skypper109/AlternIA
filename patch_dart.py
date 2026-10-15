import os

path = "../det-mobile/lib/features/culture/exploration/presentation/screens/cultural_sage_chat_page.dart"

with open(path, "r") as f:
    content = f.read()

target = """        _scrollToBottom();
        await _tts.speak(reply);"""

replacement = """        _scrollToBottom();
        _simliService.generateSageVideo(text: reply);
        await _tts.speak(reply);"""

if target in content:
    content = content.replace(target, replacement)
    with open(path, "w") as f:
        f.write(content)
    print("Dart file patched successfully.")
else:
    print("Target still not found.")

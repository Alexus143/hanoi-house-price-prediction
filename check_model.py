import google.generativeai as genai
import os

# Thay API KEY của bạn vào đây
os.environ["GOOGLE_API_KEY"] = "AIzaSyDZknlLHIsQeaO07uou-Sa_dkIMkupv9ao"
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

print("Danh sách các model hỗ trợ tạo nội dung (generateContent):")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f"- {m.name}")
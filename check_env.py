# check_env.py
import os

def check_env_var(var_name: str):
    value = os.getenv(var_name)
    if value:
        print(f"{var_name} = {value}")
    else:
        print(f"{var_name} chưa được set hoặc không đọc được trong session này.")

if __name__ == "__main__":
    print("=== Kiểm tra biến môi trường OPENAI_API_KEY ===")
    check_env_var("OPENAI_API_KEY")

    print("\n=== Kiểm tra các biến liên quan Ollama (nếu có) ===")
    check_env_var("OLLAMA_HOST")
    check_env_var("OLLAMA_API_KEY")
